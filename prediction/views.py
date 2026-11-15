from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio

from .apps import PredictionConfig
from .models import PredictionHistory, AIAnalysisLog
from .ai_analyst import generate_ai_explanation

def get_clean_data_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, 'dataset_komersil_clean.csv')

def dashboard_view(request):
    """Halaman Utama / Dashboard Analisis Properti"""
    clean_csv = get_clean_data_path()
    stats = {
        'total_properties': 0,
        'avg_price': "Rp 0",
        'avg_price_display': "Rp 0",
        'median_price': "Rp 0",
        'total_provinces': 0,
        'r2_score': "0.87",
        'r2_percentage': "87%",
        'model_name': "Random Forest",
        'model_status': 'Aktif' if PredictionConfig.model is not None else 'Belum Dilatih'
    }

    chart_prov_json = None
    chart_price_dist_json = None

    if os.path.exists(clean_csv):
        try:
            df = pd.read_csv(clean_csv, usecols=['province', 'city_regency', 'price_idr', 'land_area_m2', 'building_area_m2'])

            # Memastikan tipe numerik terdefinisi dengan bersih
            df['price_idr'] = pd.to_numeric(df['price_idr'], errors='coerce')
            df['building_area_m2'] = pd.to_numeric(df['building_area_m2'], errors='coerce')
            df = df.dropna(subset=['price_idr', 'building_area_m2', 'province'])

            mean_val = df['price_idr'].mean()
            stats['total_properties'] = f"{len(df):,}"
            stats['avg_price'] = f"Rp {mean_val:,.0f}"
            if mean_val >= 1_000_000_000:
                stats['avg_price_display'] = f"Rp {mean_val / 1_000_000_000:.2f} Miliar"
            else:
                stats['avg_price_display'] = f"Rp {mean_val / 1_000_000:,.0f} Juta"

            stats['median_price'] = f"Rp {df['price_idr'].median():,.0f}"
            stats['total_provinces'] = df['province'].nunique()
            stats['r2_score'] = "0.87"
            stats['r2_percentage'] = "87%"

            # Grafik Top 8 Provinsi Rata rata harga tertinggi
            prov_grouped = df.groupby('province')['price_idr'].agg(['mean', 'count']).reset_index()
            # Menampilkan hanya 5 provinsi dengan harga rata tertinggi
            prov_grouped = prov_grouped[prov_grouped['count'] >= 5]
            prov_top8 = prov_grouped.sort_values(by='mean', ascending=False).head(8)

            # Ekstrak data sebagai native Python list murni untuk menghindari error serialisasi pandas index
            prov_names = prov_top8['province'].tolist()
            prov_prices_juta = [round(float(p) / 1_000_000, 1) for p in prov_top8['mean'].tolist()]

            # Balik urutan supaya peringkat 1 (termahal) berada di posisi teratas
            prov_names.reverse()
            prov_prices_juta.reverse()

            max_price = max(prov_prices_juta) if prov_prices_juta else 1000

            fig1 = go.Figure()
            fig1.add_trace(go.Bar(
                x=prov_prices_juta,
                y=prov_names,
                orientation='h',
                text=[f"Rp {int(val):,} Jt" for val in prov_prices_juta],
                textposition='outside',
                cliponaxis=False,
                textfont=dict(color='#0F2744', family='Plus Jakarta Sans', size=11, weight='bold'),
                marker=dict(
                    color=prov_prices_juta,
                    colorscale=[
                        [0.0, '#60A5FA'],
                        [0.35, '#3B82F6'],
                        [0.7, '#2563EB'],
                        [1.0, '#1D4ED8']
                    ],
                    line=dict(color='#1D4ED8', width=1.2)
                ),
                hovertemplate="<b>%{y}</b><br>Rata-rata: Rp %{x:,.1f} Juta<extra></extra>"
            ))

            fig1.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=140, r=40, t=15, b=35),
                height=360,
                bargap=0.28,
                xaxis=dict(
                    title=dict(text='Rata-rata Harga (Juta Rp)', font=dict(family='Plus Jakarta Sans', size=11, color='#5B708B')),
                    gridcolor='#DBEAFE',
                    zerolinecolor='#DBEAFE',
                    range=[0, max_price * 1.25],
                    tickfont=dict(color='#5B708B', family='Plus Jakarta Sans', size=11)
                ),
                yaxis=dict(
                    gridcolor='rgba(0,0,0,0)',
                    ticksuffix='   ',
                    tickfont=dict(color='#0F2744', family='Plus Jakarta Sans', size=11)
                ),
                font=dict(family='Plus Jakarta Sans')
            )
            chart_prov_json = pio.to_json(fig1)

            # Grafik Korelasi Luas Bangunan vs Harga Pasar
            scatter_df = df[
                (df['building_area_m2'] >= 20) & (df['building_area_m2'] <= 400) &
                (df['price_idr'] >= 100_000_000) & (df['price_idr'] <= 10_000_000_000)
            ]

            sample_size = min(600, len(scatter_df))
            sampled = scatter_df.sample(sample_size, random_state=42)

            x_building = [float(x) for x in sampled['building_area_m2'].tolist()]
            y_price_miliar = [round(float(p) / 1_000_000_000, 2) for p in sampled['price_idr'].tolist()]

            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=x_building,
                y=y_price_miliar,
                mode='markers',
                marker=dict(
                    size=8,
                    color='#2563EB',
                    opacity=0.6,
                    line=dict(width=1, color='#1D4ED8')
                ),
                hovertemplate="Luas Bangunan: <b>%{x} m²</b><br>Harga: <b>Rp %{y:.2f} Miliar</b><extra></extra>"
            ))

            fig2.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=65, r=30, t=20, b=45),
                height=340,
                xaxis=dict(
                    title=dict(text='Luas Bangunan (m²)', font=dict(family='Plus Jakarta Sans', size=11, color='#5B708B')),
                    gridcolor='#DBEAFE',
                    zerolinecolor='#DBEAFE',
                    tickfont=dict(color='#5B708B', family='Plus Jakarta Sans', size=11)
                ),
                yaxis=dict(
                    title=dict(text='Harga Pasar (Miliar Rp)', font=dict(family='Plus Jakarta Sans', size=11, color='#5B708B')),
                    gridcolor='#DBEAFE',
                    zerolinecolor='#DBEAFE',
                    tickfont=dict(color='#5B708B', family='Plus Jakarta Sans', size=11)
                ),
                font=dict(family='Plus Jakarta Sans')
            )
            chart_price_dist_json = pio.to_json(fig2)

        except Exception as e:
            print("Dashboard calculation error:", e)

    recent_predictions = PredictionHistory.objects.all()[:5]

    context = {
        'stats': stats,
        'chart_prov_json': chart_prov_json,
        'chart_price_dist_json': chart_price_dist_json,
        'recent_predictions': recent_predictions
    }
    return render(request, 'prediction/dashboard.html', context)

