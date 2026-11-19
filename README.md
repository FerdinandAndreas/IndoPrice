# IndoPrice: Sistem Prediksi Harga Rumah di Indonesia

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.x-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3%2B-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/)
[![Gemini AI](https://img.shields.io/badge/Google%20Gemini-API-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)

> **Ferdinand Andreas Saputra** 

---

## Tentang Proyek

IndoPrice adalah aplikasi web yang membantu mengestimasi harga wajar rumah komersil di Indonesia menggunakan Machine Learning. Pengguna cukup memasukkan spesifikasi rumah seperti lokasi, luas tanah, luas bangunan, dan jumlah kamar. Kemudian sistem akan memberikan estimasi harga nilai wajar, rentang toleransi pasar, serta valuasi harga per meter persegi secara otomatis.

Aplikasi ini juga mencakup halaman informasi untuk rumah subsidi (FLPP/BP Tapera) yang plafon harganya sudah diatur oleh Keputusan Menteri PUPR.

---

## Fitur Utama

| Fitur | Keterangan |
|---|---|
| **Dashboard** | Pengenalan sistem cerdas, materi praktikum semester 3, dan ringkasan teknologi |
| **Estimasi Harga** | Prediksi nilai pasar wajar + rentang toleransi (P15–P85) dan valuasi per m² |
| **Visualisasi Data** | Grafik interaktif sebaran rata-rata harga antar provinsi dan korelasi luas tanah vs harga |
| **AI Analyst** | Narasi penjelasan hasil estimasi otomatis berbasis Google Gemini (dengan fallback) |
| **Chatbot IndoPrice** | Asisten tanya jawab seputar pasar properti dan panduan sistem |
| **Rumah Subsidi** | Informasi aturan zonasi dan plafon harga FLPP (Kepmen PUPR) |
| **Riwayat Estimasi** | Seluruh simulasi tersimpan otomatis di database SQLite untuk referensi |

---

## Antarmuka Aplikasi

### Dashboard Utama
![Dashboard Utama](static/img/Dashboard%20Utama.png)

### Kalkulator Estimasi Harga Rumah
![Kalkulator Estimasi Harga Rumah](static/img/Kalkulator%20Estimasi%20Harga%20Rumah.png)

### Visualisasi Data
![Visualisasi Data](static/img/Visualiasi%20Data.png)

### Chatbot IndoPrice
![Chatbot IndoPrice](static/img/Chatbot%20IndoPrice.png)

---

## Teknologi yang Digunakan

- **Backend**: Django 5.x, Python 3.10+
- **Machine Learning**: Scikit-Learn (Random Forest, Ridge Regression), LightGBM, Joblib
- **Data**: Pandas, NumPy
- **Visualisasi**: Plotly (grafik interaktif)
- **Generative AI**: Google Gemini API
- **Frontend**: Bootstrap 5, Font Awesome 6, Custom CSS
- **Database**: SQLite3 (dev)

---

## Instalasi & Menjalankan

### 1. Clone repositori

```bash
git clone https://github.com/FerdinandAndreas/IndoPrice.git
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

Salin template file `.env`:

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Buka file `.env` yang baru dibuat, lalu isi API Key Gemini:

```env
GEMINI_API_KEY=masukkan_disini
```

Jika `GEMINI_API_KEY` dikosongkan aplikasi tetap bisa berjalan dengan normal dengan fallback bawaan. 

### 5. Migrasi database

```bash
python manage.py migrate
```

### 6. Jalankan server

```bash
python manage.py runserver
```

Buka di browser: **`http://127.0.0.1:8000/`**

