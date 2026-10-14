"""
Script Otomatisasi Pembersihan Data (Data Cleansing Pipeline)
Penyusun: Anggota 2 (Data Quality & Cleansing Engineer)
Dataset: Brazilian E-Commerce by Olist (Kaggle)
Tujuan:
1. Membaca data mentah dari folder 'data/raw/'.
2. Menerapkan standarisasi format teks (title case, uppercase state, zip codes).
3. Menyelaraskan format tanggal menjadi 'YYYY-MM-DD HH:MM:SS'.
4. Menggabungkan kategori produk dengan terjemahan bahasa Inggris dan menangani nilai null.
5. Mengelompokkan cicilan pembayaran ke dalam 'payment_installments_group'.
6. Membersihkan komentar ulasan dan menghapus duplikasi.
7. Mengekspor dataset bersih berkualitas tinggi ke 'data/staging/'.
"""

import os
import sys
import pandas as pd
import numpy as np

# Konfigurasi encoding console Windows ke UTF-8
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
STAGING_DIR = os.path.join(BASE_DIR, 'data', 'staging')

os.makedirs(STAGING_DIR, exist_ok=True)

print("=" * 70)
print("🚀 MEMULAI PIPELINE PEMBERSIHAN DATA (DATA CLEANSING) - ANGGOTA 2")
print("=" * 70)
print(f"Direktori Sumber Raw   : {RAW_DIR}")
print(f"Direktori Target Staging: {STAGING_DIR}\n")

# ------------------------------------------------------------------------------
# 1. PEMBERSIHAN TABEL PELANGGAN (CUSTOMERS)
# ------------------------------------------------------------------------------
print("📦 [1/7] Membersihkan olist_customers_dataset.csv ...")
df_cust = pd.read_csv(os.path.join(RAW_DIR, 'olist_customers_dataset.csv'))
initial_cust_rows = len(df_cust)

df_cust['customer_id'] = df_cust['customer_id'].astype(str).str.strip()
df_cust['customer_unique_id'] = df_cust['customer_unique_id'].astype(str).str.strip()
df_cust['customer_zip_code_prefix'] = df_cust['customer_zip_code_prefix'].astype(str).str.zfill(5)
df_cust['customer_city'] = df_cust['customer_city'].astype(str).str.strip().str.title()
df_cust['customer_state'] = df_cust['customer_state'].astype(str).str.strip().str.upper()

# Hapus duplikasi jika ada pada natural key customer_id
df_cust = df_cust.drop_duplicates(subset=['customer_id'])
cust_output_path = os.path.join(STAGING_DIR, 'clean_customers.csv')
df_cust.to_csv(cust_output_path, index=False, encoding='utf-8')
print(f"   -> Selesai: {len(df_cust):,} baris diekspor ke clean_customers.csv (Awal: {initial_cust_rows:,})")


# ------------------------------------------------------------------------------
# 2. PEMBERSIHAN TABEL PENJUAL (SELLERS)
# ------------------------------------------------------------------------------
print("\n📦 [2/7] Membersihkan olist_sellers_dataset.csv ...")
df_sellers = pd.read_csv(os.path.join(RAW_DIR, 'olist_sellers_dataset.csv'))
initial_sellers_rows = len(df_sellers)

df_sellers['seller_id'] = df_sellers['seller_id'].astype(str).str.strip()
df_sellers['seller_zip_code_prefix'] = df_sellers['seller_zip_code_prefix'].astype(str).str.zfill(5)
df_sellers['seller_city'] = df_sellers['seller_city'].astype(str).str.strip().str.title()
df_sellers['seller_state'] = df_sellers['seller_state'].astype(str).str.strip().str.upper()

df_sellers = df_sellers.drop_duplicates(subset=['seller_id'])
sellers_output_path = os.path.join(STAGING_DIR, 'clean_sellers.csv')
df_sellers.to_csv(sellers_output_path, index=False, encoding='utf-8')
print(f"   -> Selesai: {len(df_sellers):,} baris diekspor ke clean_sellers.csv (Awal: {initial_sellers_rows:,})")


# ------------------------------------------------------------------------------
# 3. PEMBERSIHAN TABEL PRODUK & TERJEMAHAN KATEGORI (PRODUCTS)
# ------------------------------------------------------------------------------
print("\n📦 [3/7] Membersihkan olist_products_dataset.csv & product_category_name_translation.csv ...")
df_prod = pd.read_csv(os.path.join(RAW_DIR, 'olist_products_dataset.csv'))
df_trans = pd.read_csv(os.path.join(RAW_DIR, 'product_category_name_translation.csv'))
initial_prod_rows = len(df_prod)

