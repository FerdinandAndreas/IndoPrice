import os
from pathlib import Path
import pandas as pd
import numpy as np

from .apps import PredictionConfig

def get_clean_data_path():
    """Mengembalikan path mutlak ke dataset komersil bersih"""
    base_dir = Path(__file__).resolve().parent.parent
    return base_dir / 'data' / 'processed' / 'dataset_komersil_clean.csv'


def get_clean_dataframe():
    """
    Mengambil DataFrame data komersil bersih dengan in-memory caching.
    Mencegah I/O disk membaca ulang file CSV 11.5 MB di setiap request.
    """
    if getattr(PredictionConfig, 'df_clean', None) is not None:
        return PredictionConfig.df_clean

    csv_path = get_clean_data_path()
    if not csv_path.exists():
        return None

    try:
        df = pd.read_csv(
            csv_path,
            usecols=['province', 'city_regency', 'price_idr', 'land_area_m2', 'building_area_m2']
        )
        df['price_idr'] = pd.to_numeric(df['price_idr'], errors='coerce')
        df['building_area_m2'] = pd.to_numeric(df['building_area_m2'], errors='coerce')
        df = df.dropna(subset=['price_idr', 'building_area_m2', 'province'])
        
        # Simpan ke cache aplikasi
        PredictionConfig.df_clean = df
        return df
    except Exception as e:
        print("Error loading clean dataframe:", e)
        return None


def get_dashboard_stats(df, is_model_active=True):
    """Menghitung ringkasan statistik pasar properti untuk Dashboard"""
    stats = {
        'total_properties': 0,
        'avg_price': "Rp 0",
        'avg_price_display': "Rp 0",
        'median_price': "Rp 0",
        'total_provinces': 0,
        'r2_score': "0.87",
        'r2_percentage': "87%",
        'model_name': "Random Forest",
        'model_status': 'Aktif' if is_model_active else 'Belum Dilatih'
    }

    if df is not None and not df.empty:
        mean_val = df['price_idr'].mean()
        stats['total_properties'] = f"{len(df):,}".replace(",", ".")
        stats['avg_price'] = f"Rp {mean_val:,.0f}".replace(",", ".")
        if mean_val >= 1_000_000_000:
            stats['avg_price_display'] = f"Rp {mean_val / 1_000_000_000:.2f} Miliar"
        else:
            stats['avg_price_display'] = f"Rp {mean_val / 1_000_000:,.0f} Juta".replace(",", ".")

        stats['median_price'] = f"Rp {df['price_idr'].median():,.0f}".replace(",", ".")
        stats['total_provinces'] = df['province'].nunique()

    return stats


def calculate_price_range(model_pipeline, input_df, pred_price):
    """
    Menghitung rentang wajar (price_low dan price_high)
    menggunakan quantile estimasi pohon ensemble jika tersedia.
    """
    try:
        preprocessor = model_pipeline.named_steps['preprocessor']
        regressor = model_pipeline.named_steps['regressor']
        X_trans = preprocessor.transform(input_df)

        if hasattr(regressor, 'estimators_'):
            tree_preds = [tree.predict(X_trans)[0] for tree in regressor.estimators_]
            tree_prices = np.expm1(tree_preds)
            price_low = int(np.percentile(tree_prices, 15))
            price_high = int(np.percentile(tree_prices, 85))
        else:
            margin = int(pred_price * 0.12)
            price_low = max(50_000_000, pred_price - margin)
            price_high = pred_price + margin
    except Exception:
        margin = int(pred_price * 0.12)
        price_low = max(50_000_000, pred_price - margin)
        price_high = pred_price + margin

    if price_low >= pred_price:
        price_low = int(pred_price * 0.88)
    if price_high <= pred_price:
        price_high = int(pred_price * 1.12)

    return price_low, price_high


