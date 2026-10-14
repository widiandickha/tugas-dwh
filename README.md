# 🛒 Data Warehouse & AI-assisted ETL: Olist Brazilian E-Commerce

Repository ini berisi rancangan menyeluruh arsitektur **Data Warehouse (DWH)**, pemodelan dimensional (*Star Schema*), kamus data teknis, skrip DDL MySQL, serta panduan pipeline ETL berbasis kecerdasan buatan (AI) menggunakan dataset publik Kaggle **Brazilian E-Commerce by Olist**.

---

## 📖 Latar Belakang & Konteks Proyek

Dalam ekosistem e-commerce modern, data transaksi operasional harian (OLTP) dihasilkan dalam volume tinggi dengan relasi yang kompleks. Tanpa repositori data analitik terstruktur (OLAP), tim bisnis menghadapi kendala besar dalam mengevaluasi metrik kinerja penjualan, logistik pengiriman, maupun kepuasan pelanggan secara cepat dan akurat.

### Domain Bisnis: Olist Brazil
Olist adalah platform marketplace integrator terbesar di Brazil yang menjembatani ribuan pedagang kecil dan menengah (*sellers*) dengan berbagai pasar ritel daring nasional. Karakteristik dataset ini mencakup:
* **100.000+ Pesanan:** Transaksi nyata yang tercatat sepanjang periode 2016 hingga 2018.
* **Multi-Seller Fulfillment:** Satu nomor pesanan pelanggan dapat berisi beberapa barang yang dikirimkan oleh penjual berbeda dari berbagai negara bagian di Brazil.
* **Kompleksitas Logistik:** Siklus waktu detail sejak pemesanan, verifikasi pembayaran, penyerahan ke kurir, estimasi tiba, hingga penerimaan paket oleh pembeli.
* **Ulasan Pelanggan Bebas:** Ribuan catatan teks ulasan kepuasan yang belum terstruktur, membuka peluang pemanfaatan model AI/LLM untuk analisis sentimen otomatis.

Tujuan utama dari proyek ini adalah mentransformasi data mentah yang terdistribusi tersebut ke dalam **Star Schema Data Warehouse** yang optimal untuk pelaporan bisnis (*Business Intelligence & Analytics*).

---

## 🛠️ Keputusan Teknologi: Mengapa MySQL 8.x?

Tim menyepakati penggunaan **MySQL 8.x** sebagai database engine target DWH dengan pertimbangan teknis berikut:
1. **Fitur Analitik Modern:** Mendukung *Common Table Expressions (CTE)* dan *Window Functions* (`LAG()`, `SUM() OVER()`, `ROW_NUMBER()`) yang esensial untuk perhitungan metrik MoM (*Month-over-Month*) dan kontribusi penjualan.
2. **Kestabilan & Integritas Data:** Mesin penyimpanan `InnoDB` menjamin kepatuhan ACID, integritas *Foreign Key Constraints*, dan indexing efisien pada surrogate keys.
3. **Standar Industri & Kemudahan Setup:** Mudah dioperasikan secara lokal oleh seluruh anggota tim (melalui Docker, MySQL Workbench, XAMPP, atau CLI) dengan konsumsi memori yang terukur.
4. **Konfigurasi Target:**
   * Nama Database: `dwh_olist`
   * Karakter Default: `utf8mb4` (mendukung teks ulasan bahasa Portugis dengan aksen karakter khusus)
   * Collate: `utf8mb4_unicode_ci`

---

## 📐 Arsitektur Dimensional (Star Schema)

Arsitektur DWH dirancang menggunakan metodologi dimensional Kimball dengan pendekatan **Star Schema**:

![Star Schema Diagram](docs/images/star_schema.png)

### 1. Penetapan Grain (Granularitas Baris Data)
* **Grain:** Setiap 1 baris pada tabel fakta `fact_order_items` mewakili **satu unit item produk yang dibeli dalam suatu nomor pesanan transaksi**.
* Tingkat detail ini memungkinkan analisis hingga ke level kombinasi terkecil: per produk, per penjual, tarif ongkir per item, serta durasi pengiriman spesifik.

