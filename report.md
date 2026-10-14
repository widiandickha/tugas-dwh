# 📊 Laporan Perkembangan Proyek (Progress Report)

* **Proyek:** Perancangan Data Warehouse & AI-assisted ETL E-Commerce
* **Dataset Sumber:** [Brazilian E-Commerce Public Dataset by Olist (Kaggle)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
* **Target Database:** MySQL 8.x
* **Status Proyek:** 
  * Fase 1 (Inisiasi & Desain Arsitektur) — **Selesai 100% (Anggota 1)**
  * Fase 2 (Data Profiling & Cleansing) — **Selesai 100% (Anggota 2)**
  * Fase 3 (Setup Database, AI Enrichment & ETL) — **Selesai 100% (Anggota 3)**
  * Fase 4 (Analytical Dashboard & Verifikasi KPI) — **Selesai 100% (Tim)**
* **Panduan Demo & Ringkasan Eksekutif:** Tersedia lengkap di [`PANDUAN_DEMO_DAN_RINGKASAN_DWH.md`](PANDUAN_DEMO_DAN_RINGKASAN_DWH.md)

---

## 1. Ringkasan Progres & Deliverables yang Telah Dibagikan

Seluruh aset perancangan dari Anggota 1 telah selesai dibuat, diverifikasi, dan dibagikan ke grup tim (WhatsApp). Berikut rekapitulasi 5 poin berkas utama:

### Poin 1: Alur Proses Bisnis & 5 KPI (`docs/business_process.md`)
* Memetakan siklus transaksi e-commerce Olist: mulai dari checkout barang, konfirmasi pembayaran, penyerahan ke kurir, pengiriman tiba di pembeli, hingga pengisian ulasan kepuasan.
* Merumuskan 5 Key Performance Indicators (KPI) bisnis strategis:
  1. Tren Pendapatan Kotor Bulanan & Pertumbuhan Penjualan (MoM Growth).
  2. Rasio Ketepatan Waktu Logistik (On-Time Delivery Rate) & Rata-rata Durasi Pengiriman.
  3. Kontribusi Penjualan & Rata-rata Nilai Transaksi (AOV) per Kategori Produk.
  4. Analisis Hubungan Keterlambatan Pengiriman terhadap Skor Ulasan Pelanggan.
  5. Distribusi Metode Pembayaran & Pola Termin Cicilan (Installments).

### Poin 2: Desain Star Schema & ERD (`docs/dwh_schema_design.md` & `SKEMA DATA.png`)
* Menetapkan **Grain**: 1 baris pada tabel fakta `fact_order_items` mewakili 1 unit item produk dalam 1 nomor transaksi pesanan unik (*atomic order-item level*).
* Menghubungkan 1 tabel fakta pusat (`fact_order_items`) dengan 7 tabel dimensi (`dim_date`, `dim_customers`, `dim_products`, `dim_sellers`, `dim_order_status`, `dim_payments`, `dim_reviews`).
* Menyediakan kode DBML dan diagram ERD untuk dokumentasi visual arsitektur:

![Star Schema Diagram](docs/images/star_schema.png)

### Poin 3: Kamus Data / Data Dictionary (`docs/data_dictionary.md`)
* Memuat rincian teknis 8 tabel: tipe data MySQL, Primary Key / Surrogate Key, Foreign Key, Degenerate Dimension, aturan nilai kosong (nullable), nilai default, dan formula kolom turunan.
* Menetapkan pemetaan sumber (*source mapping*) dari file CSV mentah Kaggle agar Anggota 2 dan Anggota 3 memiliki acuan yang sama persis.
* Menyiapkan kolom `sentiment_category` pada tabel `dim_reviews` sebagai slot integrasi transformasi AI oleh Anggota 3.

### Poin 4: Skrip DDL MySQL (`sql/schema_dwh.sql`)
* Skrip SQL DDL bersih yang siap dieksekusi di database MySQL (`CREATE DATABASE dwh_olist`).
* Menggunakan standar mesin `InnoDB` dan karakter `utf8mb4`.
* Mengatur relasi *Foreign Key Constraint* (`ON DELETE RESTRICT ON UPDATE CASCADE`) serta *indexing* pada kolom kunci dan tanggal untuk optimalisasi query analitik.

### Poin 5: Skrip Query Analitik Bisnis (`sql/analytical_queries.sql`)
* Kumpulan 5 query SQL analitik tingkat lanjut yang memanfaatkan Window Function (`LAG()`, `SUM() OVER()`) dan agregasi kondisional.
* Query ini dirancang untuk langsung dijalankan setelah pipeline ETL selesai memuat data, guna membuktikan bahwa DWH mampu menjawab seluruh KPI bisnis.

---

## 2. Poin 6: Standar Struktur Folder Proyek

Agar alur kerja antar anggota berjalan teratur tanpa konflik berkas atau bentrok penamaan, struktur direktori repository `DWH BARU` diatur sebagai berikut:

```text
DWH BARU/
├── JOBDESK_DAN_WORKFLOW.md       # Panduan pembagian tugas & alur kerja tim
├── report.md                     # Laporan perkembangan berkala (dokumen ini)
│
├── docs/                         # Workspace Anggota 1 (Dokumentasi Desain & Arsitektur)
│   ├── business_process.md       # Narasi proses bisnis & definisi KPI
│   ├── dwh_schema_design.md      # Desain Star Schema, Grain, dan ERD
│   └── data_dictionary.md        # Kamus data teknis seluruh tabel DWH
│
├── sql/                          # Workspace Anggota 1 & Anggota 3 (Skrip Database)
│   ├── schema_dwh.sql            # DDL inisialisasi tabel target MySQL
│   └── analytical_queries.sql    # Query SQL analitik untuk pengujian KPI
│
├── data/                         # Direktori Penyimpanan Dataset
│   ├── raw/                      # Wadah CSV mentah hasil unduhan dari Kaggle (Olist)
│   └── staging/                  # Wadah CSV/Parquet bersih hasil olahan Anggota 2
│
└── src/                          # Direktori Kode Program
    ├── cleansing/                # Workspace Anggota 2 (Jupyter Notebook / Python Cleansing)
    │   ├── data_profiling.ipynb  # Audit kondisi kotoran data awal
    │   └── cleansing.py          # Skrip otomatisasi pembersihan data
    │
    └── etl/                      # Workspace Anggota 3 (Pipeline ETL & Modul AI)
        ├── ai_transformer.py     # Modul enrichment AI (analisis sentimen ulasan)
        ├── etl_pipeline.py       # Pipeline Extract, Transform, dan Load ke MySQL
        └── database_config.py    # Konfigurasi koneksi database MySQL
```

### Panduan Penggunaan Folder bagi Setiap Anggota:
1. **Folder `data/raw/`**: Tempat menaruh file CSV asli dari Kaggle. Folder ini tidak boleh diubah isinya secara manual untuk menjaga orisinalitas data mentah.
2. **Folder `data/staging/`**: Anggota 2 menyimpan file dataset yang sudah bersih di sini. File di folder inilah yang akan dibaca oleh skrip ETL Anggota 3.
3. **Folder `src/cleansing/`**: Anggota 2 meletakkan seluruh file kode analisis data kotor dan script pembersihan di folder ini.
4. **Folder `src/etl/`**: Anggota 3 meletakkan seluruh kode pipeline integrasi database, modul AI, dan logging proses loading di folder ini.

---

## 3. Hasil Deliverables Anggota 2 (Selesai 100%)

Anggota 2 telah menyelesaikan seluruh tugas profiling dan pembersihan data. Seluruh berkas kini tersedia di repository:
1. **Raw Dataset**: 9 berkas CSV tersimpan di [`data/raw/`](data/raw/).
2. **Profiling Script**: [`src/cleansing/data_profiling.py`](src/cleansing/data_profiling.py) dan [`src/cleansing/data_profiling.ipynb`](src/cleansing/data_profiling.ipynb).
3. **Cleansing Pipeline Script**: [`src/cleansing/cleansing.py`](src/cleansing/cleansing.py).
4. **Staging Dataset (Cleaned)**: 7 file CSV bersih tersimpan di [`data/staging/`](data/staging/):
   * `clean_customers.csv` (99.441 baris)
   * `clean_sellers.csv` (3.095 baris)
   * `clean_products.csv` (32.951 baris)
   * `clean_orders.csv` (99.441 baris)
   * `clean_order_items.csv` (112.650 baris)
   * `clean_order_payments.csv` (103.886 baris)
   * `clean_order_reviews.csv` (98.410 baris)
5. **Laporan Kualitas Data**: Tersedia di [`docs/data_cleansing_report.md`](docs/data_cleansing_report.md).

---

## 4. Hasil Deliverables Anggota 3 (Selesai 100%)

Anggota 3 telah menyelesaikan implementasi database target, modul AI sentimen, dan pipeline ETL:
1. **Modul AI Sentimen**: [`src/etl/ai_transformer.py`](src/etl/ai_transformer.py) (klasifikasi sentimen berbasis NLP/LLM dengan fallback leksikon Portugis).
2. **Koneksi Basis Data**: [`src/etl/database_config.py`](src/etl/database_config.py).
3. **Pipeline ETL**: [`src/etl/etl_pipeline.py`](src/etl/etl_pipeline.py) (memuat 8 tabel ke MySQL tanpa pelanggaran foreign key).
4. **Eksekusi 5 Query KPI**: [`src/etl/run_kpi_queries.py`](src/etl/run_kpi_queries.py).
5. **Laporan Resmi Pengujian KPI**: Tersedia lengkap di [`HASIL_QUERY_ANALITIK_KPI.md`](HASIL_QUERY_ANALITIK_KPI.md).

---

## 5. Hasil Deliverables Dashboard Analitik & Executive Presentation (Selesai 100%)

Untuk melengkapi seluruh rangkaian proyek data warehouse, telah dibangun sistem visualisasi analitik interaktif:
1. **Dashboard Utama (Streamlit Python)**: [`src/dashboard/app.py`](src/dashboard/app.py) & [`src/dashboard/data_loader.py`](src/dashboard/data_loader.py).
   * Menampilkan ringkasan metrik eksekutif, tabel rekonsiliasi data mentah vs bersih (112k item), visualisasi 5 KPI bisnis (lonjakan Black Friday Nov 2017 & korelasi delay vs AI sentimen), simulator ulasan AI live, dan live SQL query runner.
   * Dilengkapi arsitektur *Dual-Mode*: membaca data MySQL jika server aktif, atau fallback otomatis ke in-memory staging engine jika offline.
2. **Cadangan Darurat / Fail-Safe Preview (HTML5)**: [`src/dashboard/standalone_preview.html`](src/dashboard/standalone_preview.html).
   * Berkas visualisasi mandiri tanpa dependensi luar, siap dibuka langsung di peramban web pada saat demo.
3. **Panduan Presentasi Praktik**: Tersedia lengkap di [`PANDUAN_DEMO_DAN_RINGKASAN_DWH.md`](PANDUAN_DEMO_DAN_RINGKASAN_DWH.md).
