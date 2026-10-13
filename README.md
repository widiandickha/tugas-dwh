# Proyek Data Warehouse & AI-assisted ETL (Olist Brazilian E-Commerce)

Repository ini berisi rancangan arsitektur Data Warehouse (DWH), pemodelan dimensional (*Star Schema*), skrip DDL MySQL, serta panduan pipeline ETL berbasis dataset publik Kaggle Olist Brazil.

---

## 📌 Ringkasan Proyek

* **Dataset Sumber:** [Brazilian E-Commerce Public Dataset by Olist (Kaggle)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
* **Database Engine:** MySQL 8.x
* **Arsitektur DWH:** Star Schema (Kimball Methodology)
* **Granularitas Data (Grain):** 1 baris per unit item produk transaksi (`fact_order_items`)

---

## 👥 Pembagian Peran Kelompok

1. **Anggota 1 (Data Architect & Business Analyst):**
   * Pemodelan proses bisnis dan perumusan 5 KPI bisnis.
   * Perancangan Star Schema, penetapan Grain, dan Diagram ERD.
   * Penyusunan Kamus Data (*Data Dictionary*) dan skrip DDL SQL (`schema_dwh.sql`).
   * Penyusunan query pengujian analitik (`analytical_queries.sql`).
2. **Anggota 2 (Data Quality & Cleansing Engineer):**
   * Data profiling dan audit data mentah.
   * Pembersihan data (standarisasi tanggal, penanganan missing values, terjemahan kategori).
   * Menghasilkan data bersih di folder `data/staging/`.
3. **Anggota 3 (AI-Driven ETL & Database Engineer):**
   * Setup database target MySQL dan eksekusi skrip DDL.
   * Membangun pipeline ETL (Extract, Transform, Load).
   * Mengintegrasikan modul AI untuk pengayaan sentimen teks ulasan pada `dim_reviews`.

---

## 📂 Struktur Direktori Proyek

```text
.
├── JOBDESK_DAN_WORKFLOW.md       # Panduan pembagian tugas & alur kerja tim
├── report.md                     # Laporan perkembangan berkala proyek
├── README.md                     # Ringkasan repository (berkas ini)
│
├── docs/                         # Dokumentasi Arsitektur & Desain DWH
│   ├── business_process.md       # Narasi alur bisnis Olist & 5 KPI
│   ├── dwh_schema_design.md      # Desain Star Schema, Grain, dan ERD
│   └── data_dictionary.md        # Kamus data teknis seluruh tabel DWH
│
├── sql/                          # Skrip Basis Data MySQL
│   ├── schema_dwh.sql            # Skrip DDL CREATE TABLE DWH MySQL 8.x
│   └── analytical_queries.sql    # 5 Query SQL analitik untuk pengujian KPI
│
├── data/                         # Direktori Dataset
│   ├── raw/                      # File CSV mentah unduhan Kaggle
│   └── staging/                  # File data bersih hasil olahan Anggota 2
│
└── src/                          # Direktori Sumber Kode
    ├── cleansing/                # Workspace kode pembersihan data (Anggota 2)
    └── etl/                      # Workspace kode ETL & modul AI (Anggota 3)
```

---

## 🚀 Panduan Memulai Cepat

### 1. Inisialisasi Database
Jalankan skrip DDL pada server MySQL lokal Anda:
```bash
mysql -u root -p < sql/schema_dwh.sql
```

### 2. Memeriksa Kamus Data & Desain Skema
* Pelajari struktur tabel dan mapping kolom pada [`docs/data_dictionary.md`](docs/data_dictionary.md).
* Buka kode DBML pada [`docs/dwh_schema_design.md`](docs/dwh_schema_design.md) dan tempel ke [dbdiagram.io](https://dbdiagram.io) untuk melihat ERD interaktif.

### 3. Pengujian Query Analitik
Setelah data selesai dimuat oleh pipeline ETL, jalankan query bisnis pada [`sql/analytical_queries.sql`](sql/analytical_queries.sql) untuk menjawab 5 KPI bisnis.