# Kamus terjemahan manual tambahan untuk kategori yang belum terdaftar di Kaggle translation
extra_translations = {
    'pc_gamer': 'pc_gamer',
    'portateis_cozinha_e_preparadores_de_alimentos': 'small_appliances_kitchen_and_food_preparers'
}
for pt, en in extra_translations.items():
    if pt not in df_trans['product_category_name'].values:
        df_trans = pd.concat([df_trans, pd.DataFrame([{'product_category_name': pt, 'product_category_name_english': en}])], ignore_index=True)

df_prod['product_id'] = df_prod['product_id'].astype(str).str.strip()
df_prod['product_category_name'] = df_prod['product_category_name'].fillna('Unknown').astype(str).str.strip()

# Gabungkan terjemahan bahasa Inggris
df_prod = df_prod.merge(df_trans, on='product_category_name', how='left')
df_prod['product_category_name_english'] = df_prod['product_category_name_english'].fillna(
    df_prod['product_category_name']
)
df_prod.loc[df_prod['product_category_name'] == 'Unknown', 'product_category_name_english'] = 'Unknown'

# Tangani atribut fisik (bobot dan dimensi)
df_prod['product_weight_g'] = df_prod['product_weight_g'].fillna(0.0).round(2)
df_prod['product_length_cm'] = df_prod['product_length_cm'].fillna(0.0).round(2)
df_prod['product_height_cm'] = df_prod['product_height_cm'].fillna(0.0).round(2)
df_prod['product_width_cm'] = df_prod['product_width_cm'].fillna(0.0).round(2)

selected_prod_cols = [
    'product_id', 'product_category_name', 'product_category_name_english',
    'product_weight_g', 'product_length_cm', 'product_height_cm', 'product_width_cm'
]
df_prod_clean = df_prod[selected_prod_cols].drop_duplicates(subset=['product_id'])
prod_output_path = os.path.join(STAGING_DIR, 'clean_products.csv')
df_prod_clean.to_csv(prod_output_path, index=False, encoding='utf-8')
print(f"   -> Selesai: {len(df_prod_clean):,} baris diekspor ke clean_products.csv (Awal: {initial_prod_rows:,})")


# ------------------------------------------------------------------------------
# 4. PEMBERSIHAN TABEL PESANAN & STANDARISASI TANGGAL (ORDERS)
# ------------------------------------------------------------------------------
print("\n📦 [4/7] Membersihkan olist_orders_dataset.csv ...")
df_orders = pd.read_csv(os.path.join(RAW_DIR, 'olist_orders_dataset.csv'))
initial_orders_rows = len(df_orders)

df_orders['order_id'] = df_orders['order_id'].astype(str).str.strip()
df_orders['customer_id'] = df_orders['customer_id'].astype(str).str.strip()
df_orders['order_status'] = df_orders['order_status'].astype(str).str.strip().str.lower()

date_cols_orders = [
    'order_purchase_timestamp', 'order_approved_at',
    'order_delivered_carrier_date', 'order_delivered_customer_date',
    'order_estimated_delivery_date'
]