### 2. Struktur Tabel
* **Tabel Fakta Pusat (`fact_order_items`):**
  * Metrik Numerik: `price`, `freight_value`, `total_item_value`, `shipping_duration_days`, `delivery_delay_days`.
  * Flag Analitik: `is_delayed` (penanda keterlambatan tiba).
  * Degenerate Dimension: `order_id`, `order_item_id`.
* **7 Tabel Dimensi Kontekstual:**
  * `dim_date`: Kalender waktu transaksi (hari, bulan, kuartal, tahun, nama hari, akhir pekan).
  * `dim_customers`: Geografi domisili pembeli (kota, negara bagian, kode pos, customer unique ID).
  * `dim_products`: Katalog produk, kategori terjemahan bahasa Inggris, serta dimensi fisik (berat, volume).
  * `dim_sellers`: Toko pedagang rekanan dan lokasi gudang pengiriman.
  * `dim_order_status`: Status siklus pesanan (delivered, shipped, canceled, invoiced, processing, dsb).
  * `dim_payments`: Metode bayar (credit card, boleto, voucher, debit) dan profil cicilan (*installments group*).
  * `dim_reviews`: Skor ulasan bintang (1-5) dan kolom **`sentiment_category`** (Positive/Neutral/Negative) yang diperkaya oleh modul AI.

---

## 🎯 5 Key Performance Indicators (KPI) Bisnis

Skema data warehouse ini dirancang untuk menjawab 5 pertanyaan bisnis strategis yang telah disiapkan query pengujiannya pada `sql/analytical_queries.sql`:

1. **Tren Pendapatan Bulanan & Pertumbuhan Penjualan (MoM Growth):**
   * Mengukur total nilai transaksi kotor bulanan dan laju pertumbuhan dibandingkan bulan sebelumnya dengan window function `LAG()`.
2. **Performa Logistik & Rasio Ketepatan Waktu Pengiriman (On-Time Rate):**
   * Menghitung persentase paket yang tiba tepat waktu per negara bagian (*state*) dan rata-rata waktu tempuh pengiriman dalam hitungan hari.
3. **Kontribusi Penjualan & Rata-rata Nilai Transaksi (AOV) per Kategori Produk:**
   * Mengidentifikasi 10 kategori produk penyumbang omzet terbesar beserta persentase kontribusinya terhadap total volume pasar.
4. **Dampak Keterlambatan Logistik terhadap Skor Ulasan & Sentimen Pelanggan:**
   * Membuktikan hubungan antara keterlambatan pengiriman paket terhadap penurunan skor rating ulasan (skor 1-2) dan distribusi sentimen negatif hasil deteksi AI.
5. **Preferensi Metode Pembayaran & Distribusi Termin Cicilan:**
   * Menganalisis proporsi cara bayar konsumen Brazil dan peran fasilitas cicilan (*installments*) dalam mendorong transaksi beromzet tinggi.

---

## 👥 Pembagian Tugas Kelompok (RACI Workflow)

| Peran | Penanggung Jawab | Fokus Utama & Deliverables |
| :--- | :--- | :--- |
| **Anggota 1** | Data Architect & Business Analyst | Pemahaman proses bisnis, perumusan KPI, perancangan Star Schema, penyusunan Kamus Data (`docs/data_dictionary.md`), DDL MySQL (`sql/schema_dwh.sql`), dan query analitik (`sql/analytical_queries.sql`). |
| **Anggota 2** | Data Quality & Cleansing Engineer | Data profiling kondisi awal data mentah, standarisasi format teks dan tanggal, penanganan missing values, penerjemahan kategori produk, dan ekspor data bersih ke `data/staging/`. |
| **Anggota 3** | AI-Driven ETL & Database Engineer | Setup database MySQL `dwh_olist`, eksekusi skrip DDL, integrasi API AI untuk klasifikasi sentimen ulasan pembeli, serta pembangunan pipeline ETL (Extract, Transform, Load) ke database. |

---

## 📂 Struktur Direktori Proyek