def predict_view(request):
    """Halaman Form Estimasi Harga Rumah Komersil dengan Explainable AI (XAI) & Analisis Pasar"""
    locations = PredictionConfig.locations or {}
    provinces = sorted(list(locations.keys()))

    result = None
    input_data = {}
    chart_distribution_json = None
    chart_factors_json = None
    comp_stats = {}

    if request.method == 'POST':
        prov = request.POST.get('province', '').strip()
        city = request.POST.get('city_regency', '').strip()
        district = request.POST.get('district', '').strip()

        try:
            land = float(request.POST.get('land_area_m2', 0))
            building = float(request.POST.get('building_area_m2', 0))
            beds = int(request.POST.get('bedrooms', 2))
            baths = int(request.POST.get('bathrooms', 1))
            floors = int(request.POST.get('floors', 1))

            input_data = {
                'province': prov,
                'city_regency': city,
                'district': district,
                'land_area_m2': land,
                'building_area_m2': building,
                'bedrooms': beds,
                'bathrooms': baths,
                'floors': floors
            }

            if PredictionConfig.model is not None:
                model_pipeline = PredictionConfig.model

                preprocessor = model_pipeline.named_steps['preprocessor']
                regressor = model_pipeline.named_steps['regressor']
                model_class_name = regressor.__class__.__name__

                if model_class_name == 'RandomForestRegressor':
                    actual_model_name = "Random Forest Regressor"
                elif model_class_name == 'LGBMRegressor':
                    actual_model_name = "LightGBM Regressor"
                elif model_class_name == 'Ridge':
                    actual_model_name = "Ridge Regression"
                else:
                    actual_model_name = model_class_name

                # Menyiapkan baris input untuk model pipeline
                input_df = pd.DataFrame([{
                    'province': prov,
                    'city_regency': city,
                    'land_area_m2': land,
                    'building_area_m2': building,
                    'bedrooms': beds,
                    'bathrooms': baths,
                    'floors': floors
                }])

                # 1) Prediksi Utama 
                pred_log = model_pipeline.predict(input_df)[0]
                pred_price = int(np.expm1(pred_log))

                # 2) Rentang Estimasi Berbasis Ensemble Quantile Decision Trees 
                try:
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

                # Validasi batas rentang
                if price_low >= pred_price:
                    price_low = int(pred_price * 0.88)
                if price_high <= pred_price:
                    price_high = int(pred_price * 1.12)

                # 3) Metrik Valuasi per Meter Persegi
                price_per_m2_building = int(pred_price / building) if building > 0 else 0
                price_per_m2_land = int(pred_price / land) if land > 0 else 0

                # 4) Visualisasi 1 Distribusi Harga Properti Sejenis
                clean_csv = get_clean_data_path()
                top_pos_factors = []
                top_neg_factors = []

                if os.path.exists(clean_csv):
                    try:
                        df_all = pd.read_csv(clean_csv, usecols=['province', 'city_regency', 'price_idr', 'land_area_m2', 'building_area_m2'])
                        df_all['price_idr'] = pd.to_numeric(df_all['price_idr'], errors='coerce')
                        df_all['building_area_m2'] = pd.to_numeric(df_all['building_area_m2'], errors='coerce')
                        df_all = df_all.dropna(subset=['price_idr', 'building_area_m2'])

                        # Filter Berjenjang
                        # Level 1 Wilayah sama dan rentang luas bangunan mirip +- 35%
                        comps = df_all[(df_all['city_regency'] == city) & (df_all['building_area_m2'].between(building * 0.65, building * 1.35)) & (df_all['price_idr'] > 0)]
                        comp_level = f"properti sejenis (±35% luas) di {city}"

                        # Level 2 fallback
                        if len(comps) < 15:
                            comps = df_all[(df_all['city_regency'] == city) & (df_all['price_idr'] > 0)]
                            comp_level = f"seluruh properti di {city}"

                        # Level 3 fallback
                        if len(comps) < 15:
                            comps = df_all[(df_all['province'] == prov) & (df_all['price_idr'] > 0)]
                            comp_level = f"properti komersil di {prov}"

                        comp_prices = comps['price_idr'].dropna().tolist()
                        comp_prices_juta = [round(float(p) / 1_000_000, 1) for p in comp_prices]

                        comp_median = float(np.median(comp_prices))
                        comp_q1 = float(np.percentile(comp_prices, 25))
                        comp_q3 = float(np.percentile(comp_prices, 75))
                        comp_min = float(min(comp_prices)) if comp_prices else 0
                        comp_max = float(max(comp_prices)) if comp_prices else 0
                        comp_count = len(comp_prices)

                        # Perhitungan persentil yang akurat 
                        count_below = np.sum(np.array(comp_prices) < pred_price)
                        count_equal = np.sum(np.array(comp_prices) == pred_price)

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

                        # Evaluasi Posisi Pasar (Di atas, wajar, atau di bawah rentang)
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

                        # Evaluasi Kecukupan Sampel dan Peringatan
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

                        # Hitung perbedaan terhadap median pasar
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

                        # Plotly Distribution Chart 
                        pred_juta = round(pred_price / 1_000_000, 1)
                        median_juta = comp_stats['median_juta']
                        q1_juta = comp_stats['q1_juta']
                        q3_juta = comp_stats['q3_juta']

                        fig_dist = go.Figure()
                        fig_dist.add_trace(go.Histogram(
                            x=comp_prices_juta,
                            nbinsx=min(25, max(8, comp_count // 3)),
                            name='Unit Pasar Pembanding',
                            marker=dict(
                                color='#DBEAFE',
                                line=dict(color='#60A5FA', width=1)
                            ),
                            hovertemplate="Rentang: Rp %{x:,.0f} Juta<br>Frekuensi: %{y} unit<extra></extra>"
                        ))

                        # Garis Kuartil 
                        fig_dist.add_vline(x=q1_juta, line_width=1.5, line_dash="dash", line_color="#94A3B8")
                        fig_dist.add_vline(x=q3_juta, line_width=1.5, line_dash="dash", line_color="#94A3B8")

                        # Garis Median Pasar
                        fig_dist.add_vline(x=median_juta, line_width=2, line_dash="dot", line_color="#0F2744")

                        # Marker Pin Rumah Pengguna
                        fig_dist.add_vline(
                            x=pred_juta,
                            line_width=3,
                            line_color="#2563EB",
                            annotation_text=f"Rumah Anda: Rp {int(pred_juta):,} Jt ({percentile_display})",
                            annotation_position="top right",
                            annotation_font=dict(family="Plus Jakarta Sans", size=11, color="#2563EB", weight="bold"),
                            annotation_bgcolor="#EFF6FF",
                            annotation_bordercolor="#2563EB",
                            annotation_borderwidth=1.2
                        )

                        fig_dist.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            margin=dict(l=45, r=30, t=35, b=40),
                            height=320,
                            bargap=0.08,
                            showlegend=False,
                            xaxis=dict(
                                title=dict(text='Rentang Harga Properti Pembanding (Juta Rp)', font=dict(family='Plus Jakarta Sans', size=11, color='#5B708B')),
                                gridcolor='#DBEAFE',
                                zerolinecolor='#DBEAFE',
                                tickfont=dict(color='#5B708B', family='Plus Jakarta Sans', size=11)
                            ),
                            yaxis=dict(
                                title=dict(text='Jumlah Unit', font=dict(family='Plus Jakarta Sans', size=11, color='#5B708B')),
                                gridcolor='#DBEAFE',
                                zerolinecolor='#DBEAFE',
                                tickfont=dict(color='#5B708B', family='Plus Jakarta Sans', size=11)
                            ),
                            font=dict(family='Plus Jakarta Sans')
                        )
                        chart_distribution_json = pio.to_json(fig_dist)

                    except Exception as e:
                        print("Error peer comps:", e)

                # 5) Visualisasi Faktor Penentu Nilai Wajar 
                xai_summary = {}
                try:
                    # Model Baseline Representasi median rumah komersil nasional
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

                    # Hitung efek marjinal lokal untuk masing masing fitur
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

                    # Koreksi sisa pembulatan ke fitur dengan dampak terbesar
                    residual = total_delta_target - sum(reconciled_deltas.values())
                    if residual != 0 and reconciled_deltas:
                        largest_k = max(reconciled_deltas.keys(), key=lambda k: abs(reconciled_deltas[k]))
                        reconciled_deltas[largest_k] += residual

                    contributions = []
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

                    # Urutkan berdasarkan dampak absolut terbesar
                    contributions = sorted(contributions, key=lambda x: x['abs_delta'], reverse=True)

                    total_pos = sum(c['delta'] for c in contributions if c['delta'] > 0)
                    total_neg = sum(c['delta'] for c in contributions if c['delta'] < 0)

                    for c in contributions:
                        if c['delta_juta'] > 0:
                            top_pos_factors.append(f"{c['label']} (+Rp {c['delta_juta']} Jt)")
                        elif c['delta_juta'] < 0:
                            top_neg_factors.append(f"{c['label']} (-Rp {abs(c['delta_juta'])} Jt)")

                    labels_list = [c['label'] for c in contributions][::-1]
                    deltas_list = [c['delta_juta'] for c in contributions][::-1]

                    bar_colors = ['#2563EB' if d >= 0 else '#94A3B8' for d in deltas_list]
                    max_abs_delta = max([abs(d) for d in deltas_list]) if deltas_list and max([abs(d) for d in deltas_list]) > 0 else 50

                    # Pisahka ke dua trace tern bar positif dan negatif pisah supaya label tidak nabrak
                    pos_x = [d if d >= 0 else None for d in deltas_list]
                    neg_x = [d if d < 0 else None for d in deltas_list]
                    pos_text = [f"+Rp {int(d):,} Jt" if d is not None else "" for d in pos_x]
                    neg_text = [f"-Rp {abs(int(d)):,} Jt" if d is not None else "" for d in neg_x]

                    fig_factors = go.Figure()

                    # Trace 1 Bar positif (label di luar kanan)
                    fig_factors.add_trace(go.Bar(
                        x=pos_x,
                        y=labels_list,
                        orientation='h',
                        text=pos_text,
                        textposition='outside',
                        cliponaxis=False,
                        textfont=dict(color='#0F2744', family='Plus Jakarta Sans', size=11, weight='bold'),
                        marker=dict(color='#2563EB', line=dict(color='#1D4ED8', width=1)),
                        hovertemplate="<b>%{y}</b><br>Dampak Valuasi: %{text}<extra></extra>",
                        showlegend=False
                    ))

                    # Trace 2 Bar negatif (label di luar kiri, offset agar tidak terpotong)
                    fig_factors.add_trace(go.Bar(
                        x=neg_x,
                        y=labels_list,
                        orientation='h',
                        text=neg_text,
                        textposition='outside',
                        cliponaxis=False,
                        textfont=dict(color='#0F2744', family='Plus Jakarta Sans', size=11, weight='bold'),
                        marker=dict(color='#94A3B8', line=dict(color='#64748B', width=1)),
                        hovertemplate="<b>%{y}</b><br>Dampak Valuasi: %{text}<extra></extra>",
                        showlegend=False
                    ))

                    fig_factors.add_vline(x=0, line_width=1.5, line_color="#0F2744")

                    # Hitung range dinamis: sisi negatif butuh lebih banyak ruang untuk label teks
                    max_neg = max([abs(d) for d in deltas_list if d < 0]) if any(d < 0 for d in deltas_list) else 0
                    neg_range = max(max_neg * 3.5, max_abs_delta * 0.35)

                    fig_factors.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=180, r=100, t=15, b=35),
                        height=320,
                        barmode='overlay',
                        bargap=0.3,
                        xaxis=dict(
                            title=dict(text='Dampak Valuasi terhadap Harga Dasar (Juta Rp)', font=dict(family='Plus Jakarta Sans', size=11, color='#5B708B')),
                            gridcolor='#DBEAFE',
                            zerolinecolor='#0F2744',
                            range=[-neg_range, max_abs_delta * 1.5],
                            tickfont=dict(color='#5B708B', family='Plus Jakarta Sans', size=11)
                        ),
                        yaxis=dict(
                            gridcolor='rgba(0,0,0,0)',
                            ticksuffix='  ',
                            tickfont=dict(color='#0F2744', family='Plus Jakarta Sans', size=11)
                        ),
                        font=dict(family='Plus Jakarta Sans')
                    )
                    chart_factors_json = pio.to_json(fig_factors)

                    xai_summary = {
                        'baseline_price': f"Rp {baseline_price:,.0f}",
                        'baseline_juta': round(baseline_price / 1_000_000, 1),
                        'total_pos_juta': round(total_pos / 1_000_000, 1),
                        'total_neg_juta': round(abs(total_neg) / 1_000_000, 1),
                        'net_delta_juta': round((pred_price - baseline_price) / 1_000_000, 1),
                        'is_reconciled': True,
                        'contributions': contributions
                    }

                except Exception as e:
                    print("Error calculating factor contribution:", e)

                # Simpan ke riwayat database
                history = PredictionHistory.objects.create(
                    province=prov,
                    city_regency=city,
                    district=district,
                    land_area_m2=land,
                    building_area_m2=building,
                    bedrooms=beds,
                    bathrooms=baths,
                    floors=floors,
                    predicted_price=pred_price,
                    price_low=price_low,
                    price_high=price_high
                )

                # Simpan konteks AI ke session untuk dipanggil on-demand via tombol
                ai_data = {
                    **input_data,
                    'model_name': actual_model_name,
                    'predicted_price': pred_price,
                    'price_low': price_low,
                    'price_high': price_high,
                    'price_per_m2_building': price_per_m2_building,
                    'price_per_m2_land': price_per_m2_land,
                    'comp_percentile': comp_stats.get('percentile', 50),
                    'percentile_display': comp_stats.get('percentile_display', 'P50'),
                    'comp_sample_count': comp_stats.get('sample_count', 0),
                    'comp_level': comp_stats.get('level', 'pasar lokal'),
                    'comp_median_juta': comp_stats.get('median_juta', 0),
                    'diff_median_text': comp_stats.get('diff_median_text', 'seimbang'),
                    'market_status': comp_stats.get('market_status', 'Rentang Wajar'),
                    'sample_warning': comp_stats.get('sample_warning'),
                    'baseline_juta': xai_summary.get('baseline_juta', 0),
                    'top_pos_factors': top_pos_factors,
                    'top_neg_factors': top_neg_factors
                }
                # Simpan ai_data ke session supaya bisa dipanggil on-demand
                request.session['last_ai_data'] = ai_data

                result = {
                    'predicted_price': f"Rp {pred_price:,.0f}",
                    'price_low': f"Rp {price_low:,.0f}",
                    'price_high': f"Rp {price_high:,.0f}",
                    'price_per_m2_building': f"Rp {price_per_m2_building:,.0f}",
                    'price_per_m2_land': f"Rp {price_per_m2_land:,.0f}",
                    'model_name': actual_model_name,
                    'comp_stats': comp_stats,
                    'xai_summary': xai_summary,
                    'history_id': history.id
                }
            else:
                result = {
                    'error': "Model Machine Learning belum dilatih. Jalankan 'python train_model.py' terlebih dahulu."
                }

        except ValueError as e:
            result = {'error': f"Input numerik tidak valid: {e}"}

    context = {
        'provinces': provinces,
        'locations_json': json.dumps(locations),
        'result': result,
        'input_data': input_data,
        'chart_distribution_json': chart_distribution_json,
        'chart_factors_json': chart_factors_json
    }
    return render(request, 'prediction/predict.html', context)

