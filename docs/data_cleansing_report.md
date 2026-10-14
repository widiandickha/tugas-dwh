# 🧹 Laporan Kualitas & Pembersihan Data (Data Cleansing Report)

* **Proyek:** Perancangan Data Warehouse & AI-assisted ETL: Olist Brazilian E-Commerce
* **Penyusun:** Anggota 2 (Data Quality & Cleansing Engineer)
* **Tanggal:** 13 Oktober 2026
* **Status:** Selesai 100% — Data bersih siap digunakan untuk Staging & ETL oleh Anggota 3.

---

## 1. Ringkasan Eksekutif

Tahapan *Data Profiling* dan *Data Cleansing* telah berhasil diselesaikan oleh **Anggota 2**. Seluruh data mentah dari 9 file CSV Kaggle telah diaudit, dibersihkan dari *missing values*, dinormalisasi format teks dan tanggalnya, diperkaya dengan terjemahan bahasa Inggris, serta diekspor ke format CSV bersih di direktori `data/staging/`.

Struktur data pada folder `data/staging/` telah sepenuhnya diselaraskan dengan spesifikasi kamus data teknis pada [`docs/data_dictionary.md`](data_dictionary.md) sehingga **Anggota 3** dapat langsung memproses tahap ETL tanpa kendala inkonsistensi skema.

---

## 2. Temuan Audit Kualitas Data Awal (*Data Profiling Findings*)

Sebelum dilakukan pembersihan, skrip [`src/cleansing/data_profiling.py`](../src/cleansing/data_profiling.py) dijalankan untuk mengaudit 9 file CSV mentah di `data/raw/`. Temuan-temuan kunci meliputi:

1. **Inkonsistensi Format Teks & Spasi:**
   * Kolom kota pada pelanggan (`customer_city`) dan penjual (`seller_city`) memuat teks campuran huruf kecil acak, singkatan, serta spasi berlebih.
   * Kolom kode negara bagian (`customer_state`, `seller_state`) memerlukan penyeragaman menjadi huruf kapital (2 karakter standar).
2. **Ketiadaan Terjemahan Kategori Produk:**
   * Terdapat 610 baris pada `olist_products_dataset.csv` dengan kategori `NULL`.
   * Dua kategori Portugis (`pc_gamer` dan `portateis_cozinha_e_preparadores_de_alimentos`) belum memiliki pasangan terjemahan pada `product_category_name_translation.csv`.
   * Kolom dimensi fisik barang (`product_weight_g`, panjang, tinggi, lebar) memiliki beberapa nilai `NULL`.
3. **Format Tanggal Campuran:**
   * Kolom waktu pada tabel pesanan (`orders`) dan ulasan (`reviews`) tersimpan sebagai *string* dengan format timestamp bervariasi yang berisiko gagal saat di-parsing ke MySQL `DATETIME`.
4. **Anomali Karakter pada Ulasan Pelanggan:**
   * Kolom komentar ulasan (`review_comment_message`) memuat karakter *newline* (`\n`) dan *carriage return* (`\r`) yang dapat merusak pembacaan baris saat di-load oleh parser file atau pipeline ETL.
   * Terdapat 814 duplikasi pada `review_id` yang memerlukan deduplikasi berdasarkan timestamp jawaban terakhir (`review_answer_timestamp`).
5. **Kebutuhan Pengelompokan Pembayaran:**
   * Kolom cicilan (`payment_installments`) memiliki rentang 0 hingga 24 kali cicilan yang belum terkelompokkan ke dalam kategori analitik.

---

## 3. Aturan & Transformasi Pembersihan Data (*Cleansing Rules*)

Pembersihan diotomatisasi melalui skrip Python [`src/cleansing/cleansing.py`](../src/cleansing/cleansing.py) dengan aturan berikut:

### A. Tabel Pelanggan (`clean_customers.csv`)
* **Trimming & Normalisasi Teks:** Kolom `customer_id` dan `customer_unique_id` di-strip dari spasi luar.
* **Standarisasi Lokasi:** `customer_city` diubah menjadi *Title Case* (contoh: `sao paulo` -> `Sao Paulo`). `customer_state` diubah menjadi *Uppercase* (contoh: `sp` -> `SP`).
* **Format Kode Pos:** `customer_zip_code_prefix` diformat konsisten 5 digit string dengan padding nol kiri (`zfill(5)`).
* **Deduplikasi:** Verifikasi keunikan natural key `customer_id`.

### B. Tabel Penjual (`clean_sellers.csv`)
* **Standarisasi Lokasi:** `seller_city` diformat *Title Case*, `seller_state` diformat *Uppercase*.
* **Format Kode Pos:** `seller_zip_code_prefix` diformat 5 digit string.
* **Deduplikasi:** Memastikan keunikan `seller_id`.

### C. Tabel Produk (`clean_products.csv`)
* **Penanganan Null Kategori:** Kategori produk yang kosong diisi dengan string `'Unknown'`.
* **Penyempurnaan Terjemahan:** Menambahkan kamus khusus untuk kategori `pc_gamer` dan `portateis_cozinha_e_preparadores_de_alimentos` ke terjemahan bahasa Inggris sebelum digabungkan (*left join*).
* **Imputasi Nilai Numerik Fisik:** Kolom `product_weight_g`, `product_length_cm`, `product_height_cm`, dan `product_width_cm` yang bernilai `NULL` diisi dengan `0.00` dan dibulatkan 2 desimal.

