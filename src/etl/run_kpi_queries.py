import os
import sys
import pandas as pd
from sqlalchemy import create_engine

# Pastikan UTF-8 encoding
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

engine = create_engine("mysql+pymysql://root@localhost:3306/dwh_olist?charset=utf8mb4")

queries = {
    "KPI 1: Tren Pendapatan Kotor Bulanan & MoM Growth": """
    WITH monthly_sales AS (
        SELECT 
            d.year,
            d.month,
            d.month_name,
            COUNT(DISTINCT f.order_id) AS total_orders,
            COUNT(f.fact_id) AS total_items_sold,
            ROUND(SUM(f.price), 2) AS total_product_revenue,
            ROUND(SUM(f.freight_value), 2) AS total_freight_revenue,
            ROUND(SUM(f.total_item_value), 2) AS total_gross_revenue
        FROM fact_order_items f
        JOIN dim_date d ON f.order_date_key = d.date_key
        JOIN dim_order_status s ON f.order_status_key = s.status_key
        WHERE s.order_status_name = 'delivered'
        GROUP BY d.year, d.month, d.month_name
    )
    SELECT 
        year,
        month,
        month_name,
        total_orders,
        total_items_sold,
        total_gross_revenue,
        LAG(total_gross_revenue, 1) OVER (ORDER BY year, month) AS previous_month_revenue,
        ROUND(
            ((total_gross_revenue - LAG(total_gross_revenue, 1) OVER (ORDER BY year, month)) 
            / LAG(total_gross_revenue, 1) OVER (ORDER BY year, month)) * 100, 
            2
        ) AS mom_growth_percentage
    FROM monthly_sales
    ORDER BY year ASC, month ASC;
    """,

    "KPI 2: Evaluasi Performa Logistik & On-Time Delivery Rate per Wilayah": """
    SELECT 
        c.customer_state,
        COUNT(DISTINCT f.order_id) AS total_delivered_orders,
        ROUND(AVG(f.shipping_duration_days), 1) AS avg_delivery_days,
        ROUND(AVG(f.delivery_delay_days), 1) AS avg_delay_against_estimate_days,
        COUNT(CASE WHEN f.is_delayed = 0 THEN 1 END) AS on_time_orders_count,
        COUNT(CASE WHEN f.is_delayed = 1 THEN 1 END) AS delayed_orders_count,
        ROUND(
            (COUNT(CASE WHEN f.is_delayed = 0 THEN 1 END) / COUNT(f.fact_id)) * 100, 
            2
        ) AS on_time_delivery_rate_percentage
    FROM fact_order_items f
    JOIN dim_customers c ON f.customer_key = c.customer_key
    JOIN dim_order_status s ON f.order_status_key = s.status_key
    WHERE s.order_status_name = 'delivered'
      AND f.shipping_duration_days IS NOT NULL
    GROUP BY c.customer_state
    HAVING total_delivered_orders >= 50
    ORDER BY on_time_delivery_rate_percentage ASC, total_delivered_orders DESC;
    """,

    "KPI 3: Top 10 Kategori Produk Terlaris & Kontribusi Omzet": """
    WITH category_summary AS (
        SELECT 
            COALESCE(p.product_category_name_english, 'Other / Uncategorized') AS category_name,
            COUNT(DISTINCT f.order_id) AS unique_orders,
            COUNT(f.fact_id) AS items_sold_qty,
            ROUND(AVG(f.price), 2) AS avg_item_price,
            ROUND(SUM(f.total_item_value), 2) AS total_category_revenue
        FROM fact_order_items f
        JOIN dim_products p ON f.product_key = p.product_key
        JOIN dim_order_status s ON f.order_status_key = s.status_key
        WHERE s.order_status_name = 'delivered'
        GROUP BY COALESCE(p.product_category_name_english, 'Other / Uncategorized')
    )
    SELECT 
        category_name,
        unique_orders,
        items_sold_qty,
        avg_item_price,
        total_category_revenue,
        ROUND(
            (total_category_revenue / SUM(total_category_revenue) OVER ()) * 100, 
            2
        ) AS revenue_contribution_percentage
    FROM category_summary
    ORDER BY total_category_revenue DESC
    LIMIT 10;
    """,

    "KPI 4: Hubungan Keterlambatan Logistik terhadap Skor Kepuasan & Sentimen AI": """
    SELECT 
        CASE 
            WHEN f.is_delayed = 1 THEN 'Terlambat (Delayed)'
            ELSE 'Tepat Waktu (On-Time)'
        END AS delivery_performance_status,
        COUNT(f.fact_id) AS total_items_reviewed,
        ROUND(AVG(r.review_score), 2) AS average_review_score,
        ROUND(
            (COUNT(CASE WHEN r.review_score IN (4, 5) THEN 1 END) / COUNT(f.fact_id)) * 100, 
            2
        ) AS positive_review_percentage,
        ROUND(
            (COUNT(CASE WHEN r.review_score IN (1, 2) THEN 1 END) / COUNT(f.fact_id)) * 100, 
            2
        ) AS negative_review_percentage,
        COUNT(CASE WHEN r.sentiment_category = 'Positive' THEN 1 END) AS ai_positive_count,
        COUNT(CASE WHEN r.sentiment_category = 'Negative' THEN 1 END) AS ai_negative_count
    FROM fact_order_items f
    JOIN dim_reviews r ON f.review_key = r.review_key
    JOIN dim_order_status s ON f.order_status_key = s.status_key
    WHERE s.order_status_name = 'delivered'
    GROUP BY f.is_delayed;
    """,

    "KPI 5: Profil Metode Pembayaran & Distribusi Termin Cicilan": """
    SELECT 
        pay.payment_type,
        COALESCE(pay.payment_installments_group, 'Single Payment') AS installment_group,
        COUNT(DISTINCT f.order_id) AS total_transactions,
        ROUND(SUM(f.total_item_value), 2) AS total_volume_value,
        ROUND(AVG(f.total_item_value), 2) AS avg_transaction_value,
        ROUND(
            (SUM(f.total_item_value) / SUM(SUM(f.total_item_value)) OVER ()) * 100, 
            2
        ) AS payment_share_percentage
    FROM fact_order_items f
    JOIN dim_payments pay ON f.payment_key = pay.payment_key
    JOIN dim_order_status s ON f.order_status_key = s.status_key
    WHERE s.order_status_name = 'delivered'
    GROUP BY pay.payment_type, pay.payment_installments_group
    ORDER BY total_volume_value DESC;
    """
}