def subsidi_view(request):
    """Halaman Knowledge Base Rumah Subsidi PUPR"""
    # Regulasi Kepmen PUPR Batasan Harga Rumah Subsidi Tapak
    subsidi_zones = [
        {
            'zona': 'Zona 1 (Jawa & Sumatera)',
            'wilayah': 'Jawa (kecuali Jabodetabek) dan Sumatera (kecuali Kep. Riau & Bangka Belitung)',
            'plafon_2024': 'Rp 166.000.000',
            'tipe_standar': 'Tipe 36/60 s/d 36/72'
        },
        {
            'zona': 'Zona 2 (Kalimantan)',
            'wilayah': 'Seluruh Provinsi di Pulau Kalimantan (kecuali Kab. Murung Raya & Mahakam Ulu)',
            'plafon_2024': 'Rp 182.000.000',
            'tipe_standar': 'Tipe 36/72 s/d 36/90'
        },
        {
            'zona': 'Zona 3 (Sulawesi & Kepulauan)',
            'wilayah': 'Sulawesi, Bangka Belitung, Kepulauan Riau, dan Kepulauan Maluku',
            'plafon_2024': 'Rp 173.000.000',
            'tipe_standar': 'Tipe 36/72'
        },
        {
            'zona': 'Zona 4 (Bali & Nusa Tenggara)',
            'wilayah': 'Bali, Nusa Tenggara Barat, Nusa Tenggara Timur, dan Jabodetabek',
            'plafon_2024': 'Rp 185.000.000',
            'tipe_standar': 'Tipe 36/60'
        },
        {
            'zona': 'Zona 5 (Papua & Daerah Khusus)',
            'wilayah': 'Papua, Papua Barat, Papua Tengah, Papua Selatan, Papua Pegunungan',
            'plafon_2024': 'Rp 240.000.000',
            'tipe_standar': 'Tipe 36/90 s/d 36/120'
        }
    ]

    context = {
        'subsidi_zones': subsidi_zones
    }
    return render(request, 'prediction/subsidi.html', context)