for col in date_cols_orders:
    df_orders[col] = pd.to_datetime(df_orders[col], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')

df_orders = df_orders.drop_duplicates(subset=['order_id'])
orders_output_path = os.path.join(STAGING_DIR, 'clean_orders.csv')
df_orders.to_csv(orders_output_path, index=False, encoding='utf-8')
print(f"   -> Selesai: {len(df_orders):,} baris diekspor ke clean_orders.csv (Awal: {initial_orders_rows:,})")


# ------------------------------------------------------------------------------
# 5. PEMBERSIHAN TABEL ITEM PESANAN (ORDER ITEMS)
# ------------------------------------------------------------------------------
print("\n📦 [5/7] Membersihkan olist_order_items_dataset.csv ...")
df_items = pd.read_csv(os.path.join(RAW_DIR, 'olist_order_items_dataset.csv'))
initial_items_rows = len(df_items)

df_items['order_id'] = df_items['order_id'].astype(str).str.strip()
df_items['order_item_id'] = df_items['order_item_id'].astype(int)
df_items['product_id'] = df_items['product_id'].astype(str).str.strip()
df_items['seller_id'] = df_items['seller_id'].astype(str).str.strip()
df_items['shipping_limit_date'] = pd.to_datetime(df_items['shipping_limit_date'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')

df_items['price'] = df_items['price'].fillna(0.0).clip(lower=0.0).round(2)
df_items['freight_value'] = df_items['freight_value'].fillna(0.0).clip(lower=0.0).round(2)
df_items['total_item_value'] = (df_items['price'] + df_items['freight_value']).round(2)

df_items = df_items.drop_duplicates(subset=['order_id', 'order_item_id'])
items_output_path = os.path.join(STAGING_DIR, 'clean_order_items.csv')
df_items.to_csv(items_output_path, index=False, encoding='utf-8')
print(f"   -> Selesai: {len(df_items):,} baris diekspor ke clean_order_items.csv (Awal: {initial_items_rows:,})")


# ------------------------------------------------------------------------------
# 6. PEMBERSIHAN TABEL PEMBAYARAN (PAYMENTS)
# ------------------------------------------------------------------------------
print("\n📦 [6/7] Membersihkan olist_order_payments_dataset.csv ...")
df_pay = pd.read_csv(os.path.join(RAW_DIR, 'olist_order_payments_dataset.csv'))
initial_pay_rows = len(df_pay)

df_pay['order_id'] = df_pay['order_id'].astype(str).str.strip()
df_pay['payment_sequential'] = df_pay['payment_sequential'].astype(int)
df_pay['payment_type'] = df_pay['payment_type'].astype(str).str.strip().str.lower()
df_pay['payment_installments'] = df_pay['payment_installments'].astype(int)
df_pay['payment_value'] = df_pay['payment_value'].fillna(0.0).clip(lower=0.0).round(2)

# Pembagian termin cicilan
def categorize_installments(x):
    if x <= 1:
        return 'Single Payment'
    elif 2 <= x <= 4:
        return 'Short Term (2-4x)'
    elif 5 <= x <= 8:
        return 'Medium Term (5-8x)'
    else:
        return 'Long Term (>8x)'

df_pay['payment_installments_group'] = df_pay['payment_installments'].apply(categorize_installments)
pay_output_path = os.path.join(STAGING_DIR, 'clean_order_payments.csv')
df_pay.to_csv(pay_output_path, index=False, encoding='utf-8')
print(f"   -> Selesai: {len(df_pay):,} baris diekspor ke clean_order_payments.csv (Awal: {initial_pay_rows:,})")


# ------------------------------------------------------------------------------
# 7. PEMBERSIHAN TABEL ULASAN (REVIEWS)
# ------------------------------------------------------------------------------
print("\n📦 [7/7] Membersihkan olist_order_reviews_dataset.csv ...")
df_rev = pd.read_csv(os.path.join(RAW_DIR, 'olist_order_reviews_dataset.csv'))
initial_rev_rows = len(df_rev)

df_rev['review_id'] = df_rev['review_id'].astype(str).str.strip()
df_rev['order_id'] = df_rev['order_id'].astype(str).str.strip()
df_rev['review_score'] = df_rev['review_score'].astype(int).clip(lower=1, upper=5)

# Bersihkan teks review dari newlines/returns yang dapat merusak parsing CSV
def clean_text_field(series):
    return (
        series.fillna('')
        .astype(str)
        .str.replace('\r', ' ', regex=False)
        .str.replace('\n', ' ', regex=False)
        .str.replace('\t', ' ', regex=False)
        .str.strip()
    )

df_rev['review_comment_title'] = clean_text_field(df_rev['review_comment_title'])
df_rev['review_comment_message'] = clean_text_field(df_rev['review_comment_message'])

df_rev['review_creation_date'] = pd.to_datetime(df_rev['review_creation_date'], errors='coerce').dt.strftime('%Y-%m-%d')
df_rev['review_answer_timestamp'] = pd.to_datetime(df_rev['review_answer_timestamp'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')

# Deduplikasi review jika ada review_id ganda: ambil ulasan paling akhir (latest answer_timestamp)
df_rev = df_rev.sort_values(by='review_answer_timestamp', ascending=False)
df_rev = df_rev.drop_duplicates(subset=['review_id'], keep='first')

rev_output_path = os.path.join(STAGING_DIR, 'clean_order_reviews.csv')
df_rev.to_csv(rev_output_path, index=False, encoding='utf-8')
print(f"   -> Selesai: {len(df_rev):,} baris diekspor ke clean_order_reviews.csv (Awal: {initial_rev_rows:,}, Deduplikasi: {initial_rev_rows - len(df_rev):,})")

print("\n" + "=" * 70)
print("✅ SEMUA DATASET TELAH BERHASIL DIBERSIHKAN DAN DIMUAT KE DATA/STAGING/")
print("=" * 70)
