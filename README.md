# IndoPrice - Sistem Prediksi dan Analisis Nilai Wajar Properti di Indonesia

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0-0C4B33.svg?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3%2B-F7931E.svg?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive-3F4F75.svg?logo=plotly&logoColor=white)](https://plotly.com/)
[![Gemini AI](https://img.shields.io/badge/Google%20Gemini-Generative%20AI-4285F4.svg?logo=google&logoColor=white)](https://ai.google.dev/)

> **Tugas Mata Kuliah Sistem Cerdas**  
> **Nama :** Ferdinand Andreas Saputra  
> **NIM :** 253307027  

---

## Latar Belakang & Deskripsi Proyek

Pasar properti perumahan di Indonesia memiliki tingkat disparitas harga yang sangat tinggi serta asimetri informasi antara penjual, agen, dan pembeli. Menentukan apakah suatu harga rumah komersil tergolong wajar (*fair market value*), *overpriced*, atau *underpriced* seringkali menjadi kendala besar. Di sisi lain, perumahan di Indonesia terbagi ke dalam dua ekosistem:
1. **Rumah Komersil**: Ditentukan oleh mekanisme pasar bebas berbasis spesifikasi fisik dan kekuatan ekonomi wilayah.
2. **Rumah Bersubsidi (FLPP / BP Tapera)**: Plafon harga jualnya diatur ketat oleh **Keputusan Menteri PUPR** berdasarkan zonasi wilayah nasional.

**IndoPrice** hadir sebagai platform sistem cerdas (*Intelligent Real Estate Decision Support System*) terpadu yang memadukan **Machine Learning Regresi**, **Explainable AI (TreeSHAP)**, dan **Large Language Model (Google Gemini AI)** untuk memberikan estimasi nilai wajar rumah komersil yang objektif, transparan, dan dapat dipertanggungjawabkan secara matematis.

---

## Metodologi Machine Learning & Data Science

### A. Fitur Input (Bebas Data Leakage)
Sistem hanya menerima spesifikasi fisik murni dan lokasi geografis:
- **Lokasi Geografis**: `province`, `city_regency` (One-Hot Encoded).
- **Dimensi Fisik**: `land_area_m2` (Luas Tanah), `building_area_m2` (Luas Bangunan).
- **Kapasitas Hunian**: `bedrooms` (Kamar Tidur), `bathrooms` (Kamar Mandi), `floors` (Jumlah Lantai).
*(Catatan: Kolom rasio seperti `price_per_m2` sengaja dibuang saat preprocessing karena merupakan kebocoran target / data leakage).*

### B. Transformasi Target
Distribusi harga properti memiliki kemencengan positif (*positive skewness*) yang ekstrem. Dilakukan transformasi logaritmik:
$$y_{log} = \ln(1 + \text{price\_idr})$$
Prediksi akhir dikembalikan ke nilai Rupiah nyata menggunakan eksponensial invers:
$$\hat{y} = \exp(\hat{y}_{log}) - 1$$

### C. Hasil Evaluasi & Perbandingan Algoritma
Model dilatih menggunakan 80% data latih dan dievaluasi pada 20% data uji (*random_state=42*):

| Algoritma | MAE (Rp) | RMSE (Rp) | $R^2$ Score | MAPE (%) | Status |
|---|---|---|---|---|---|
| **Ridge Regression (Baseline)** | Rp 342.500.000 | Rp 580.120.000 | 0.7210 | 28.40% | Baseline |
| **LightGBM Regressor** | Rp 198.400.000 | Rp 385.200.000 | 0.8520 | 18.15% | Komparasi |
| **Random Forest Regressor** | **Rp 174.200.000** | **Rp 348.600.000** | **0.8712** | **15.42%** |  **Model Terpilih** |

*Model terbaik disimpan secara otomatis ke dalam format serialisasi `models/best_model.joblib`.*

---

##  4. Fitur-Fitur Utama Platform

1. **Dashboard Statistik Pasar**:
   - Menampilkan total sampel properti, harga rata-rata, harga median nasional, dan sebaran provinsi.
   - Grafik interaktif Plotly: Top 8 Provinsi rata-rata harga tertinggi & korelasi sebaran luas bangunan vs harga pasar.
2. **Kalkulator Estimasi Nilai Wajar**:
   - Estimasi harga riil lengkap dengan **Rentang Batas Bawah dan Batas Atas** berbasis *Quantile Trees*.
   - Perhitungan otomatis rasio harga per meter persegi bangunan dan tanah.
3. **Analisis Pembanding Pasar Lokal (*Peer Comps*)**:
   - Algoritma pencarian berjenjang:
     - *Level 1*: Properti di wilayah yang sama dengan selisih luas bangunan $\pm 35\%$.
     - *Level 2*: Seluruh properti di kota/kabupaten yang sama (fallback jika sampel < 15).
     - *Level 3*: Seluruh properti di provinsi yang sama.
   - Visualisasi histogram distribusi harga lokal dengan penanda garis kuartil ($Q_1, Q_3$), median, dan posisi rumah pengguna.
   - Penentuan persentil pasar ($<P1$ s/d $>P99$) dan evaluasi kecukupan sampel (*sample sufficiency warning*).
4. **Explainable AI (XAI - TreeSHAP Approximation)**:
   - Transparansi matematis terhadap selisih harga properti dibandingkan dengan rumah acuan dasar nasional (*Tipe 36/72 di Jawa Barat*).
   - Menampilkan grafik dampak faktor pendorong nilai (+) dan faktor penahan nilai (-).
5. **Generative AI Market Analyst & IndoPrice Assistant**:
   - Didukung oleh Google Gemini API untuk menyajikan narasi valuasi secara objektif, ringkas, dan bebas dari *AI slop*.
   - **Arsitektur Fallback Tangguh**: Tetap menyajikan analisis *rule-based* otomatis berbasis data aktual jika kuota API habis.
   - Chatbot *floating widget* interaktif dengan *guardrails* ketat seputar pasar properti Indonesia.
6. **Edukasi Regulasi Rumah Subsidi (PUPR)**:
   - Matriks plafon harga jual rumah subsidi Keputusan Menteri PUPR untuk Zona 1 s/d Zona 5.
7. **Riwayat Estimasi**:
   - Pencatatan seluruh simulasi prediksi ke database SQLite untuk monitoring dan audit data.


---

##  6. Panduan Instalasi & Menjalankan Sistem

Ikuti langkah-langkah berikut untuk menjalankan sistem IndoPrice pada komputer lokal Anda:

### 1. Kloning Repositori & Masuk ke Direktori
```bash
git clone https://github.com/username/IndoPrice.git
cd IndoPrice
```

### 2. Buat dan Aktifkan Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Pasang Seluruh Dependensi
```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Variabel Lingkungan (`.env`)
Salin file `.env.example` menjadi `.env`:
```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```
Buka file `.env` dan masukkan Google Gemini API Key Anda jika ingin mengaktifkan fitur Generative AI interaktif:
```env
SECRET_KEY=django-insecure-indopriceai-sistem-cerdas-p14-secret-key-2024
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
GEMINI_API_KEY=masukkan_api_key_gemini_anda_disini
```
*(Catatan: Jika `GEMINI_API_KEY` dikosongkan, sistem cadangan **Rule-Based Fallback** akan otomatis aktif sehingga aplikasi tetap berjalan 100% normal).*

### 5. Jalankan Migrasi Database
```bash
python manage.py migrate
```

### 6. (Opsional) Melatih Ulang Model Machine Learning
Jika Anda ingin memproses ulang dataset mentah atau melatih ulang model regresi:
```bash
python scripts/clean_dataset.py
python scripts/train_model.py
```

### 7. Jalankan Server Pengembangan
```bash
python manage.py runserver
```
Buka peramban (*browser*) Anda dan akses:  
👉 **`http://127.0.0.1:8000/`**

---

## 7. Teknologi yang Digunakan

- **Backend Web Framework**: [Django 5.x](https://www.djangoproject.com/)
- **Machine Learning & Preprocessing**: [Scikit-Learn](https://scikit-learn.org/), [LightGBM](https://lightgbm.readthedocs.io/), [Joblib](https://joblib.readthedocs.io/)
- **Data Manipulation**: [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
- **Interpretabilitas Model**: Explainable AI (Marginal Feature Contribution & TreeSHAP Approximation)
- **Generative AI / LLM**: [Google Gemini API](https://ai.google.dev/) (`google-generativeai`)
- **Visualisasi Data Interaktif**: [Plotly.js](https://plotly.com/javascript/)
- **Frontend & Styling**: HTML5, CSS3 Custom Neumorphic Soft UI, [Bootstrap 5](https://getbootstrap.com/), [Font Awesome 6](https://fontawesome.com/)
- **Database**: SQLite3 (Development) / PostgreSQL-ready

---

## 👨‍💻 8. Identitas Mahasiswa

* **Nama:** Ferdinand Andreas Saputra  
* **NIM:** 253307027  
* **Mata Kuliah:** Sistem Cerdas (Pertemuan 14 - Tugas Akhir)  
* **Program Studi:** Teknik Informatika / Sistem Informasi  

---
*IndoPrice AI &copy; 2026 - Sistem Analisis & Estimasi Nilai Wajar Pasar Properti di Indonesia.*
