-- =============================================================================
-- Skrip DDL Data Warehouse (DWH) Olist Brazilian E-Commerce
-- Target Database Engine: MySQL 8.x
-- Dibuat oleh: Anggota 1 (Data Architect & Business Analyst)
-- =============================================================================

-- 1. Inisialisasi Database
CREATE DATABASE IF NOT EXISTS dwh_olist
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE dwh_olist;

-- Nonaktifkan pengecekan foreign key sementara saat inisialisasi ulang
SET FOREIGN_KEY_CHECKS = 0;

-- Drop tabel jika sudah ada sebelumnya (urutan tabel fakta terlebih dahulu)
DROP TABLE IF EXISTS fact_order_items;
DROP TABLE IF EXISTS dim_reviews;
DROP TABLE IF EXISTS dim_payments;
DROP TABLE IF EXISTS dim_order_status;
DROP TABLE IF EXISTS dim_sellers;
DROP TABLE IF EXISTS dim_products;
DROP TABLE IF EXISTS dim_customers;
DROP TABLE IF EXISTS dim_date;

SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================================
-- 2. Pembuatan Tabel-Tabel Dimensi (Dimension Tables)
-- =============================================================================

-- Dimensi 1: Dimensi Tanggal (dim_date)
CREATE TABLE dim_date (
    date_key INT NOT NULL COMMENT 'Format YYYYMMDD (contoh: 20180115)',
    full_date DATE NOT NULL COMMENT 'Nilai tanggal YYYY-MM-DD',
    day INT NOT NULL COMMENT 'Hari dalam bulan (1-31)',
    month INT NOT NULL COMMENT 'Nomor bulan (1-12)',
    month_name VARCHAR(20) NOT NULL COMMENT 'Nama bulan (January, February, dst)',
    quarter INT NOT NULL COMMENT 'Kuartal kalender (1-4)',
    year INT NOT NULL COMMENT 'Tahun transaksi (2016-2018)',
    day_of_week VARCHAR(20) NOT NULL COMMENT 'Nama hari (Monday, Tuesday, dst)',
    is_weekend TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Flag akhir pekan: 1=Ya, 0=Tidak',
    PRIMARY KEY (date_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tabel dimensi kalender waktu transaksi';

-- Dimensi 2: Dimensi Pelanggan (dim_customers)
CREATE TABLE dim_customers (
    customer_key INT NOT NULL AUTO_INCREMENT COMMENT 'Surrogate key pelanggan',
    customer_id VARCHAR(50) NOT NULL COMMENT 'Natural key per transaksi pesanan',
    customer_unique_id VARCHAR(50) NOT NULL COMMENT 'Identitas unik individu pembeli',
    customer_city VARCHAR(100) NULL COMMENT 'Kota domisili pelanggan',
    customer_state VARCHAR(10) NULL COMMENT 'Negara bagian domisili (SP, RJ, dsb)',
    customer_zip_code_prefix VARCHAR(10) NULL COMMENT 'Kode pos 5 digit pelanggan',
    PRIMARY KEY (customer_key),
    UNIQUE KEY uk_customer_id (customer_id),
    INDEX idx_customer_unique (customer_unique_id),
    INDEX idx_customer_state (customer_state)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tabel dimensi profil dan lokasi geografi pelanggan';

-- Dimensi 3: Dimensi Produk (dim_products)
CREATE TABLE dim_products (
    product_key INT NOT NULL AUTO_INCREMENT COMMENT 'Surrogate key produk',
    product_id VARCHAR(50) NOT NULL COMMENT 'Natural key produk Olist',
    product_category_name VARCHAR(100) NULL DEFAULT 'Unknown' COMMENT 'Nama kategori asli Portugis',
    product_category_name_english VARCHAR(100) NULL DEFAULT 'Unknown' COMMENT 'Nama kategori terjemahan Inggris',
    product_weight_g DECIMAL(10,2) NULL DEFAULT 0.00 COMMENT 'Berat produk dalam gram',
    product_length_cm DECIMAL(10,2) NULL DEFAULT 0.00 COMMENT 'Panjang produk dalam cm',
    product_height_cm DECIMAL(10,2) NULL DEFAULT 0.00 COMMENT 'Tinggi produk dalam cm',
    product_width_cm DECIMAL(10,2) NULL DEFAULT 0.00 COMMENT 'Lebar produk dalam cm',
    PRIMARY KEY (product_key),
    UNIQUE KEY uk_product_id (product_id),
    INDEX idx_product_category (product_category_name_english)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tabel dimensi katalog produk dan spesifikasi fisik';

-- Dimensi 4: Dimensi Penjual / Merchant (dim_sellers)
CREATE TABLE dim_sellers (
    seller_key INT NOT NULL AUTO_INCREMENT COMMENT 'Surrogate key penjual',
    seller_id VARCHAR(50) NOT NULL COMMENT 'Natural key penjual Olist',
    seller_city VARCHAR(100) NULL COMMENT 'Kota domisili penjual',
    seller_state VARCHAR(10) NULL COMMENT 'Negara bagian penjual (SP, PR, dsb)',
    seller_zip_code_prefix VARCHAR(10) NULL COMMENT 'Kode pos 5 digit penjual',
    PRIMARY KEY (seller_key),
    UNIQUE KEY uk_seller_id (seller_id),
    INDEX idx_seller_state (seller_state)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tabel dimensi toko dan lokasi penjual';

-- Dimensi 5: Dimensi Status Pesanan (dim_order_status)
CREATE TABLE dim_order_status (
    status_key INT NOT NULL AUTO_INCREMENT COMMENT 'Surrogate key status',
    order_status_name VARCHAR(50) NOT NULL COMMENT 'Nama status (delivered, shipped, canceled, dsb)',
    PRIMARY KEY (status_key),
    UNIQUE KEY uk_order_status_name (order_status_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tabel dimensi lookup status transaksi';

-- Dimensi 6: Dimensi Metode Pembayaran (dim_payments)
CREATE TABLE dim_payments (
    payment_key INT NOT NULL AUTO_INCREMENT COMMENT 'Surrogate key pembayaran',
    payment_type VARCHAR(50) NOT NULL COMMENT 'Tipe pembayaran (credit_card, boleto, voucher, debit_card)',
    payment_installments_group VARCHAR(50) NULL DEFAULT 'Single Payment' COMMENT 'Kelompok termin cicilan',
    PRIMARY KEY (payment_key),
    INDEX idx_payment_type (payment_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tabel dimensi metode pembayaran dan kelompok cicilan';

-- Dimensi 7: Dimensi Ulasan Pelanggan (dim_reviews)
CREATE TABLE dim_reviews (
    review_key INT NOT NULL AUTO_INCREMENT COMMENT 'Surrogate key ulasan',
    review_id VARCHAR(50) NOT NULL COMMENT 'Natural key ulasan Olist',
    review_score INT NOT NULL COMMENT 'Skor rating ulasan (1-5)',
    review_comment_title VARCHAR(255) NULL COMMENT 'Judul singkat ulasan',
    review_comment_message TEXT NULL COMMENT 'Isi teks pesan ulasan',
    sentiment_category VARCHAR(50) NULL DEFAULT 'Unassigned' COMMENT 'Kategori sentimen hasil klasifikasi AI (Positive/Neutral/Negative)',
    PRIMARY KEY (review_key),
    INDEX idx_review_score (review_score),
    INDEX idx_sentiment (sentiment_category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tabel dimensi ulasan pelanggan dan anotasi sentimen AI';

-- =============================================================================
-- 3. Pembuatan Tabel Fakta (Fact Table)
-- =============================================================================

CREATE TABLE fact_order_items (
    fact_id BIGINT NOT NULL AUTO_INCREMENT COMMENT 'Surrogate key baris fakta',
    customer_key INT NOT NULL COMMENT 'Foreign key ke dim_customers',
    product_key INT NOT NULL COMMENT 'Foreign key ke dim_products',
    seller_key INT NOT NULL COMMENT 'Foreign key ke dim_sellers',
    order_date_key INT NOT NULL COMMENT 'Foreign key ke dim_date (tanggal beli)',
    order_status_key INT NOT NULL COMMENT 'Foreign key ke dim_order_status',
    payment_key INT NOT NULL COMMENT 'Foreign key ke dim_payments',
    review_key INT NULL COMMENT 'Foreign key opsional ke dim_reviews',
    order_id VARCHAR(50) NOT NULL COMMENT 'Degenerate dimension nomor pesanan asli',
    order_item_id INT NOT NULL COMMENT 'Degenerate dimension nomor urut item dalam pesanan',
    price DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT 'Harga satuan item produk (BRL)',
    freight_value DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT 'Biaya ongkos kirim item (BRL)',
    total_item_value DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT 'Total nilai kotor item: price + freight_value',
    shipping_duration_days DECIMAL(6,2) NULL COMMENT 'Durasi hari pengiriman aktual',
    delivery_delay_days DECIMAL(6,2) NULL COMMENT 'Selisih hari terhadap estimasi tiba (positif = telat)',
    is_delayed TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Flag keterlambatan: 1=Terlambat, 0=Tepat Waktu',
    PRIMARY KEY (fact_id),
    
    -- Relasi Foreign Key
    CONSTRAINT fk_fact_customer FOREIGN KEY (customer_key)
        REFERENCES dim_customers (customer_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fact_product FOREIGN KEY (product_key)
        REFERENCES dim_products (product_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fact_seller FOREIGN KEY (seller_key)
        REFERENCES dim_sellers (seller_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fact_date FOREIGN KEY (order_date_key)
        REFERENCES dim_date (date_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fact_status FOREIGN KEY (order_status_key)
        REFERENCES dim_order_status (status_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fact_payment FOREIGN KEY (payment_key)
        REFERENCES dim_payments (payment_key)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fact_review FOREIGN KEY (review_key)
        REFERENCES dim_reviews (review_key)
        ON DELETE SET NULL ON UPDATE CASCADE,

    -- Indeks Kinerja Analitik
    INDEX idx_fact_order_id (order_id),
    INDEX idx_fact_date (order_date_key),
    INDEX idx_fact_product (product_key),
    INDEX idx_fact_customer (customer_key),
    INDEX idx_fact_seller (seller_key),
    INDEX idx_fact_status (order_status_key),
    INDEX idx_fact_payment (payment_key),
    INDEX idx_fact_review (review_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tabel fakta penjualan e-commerce pada tingkat unit item produk';