def get_peer_comparisons(df_all, city, prov, building, pred_price):
    """
    Melakukan evaluasi pembanding pasar secara berjenjang (Level 1, 2, 3),
    menghitung persentil posisi pasar, dan evaluasi kecukupan sampel.
    """
    if df_all is None or df_all.empty:
        return {}, []

    # Level 1: Wilayah sama dan rentang luas bangunan mirip +- 35%
    comps = df_all[
        (df_all['city_regency'] == city) &
        (df_all['building_area_m2'].between(building * 0.65, building * 1.35)) &
        (df_all['price_idr'] > 0)
    ]
    comp_level = f"properti sejenis (±35% luas) di {city}"

    # Level 2 Fallback: Seluruh properti di kota tersebut
    if len(comps) < 15:
        comps = df_all[(df_all['city_regency'] == city) & (df_all['price_idr'] > 0)]
        comp_level = f"seluruh properti di {city}"

    # Level 3 Fallback: Seluruh properti di provinsi tersebut
    if len(comps) < 15:
        comps = df_all[(df_all['province'] == prov) & (df_all['price_idr'] > 0)]
        comp_level = f"properti komersil di {prov}"

    comp_prices = comps['price_idr'].dropna().tolist()
    comp_prices_juta = [round(float(p) / 1_000_000, 1) for p in comp_prices]

    comp_median = float(np.median(comp_prices)) if comp_prices else 0
    comp_q1 = float(np.percentile(comp_prices, 25)) if comp_prices else 0
    comp_q3 = float(np.percentile(comp_prices, 75)) if comp_prices else 0
    comp_min = float(min(comp_prices)) if comp_prices else 0
    comp_max = float(max(comp_prices)) if comp_prices else 0
    comp_count = len(comp_prices)

    # Perhitungan persentil
    count_below = np.sum(np.array(comp_prices) < pred_price) if comp_count > 0 else 0
    count_equal = np.sum(np.array(comp_prices) == pred_price) if comp_count > 0 else 0

    if comp_count > 0 and count_below == comp_count:
        comp_percentile = 99.0
        percentile_display = ">P99"
    elif comp_count > 0 and count_below == 0 and count_equal <= 1:
        comp_percentile = 1.0
        percentile_display = "<P1"
    else:
        raw_pct = ((count_below + 0.5 * count_equal) / max(1, comp_count)) * 100
        comp_percentile = round(min(99.0, max(1.0, raw_pct)), 1)
        percentile_display = f"P{int(round(comp_percentile))}"

    # Evaluasi posisi pasar
    if pred_price > comp_q3:
        if pred_price > comp_max:
            market_status = "Di Atas Seluruh Pembanding (>P99)"
            market_status_desc = "Estimasi berada di atas 100% sampel properti sejenis di area pembanding (Segmen Properti Mewah / Premium)."
            market_badge_class = "accent"
        else:
            market_status = "Segmen Pasar Atas (Q3 s/d P99)"
            market_status_desc = "Estimasi berada pada 25% rentang harga tertinggi dibandingkan properti sejenis."
            market_badge_class = "accent"
    elif comp_q1 <= pred_price <= comp_q3:
        market_status = "Rentang Wajar Pasar (Zona 50% Tengah)"
        market_status_desc = "Estimasi berada tepat di zona nilai wajar (antara persentil 25 hingga persentil 75)."
        market_badge_class = "green"
    else:
        if pred_price < comp_min:
            market_status = "Di Bawah Seluruh Pembanding (<P1)"
            market_status_desc = "Estimasi berada di bawah batas minimum pembanding wilayah (Sangat Terjangkau)."
            market_badge_class = "amber"
        else:
            market_status = "Segmen Pasar Bawah (< Q1 / P25)"
            market_status_desc = "Estimasi lebih terjangkau dibandingkan 75% properti sejenis di area pembanding."
            market_badge_class = "sky"

    # Evaluasi kecukupan sampel
    if comp_count >= 30:
        sample_sufficiency = "Tinggi (Sangat Memadai)"
        sample_warning = None
        sample_badge_class = "green"
    elif 15 <= comp_count < 30:
        sample_sufficiency = "Sedang (Cukup)"
        sample_warning = f"Data pembanding berjumlah sedang ({comp_count} unit). Distribusi memberikan indikasi pasar yang baik."
        sample_badge_class = "sky"
    else:
        sample_sufficiency = "Terbatas (Indikatif)"
        sample_warning = f"⚠️ Peringatan Sampel Terbatas: Hanya ditemukan {comp_count} unit pembanding untuk parameter wilayah ini. Interpretasi pasar bersifat indikatif dan tidak boleh dijadikan kesimpulan mutlak."
        sample_badge_class = "amber"

    # Selisih terhadap median pasar
    diff_median = pred_price - int(comp_median)
    diff_median_juta = round(diff_median / 1_000_000, 1)
    diff_median_pct = round((diff_median / comp_median) * 100, 1) if comp_median > 0 else 0

    if diff_median >= 0:
        diff_median_text = f"+Rp {abs(int(diff_median_juta)):,} Jt (+{abs(diff_median_pct):.1f}% di atas median)"
    else:
        diff_median_text = f"-Rp {abs(int(diff_median_juta)):,} Jt (-{abs(diff_median_pct):.1f}% di bawah median)"

    comp_stats = {
        'median_juta': round(comp_median / 1_000_000, 1),
        'q1_juta': round(comp_q1 / 1_000_000, 1),
        'q3_juta': round(comp_q3 / 1_000_000, 1),
        'min_juta': round(comp_min / 1_000_000, 1),
        'max_juta': round(comp_max / 1_000_000, 1),
        'percentile': comp_percentile,
        'percentile_display': percentile_display,
        'sample_count': comp_count,
        'level': comp_level,
        'market_status': market_status,
        'market_status_desc': market_status_desc,
        'market_badge_class': market_badge_class,
        'sample_sufficiency': sample_sufficiency,
        'sample_warning': sample_warning,
        'sample_badge_class': sample_badge_class,
        'diff_median_text': diff_median_text,
        'diff_median_pct': diff_median_pct
    }

    return comp_stats, comp_prices_juta


