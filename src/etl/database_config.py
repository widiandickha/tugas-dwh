"""
Konfigurasi Koneksi Basis Data Data Warehouse (MySQL 8.x)
Penyusun: Anggota 3 (AI-Driven ETL & Database Engineer)
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# Konfigurasi parameter database MySQL
# Sesuaikan DB_USER dan DB_PASSWORD sesuai dengan kredensial server MySQL lokal Anda
DB_HOST = os.getenv('DWH_MYSQL_HOST', 'localhost')
DB_PORT = int(os.getenv('DWH_MYSQL_PORT', 3306))
DB_USER = os.getenv('DWH_MYSQL_USER', 'root')
DB_PASS = os.getenv('DWH_MYSQL_PASSWORD', '')  # Masukkan password root MySQL Anda di sini jika ada
DB_NAME = os.getenv('DWH_MYSQL_DATABASE', 'dwh_olist')

def get_db_url() -> str:
    """Mengembalikan connection string URL SQLAlchemy untuk MySQL."""
    if DB_PASS:
        return f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    else:
        return f"mysql+pymysql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

def get_db_engine():
    """Membuat dan mengembalikan SQLAlchemy Engine."""
    url = get_db_url()
    return create_engine(url, pool_recycle=3600, echo=False)

if __name__ == "__main__":
    print(f"Target Database URL: mysql+pymysql://{DB_USER}:****@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            print("✅ Koneksi ke MySQL 'dwh_olist' BERHASIL!")
    except Exception as e:
        print(f"❌ Gagal koneksi ke MySQL: {e}")
        print("💡 Tips: Pastikan server MySQL 8.x aktif dan database 'dwh_olist' sudah dibuat via sql/schema_dwh.sql")
