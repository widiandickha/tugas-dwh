"""
Script Profiling Kualitas Data Mentah (Olist Brazilian E-Commerce)
Penyusun: Anggota 2 (Data Quality & Cleansing Engineer)
Tujuan: Mengidentifikasi missing values, duplikasi, anomali tipe data, dan inkonsistensi
        sebelum data dibersihkan untuk staging.
"""

import os
import sys
import glob
import pandas as pd
import numpy as np

# Pastikan output konsol Windows mendukung UTF-8
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw')
OUTPUT_REPORT = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'profiling_raw_summary.txt')

def profile_dataset(file_path):
    filename = os.path.basename(file_path)
    print(f"\n========================================================")
    print(f"📊 MEMERIKSA FILE: {filename}")
    print(f"========================================================")
    
    df = pd.read_csv(file_path)
    total_rows, total_cols = df.shape
    total_dupes = df.duplicated().sum()
    
    summary = []
    summary.append(f"Berkas: {filename}")
    summary.append(f"Dimensi: {total_rows:,} baris x {total_cols} kolom")
    summary.append(f"Duplikasi Baris Penuh: {total_dupes:,} baris ({total_dupes/total_rows*100:.2f}%)")
    summary.append("\nRincian Kolom, Tipe Data, & Missing Values:")
    summary.append(f"{'Nama Kolom':<35} | {'Tipe Data':<12} | {'Null Count':<10} | {'Null (%)':<8} | {'Nilai Unik':<10}")
    summary.append("-" * 85)
    
    for col in df.columns:
        null_count = df[col].isnull().sum()
        null_pct = (null_count / total_rows) * 100
        dtype_str = str(df[col].dtype)
        unique_cnt = df[col].nunique()
        summary.append(f"{col:<35} | {dtype_str:<12} | {null_count:<10,d} | {null_pct:<7.2f}% | {unique_cnt:<10,d}")
        
    print("\n".join(summary))
    return "\n".join(summary) + "\n\n"

def main():
    if not os.path.exists(RAW_DIR):
        print(f"Error: Direktori {RAW_DIR} tidak ditemukan!")
        return

    csv_files = sorted(glob.glob(os.path.join(RAW_DIR, "*.csv")))
    if not csv_files:
        print(f"Peringatan: Tidak ada file CSV di {RAW_DIR}")
        return

    full_log = ["=== LAPORAN PROFILING DATA MENTAH (RAW DATASET PROFILING) ===\n"]
    for f in csv_files:
        res = profile_dataset(f)
        full_log.append(res)

    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as out_f:
        out_f.writelines(full_log)
        
    print(f"\n[SUKSES] Profiling selesai! Hasil lengkap disimpan di: {OUTPUT_REPORT}")

if __name__ == "__main__":
    main()