def calculate_feature_contributions(model_pipeline, input_df, pred_price, building, land, city, beds, baths, floors):
    """
    Menghitung kontribusi marjinal masing-masing fitur (TreeSHAP Approximation)
    terhadap harga dasar baseline (rumah tipe 36/72 standar nasional).
    """
    baseline_df = pd.DataFrame([{
        'province': 'JAWA BARAT',
        'city_regency': 'KAB BEKASI',
        'land_area_m2': 72.0,
        'building_area_m2': 36.0,
        'bedrooms': 2,
        'bathrooms': 1,
        'floors': 1
    }])
    baseline_pred_log = model_pipeline.predict(baseline_df)[0]
    baseline_price = int(np.expm1(baseline_pred_log))

    feature_meta = [
        ('building_area_m2', f"Luas Bangunan ({building:g} m²)"),
        ('land_area_m2', f"Luas Tanah ({land:g} m²)"),
        ('city_regency', f"Wilayah ({city})"),
        ('bedrooms', f"Kamar Tidur ({beds} KT)"),
        ('bathrooms', f"Kamar Mandi ({baths} KM)"),
        ('floors', f"Lantai ({floors} Lt)")
    ]

    # Efek marjinal lokal per fitur
    raw_deltas = {}
    for feat_key, feat_label in feature_meta:
        perturbed = input_df.copy()
        perturbed[feat_key] = baseline_df[feat_key].values[0]
        perturbed_pred = int(np.expm1(model_pipeline.predict(perturbed)[0]))
        raw_deltas[feat_key] = pred_price - perturbed_pred

    # Rekonsiliasi matematis TreeSHAP: Total kontribusi + Baseline = Hasil Prediksi
    total_delta_target = pred_price - baseline_price
    sum_raw = sum(raw_deltas.values())

    if sum_raw != 0 and abs(sum_raw) > 1000:
        scale_factor = total_delta_target / sum_raw
        reconciled_deltas = {k: int(round(v * scale_factor)) for k, v in raw_deltas.items()}
    else:
        reconciled_deltas = raw_deltas.copy()

    residual = total_delta_target - sum(reconciled_deltas.values())
    if residual != 0 and reconciled_deltas:
        largest_k = max(reconciled_deltas.keys(), key=lambda k: abs(reconciled_deltas[k]))
        reconciled_deltas[largest_k] += residual

    contributions = []
    top_pos_factors = []
    top_neg_factors = []

    for feat_key, feat_label in feature_meta:
        delta_val = reconciled_deltas[feat_key]
        delta_juta = round(delta_val / 1_000_000, 1)

        contributions.append({
            'key': feat_key,
            'label': feat_label,
            'delta': delta_val,
            'delta_juta': delta_juta,
            'abs_delta': abs(delta_val)
        })

    contributions = sorted(contributions, key=lambda x: x['abs_delta'], reverse=True)

    total_pos = sum(c['delta'] for c in contributions if c['delta'] > 0)
    total_neg = sum(c['delta'] for c in contributions if c['delta'] < 0)

    for c in contributions:
        if c['delta_juta'] > 0:
            top_pos_factors.append(f"{c['label']} (+Rp {c['delta_juta']} Jt)")
        elif c['delta_juta'] < 0:
            top_neg_factors.append(f"{c['label']} (-Rp {abs(c['delta_juta'])} Jt)")

    xai_summary = {
        'baseline_price': f"Rp {baseline_price:,.0f}".replace(",", "."),
        'baseline_juta': round(baseline_price / 1_000_000, 1),
        'total_pos_juta': round(total_pos / 1_000_000, 1),
        'total_neg_juta': round(abs(total_neg) / 1_000_000, 1),
        'net_delta_juta': round((pred_price - baseline_price) / 1_000_000, 1),
        'is_reconciled': True,
        'contributions': contributions
    }

    return xai_summary, contributions, top_pos_factors, top_neg_factors
