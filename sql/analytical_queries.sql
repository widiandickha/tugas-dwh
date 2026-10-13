-- =============================================================================
-- Kumpulan Query SQL Analitik Bisnis Data Warehouse Olist
-- Target Database Engine: MySQL 8.x
-- Dibuat oleh: Anggota 1 (Data Architect & Business Analyst)
-- Tujuan: Membuktikan bahwa skema DWH berhasil menjawab 5 KPI bisnis strategis.
-- =============================================================================

USE dwh_olist;

-- -----------------------------------------------------------------------------
-- Query 1 (Menjawab KPI 1):
-- Tren Pendapatan Kotor Bulanan dan Pertumbuhan Penjualan (MoM Growth)
-- -----------------------------------------------------------------------------
-- Rumus:
-- Revenue = SUM(total_item_value)
-- MoM Growth = ((Revenue_Bulan_Ini - Revenue_Bulan_Lalu) / Revenue_Bulan_Lalu) * 100%
-- Menggunakan Window Function LAG() untuk membandingkan performa antar bulan.

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


-- -----------------------------------------------------------------------------
-- Query 2 (Menjawab KPI 2):
-- Evaluasi Performa Logistik & Rasio Ketepatan Waktu Pengiriman per Wilayah
-- -----------------------------------------------------------------------------
-- Rumus:
-- On-Time Rate (%) = (Pesanan Tepat Waktu / Total Pesanan Selesai) * 100%
-- Lead Time = Rata-rata hari dari tanggal checkout hingga barang diterima pembeli.

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


-- -----------------------------------------------------------------------------
-- Query 3 (Menjawab KPI 3):
-- Top 10 Kategori Produk Terlaris dan Kontribusi terhadap Total Penjualan
-- -----------------------------------------------------------------------------
-- Menghitung total omzet per kategori, rata-rata harga produk, serta persentase
-- kontribusi kategori terhadap total penjualan pasar (menggunakan SUM OVER()).

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


-- -----------------------------------------------------------------------------
-- Query 4 (Menjawab KPI 4):
-- Analisis Hubungan Keterlambatan Logistik terhadap Skor Kepuasan & Sentimen Ulasan
-- -----------------------------------------------------------------------------
-- Membandingkan skor kepuasan ulasan (1-5) antara pesanan tepat waktu vs terlambat,
-- serta menampilkan distribusi sentimen yang dihasilkan oleh modul AI Anggota 3.

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
    -- Memanfaatkan kolom anotasi AI dari tabel dim_reviews
    COUNT(CASE WHEN r.sentiment_category = 'Positive' THEN 1 END) AS ai_positive_count,
    COUNT(CASE WHEN r.sentiment_category = 'Negative' THEN 1 END) AS ai_negative_count
FROM fact_order_items f
JOIN dim_reviews r ON f.review_key = r.review_key
JOIN dim_order_status s ON f.order_status_key = s.status_key
WHERE s.order_status_name = 'delivered'
GROUP BY f.is_delayed;


-- -----------------------------------------------------------------------------
-- Query 5 (Menjawab KPI 5):
-- Profil Metode Pembayaran dan Distribusi Termin Cicilan (Installments)
-- -----------------------------------------------------------------------------
-- Menganalisis preferensi cara bayar konsumen Brazil dan peran cicilan dalam
-- mendorong transaksi beromzet besar.

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