```text
.
├── JOBDESK_DAN_WORKFLOW.md       # Panduan pembagian tugas & alur kerja lengkap tim
├── report.md                     # Laporan perkembangan berkala proyek
├── README.md                     # Dokumentasi utama repository (berkas ini)
│
├── docs/                         # Dokumentasi Arsitektur & Desain DWH (Anggota 1)
│   ├── business_process.md       # Narasi proses bisnis Olist & rumusan 5 KPI
│   ├── dwh_schema_design.md      # Desain Star Schema, Grain, Mermaid ERD, dan DBML
│   ├── data_dictionary.md        # Kamus data teknis seluruh tabel DWH
│   ├── SKEMA DATA.png            # File gambar ekspor diagram Star Schema
│   └── images/
│       └── star_schema.png       # Asset gambar diagram untuk visualisasi Markdown
│
├── sql/                          # Workspace Skrip Database (Anggota 1 & Anggota 3)
│   ├── schema_dwh.sql            # DDL inisialisasi tabel target MySQL 8.x
│   └── analytical_queries.sql    # 5 Query SQL analitik untuk pembuktian KPI
│
├── data/                         # Direktori Penyimpanan Dataset
│   ├── raw/                      # Wadah CSV mentah unduhan Kaggle (diatur via .gitignore)
│   └── staging/                  # Wadah data bersih hasil olahan Anggota 2
│
└── src/                          # Direktori Kode Program
    ├── cleansing/                # Workspace Anggota 2 (Profiling & Cleansing)
    └── etl/                      # Workspace Anggota 3 (Pipeline ETL & Modul AI)
```

---

## 📥 Pengelolaan Dataset (Data Governance)

Dataset mentah Olist berukuran total sekitar **~126 MB** (9 berkas CSV). Sesuai dengan aturan standar rekayasa perangkat lunak dan batasan ukuran berkas GitHub (maksimal 100 MB per file):
* File dataset mentah di `data/raw/` dan data staging di `data/staging/` **tidak di-commit ke Git** (sudah diproteksi melalui `.gitignore`).
* Setiap anggota tim dapat mengunduh dataset secara mandiri dari tautan resmi:  
  🔗 [Kaggle Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
* Ekstrak seluruh file CSV hasil unduhan ke dalam folder `data/raw/` pada laptop masing-masing sebelum menjalankan proses pembersihan data.

---

## 🚀 Panduan Memulai Cepat (Quick Start)

### 1. Clone Repository
```bash
git clone https://github.com/widiandickha/tugas-dwh.git
cd tugas-dwh
```

### 2. Inisialisasi Database MySQL
Pastikan server MySQL 8.x Anda telah aktif, lalu eksekusi skrip DDL:
```bash
mysql -u root -p < sql/schema_dwh.sql
```
Perintah ini akan secara otomatis membuat database `dwh_olist` beserta 8 tabel, primary key surrogate, relasi foreign key, dan indeks analitik.

### 3. Pelajari Desain & Kamus Data
* Buka [`docs/data_dictionary.md`](docs/data_dictionary.md) untuk mempelajari tipe data kolom, aturan nullable, dan pemetaan dari file sumber Kaggle.
* Buka kode DBML pada [`docs/dwh_schema_design.md`](docs/dwh_schema_design.md) dan salin ke [dbdiagram.io](https://dbdiagram.io) untuk inspeksi relasi secara interaktif.

### 4. Eksekusi Pipeline ETL & Pengujian Analitik
* Setelah data bersih dari Anggota 2 dimuat ke MySQL oleh Anggota 3, jalankan berkas query pengujian:
```bash
mysql -u root -p dwh_olist < sql/analytical_queries.sql
```
* Hasil query akan menampilkan visualisasi data tabular untuk validasi 5 KPI bisnis.

### 5. Menjalankan Dashboard Analitik Interaktif
Proyek ini dilengkapi dengan **Executive & Analytical Dashboard** yang memvisualisasikan seluruh 5 KPI bisnis, tabel rekonsiliasi mutu data, korelasi ulasan AI sentimen, dan live SQL explorer:

* **Opsi 1 — Streamlit Dashboard (Python)**:
  ```bash
  ./venv/bin/streamlit run src/dashboard/app.py
  ```
  *(Otomatis membuka http://localhost:8501 di browser dengan visualisasi interaktif Plotly)*

* **Opsi 2 — Standalone Fail-Safe Preview (HTML5 / Zero-Setup)**:
  Cukup klik ganda atau buka file [`src/dashboard/standalone_preview.html`](src/dashboard/standalone_preview.html) langsung di peramban web (Chrome/Edge/Safari). Sangat ideal sebagai cadangan darurat presentasi.
