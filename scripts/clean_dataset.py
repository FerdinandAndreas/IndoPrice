import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Path root proyek
BASE_DIR = Path(__file__).resolve().parent.parent

def clean_data(input_csv=None):
    if input_csv is None:
        input_csv = BASE_DIR / "data" / "raw" / "dataset.csv"
    else:
        input_csv = Path(input_csv)

    if not input_csv.exists():
        print(f"Error: File '{input_csv}' tidak ditemukan.")
        return

    print("=" * 60)
    print("IndoPrice AI - Memulai Pembersihan Dataset...")
    print("=" * 60)

    # Load data
    print(f"Membaca '{input_csv}'...")
    df = pd.read_csv(input_csv, low_memory=False)
    initial_rows = len(df)
    print(f"Total baris mentah: {initial_rows:,}")

    # Standardisasi nama kolom dan nilai string dasar
    df.columns = [c.strip() for c in df.columns]
    if 'subsidy_status' in df.columns:
        df['subsidy_status'] = df['subsidy_status'].astype(str).str.strip().str.lower()

    # Segmentasi Komersil vs Subsidi
    df_komersil = df[df['subsidy_status'] == 'komersil'].copy()
    df_subsidi = df[df['subsidy_status'] == 'subsidi'].copy()
    print(f"\n[Segmentasi]")
    print(f"- Data Komersil : {len(df_komersil):,} baris")
    print(f"- Data Subsidi  : {len(df_subsidi):,} baris")

    # Pembersihan Data Komersil (Fokus Machine Learning)
    print(f"\n[Pembersihan Data Komersil]")

    # Hapus harga tidak valid (<= 0 atau NaN)
    n_before = len(df_komersil)
    df_komersil = df_komersil[df_komersil['price_idr'].notnull()]
    df_komersil['price_idr'] = pd.to_numeric(df_komersil['price_idr'], errors='coerce')
    df_komersil = df_komersil[df_komersil['price_idr'] > 0]
    print(f"1. Menghapus harga 0 atau kosong       : -{n_before - len(df_komersil):,} baris")

    # Hapus outlier harga ekstrim (misal: < 50 juta atau > 30 miliar)
    n_before = len(df_komersil)
    df_komersil = df_komersil[(df_komersil['price_idr'] >= 50_000_000) & (df_komersil['price_idr'] <= 30_000_000_000)]
    print(f"2. Membatasi harga wajar (50jt - 30M)  : -{n_before - len(df_komersil):,} baris")

    # Hapus nilai kamar negatif
    n_before = len(df_komersil)
    df_komersil['bedrooms'] = pd.to_numeric(df_komersil['bedrooms'], errors='coerce')
    df_komersil['bathrooms'] = pd.to_numeric(df_komersil['bathrooms'], errors='coerce')
    df_komersil = df_komersil[(df_komersil['bedrooms'] >= 0) & (df_komersil['bathrooms'] >= 0)]
    print(f"3. Menghapus nilai kamar negatif       : -{n_before - len(df_komersil):,} baris")

    # Validasi luas tanah dan bangunan (> 0)
    n_before = len(df_komersil)
    df_komersil['land_area_m2'] = pd.to_numeric(df_komersil['land_area_m2'], errors='coerce')
    df_komersil['building_area_m2'] = pd.to_numeric(df_komersil['building_area_m2'], errors='coerce')
    df_komersil = df_komersil[(df_komersil['land_area_m2'] > 0) & (df_komersil['building_area_m2'] > 0)]
    print(f"4. Menghapus luas tanah/bangunan <= 0  : -{n_before - len(df_komersil):,} baris")

    # Konsistensi fisik (1 lantai: luas bangunan <= luas tanah + toleransi 1 m2)
    n_before = len(df_komersil)
    df_komersil['floors'] = pd.to_numeric(df_komersil['floors'], errors='coerce').fillna(1)
    # Jika lantai 1, bangunan tidak boleh jauh lebih besar dari tanah
    is_valid_layout = ~((df_komersil['floors'] == 1) & (df_komersil['building_area_m2'] > df_komersil['land_area_m2'] + 1))
    df_komersil = df_komersil[is_valid_layout]
    print(f"5. Menghapus inkonsistensi layout (1 lt): -{n_before - len(df_komersil):,} baris")

    # Pembersihan lokasi wajib
    n_before = len(df_komersil)
    df_komersil = df_komersil[df_komersil['province'].notnull() & df_komersil['city_regency'].notnull()]
    print(f"6. Menghapus lokasi (provinsi/kab) kosong: -{n_before - len(df_komersil):,} baris")

    # Koordinat geografis wajar (Indonesia: Lat -11 s/d 6, Lon 95 s/d 141)
    # Baris dengan 0.0, 0.0 diisi NaN agar tidak merusak visualisasi peta
    df_komersil['latitude'] = pd.to_numeric(df_komersil['latitude'], errors='coerce')
    df_komersil['longitude'] = pd.to_numeric(df_komersil['longitude'], errors='coerce')
    is_null_island = (df_komersil['latitude'].between(-0.01, 0.01)) & (df_komersil['longitude'].between(-0.01, 0.01))
    df_komersil.loc[is_null_island, ['latitude', 'longitude']] = np.nan

    # Hapus Kolom Kebocoran Target dan Kolom Tanpa Variansi
    cols_to_drop = [
        'property_type',           # 100% Rumah Tapak
        'price_per_m2_land',       # Data leakage
        'price_per_m2_building'    # Data leakage
    ]
    df_komersil = df_komersil.drop(columns=[c for c in cols_to_drop if c in df_komersil.columns])

    # Ekspor Data Bersih
    output_dir = BASE_DIR / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_komersil = output_dir / "dataset_komersil_clean.csv"
    output_subsidi = output_dir / "dataset_subsidi_clean.csv"

    df_komersil.to_csv(output_komersil, index=False)
    print(f"\n[Hasil]")
    print(f"-> Selesai! Data Komersil Bersih tersimpan di: '{output_komersil}'")
    print(f"-> Total baris komersil bersih: {len(df_komersil):,} baris")

    # Ekspor subsidi untuk referensi PUPR
    df_subsidi_clean = df_subsidi[(df_subsidi['price_idr'] > 0) & (df_subsidi['price_idr'].notnull())]
    df_subsidi_clean.to_csv(output_subsidi, index=False)
    print(f"-> Selesai! Data Subsidi tersimpan di: '{output_subsidi}' ({len(df_subsidi_clean):,} baris)")

    print("\nRingkasan Statistik Harga Komersil (Rupiah):")
    print(df_komersil['price_idr'].describe(percentiles=[0.25, 0.5, 0.75, 0.90]))
    print("=" * 60)

if __name__ == "__main__":
    clean_data()
