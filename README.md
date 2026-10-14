# 🛒 Data Warehouse & AI-assisted ETL: Olist Brazilian E-Commerce

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](#-metode-1-docker-compose-paling-mudah--direkomendasikan)
[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.11-3776AB?logo=python&logoColor=white)](#-metode-2-lokal-python-virtual-environment)
[![MySQL](https://img.shields.io/badge/MySQL-8.x%20InnoDB-4479A1?logo=mysql&logoColor=white)](#-keputusan-arsitektur-mengapa-mysql-8x--star-schema)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit%201.50-FF4B4B?logo=streamlit&logoColor=white)](#-dashboard-analitik-interaktif)
[![Dataset](https://img.shields.io/badge/Dataset-Kaggle%20Olist%20Brazil-20BEFF?logo=kaggle&logoColor=white)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

Repository ini memuat perancangan dan implementasi menyeluruh sistem **Data Warehouse (DWH)** analitik berbasis metodologi **Kimball Star Schema**, pipeline ETL cerdas dengan integrasi model NLP sentimen ulasan (*AI-Assisted ETL*), serta **Executive & Analytical Dashboard** interaktif menggunakan dataset publik **Olist Brazilian E-Commerce (Kaggle)** yang mencakup lebih dari 100.000 transaksi pesanan.

---

## 📑 Daftar Isi
1. [Latar Belakang & Domain Bisnis](#-latar-belakang--domain-bisnis)
2. [Keputusan Arsitektur: Mengapa MySQL 8.x & Star Schema?](#-keputusan-arsitektur-mengapa-mysql-8x--star-schema)
3. [Arsitektur Star Schema Kimball](#-arsitektur-star-schema-kimball)
4. [Data Quality, Cleansing & Rekonsiliasi](#-data-quality-cleansing--rekonsiliasi)
5. [Integrasi AI dalam Pipeline ETL (NLP Sentimen)](#-integrasi-ai-dalam-pipeline-etl-nlp-sentimen)
6. [5 Key Performance Indicators (KPI) & Temuan Bisnis](#-5-key-performance-indicators-kpi--temuan-bisnis)
7. [Dashboard Analitik Interaktif](#-dashboard-analitik-interaktif)
8. [Panduan Instalasi & Eksekusi Cepat (3 Cara)](#-panduan-instalasi--eksekusi-cepat-3-cara)
   * [Metode 1: Docker Compose (Satu Perintah / Plug & Play)](#metode-1-docker-compose-satu-perintah--plug--play)
   * [Metode 2: Lokal Python Virtual Environment](#metode-2-lokal-python-virtual-environment)
   * [Metode 3: Standalone Fail-Safe Preview (Cadangan Darurat)](#metode-3-standalone-fail-safe-preview-cadangan-darurat)
9. [Panduan Eksekusi Pipeline ETL Manual](#-panduan-eksekusi-pipeline-etl-manual)
10. [Struktur Direktori Repositori](#-struktur-direktori-repositori)
11. [Panduan Demo & Tanya-Jawab Dosen](#-panduan-demo--tanya-jawab-dosen)

---

## 📖 Latar Belakang & Domain Bisnis

### Apa Itu Olist Brazil?
**Olist** adalah platform *marketplace integrator* terbesar di Brazil yang menghubungkan ribuan usaha kecil menengah (*merchants/sellers*) dengan pasar e-commerce ritel nasional.

### Karakteristik Kompleksitas Operasional:
1. **Multi-Seller Fulfillment**: Satu pesanan pembeli (`order_id`) dapat memuat beberapa produk berbeda yang dikirimkan oleh penjual berbeda dari berbagai pelosok wilayah Brazil.
2. **Multi-Payment Split**: Pembeli dapat membayar satu transaksi menggunakan kombinasi metode pembayaran (misal gabungan voucher belanja dan kartu kredit).
3. **Siklus Logistik Luas**: Memiliki rekam jejak waktu lengkap mulai dari checkout, otorisasi bayar, serah terima kurir, tanggal estimasi tiba, hingga paket diterima pelanggan di 27 negara bagian.
4. **Ulasan Pelanggan Bebas (Unstructured Text)**: Ribuan ulasan berisi pesan teks bahasa Portugis yang belum terlabeli secara rapi.

---

## 🛠️ Keputusan Arsitektur: Mengapa MySQL 8.x & Star Schema?

### 1. Mengapa Star Schema (Bukan Snowflake Schema)?
* **Kecepatan Query OLAP**: Pada Star Schema, tabel dimensi sengaja di-denormalisasi untuk meminimalkan operasi `JOIN`. Query agregasi dengan *Window Functions* pada 112k+ baris berjalan dalam hitungan milidetik.
* **Intuitif bagi Business Intelligence**: Skema bintang mudah dipahami oleh analis bisnis dan mempermudah visualisasi data di dashboard.

### 2. Mengapa Memilih MySQL 8.x?
* **Dukungan Window Functions & CTE**: Mendukung `LAG()`, `LEAD()`, `SUM() OVER ()`, dan `WITH` clauses yang esensial untuk kalkulasi Month-over-Month (MoM) growth dan persentase kontribusi omzet.
* **InnoDB Storage Engine**: Menjamin kepatuhan integritas relasional (*ACID compliant*), *foreign key constraint checks*, dan efisiensi pengindeksan surrogate keys.
* **Charset `utf8mb4`**: Mendukung penyimpanan teks ulasan Portugis berkarakter khusus dan aksen latin (*ç, ã, é, ó*).

---

## 📐 Arsitektur Star Schema Kimball

Sistem memodelkan data transaksional ke dalam **1 Tabel Fakta Pusat** dan **7 Tabel Dimensi Kontekstual**:

![Star Schema Diagram](docs/images/star_schema.png)

### Penetapan Grain (Granularitas Fakta):
* **Grain**: **Satu baris mewakili 1 unit item produk dalam 1 nomor pesanan unik** (`order_id` + `order_item_id`).
* **Rasional Desain**: Granularitas *atomic order-item level* memungkinkan analisis fleksibel hingga kombinasi terkecil (tarif ongkir per unit, performa seller per item, serta durasi ekspedisi).

### Ringkasan 8 Tabel Relasional:
| Tipe Tabel | Nama Tabel | Total Baris | Granularitas & Keterangan Kunci |
| :--- | :--- | :---: | :--- |
| **Tabel Fakta** | `fact_order_items` | **112.650** | Atomic unit item produk. Memuat metrik: `price`, `freight_value`, `total_item_value`, `shipping_duration_days`, `delivery_delay_days`, `is_delayed`. |
| **Dimensi** | `dim_date` | 775 | Kalender transaksi harian 2016-2018 (`date_key`, hari, bulan, kuartal, tahun, flag weekend). |
| **Dimensi** | `dim_customers` | 99.441 | Profil geografis pembeli (`customer_city`, `customer_state`, kode pos). |
| **Dimensi** | `dim_products` | 32.951 | Katalog produk, kategori Portugis & terjemahan Inggris, dimensi fisik. |
| **Dimensi** | `dim_sellers` | 3.095 | Profil pedagang mitra dan lokasi gudang merchant. |
| **Dimensi** | `dim_order_status` | 8 | Lookup status siklus pesanan (`delivered`, `shipped`, `canceled`, dsb). |
| **Dimensi** | `dim_payments` | 8 | Profil kombinasi metode bayar dan kelompok tenor cicilan (*installments group*). |
| **Dimensi** | `dim_reviews` | 98.410 | Skor ulasan bintang (1-5) dan kolom hasil anotasi AI **`sentiment_category`**. |

---

## 🧹 Data Quality, Cleansing & Rekonsiliasi

Sebelum masuk ke tahap DWH, data mentah diaudit secara ketat oleh skrip [`src/cleansing/cleansing.py`](src/cleansing/cleansing.py) untuk memastikan kualitas data enterprise:

### Tabel Rekonsiliasi Mutu Data (Audit Sebelum vs Sesudah):
| Entitas Bisnis | Berkas Mentah (Raw) | Baris Awal | Baris Bersih | Selisih (Deduplikasi) | Transformasi Kualitas Utama |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Customers** | `olist_customers_dataset.csv` | 99.441 | 99.441 | 0 | Standarisasi City Title Case, State 2-huruf kapital (SP, RJ), Zip 5-digit padding. |
| **Sellers** | `olist_sellers_dataset.csv` | 3.095 | 3.095 | 0 | Standarisasi kota dan negara bagian merchant, verifikasi keunikan natural key. |
| **Products** | `olist_products_dataset.csv` | 32.951 | 32.951 | 0 | Imputasi 610 kategori NULL ke `'Unknown'`, gabung kamus EN, imputasi dimensi fisik. |
| **Orders** | `olist_orders_dataset.csv` | 99.441 | 99.441 | 0 | Penyeragaman 5 kolom tanggal ke format ISO `YYYY-MM-DD HH:MM:SS`. |
| **Order Items** | `olist_order_items_dataset.csv` | 112.650 | 112.650 | 0 | Validasi moneter non-negatif, hitung `total_item_value` = `price + freight`. |
| **Payments** | `olist_order_payments_dataset.csv` | 103.886 | 103.886 | 0 | Kategorisasi tenor cicilan: Single, Short (2-4x), Medium (5-8x), Long (>8x). |
| **Reviews** | `olist_order_reviews_dataset.csv` | 99.224 | **98.410** | **-814** | **Deduplikasi 814 duplikat review** (ambil timestamp terbaru) & sanitasi string `\r\n`. |

---

## 🤖 Integrasi AI dalam Pipeline ETL (NLP Sentimen)

Modul [`src/etl/ai_transformer.py`](src/etl/ai_transformer.py) mengotomatisasi pengkayaan data ulasan (*data enrichment*) dengan label sentimen:
* **Kategori Target**: `Positive`, `Neutral`, dan `Negative`.
* **Arsitektur Dual AI Engine**:
  1. **Mode Google Gemini API**: Melakukan inferensi NLP berbasis LLM jika API Key `GEMINI_API_KEY` terpasang.
  2. **Mode Leksikon Heuristik Cerdas**: Fallback otomatis berbasis kosakata sentimen ulasan bahasa Portugis (misal: *otimo, excelente, adorei* vs *pessimo, atraso, defeito*) dan rating skor sehingga pipeline dapat berjalan secara offline tanpa kendala kuota token.
* Hasil klasifikasi disimpan langsung pada tabel `dim_reviews` di kolom `sentiment_category`.

---

## 📊 5 Key Performance Indicators (KPI) & Temuan Bisnis

Seluruh query analitik tersedia pada [`sql/analytical_queries.sql`](sql/analytical_queries.sql) dan telah diuji dengan output laporan di [`HASIL_QUERY_ANALITIK_KPI.md`](HASIL_QUERY_ANALITIK_KPI.md):

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                RINGKASAN TEMUAN 5 KPI BISNIS                           │
├────────┬─────────────────────────────┬─────────────────────────────────────────────────┤
│ KPI 1  │ Tren Omzet & MoM Growth     │ Total perputaran omzet R$ 15,8 Juta. Puncak     │
│        │                             │ Black Friday Nov 2017 menembus R$ 1,15 Juta.    │
├────────┼─────────────────────────────┼─────────────────────────────────────────────────┤
│ KPI 2  │ Performa Logistik Wilayah   │ Ketepatan waktu nasional 91,8%. Sao Paulo (SP)  │
│        │                             │ tercepat (8,7 hari / 94,2%), Alagoas (AL) 75,8%.│
├────────┼─────────────────────────────┼─────────────────────────────────────────────────┤
│ KPI 3  │ Top 10 Kategori Produk      │ Health & Beauty (R$ 1,41 Juta) dan Watches      │
│        │                             │ (R$ 1,26 Juta) menguasai >25% pangsa pasar.    │
├────────┼─────────────────────────────┼─────────────────────────────────────────────────┤
│ KPI 4  │ Keterlambatan vs AI Sentimen│ Paket tepat waktu: Rating 4.21, Positif 80.5%.  │
│        │                             │ Paket telat: Rating anjlok 2.55, Negatif 54.7%. │
├────────┼─────────────────────────────┼─────────────────────────────────────────────────┤
│ KPI 5  │ Metode Bayar & Tenor Cicilan│ Kartu Kredit mendominasi 79,6% omzet. Cicilan   │
│        │                             │ >8x mendorong pembelian keranjang mahal (R$ 303)│
└────────┴─────────────────────────────┴─────────────────────────────────────────────────┘
```

---

## 🖥️ Dashboard Analitik Interaktif

Sistem dilengkapi dengan antarmuka visualisasi eksekutif berbasis Streamlit ([`src/dashboard/app.py`](src/dashboard/app.py)):

### Fitur Utama Dashboard:
1. **Hero Cards**: Ringkasan omzet kotor, total unit item, rasio on-time, dan skor rating kepuasan.
2. **Tab Data Quality**: Tabel rekonsiliasi data mentah vs bersih untuk pembuktian mutu data di depan dosen.
3. **Tab KPI 1 - 5**: Visualisasi grafik interaktif Plotly (area chart tren omzet, bar chart logistik wilayah, donut chart kategori, dan grouped bar sentimen AI).
4. **Live AI Sentiment Simulator**: Fitur interaktif di mana penguji dapat mengetik contoh kalimat ulasan bahasa Portugis dan melihat klasifikasi AI secara realtime.
5. **Star Schema & SQL Explorer**: Penjelasan metadata 8 tabel dan runner query SQL resmi yang siap dieksekusi langsung.
6. **Arsitektur Dual-Mode**: Menghubungkan langsung ke server MySQL jika aktif, atau otomatis beralih ke engine in-memory staging data jika offline (**100% fail-safe**).

---

## 🚀 Panduan Instalasi & Eksekusi Cepat (3 Cara)

Pilih salah satu dari 3 cara berikut sesuai kebutuhan presentasi Anda:

### Metode 1: Docker Compose (Satu Perintah / Plug & Play)
*Cocok untuk rekan tim atau penguji yang ingin langsung menjalankan seluruh ekosistem tanpa install Python atau MySQL.*

1. **Pastikan Docker Desktop aktif di laptop Anda.**
2. **Jalankan perintah berikut:**
   ```bash
   git clone https://github.com/widiandickha/tugas-dwh.git
   cd tugas-dwh
   docker compose up -d
   ```
3. **Akses Layanan:**
   * **Dashboard Streamlit**: Buka peramban di `http://localhost:8501`
   * **Database MySQL 8.x**: Aktif di `localhost:3306` (Database: `dwh_olist`, User: `root`, Password kosong). Skema DDL otomatis terinisialisasi.
4. **Menghentikan Layanan:**
   ```bash
   docker compose down
   ```

---

### Metode 2: Lokal Python Virtual Environment
*Cocok untuk pengembangan lokal dan demonstrasi langsung di komputer pengembang.*

1. **Clone dan Masuk ke Direktori Proyek:**
   ```bash
   git clone https://github.com/widiandickha/tugas-dwh.git
   cd tugas-dwh
   ```
2. **Buat dan Aktifkan Virtual Environment:**
   ```bash
   # Di macOS / Linux:
   python3 -m venv venv
   source venv/bin/activate

   # Di Windows:
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. **Instal Dependensi:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Jalankan Dashboard Streamlit:**
   ```bash
   streamlit run src/dashboard/app.py
   ```
   *(Browser akan terbuka secara otomatis di `http://localhost:8501`)*

---

### Metode 3: Standalone Fail-Safe Preview (Cadangan Darurat)
*Sangat direkomendasikan sebagai rencana darurat (backup plan) jika laptop di ruang kuliah mengalami kendala koneksi atau tidak memiliki Python/Docker.*

* Cukup klik ganda atau buka berkas berikut di peramban web (Google Chrome, Microsoft Edge, Safari):
  👉 [`src/dashboard/standalone_preview.html`](src/dashboard/standalone_preview.html)
* **Keunggulan**: Memuat visualisasi Chart.js lengkap, kartu metrik 5 KPI, tabel rekonsiliasi data, dan SQL viewer tanpa memerlukan instalasi software apa pun.

---

## ⚙️ Panduan Eksekusi Pipeline ETL Manual

Jika Anda ingin menjalankan alur pembersihan dan pemuatan data ke database MySQL dari awal:

### 1. Inisialisasi Database MySQL
Pastikan server MySQL 8.x lokal aktif, lalu jalankan:
```bash
mysql -u root -p < sql/schema_dwh.sql
```

### 2. Jalankan Pembersihan Data (Anggota 2)
```bash
python src/cleansing/cleansing.py
```
*Membaca dataset mentah dari `data/raw/` dan mengekspor 7 CSV bersih ke `data/staging/`.*

### 3. Jalankan Pipeline ETL & AI Transformer (Anggota 3)
```bash
python src/etl/etl_pipeline.py
```
*Mengekstrak data staging, melakukan pengayaan sentimen ulasan AI, menghitung metrik logistik, dan memuat 112.650 baris ke database `dwh_olist`.*

### 4. Eksekusi Pengujian 5 Query KPI
```bash
python src/etl/run_kpi_queries.py
```
*Mengeksekusi 5 query SQL analitik dan memperbarui berkas `HASIL_QUERY_ANALITIK_KPI.md`.*

---

## 📂 Struktur Direktori Repositori

```text
DWH BARU/
├── Dockerfile                           # Definisi image kontainer Streamlit dashboard
├── docker-compose.yml                   # Orkestrasi kontainer MySQL 8.x + Dashboard
├── requirements.txt                     # Daftar pustaka Python yang dibutuhkan
├── HASIL_QUERY_ANALITIK_KPI.md          # Laporan resmi hasil pengujian 5 KPI
├── JOBDESK_DAN_WORKFLOW.md              # Pembagian jobdesk & alur kerja RACI tim
├── PANDUAN_ANGGOTA_3.md                 # Panduan teknis ETL & Database Engineer
├── PANDUAN_DEMO_DAN_RINGKASAN_DWH.md    # Panduan praktis skrip demo di depan dosen
├── README.md                            # Dokumentasi utama proyek (berkas ini)
├── report.md                            # Laporan progres berkala proyek (Status 100%)
│
├── sql/                                 # Skrip Basis Data
│   ├── schema_dwh.sql                   # DDL skema Star Schema 8 tabel MySQL 8.x
│   └── analytical_queries.sql           # 5 Query SQL analitik analitis KPI bisnis
│
├── docs/                                # Dokumentasi Arsitektur & Kamus Data
│   ├── business_process.md              # Alur operasional bisnis & rumusan KPI
│   ├── data_cleansing_report.md         # Laporan metrik kualitas data sebelum vs sesudah
│   ├── data_dictionary.md               # Kamus data teknis seluruh atribut tabel
│   ├── dwh_schema_design.md             # Desain Star Schema, Grain, dan ERD DBML
│   └── images/
│       └── star_schema.png              # Gambar diagram ERD Star Schema
│
├── data/                                # Wadah Penyimpanan Dataset
│   ├── raw/                             # Wadah CSV asli Kaggle (diabaikan oleh git)
│   └── staging/                         # 7 File CSV bersih siap pakai (diabaikan oleh git)
│
└── src/                                 # Source Code Program
    ├── cleansing/                       # Modul Pembersihan Data (Anggota 2)
    │   ├── cleansing.py                 # Pipeline pembersihan data otomatis
    │   ├── data_profiling.py            # Skrip audit profil kotoran data awal
    │   └── data_profiling.ipynb         # Notebook eksplorasi kualitas data
    │
    ├── etl/                             # Modul Database & Pipeline ETL (Anggota 3)
    │   ├── ai_transformer.py            # Modul klasifikasi sentimen ulasan (NLP/LLM)
    │   ├── database_config.py           # Konfigurasi koneksi basis data MySQL
    │   ├── etl_pipeline.py              # Pipeline ekstraksi, transformasi, & load DWH
    │   └── run_kpi_queries.py           # Runner pengujian otomatis 5 KPI bisnis
    │
    └── dashboard/                       # Modul Antarmuka Visualisasi Analitik
        ├── app.py                       # Dashboard analitik interaktif (Streamlit)
        ├── data_loader.py               # Dual-mode data engine (MySQL + Staging Fallback)
        └── standalone_preview.html      # Cadangan darurat dashboard (HTML5 / Tailwind)
```

---

## 🎓 Panduan Demo & Tanya-Jawab Dosen

Untuk persiapan demonstrasi di hadapan dosen pengampu, buka panduan lengkap langkah-demi-langkah pada:  
👉 **[`PANDUAN_DEMO_DAN_RINGKASAN_DWH.md`](PANDUAN_DEMO_DAN_RINGKASAN_DWH.md)**

Dokumen tersebut memuat skrip presentasi 7-10 menit, contekan jawaban pertanyaan dosen (*Q&A Defense Guide*: mengapa Star Schema, mengapa grain item-level, cara kerja modul AI), serta alur demonstrasi interaktif.

---
*Proyek ini disusun untuk memenuhi Tugas Besar Mata Kuliah Pangkalan Data (Data Warehouse & AI-Assisted ETL).*
