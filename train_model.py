import os
import json
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def mean_absolute_percentage_error(y_true, y_pred):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    non_zero = y_true != 0
    return np.mean(np.abs((y_true[non_zero] - y_pred[non_zero]) / y_true[non_zero])) * 100

def train():
    clean_csv = "dataset_komersil_clean.csv"
    if not os.path.exists(clean_csv):
        print(f"File '{clean_csv}' belum ada. Harap jalankan 'python clean_dataset.py' terlebih dahulu!")
        return

    print("=" * 60)
    print("IndoPrice AI - Pelatihan Model Regresi")
    print("=" * 60)

    print(f"Membaca '{clean_csv}'...")
    df = pd.read_csv(clean_csv, low_memory=False)
    print(f"Total sampel: {len(df):,} baris")

    # 1) Ekspor Hierarki Lokasi untuk Dropdown Form Django
    print("\nMenyimpan hierarki dropdown lokasi...")
    locations = {}
    for prov, p_group in df.groupby('province'):
        prov = str(prov).strip()
        locations[prov] = {}
        for city, c_group in p_group.groupby('city_regency'):
            city = str(city).strip()
            districts = sorted([str(d).strip() for d in c_group['district'].dropna().unique()])
            locations[prov][city] = districts

    with open("locations_map.json", "w", encoding="utf-8") as f:
        json.dump(locations, f, ensure_ascii=False, indent=2)
    print("-> Selesai: 'locations_map.json' tersimpan.")

    # 2) Pemilihan Fitur
    cat_features = ['province', 'city_regency']
    num_features = ['land_area_m2', 'building_area_m2', 'bedrooms', 'bathrooms', 'floors']
    target_col = 'price_idr'

    X = df[cat_features + num_features].copy()
    y = df[target_col].copy()

    # Log transformation pada target
    y_log = np.log1p(y)

    # 3) Train-Test Split (80% Train, 20% Test)
    X_train, X_test, y_train_log, y_test_log, y_train_real, y_test_real = train_test_split(
        X, y_log, y, test_size=0.2, random_state=42
    )

    print(f"Data Latih: {len(X_train):,} sampel | Data Uji: {len(X_test):,} sampel")

    # 4) Pipeline Preprocessing
    num_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    cat_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value='UNKNOWN')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])

    preprocessor = ColumnTransformer([
        ('num', num_pipeline, num_features),
        ('cat', cat_pipeline, cat_features)
    ])

    # 5) Algoritma Pembanding
    models = {
        "Ridge Regression (Baseline)": Ridge(alpha=1.0),
        "Random Forest Regressor": RandomForestRegressor(n_estimators=100, max_depth=15, n_jobs=-1, random_state=42)
    }

    # Cek ketersediaan LightGBM
    try:
        from lightgbm import LGBMRegressor
        models["LightGBM Regressor"] = LGBMRegressor(n_estimators=200, learning_rate=0.08, num_leaves=31, random_state=42, n_jobs=-1)
    except ImportError:
        pass

    results = []
    best_model_name = None
    best_mape = float('inf')
    best_pipeline = None

    print("\nMelatih dan mengevaluasi model...")
    print("-" * 60)

    for name, model in models.items():
        print(f"Sedang melatih: {name}...")
        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('regressor', model)
        ])

        pipeline.fit(X_train, y_train_log)

        # Prediksi pada Test Set (Inverse log transform)
        y_pred_log = pipeline.predict(X_test)
        y_pred_real = np.expm1(y_pred_log)

        mae = mean_absolute_error(y_test_real, y_pred_real)
        rmse = np.sqrt(mean_squared_error(y_test_real, y_pred_real))
        r2 = r2_score(y_test_real, y_pred_real)
        mape = mean_absolute_percentage_error(y_test_real, y_pred_real)

        results.append({
            "Algoritma": name,
            "MAE (Rp)": f"Rp {mae:,.0f}",
            "RMSE (Rp)": f"Rp {rmse:,.0f}",
            "R2 Score": f"{r2:.4f}",
            "MAPE (%)": f"{mape:.2f}%"
        })

        if mape < best_mape:
            best_mape = mape
            best_model_name = name
            best_pipeline = pipeline

    # 6) Tampilkan Hasil
    print("\n" + "=" * 60)
    print("HASIL PERBANDINGAN MODEL:")
    print("=" * 60)
    res_df = pd.DataFrame(results)
    print(res_df.to_string(index=False))

    # 7) Simpan Model Terbaik
    joblib.dump(best_pipeline, "best_model.joblib")
    print(f"\n-> Model terbaik ({best_model_name}) berhasil disimpan ke: 'best_model.joblib'")
    print("Artefak ini siap digunakan langsung oleh backend Django untuk inference real-time.")
    print("=" * 60)

if __name__ == "__main__":
    train()
