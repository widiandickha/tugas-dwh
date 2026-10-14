"""
Modul AI Sentiment Transformer untuk Ulasan Pelanggan (dim_reviews)
Penyusun: Anggota 3 (AI-Driven ETL & Database Engineer)

Fungsi:
1. Menerima data ulasan pelanggan dari 'clean_order_reviews.csv'.
2. Mengklasifikasikan sentimen review ke dalam: 'Positive', 'Neutral', 'Negative'.
3. Mendukung dua mode:
   - Mode AI API (Google Gemini API / OpenAI) untuk inferensi AI berbasis LLM.
   - Mode Heuristik Cerdas Berbasis Skor & Leksikon Portugis (Fallback otomatis jika offline/kuota habis).
"""

import os
import sys
import pandas as pd
from typing import List, Optional

# Pastikan console Windows mendukung UTF-8
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

def classify_sentiment_heuristic(score: int, comment: str) -> str:
    """
    Klasifikasi sentimen berbasis skor rating dan leksikon ulasan bahasa Portugis.
    Digunakan sebagai fallback cepat atau jika kuota API LLM habis.
    """
    comment_lower = str(comment).lower().strip()
    
    # Kata kunci positif & negatif dalam bahasa Portugis
    neg_keywords = ['pessimo', 'ruim', 'errado', 'defeito', 'demorou', 'atraso', 'nao recebi', 'falta', 'quebrado', 'horrivel']
    pos_keywords = ['otimo', 'excelente', 'perfeito', 'adorei', 'recomendo', 'parabens', 'rapido', 'chegou antes', 'muito bom']
    
    if any(k in comment_lower for k in neg_keywords) and score <= 3:
        return 'Negative'
    if any(k in comment_lower for k in pos_keywords) and score >= 3:
        return 'Positive'
        
    if score >= 4:
        return 'Positive'
    elif score == 3:
        return 'Neutral'
    else:
        return 'Negative'

def classify_with_gemini(sample_texts: List[str]) -> List[str]:
    """
    Klasifikasi sentimen menggunakan Google Gemini API (jika library dan API key tersedia).
    """
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = (
            "Klasifikasikan sentimen ulasan e-commerce berikut ke dalam salah satu dari: Positive, Neutral, Negative.\n"
            "Jawab hanya satu kata per baris.\n\n"
            + "\n".join([f"{i+1}. {text}" for i, text in enumerate(sample_texts)])
        )
        response = model.generate_content(prompt)
        results = [line.strip() for line in response.text.splitlines() if line.strip()]
        return results
    except Exception as e:
        print(f"[Warning] Gagal memanggil Gemini API: {e}. Mengalihkan ke heuristik cerdas.")
        return []

def enrich_reviews_with_sentiment(df_reviews: pd.DataFrame, use_ai_sample_count: int = 50) -> pd.DataFrame:
    """
    Memperkaya DataFrame ulasan dengan kolom 'sentiment_category'.
    
    Args:
        df_reviews: DataFrame yang memuat kolom 'review_score' dan 'review_comment_message'.
        use_ai_sample_count: Jumlah baris sampel yang diproses langsung via API LLM (jika API key tersedia).
    """
    print("🤖 Memulai proses klasifikasi sentimen ulasan pelanggan...")
    
    # Inisialisasi klasifikasi heuristik awal
    sentiments = []
    for _, row in df_reviews.iterrows():
        s = classify_sentiment_heuristic(row['review_score'], row.get('review_comment_message', ''))
        sentiments.append(s)
        
    df_reviews['sentiment_category'] = sentiments
    
    # Jika API key Gemini tersedia, lakukan pengujian AI pada sampel
    if GEMINI_API_KEY and use_ai_sample_count > 0:
        print(f"✨ API Key terdeteksi. Menjalankan inferensi Gemini AI pada {use_ai_sample_count} sampel teks...")
        sample_indices = df_reviews[df_reviews['review_comment_message'].str.len() > 10].head(use_ai_sample_count).index
        sample_texts = df_reviews.loc[sample_indices, 'review_comment_message'].tolist()
        ai_results = classify_with_gemini(sample_texts)
        if len(ai_results) == len(sample_indices):
            df_reviews.loc[sample_indices, 'sentiment_category'] = ai_results
            print("✅ Inferensi sampel Gemini AI berhasil diintegrasikan!")
            
    dist = df_reviews['sentiment_category'].value_counts().to_dict()
    print(f"📊 Distribusi Sentimen Hasil Transformasi AI: {dist}")
    return df_reviews

if __name__ == "__main__":
    test_data = pd.DataFrame([
        {'review_score': 5, 'review_comment_message': 'Produto excelente, chegou muito rapido! Recomendo.'},
        {'review_score': 1, 'review_comment_message': 'Nao recebi o produto, pessimo atendimento!'},
        {'review_score': 3, 'review_comment_message': 'Produto regular, de acordo com o preco.'}
    ])
    res = enrich_reviews_with_sentiment(test_data, use_ai_sample_count=0)
    print(res[['review_score', 'review_comment_message', 'sentiment_category']])
