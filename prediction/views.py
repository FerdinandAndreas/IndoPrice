"""
Modul Views (Controller) untuk Aplikasi IndoPrice.
Menangani routing HTTP, interaksi form, dan delegasi pemrosesan ke modul services & charts.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import pandas as pd
import numpy as np

from .apps import PredictionConfig
from .models import PredictionHistory, AIAnalysisLog
from .ai_analyst import generate_ai_explanation, generate_chatbot_response
from .charts import (
    create_province_chart,
    create_price_scatter_chart,
    create_distribution_chart,
    create_factors_chart
)
from .services import (
    get_clean_data_path,
    get_clean_dataframe,
    get_dashboard_stats,
    calculate_price_range,
    get_peer_comparisons,
    calculate_feature_contributions
)

def dashboard_view(request):
    """Halaman Utama / Dashboard Analisis Properti"""
    df = get_clean_dataframe()
    stats = get_dashboard_stats(df, is_model_active=(PredictionConfig.model is not None))

    chart_prov_json = None
    chart_price_dist_json = None

    if df is not None and not df.empty:
        chart_prov_json = create_province_chart(df)
        chart_price_dist_json = create_price_scatter_chart(df)

    context = {
        'stats': stats,
        'chart_prov_json': chart_prov_json,
        'chart_price_dist_json': chart_price_dist_json
    }
    return render(request, 'prediction/dashboard.html', context)


def predict_view(request):
    """Halaman Form Estimasi Harga Rumah Komersil dengan Explainable AI (XAI) & Analisis Pasar"""
    df_all = get_clean_dataframe()
    stats = get_dashboard_stats(df_all, is_model_active=(PredictionConfig.model is not None))

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

                # 2) Rentang Estimasi Quantile Trees
                price_low, price_high = calculate_price_range(model_pipeline, input_df, pred_price)

                # 3) Metrik Valuasi per m²
                price_per_m2_building = int(pred_price / building) if building > 0 else 0
                price_per_m2_land = int(pred_price / land) if land > 0 else 0

                # 4) Pembanding Pasar Lokal Berjenjang & Visualisasi Distribusi
                df_all = get_clean_dataframe()
                comp_stats, comp_prices_juta = get_peer_comparisons(df_all, city, prov, building, pred_price)

                if comp_stats and comp_prices_juta:
                    pred_juta = round(pred_price / 1_000_000, 1)
                    chart_distribution_json = create_distribution_chart(
                        comp_prices_juta,
                        comp_stats['sample_count'],
                        comp_stats['q1_juta'],
                        comp_stats['q3_juta'],
                        comp_stats['median_juta'],
                        pred_juta,
                        comp_stats['percentile_display']
                    )

                # 5) Analisis Explainable AI (TreeSHAP Marjinal) & Visualisasi Dampak
                xai_summary, contributions, top_pos_factors, top_neg_factors = calculate_feature_contributions(
                    model_pipeline, input_df, pred_price, building, land, city, beds, baths, floors
                )
                chart_factors_json = create_factors_chart(contributions)

                # 6) Simpan ke Database SQLite
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

                # 7) Simpan Konteks Analisis AI ke Session
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
                request.session['last_ai_data'] = ai_data

                result = {
                    'predicted_price': f"Rp {pred_price:,.0f}".replace(",", "."),
                    'price_low': f"Rp {price_low:,.0f}".replace(",", "."),
                    'price_high': f"Rp {price_high:,.0f}".replace(",", "."),
                    'price_per_m2_building': f"Rp {price_per_m2_building:,.0f}".replace(",", "."),
                    'price_per_m2_land': f"Rp {price_per_m2_land:,.0f}".replace(",", "."),
                    'model_name': actual_model_name,
                    'comp_stats': comp_stats,
                    'xai_summary': xai_summary,
                    'history_id': history.id
                }
            else:
                result = {
                    'error': "Model Machine Learning belum dilatih. Jalankan 'python scripts/train_model.py' terlebih dahulu."
                }

        except ValueError as e:
            result = {'error': f"Input numerik tidak valid: {e}"}

    context = {
        'stats': stats,
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
    subsidi_stats = {
        'lowest_cap': 'Rp 166 Juta',
        'highest_cap': 'Rp 240 Juta',
        'interest_rate': '5% Fixed',
        'downpayment': 'Mulai 1%',
    }
    return render(request, 'prediction/subsidi.html', {
        'subsidi_zones': subsidi_zones,
        'subsidi_stats': subsidi_stats
    })


def history_view(request):
    """Halaman Riwayat Prediksi Pengguna"""
    from django.db.models import Avg, Max, Min
    histories = PredictionHistory.objects.all()[:100]
    total_count = PredictionHistory.objects.count()

    agg = PredictionHistory.objects.aggregate(
        avg_price=Avg('predicted_price'),
        max_price=Max('predicted_price'),
        min_price=Min('predicted_price')
    )

    def _format_short(val):
        if not val:
            return "0"
        if val >= 1_000_000_000:
            return f"Rp {val / 1_000_000_000:.2f} M".replace('.', ',')
        elif val >= 1_000_000:
            return f"Rp {val / 1_000_000:.0f} Jt"
        return f"Rp {int(val):,}".replace(',', '.')

    history_stats = {
        'total_count': total_count,
        'avg_price_display': _format_short(agg['avg_price']),
        'max_price_display': _format_short(agg['max_price']),
        'min_price_display': _format_short(agg['min_price']),
    }
    return render(request, 'prediction/history.html', {
        'histories': histories,
        'history_stats': history_stats
    })


# ========================================================
# API Endpoints (AJAX & AI)
# ========================================================

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
            ai_data = request.session.get('last_ai_data')
            if not ai_data:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Tidak ada data prediksi. Silakan lakukan prediksi terlebih dahulu.'
                }, status=400)

            explanation = generate_ai_explanation('prediction', ai_data)

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


@csrf_exempt
def api_chatbot(request):
    """Endpoint AJAX untuk interaksi pesan Chatbot IndoPrice AI Assistant"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_msg = data.get('message', '').strip()
            if not user_msg:
                return JsonResponse({'status': 'error', 'message': 'Pesan tidak boleh kosong.'}, status=400)

            reply = generate_chatbot_response(user_msg)

            AIAnalysisLog.objects.create(
                topic=f"Chatbot: {user_msg[:60]}",
                prompt=user_msg,
                response=reply
            )

            return JsonResponse({'status': 'success', 'reply': reply})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