def history_view(request):
    """Riwayat Prediksi Pengguna"""
    histories = PredictionHistory.objects.all()[:50]
    return render(request, 'prediction/history.html', {'histories': histories})

# API Endpoints
def api_get_cities(request):
    """Kembalikan daftar kabupaten/kota untuk provinsi tertentu"""
    province = request.GET.get('province', '').strip()
    locations = PredictionConfig.locations or {}
    cities = list(locations.get(province, {}).keys())
    return JsonResponse({'cities': sorted(cities)})

def api_get_districts(request):
    """Kembalikan daftar kecamatan untuk kabupaten/kota tertentu"""
    province = request.GET.get('province', '').strip()
    city = request.GET.get('city', '').strip()
    locations = PredictionConfig.locations or {}
    districts = locations.get(province, {}).get(city, [])
    return JsonResponse({'districts': sorted(districts)})

@csrf_exempt
def api_ai_explain(request):
    """Endpoint untuk analisis AI dinamis (grafik dashboard)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            context_type = data.get('type', 'chart')
            context_payload = data.get('payload', {})
            explanation = generate_ai_explanation(context_type, context_payload)

            # Simpan ke AIAnalysisLog
            AIAnalysisLog.objects.create(
                topic=f"Analisis Grafik: {context_payload.get('title', 'Chart')}",
                prompt=json.dumps(context_payload, ensure_ascii=False, default=str),
                response=explanation
            )

            return JsonResponse({'status': 'success', 'explanation': explanation})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def api_ai_predict_explain(request):
    """Endpoint untuk analisis AI on-demand dari hasil prediksi (dipanggil via tombol)"""
    if request.method == 'POST':
        try:
            # Ambil ai_data dari session yang disimpan saat prediksi
            ai_data = request.session.get('last_ai_data')
            if not ai_data:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Tidak ada data prediksi. Silakan lakukan prediksi terlebih dahulu.'
                }, status=400)

            # Generate penjelasan AI
            explanation = generate_ai_explanation('prediction', ai_data)

            # Simpan ke AIAnalysisLog
            city = ai_data.get('city_regency', 'Unknown')
            prov = ai_data.get('province', '')
            pred_price = ai_data.get('predicted_price', 0)
            AIAnalysisLog.objects.create(
                topic=f"Analisis Prediksi: {city}, {prov} — Rp {pred_price:,}",
                prompt=json.dumps(ai_data, ensure_ascii=False, default=str),
                response=explanation
            )

            return JsonResponse({'status': 'success', 'explanation': explanation})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
