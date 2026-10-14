# Menggunakan image Python resmi berbasis Debian slim yang ringan dan stabil
FROM python:3.11-slim

# Menentukan direktori kerja di dalam kontainer
WORKDIR /app

# Menginstal utilitas sistem yang diperlukan
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Menyalin berkas dependensi dan menginstalnya
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Menyalin seluruh aset proyek ke dalam kontainer
COPY . .

# Mengekspos port Streamlit
EXPOSE 8501

# Konfigurasi pengecekan kesehatan kontainer (Healthcheck)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Menjalankan Streamlit Dashboard
ENTRYPOINT ["streamlit", "run", "src/dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
