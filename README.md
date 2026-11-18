# IndoPrice — Sistem Prediksi Harga Rumah di Indonesia

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.x-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3%2B-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/)
[![Gemini AI](https://img.shields.io/badge/Google%20Gemini-API-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)

> Tugas Akhir Mata Kuliah **Sistem Cerdas** — Pertemuan 14  
> **Ferdinand Andreas Saputra** — NIM 253307027

---

## Tentang Proyek

IndoPrice adalah aplikasi web yang membantu mengestimasi harga wajar rumah komersil di Indonesia menggunakan Machine Learning. Pengguna cukup memasukkan spesifikasi rumah (lokasi, luas tanah, luas bangunan, jumlah kamar), dan sistem akan memberikan estimasi harga beserta analisis pasar lokal secara otomatis.

Proyek ini juga mencakup halaman informasi rumah subsidi (FLPP/BP Tapera) yang plafon harganya diatur oleh Keputusan Menteri PUPR.

---

## Fitur Utama

| Fitur | Keterangan |
|---|---|
| **Dashboard Statistik** | Grafik interaktif tren harga dan sebaran properti per provinsi |
| **Estimasi Harga** | Prediksi nilai wajar + rentang batas bawah–atas berbasis Machine Learning |
| **Analisis Pasar Lokal** | Pembanding properti serupa di kecamatan/kota/provinsi yang sama |
| **Explainable AI** | Penjelasan faktor apa yang mendorong atau menahan nilai rumah |
| **AI Analyst** | Narasi analisis otomatis dari Google Gemini, ada fallback jika kuota habis |
| **Chatbot** | Asisten tanya-jawab seputar properti dan cara pakai IndoPrice |
| **Rumah Subsidi** | Tabel plafon harga FLPP per zona wilayah (Kepmen PUPR) |
| **Riwayat Estimasi** | Semua simulasi tersimpan di database untuk referensi |

---

## Screenshot

### Dashboard Utama
![Dashboard](static/img/Dashboard%20Utama.png)

### Estimasi Harga Properti
![Estimasi](static/img/Kalkulator%20Estimasi%20Harga%20Rumah.png)

### Chatbot IndoPrice
![Chatbot](static/img/Chatbot%20IndoPrice.png)

---

## Teknologi yang Digunakan

- **Backend**: Django 5.x, Python 3.10+
- **Machine Learning**: Scikit-Learn (Random Forest, Ridge Regression), LightGBM, Joblib
- **Data**: Pandas, NumPy
- **Visualisasi**: Plotly (grafik interaktif)
- **Generative AI**: Google Gemini API
- **Frontend**: Bootstrap 5, Font Awesome 6, Custom CSS
- **Database**: SQLite3 (dev) / PostgreSQL-ready

---

## Model Machine Learning

Model dilatih menggunakan data **44.000+ transaksi rumah komersil** di Indonesia dengan split 80% latih / 20% uji.

**Fitur input** (bebas data leakage):
- Lokasi: `province`, `city_regency`
- Fisik: `land_area_m2`, `building_area_m2`, `bedrooms`, `bathrooms`, `floors`

Harga ditransformasi dengan log (`ln(1 + harga)`) sebelum dilatih, lalu dikembalikan ke Rupiah saat prediksi.

**Hasil perbandingan model:**

| Algoritma | MAE | R² Score | MAPE | Keterangan |
|---|---|---|---|---|
| Ridge Regression | Rp 342.500.000 | 0.7210 | 28.40% | Baseline |
| LightGBM | Rp 198.400.000 | 0.8520 | 18.15% | Komparasi |
| **Random Forest** | **Rp 174.200.000** | **0.8712** | **15.42%** | ✅ Model terpilih |

Model terbaik disimpan ke `models/best_model.joblib` dan langsung dipakai oleh Django untuk prediksi real-time.

---

## Instalasi & Menjalankan

### 1. Clone repositori

```bash
git clone https://github.com/username/IndoPrice.git
cd IndoPrice
```

### 2. Buat virtual environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Buat file `.env`

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Isi file `.env`:

```env
SECRET_KEY=django-insecure-indopriceai-sistem-cerdas-p14-secret-key-2024
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
GEMINI_API_KEY=masukkan_api_key_gemini_kamu_disini
```

> `GEMINI_API_KEY` bisa dikosongkan — aplikasi tetap berjalan normal dengan fallback otomatis (tanpa AI interaktif).

### 5. Migrasi database

```bash
python manage.py migrate
```

> **Database sudah disertakan** (`db.sqlite3`) dengan 47 riwayat prediksi dan akun admin bawaan.  
> Kalau database di-reset, muat ulang data dengan:
> ```bash
> python manage.py loaddata data/seed_data.json
> ```

### 6. Jalankan server

```bash
python manage.py runserver
```

Buka di browser: **`http://127.0.0.1:8000/`**

---

### (Opsional) Latih ulang model

Kalau ingin melatih ulang dari dataset mentah:

```bash
python scripts/clean_dataset.py
python scripts/train_model.py
```

---

*IndoPrice © 2026*
