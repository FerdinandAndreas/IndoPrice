# 🏡 IndoPrice - Sistem Prediksi & Analisis Nilai Wajar Properti Indonesia

> **Tugas Akhir Mata Kuliah Sistem Cerdas (Pertemuan 14)**  
> **Pengembang:** Ferdinand Andreas Saputra (NIM: 253307027)

---

## 📌 Deskripsi Proyek
**IndoPrice** adalah platform web analitik dan valuasi properti cerdas berbasis Machine Learning dan Generative AI. Sistem ini menganalisis lebih dari **44.000+ data transaksi perumahan riil di Indonesia** untuk memberikan estimasi harga wajar (*fair market value*), rentang toleransi pasar, interpretasi kontribusi fitur fisik (*Explainable AI*), serta analisis deskriptif otomatis.

---

## 🚀 Fitur Unggulan

1. **Estimasi Nilai Wajar Rumah Komersil (*Machine Learning*)**
   - Menggunakan algoritma **Random Forest Regressor** dengan transformasi logaritmik target (`log1p`).
   - Akurasi model mencapai $R^2 \approx 0.87$, mengevaluasi parameter luas tanah, luas bangunan, jumlah kamar, lantai, serta hierarki wilayah (Provinsi, Kota/Kabupaten, Kecamatan).

2. **Pemisahan Pasar Komersil vs Subsidi (*Bebas Data Leakage*)**
   - Mengisolasi rumah subsidi berdasarkan Keputusan Menteri PUPR No. 689/KPTS/M/2023 agar batas harga patokan pemerintah tidak merusak model regresi pasar bebas komersil.

3. **Explainable AI (TreeSHAP Feature Attribution)**
   - Transparansi model dengan merinci faktor utama pendorong kenaikan harga (+) dan faktor penahan nilai (-) relatif terhadap baseline pasar lokal.

4. **Analisis AI Generatif & Rule-Based Fallback Cerdas**
   - Terintegrasi dengan **Google Gemini AI** untuk menyusun analisis naratif yang tajam, objektif, dan *to the point*.
   - Dilengkapi sistem cadangan **Rule-Based Fallback**: jika kuota API habis atau server sedang sibuk, sistem tetap menyajikan penjelasan pasar berbasis data riil secara otomatis tanpa mengalami *crash*.

5. **Dashboard Pasar Properti Interaktif**
   - Visualisasi distribusi harga per provinsi dan korelasi dimensi fisik menggunakan grafik interaktif **Plotly.js**.

---

## 🛠️ Tech Stack & Dependensi

- **Backend:** Python 3.10+, Django 5.x
- **Data Science & ML:** Scikit-Learn, LightGBM, Pandas, NumPy, Joblib
- **Generative AI:** Google Gemini API (REST Endpoint)
- **Visualisasi & Frontend:** Bootstrap 5, Plotly.js, FontAwesome 6, Plus Jakarta Sans

---

## 💻 Panduan Instalasi & Menjalankan Proyek

### 1. Clone Repository
```bash
git clone https://github.com/FerdinandAndreas/IndoPrice.git
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

### 3. Install Dependensi
```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Environment (`.env`)
Salin file `.env.example` menjadi `.env`:
```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```
Buka file `.env` dan masukkan Google Gemini API Key (dapat menggunakan API key yang tercantum pada dokumen laporan tugas / Google AI Studio):
```env
GEMINI_API_KEY=masukkan_api_key_disini
```
*(Catatan: Demi keamanan repository dan kepatuhan terhadap GitHub Push Protection, API key tidak di-hardcode pada repository publik. Jika API key dikosongkan, sistem tetap berjalan normal 100% menggunakan sistem analisis cadangan cerdas berbasis Explainable AI TreeSHAP / Rule-Based Fallback).*

### 5. Jalankan Migrasi Database
```bash
python manage.py migrate
```

### 6. Jalankan Server Django
```bash
python manage.py runserver
```
Buka browser dan akses: **`http://127.0.0.1:8000/`**

---

## 📂 Struktur Direktori Proyek

```text
IndoPrice/
│── core/                      # Konfigurasi inti Django (settings, urls, wsgi)
│── prediction/                # Aplikasi utama (views, models, ai_analyst, urls)
│   ├── ai_analyst.py          # Modul integrasi Gemini AI & Rule-Based Fallback
│   └── views.py               # Logika kalkulator, dashboard, dan visualisasi
│── templates/                 # Template HTML UI Neumorphic Soft Blue
│── static/                    # File statis CSS dan gambar
│── clean_dataset.py           # Script data cleaning & segmentasi komersil/subsidi
│── train_model.py             # Script pelatihan model ML & komparasi algoritma
│── best_model.joblib          # Model Machine Learning terlatih siap pakai
│── locations_map.json         # Data hierarki wilayah untuk dropdown dinamis
│── requirements.txt           # Daftar dependensi Python
│── .env.example               # Template variabel environment
└── README.md                  # Dokumentasi proyek
```

---

## 📜 Lisensi & Catatan Akademik
Proyek ini dikembangkan untuk keperluan akademik penugasan akhir mata kuliah **Sistem Cerdas**.
Semua data transaksi properti telah melalui proses validasi dan pembersihan anomali.
