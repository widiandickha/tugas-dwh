# 📘 Panduan Lengkap Eksekusi Tugas Anggota 3: AI-Driven ETL & Database Engineer

* **Proyek:** Data Warehouse & AI-assisted ETL — Olist Brazilian E-Commerce
* **Mata Kuliah:** Pangkalan Data (Semester 3)
* **Penanggung Jawab:** **Anggota 3**
* **Status Prasyarat:** **Fase 1 (Arsitektur oleh Anggota 1)** dan **Fase 2 (Cleansing oleh Anggota 2)** telah **SELESAI 100%**.
* **Bahan Masukan (Input):** Seluruh data bersih sudah tersedia di [`data/staging/`](data/staging/).

---

## 🧭 Daftar Isi Panduan
1. [Ringkasan Peran & Deliverables](#1-ringkasan-peran--deliverables)
2. [Persiapan Dependensi & Lingkungan Python](#2-persiapan-dependensi--lingkungan-python)
3. [Langkah 1: Setup Database MySQL & Inisialisasi Skema DDL](#langkah-1-setup-database-mysql--inisialisasi-skema-ddl)
4. [Langkah 2: Konfigurasi Koneksi Basis Data (`database_config.py`)](#langkah-2-konfigurasi-koneksi-basis-data-database_configpy)
5. [Langkah 3: Modul Transformasi AI Sentimen Ulasan (`ai_transformer.py`)](#langkah-3-modul-transformasi-ai-sentimen-ulasan-ai_transformerpy)
6. [Langkah 4: Eksekusi Pipeline ETL ke MySQL (`etl_pipeline.py`)](#langkah-4-eksekusi-pipeline-etl-ke-mysql-etl_pipelinepy)
7. [Langkah 5: Validasi Data Menggunakan 5 Query Analitik KPI](#langkah-5-validasi-data-menggunakan-5-query-analitik-kpi)
8. [Panduan Troubleshooting & Solusi Error Umum](#panduan-troubleshooting--solusi-error-umum)
9. [Checklist Final Deliverables Anggota 3](#checklist-final-deliverables-anggota-3)

---

## 1. Ringkasan Peran & Deliverables

Sebagai **Anggota 3**, fokus utama Anda adalah sisi **Database Engine, Integrasi AI, dan Pipeline Loading**. Seluruh script boilerplate telah disiapkan di folder [`src/etl/`](src/etl/) dan siap Anda eksekusi atau sesuaikan:

| No | Komponen Deliverable | Berkas Terkait | Deskripsi Output |
| :---: | :--- | :--- | :--- |
| 1 | **Database MySQL Target** | `sql/schema_dwh.sql` | Basis data `dwh_olist` yang memuat 8 tabel fisik (1 fakta + 7 dimensi) dengan Foreign Key aktif. |
| 2 | **Konfigurasi Koneksi** | `src/etl/database_config.py` | Modul koneksi SQLAlchemy & PyMySQL yang terhubung ke server lokal. |
| 3 | **Modul AI Sentimen** | `src/etl/ai_transformer.py` | Modul pengayaan ulasan pembeli (`Positive`, `Neutral`, `Negative`) berbasis LLM / cerdas. |
| 4 | **Pipeline ETL Otomatis** | `src/etl/etl_pipeline.py` | Skrip Extract dari staging, Transform surrogate keys & relasi, serta Load ke database. |
| 5 | **Validasi Query Analitik** | `sql/analytical_queries.sql` | Hasil pengujian 5 KPI bisnis untuk bahan slide & laporan akhir. |

---

## 2. Persiapan Dependensi & Lingkungan Python

Pastikan modul Python untuk koneksi MySQL dan AI telah terpasang di komputer Anda. Buka terminal (PowerShell atau Command Prompt) dan jalankan:

```bash
pip install pymysql cryptography sqlalchemy google-generativeai
```

> **Penjelasan Library:**
> * `pymysql` & `cryptography`: Driver murni Python untuk menghubungkan SQLAlchemy ke MySQL 8.x.
> * `sqlalchemy`: ORM dan engine eksekusi batch loading berkecepatan tinggi (`chunksize`).
> * `google-generativeai`: SDK resmi untuk inferensi Google Gemini API.

---

## 3. Langkah 1: Setup Database MySQL & Inisialisasi Skema DDL

Pastikan server MySQL 8.x Anda telah aktif (bisa menggunakan **XAMPP MySQL**, **MySQL Server bawaan**, **Docker**, atau **MySQL Workbench**).

### Opsi A: Menggunakan CLI MySQL (Terminal)
```bash
mysql -u root -p < sql/schema_dwh.sql
```
*(Tekan Enter dan masukkan password root MySQL Anda jika ada).*

### Opsi B: Menggunakan GUI (MySQL Workbench / DBeaver / phpMyAdmin)
1. Buka aplikasi **MySQL Workbench** atau **DBeaver**.
2. Buat koneksi ke server lokal (`localhost:3306`).
3. Buka file [`sql/schema_dwh.sql`](sql/schema_dwh.sql).
4. Klik tombol **Execute / Run (Ikon Petir)** untuk mengeksekusi seluruh skrip.
5. Lakukan *Refresh* pada panel Schema: pastikan database **`dwh_olist`** muncul dengan 8 tabel:
   * `dim_date`
   * `dim_customers`
   * `dim_products`
   * `dim_sellers`
   * `dim_order_status`
   * `dim_payments`
   * `dim_reviews`
   * `fact_order_items`

---

## 4. Langkah 2: Konfigurasi Koneksi Basis Data (`database_config.py`)

Buka file [`src/etl/database_config.py`](src/etl/database_config.py). Periksa parameter koneksi pada bagian atas file:

```python
DB_HOST = os.getenv('DWH_MYSQL_HOST', 'localhost')
DB_PORT = int(os.getenv('DWH_MYSQL_PORT', 3306))
DB_USER = os.getenv('DWH_MYSQL_USER', 'root')
DB_PASS = os.getenv('DWH_MYSQL_PASSWORD', '')  # Isi jika MySQL Anda memiliki password
DB_NAME = os.getenv('DWH_MYSQL_DATABASE', 'dwh_olist')
```

> **Tips:** Jika user `root` MySQL Anda menggunakan password (misalnya `admin123`), Anda bisa langsung mengubah nilai default `DB_PASS` menjadi `'admin123'`, atau menyetel Environment Variable di terminal:
> ```bash
> $env:DWH_MYSQL_PASSWORD="password_anda"
> ```

### Uji Coba Koneksi:
Jalankan skrip tes koneksi dari direktori `tugas-dwh`:
```bash
python src/etl/database_config.py
```
**Output yang diharapkan:**
```text
Target Database URL: mysql+pymysql://root:****@localhost:3306/dwh_olist
✅ Koneksi ke MySQL 'dwh_olist' BERHASIL!
```

---

## 5. Langkah 3: Modul Transformasi AI Sentimen Ulasan (`ai_transformer.py`)

Skrip [`src/etl/ai_transformer.py`](src/etl/ai_transformer.py) bertugas mengisi kolom `sentiment_category` pada tabel `dim_reviews`.

### Dua Mode Kerja yang Tersedia:
1. **Mode AI Berbasis Gemini API (Direkomendasikan untuk Sampel / Live Demo):**
   * Dapatkan Google Gemini API Key gratis di [Google AI Studio](https://aistudio.google.com/).
   * Set API key di terminal sebelum menjalankan script:
     ```bash
     $env:GEMINI_API_KEY="AIzaSyYourGeminiApiKeyHere"
     ```
   * Modul secara otomatis akan memproses batch sampel ulasan menggunakan model LLM `gemini-1.5-flash`.
2. **Mode Fallback Heuristik Cerdas (Otomatis & Kuota-Aman):**
   * Jika tidak ada API key atau kuota gratis habis, skrip otomatis mengklasifikasikan sentimen berdasarkan kombinasi skor rating (1-5) dan analisis kata kunci ulasan bahasa Portugis (*otimo, ruim, pessimo, recomendo, atraso, dsb*).
   * **Hasil:** 100% dari 98.410 ulasan tetap terklasifikasi secara akurat tanpa error.

### Uji Coba Modul AI:
```bash
python src/etl/ai_transformer.py
```

---

## 6. Langkah 4: Eksekusi Pipeline ETL ke MySQL (`etl_pipeline.py`)

Setelah database dan konfigurasi siap, jalankan pipeline ETL utama:

```bash
python src/etl/etl_pipeline.py
```

### Urutan Eksekusi yang Dijalankan oleh Pipeline:
1. **[FASE 1: EXTRACT]** Membaca 7 file CSV bersih dari `data/staging/`.
2. **[FASE 2: TRANSFORM & LOAD DIMENSI]**:
   * Membangun kalender transaksi `dim_date` (2016 - 2018).
   * Memuat `dim_customers` (99.441 baris).
   * Memuat `dim_products` (32.951 baris).
   * Memuat `dim_sellers` (3.095 baris).
   * Memuat lookup status `dim_order_status` (8 status).
   * Memuat kombinasi cara bayar `dim_payments` (kategori cicilan).
   * Memperkaya dan memuat `dim_reviews` (98.410 baris dengan sentimen AI).
3. **[FASE 3: TRANSFORM & LOAD TABEL FAKTA]**:
   * Menghubungkan surrogate key dari seluruh 7 tabel dimensi ke tabel fakta.
   * Menghitung metrik analitik:
     * `shipping_duration_days` = selisih tanggal terima dengan tanggal beli.
     * `delivery_delay_days` = selisih tanggal terima dengan estimasi pengiriman.
     * `is_delayed` = flag `1` jika terlambat, `0` jika tepat waktu.
     * `total_item_value` = `price + freight_value`.
   * Memuat 112.650 baris ke `fact_order_items` secara bertahap (*batching chunksize=10.000*).
4. **[FASE 4: VERIFIKASI]**: Menampilkan ringkasan jumlah baris tiap tabel di database.

---

## 7. Langkah 5: Validasi Data Menggunakan 5 Query Analitik KPI

Setelah ETL selesai, buktikan keberhasilan implementasi Data Warehouse dengan mengeksekusi berkas [`sql/analytical_queries.sql`](sql/analytical_queries.sql):

### Cara Menjalankan Query:
```bash
mysql -u root -p dwh_olist < sql/analytical_queries.sql
```
*(Atau buka dan eksekusi tab query di MySQL Workbench).*

### Rincian 5 Query & Bahan Presentasi:

#### Query 1: Tren Pendapatan & Pertumbuhan Bulanan (MoM Growth)
* **Teknik SQL:** Common Table Expression (CTE) & Window Function `LAG() OVER (ORDER BY year, month)`.
* **Insight yang Diambil:** Kapan puncak omzet terjadi (misal lonjakan belanja akhir tahun / Black Friday November 2017) dan laju persentase pertumbuhan bulanan.

#### Query 2: Performa Logistik & On-Time Delivery Rate per Negara Bagian
* **Teknik SQL:** Agregasi kondisional `COUNT(CASE WHEN is_delayed = 0 THEN 1 END) / COUNT(*) * 100`.
* **Insight yang Diambil:** Negara bagian mana yang memiliki rasio pengiriman tercepat vs wilayah pedalaman yang sering mengalami keterlambatan kirim.

#### Query 3: Top 10 Kategori Produk Terlaris & Kontribusi Omzet
* **Teknik SQL:** Window Function `SUM(total_category_revenue) OVER ()`.
* **Insight yang Diambil:** Menemukan 10 kategori produk penyumbang omzet terbesar (misal: *health_beauty*, *watches_gifts*, *bed_bath_table*) beserta persentase kontribusinya terhadap pasar.

#### Query 4: Dampak Keterlambatan Logistik terhadap Skor Ulasan & Sentimen AI
* **Teknik SQL:** `GROUP BY is_delayed` menggabungkan `review_score` dan kolom AI `sentiment_category`.
* **Insight yang Diambil:** Membuktikan hipotesis bisnis bahwa pesanan yang terlambat (`is_delayed = 1`) mengalami lonjakan ulasan rating 1-2 serta sentimen `Negative` yang signifikan dibandingkan pesanan tepat waktu.

#### Query 5: Preferensi Metode Pembayaran & Distribusi Cicilan
* **Teknik SQL:** `GROUP BY payment_type, payment_installments_group`.
* **Insight yang Diambil:** Menunjukkan dominasi transaksi kartu kredit dengan opsi cicilan jangka panjang (*Long Term >8x*) pada transaksi beromzet tinggi.

---

## 8. Panduan Troubleshooting & Solusi Error Umum

### 🔴 Error 1: `ModuleNotFoundError: No module named 'pymysql'`
* **Solusi:** Jalankan `pip install pymysql cryptography sqlalchemy`.

### 🔴 Error 2: `OperationalError: (2003, "Can't connect to MySQL server on 'localhost'")`
* **Penyebab:** Server MySQL belum menyala.
* **Solusi:** Buka XAMPP Control Panel dan klik tombol **Start** pada modul MySQL, atau aktifkan service MySQL lewat Windows Services (`services.msc`).

### 🔴 Error 3: `OperationalError: (1049, "Unknown database 'dwh_olist'")`
* **Penyebab:** Database belum dibuat.
* **Solusi:** Jalankan file `sql/schema_dwh.sql` terlebih dahulu sebelum menjalankan pipeline ETL.

### 🔴 Error 4: `IntegrityError: (1452, "Cannot add or update a child row: a foreign key constraint fails")`
* **Penyebab:** Urutan loading terbalik (memasukkan tabel fakta sebelum tabel dimensi selesai dimuat).
* **Solusi:** Pipeline `etl_pipeline.py` sudah mengatur urutan pemuatan secara otomatis (dimensi dulu, baru fakta). Pastikan Anda menjalankan pipeline secara utuh tanpa modifikasi urutan fungsi.

### 🔴 Error 5: `PacketTooBigError` atau Memori Penuh
* **Solusi:** Script `etl_pipeline.py` sudah menggunakan parameter `chunksize=10000` sehingga data di-streaming per 10.000 baris secara aman tanpa membebani RAM laptop.

---

## 9. Checklist Final Deliverables Anggota 3

Gunakan checklist ini untuk memastikan seluruh tanggung jawab Anda telah tuntas:

- [ ] Server MySQL 8.x telah terpasang dan database `dwh_olist` berhasil diinisialisasi melalui `sql/schema_dwh.sql`.
- [ ] Modul koneksi `database_config.py` berhasil terkoneksi ke MySQL lokal.
- [ ] Modul AI `ai_transformer.py` berhasil mengisi kolom sentimen ulasan.
- [ ] Pipeline `etl_pipeline.py` sukses dieksekusi sampai muncul pesan `"🎉 ETL PIPELINE SELESAI DENGAN SUKSES!"`.
- [ ] Seluruh 8 tabel di MySQL terisi data (terkonfirmasi via query `SELECT COUNT(*)`).
- [ ] Skrip `sql/analytical_queries.sql` berhasil dijalankan dan menghasilkan tabel output 5 KPI.
- [ ] Screenshot tabel output query disimpan untuk bahan penyusunan laporan akhir kelompok dan slide presentasi.

---

*Penyusun Handover: Tim Pengembang DWH Kelompok*  
*Jika ada kendala saat eksekusi kode, koordinasikan langsung di grup kelompok.*