### D. Tabel Pesanan (`clean_orders.csv`)
* **Standarisasi Datetime:** Seluruh 5 kolom waktu (`order_purchase_timestamp`, `order_approved_at`, `order_delivered_carrier_date`, `order_delivered_customer_date`, `order_estimated_delivery_date`) dikonversi ke format standar `YYYY-MM-DD HH:MM:SS`. Nilai kosong (karena pesanan belum terkirim/batal) dibiarkan kosong tanpa merusak tipe format.
* **Normalisasi Status:** Kolom `order_status` diubah menjadi huruf kecil bersih (*lowercase trimmed*).

### E. Tabel Item Pesanan (`clean_order_items.csv`)
* **Pembersihan Moneter:** Kolom `price` dan `freight_value` dipastikan berupa nilai desimal non-negatif (`clip(lower=0.0)`).
* **Kolom Turunan Awal:** Menambahkan kolom `total_item_value` = `price + freight_value` untuk mempermudah agregasi ETL.
* **Format Waktu:** Kolom batas kirim `shipping_limit_date` diseragamkan ke `YYYY-MM-DD HH:MM:SS`.

### F. Tabel Pembayaran (`clean_order_payments.csv`)
* **Normalisasi Tipe:** Kolom `payment_type` di-lowercase dan dibersihkan dari spasi liar.
* **Kategorisasi Cicilan:** Membentuk kolom `payment_installments_group` sesuai ketentuan:
  * $\le 1$ kali $\rightarrow$ `'Single Payment'`
  * $2 - 4$ kali $\rightarrow$ `'Short Term (2-4x)'`
  * $5 - 8$ kali $\rightarrow$ `'Medium Term (5-8x)'`
  * $> 8$ kali $\rightarrow$ `'Long Term (>8x)'`

### G. Tabel Ulasan (`clean_order_reviews.csv`)
* **Sanitasi Teks Komentar:** Menghapus karakter pemecah baris (`\r`, `\n`, `\t`) dari kolom `review_comment_title` dan `review_comment_message` agar file CSV tetap aman dibaca oleh parser tanpa memecah baris ulasan.
* **Validasi Skor:** Skor ulasan dipastikan berada pada rentang batas integer 1 s.d. 5.
* **Deduplikasi Ulasan:** Dari 99.224 ulasan mentah, terdapat 814 duplikasi `review_id`. Diambil data ulasan paling baru berdasarkan `review_answer_timestamp` terbesar, menghasilkan 98.410 baris ulasan unik.

---

## 4. Tabel Perbandingan Sebelum vs Sesudah Pembersihan (*Before vs After*)

| Nama Dataset Mentah | File Bersih Staging | Baris Awal | Baris Bersih | Selisih (Deduplikasi) | Transformasi Kunci yang Diterapkan |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `olist_customers_dataset.csv` | `clean_customers.csv` | 99,441 | 99,441 | 0 | City Title Case, State Uppercase, Zip 5-digit string |
| `olist_sellers_dataset.csv` | `clean_sellers.csv` | 3,095 | 3,095 | 0 | City Title Case, State Uppercase, Zip 5-digit string |
| `olist_products_dataset.csv` | `clean_products.csv` | 32,951 | 32,951 | 0 | Merge terjemahan EN, imputasi 610 missing kategori, imputasi bobot/dimensi |
| `olist_orders_dataset.csv` | `clean_orders.csv` | 99,441 | 99,441 | 0 | Standarisasi 5 kolom tanggal ke `YYYY-MM-DD HH:MM:SS`, status lowercase |
| `olist_order_items_dataset.csv` | `clean_order_items.csv` | 112,650 | 112,650 | 0 | Validasi numerik harga & ongkir, penambahan kolom `total_item_value` |
| `olist_order_payments_dataset.csv` | `clean_order_payments.csv` | 103,886 | 103,886 | 0 | Pembentukan kolom `payment_installments_group` (Single/Short/Medium/Long) |
| `olist_order_reviews_dataset.csv` | `clean_order_reviews.csv` | 99,224 | 98,410 | -814 | Penghapusan `\r\n` pada pesan review, deduplikasi ulasan terupdate |

---

## 5. Status Berkas Deliverable Anggota 2

* [x] Dataset mentah lengkap tersimpan di [`data/raw/`](../data/raw/).
* [x] Script profiling kualitas data: [`src/cleansing/data_profiling.py`](../src/cleansing/data_profiling.py).
* [x] Notebook profiling Jupyter: [`src/cleansing/data_profiling.ipynb`](../src/cleansing/data_profiling.ipynb).
* [x] Script pembersihan otomatis: [`src/cleansing/cleansing.py`](../src/cleansing/cleansing.py).
* [x] 7 File dataset bersih tersimpan di [`data/staging/`](../data/staging/).
* [x] Laporan kualitas data: [`docs/data_cleansing_report.md`](data_cleansing_report.md).

Data telah siap 100% dan diserahterimakan kepada **Anggota 3** untuk pemrosesan AI Transformer & Database Loading.
