"""
Pipeline ETL Lengkap: Ekstraksi, Transformasi, dan Loading ke DWH MySQL
Penyusun: Anggota 3 (AI-Driven ETL & Database Engineer)

Alur Eksekusi:
1. Extract: Membaca data bersih dari 'data/staging/'.
2. Transform:
   - Generate tabel dimensi kalender (dim_date).
   - Generate dimensi lookup (dim_order_status, dim_payments).
   - Transformasi AI pada ulasan pelanggan (dim_reviews).
   - Mapping Surrogate Keys untuk menghubungkan tabel fakta ke dimensi.
   - Perhitungan metrik logistik (shipping_duration_days, delivery_delay_days, is_delayed).
3. Load:
   - Memasukkan data ke MySQL 'dwh_olist' sesuai urutan dependensi foreign key.
   - Verifikasi total baris data yang berhasil dimuat.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# Konfigurasi encoding console Windows ke UTF-8
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from database_config import get_db_engine
from ai_transformer import enrich_reviews_with_sentiment

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STAGING_DIR = os.path.join(BASE_DIR, 'data', 'staging')

def run_etl():
    print("=" * 75)
    print("🚀 MEMULAI PIPELINE DATA WAREHOUSE ETL (MYSQL 8.x)")
    print("=" * 75)
    
    engine = get_db_engine()
    
    # -------------------------------------------------------------------------
    # 1. EXTRACT: Membaca dataset bersih dari data/staging/
    # -------------------------------------------------------------------------
    print("\n📥 [FASE 1: EXTRACT] Membaca data bersih dari data/staging/ ...")
    df_customers = pd.read_csv(os.path.join(STAGING_DIR, 'clean_customers.csv'))
    df_sellers = pd.read_csv(os.path.join(STAGING_DIR, 'clean_sellers.csv'))
    df_products = pd.read_csv(os.path.join(STAGING_DIR, 'clean_products.csv'))
    df_orders = pd.read_csv(os.path.join(STAGING_DIR, 'clean_orders.csv'))
    df_order_items = pd.read_csv(os.path.join(STAGING_DIR, 'clean_order_items.csv'))
    df_payments = pd.read_csv(os.path.join(STAGING_DIR, 'clean_order_payments.csv'))
    df_reviews = pd.read_csv(os.path.join(STAGING_DIR, 'clean_order_reviews.csv'))
    print("✅ Seluruh data staging berhasil dimuat ke memori.")

    # -------------------------------------------------------------------------
    # 2. TRANSFORM & LOAD TABEL DIMENSI
    # -------------------------------------------------------------------------
    print("\n⚙️ [FASE 2: TRANSFORM & LOAD DIMENSIONS]")
    
    # A. DIM_DATE
    print("📅 1. Memproses dim_date ...")
    purchase_dates = pd.to_datetime(df_orders['order_purchase_timestamp'], errors='coerce').dropna()
    min_date = purchase_dates.min().floor('D')
    max_date = purchase_dates.max().ceil('D')
    all_dates = pd.date_range(start=min_date, end=max_date, freq='D')
    
    df_dim_date = pd.DataFrame({'full_date': all_dates})
    df_dim_date['date_key'] = df_dim_date['full_date'].dt.strftime('%Y%m%d').astype(int)
    df_dim_date['day'] = df_dim_date['full_date'].dt.day
    df_dim_date['month'] = df_dim_date['full_date'].dt.month
    df_dim_date['month_name'] = df_dim_date['full_date'].dt.strftime('%B')
    df_dim_date['quarter'] = df_dim_date['full_date'].dt.quarter
    df_dim_date['year'] = df_dim_date['full_date'].dt.year
    df_dim_date['day_of_week'] = df_dim_date['full_date'].dt.strftime('%A')
    df_dim_date['is_weekend'] = df_dim_date['day_of_week'].isin(['Saturday', 'Sunday']).astype(int)
    df_dim_date['full_date'] = df_dim_date['full_date'].dt.strftime('%Y-%m-%d')
    
    df_dim_date.to_sql('dim_date', con=engine, if_exists='append', index=False, chunksize=5000)
    print(f"   -> dim_date terisi: {len(df_dim_date):,} baris.")

    # B. DIM_CUSTOMERS
    print("👤 2. Memproses dim_customers ...")
    df_dim_customers = df_customers[['customer_id', 'customer_unique_id', 'customer_city', 'customer_state', 'customer_zip_code_prefix']]
    df_dim_customers.to_sql('dim_customers', con=engine, if_exists='append', index=False, chunksize=5000)
    print(f"   -> dim_customers terisi: {len(df_dim_customers):,} baris.")
    
    # Query balik surrogate key customer untuk relasi tabel fakta
    customer_map = pd.read_sql("SELECT customer_key, customer_id FROM dim_customers", con=engine)

    # C. DIM_PRODUCTS
    print("📦 3. Memproses dim_products ...")
    df_dim_products = df_products[[
        'product_id', 'product_category_name', 'product_category_name_english',
        'product_weight_g', 'product_length_cm', 'product_height_cm', 'product_width_cm'
    ]]
    df_dim_products.to_sql('dim_products', con=engine, if_exists='append', index=False, chunksize=5000)
    print(f"   -> dim_products terisi: {len(df_dim_products):,} baris.")
    product_map = pd.read_sql("SELECT product_key, product_id FROM dim_products", con=engine)

    # D. DIM_SELLERS
    print("🏬 4. Memproses dim_sellers ...")
    df_dim_sellers = df_sellers[['seller_id', 'seller_city', 'seller_state', 'seller_zip_code_prefix']]
    df_dim_sellers.to_sql('dim_sellers', con=engine, if_exists='append', index=False, chunksize=5000)
    print(f"   -> dim_sellers terisi: {len(df_dim_sellers):,} baris.")
    seller_map = pd.read_sql("SELECT seller_key, seller_id FROM dim_sellers", con=engine)

    # E. DIM_ORDER_STATUS
    print("🔄 5. Memproses dim_order_status ...")
    statuses = df_orders['order_status'].dropna().unique()
    df_dim_status = pd.DataFrame({'order_status_name': statuses})
    df_dim_status.to_sql('dim_order_status', con=engine, if_exists='append', index=False)
    print(f"   -> dim_order_status terisi: {len(df_dim_status):,} baris.")
    status_map = pd.read_sql("SELECT status_key, order_status_name FROM dim_order_status", con=engine)

    # F. DIM_PAYMENTS
    print("💳 6. Memproses dim_payments ...")
    df_dim_pay = df_payments[['payment_type', 'payment_installments_group']].drop_duplicates().reset_index(drop=True)
    df_dim_pay.to_sql('dim_payments', con=engine, if_exists='append', index=False)
    print(f"   -> dim_payments terisi: {len(df_dim_pay):,} baris.")
    payment_map = pd.read_sql("SELECT payment_key, payment_type, payment_installments_group FROM dim_payments", con=engine)

    # G. DIM_REVIEWS (DIPERKAYA OLEH AI TRANSFORMER)
    print("⭐ 7. Memproses dim_reviews & Modul AI Sentiment ...")
    df_reviews_enriched = enrich_reviews_with_sentiment(df_reviews, use_ai_sample_count=20)
    df_dim_reviews = df_reviews_enriched[[
        'review_id', 'review_score', 'review_comment_title',
        'review_comment_message', 'sentiment_category'
    ]]
    df_dim_reviews.to_sql('dim_reviews', con=engine, if_exists='append', index=False, chunksize=5000)
    print(f"   -> dim_reviews terisi: {len(df_dim_reviews):,} baris.")
    review_map = pd.read_sql("SELECT review_key, review_id FROM dim_reviews", con=engine)

    # -------------------------------------------------------------------------
    # 3. TRANSFORM & LOAD TABEL FAKTA (FACT_ORDER_ITEMS)
    # -------------------------------------------------------------------------
    print("\n📊 [FASE 3: TRANSFORM & LOAD FACT TABLE]")
    print("🔗 Menggabungkan dimensi dan menghitung metrik logistik...")
    
    # Siapkan payment per order (ambil transaksi payment_sequential pertama per order untuk konsistensi grain)
    primary_payments = df_payments.sort_values(by=['order_id', 'payment_sequential']).drop_duplicates(subset=['order_id'])
    primary_payments = primary_payments.merge(payment_map, on=['payment_type', 'payment_installments_group'], how='left')
    
    # Siapkan review per order
    reviews_with_order = df_reviews_enriched[['order_id', 'review_id']].merge(review_map, on='review_id', how='left')
    reviews_with_order = reviews_with_order.drop_duplicates(subset=['order_id'])

    # Gabungkan order_items dengan orders
    fact_df = df_order_items.merge(
        df_orders[[
            'order_id', 'customer_id', 'order_status',
            'order_purchase_timestamp', 'order_delivered_customer_date',
            'order_estimated_delivery_date'
        ]],
        on='order_id',
        how='inner'
    )
    
    # Hitung order_date_key
    fact_df['order_date_key'] = pd.to_datetime(fact_df['order_purchase_timestamp']).dt.strftime('%Y%m%d').astype(int)
    
    # Hitung metrik logistik
    ts_purchase = pd.to_datetime(fact_df['order_purchase_timestamp'])
    ts_delivered = pd.to_datetime(fact_df['order_delivered_customer_date'])
    ts_estimated = pd.to_datetime(fact_df['order_estimated_delivery_date'])
    
    # Durasi pengiriman aktual (dalam satuan hari)
    fact_df['shipping_duration_days'] = np.where(
        ts_delivered.notnull(),
        (ts_delivered - ts_purchase).dt.total_seconds() / 86400.0,
        np.nan
    ).round(2)
    
    # Keterlambatan logistik terhadap estimasi (dalam hari, positif = telat)
    fact_df['delivery_delay_days'] = np.where(
        ts_delivered.notnull(),
        (ts_delivered - ts_estimated).dt.total_seconds() / 86400.0,
        np.nan
    ).round(2)
    
    fact_df['is_delayed'] = np.where(fact_df['delivery_delay_days'] > 0, 1, 0)
    
    # Mapping Foreign Keys
    fact_df = fact_df.merge(customer_map, on='customer_id', how='left')
    fact_df = fact_df.merge(product_map, on='product_id', how='left')
    fact_df = fact_df.merge(seller_map, on='seller_id', how='left')
    fact_df = fact_df.merge(status_map.rename(columns={'order_status_name': 'order_status', 'status_key': 'order_status_key'}), on='order_status', how='left')
    fact_df = fact_df.merge(primary_payments[['order_id', 'payment_key']], on='order_id', how='left')
    fact_df = fact_df.merge(reviews_with_order[['order_id', 'review_key']], on='order_id', how='left')
    
    # Pemilihan kolom final tabel fakta sesuai skema DDL
    final_fact_cols = [
        'customer_key', 'product_key', 'seller_key', 'order_date_key',
        'order_status_key', 'payment_key', 'review_key',
        'order_id', 'order_item_id', 'price', 'freight_value',
        'total_item_value', 'shipping_duration_days', 'delivery_delay_days', 'is_delayed'
    ]
    
    fact_to_load = fact_df[final_fact_cols].copy()
    
    # Pastikan foreign key non-null terisi dengan benar
    default_payment_key = payment_map['payment_key'].iloc[0]
    fact_to_load['payment_key'] = fact_to_load['payment_key'].fillna(default_payment_key).astype(int)
    
    print(f"🚀 Memuat {len(fact_to_load):,} baris data ke fact_order_items (chunksize=10000)...")
    fact_to_load.to_sql('fact_order_items', con=engine, if_exists='append', index=False, chunksize=10000)
    print("✅ Seluruh data tabel fakta berhasil dimuat ke MySQL!")

    # -------------------------------------------------------------------------
    # 4. VERIFIKASI AKHIR
    # -------------------------------------------------------------------------
    print("\n🔍 [FASE 4: VERIFIKASI AKHIR DATA WAREHOUSE]")
    tables = [
        'dim_date', 'dim_customers', 'dim_products', 'dim_sellers',
        'dim_order_status', 'dim_payments', 'dim_reviews', 'fact_order_items'
    ]
    for tbl in tables:
        cnt = pd.read_sql(f"SELECT COUNT(*) AS total FROM {tbl}", con=engine).iloc[0]['total']
        print(f"   -> Tabel '{tbl:<18}': {cnt:>10,d} baris")
        
    print("\n" + "=" * 75)
    print("🎉 ETL PIPELINE SELESAI DENGAN SUKSES! DWH SIAP DIUJI DENGAN QUERY ANALITIK.")
    print("=" * 75)

if __name__ == "__main__":
    run_etl()