out_md = []
out_md.append("# 📊 Laporan Hasil Pengujian 5 KPI Bisnis — Olist Brazilian E-Commerce DWH")
out_md.append("\n**Mata Kuliah:** Pangkalan Data | **Peran:** Anggota 3 (ETL & Database Engineer)")
out_md.append(f"**Database Engine:** MySQL 8.0.46 | **Waktu Eksekusi:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

for title, q in queries.items():
    df = pd.read_sql(q, con=engine)
    
    # Format angka agar rapi (ribuan berkoma & persentase)
    df_formatted = df.copy()
    for col in df_formatted.columns:
        if 'percentage' in col or 'rate' in col:
            df_formatted[col] = df_formatted[col].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "-")
        elif 'revenue' in col or 'value' in col or 'price' in col:
            df_formatted[col] = df_formatted[col].apply(lambda x: f"R$ {x:,.2f}" if pd.notnull(x) else "-")
        elif 'orders' in col or 'items' in col or 'count' in col or 'transactions' in col:
            df_formatted[col] = df_formatted[col].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "0")

    out_md.append(f"### {title}\n")
    out_md.append(df_formatted.to_markdown(index=False))
    out_md.append("\n\n---\n")

report_path = os.path.join(os.path.dirname(__file__), "..", "..", "HASIL_QUERY_ANALITIK_KPI.md")
report_path = os.path.abspath(report_path)
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(out_md))

print(f"✅ Laporan KPI terformat berhasil dibuat di: {report_path}")
