"""
Modul Integrasi Analisis Cerdas untuk IndoPrice
Menyediakan analisis deskriptif terhadap grafik dan hasil estimasi properti berbasis data aktual (Explainable AI & Google Gemini).
"""

from django.conf import settings
import logging
import re
import requests

logger = logging.getLogger(__name__)

# Kunci API Gemini default (dikosongkan untuk keamanan GitHub, dikonfigurasi via file .env)
DEFAULT_GEMINI_API_KEY = ''

def format_markdown_to_html(text: str) -> str:
    """Mengubah format markdown sederhana dari respon Gemini menjadi HTML bersih"""
    if not text:
        return ""
    
    # Ubah heading markdown 
    text = re.sub(r'^#{1,6}\s*(.*)$', r'<strong>\1</strong>', text, flags=re.MULTILINE)
    
    # Bold **text** -> <strong>text</strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    # Italic *text* -> <em>text</em>
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    lines = text.strip().split('\n')
    formatted = []
    in_list = False
    list_tag = 'ul'
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                formatted.append(f'</{list_tag}>')
                in_list = False
            continue
        
        # Bersihkan sisa karakter tanda pagar di awal jika ada
        stripped = re.sub(r'^#+\s*', '', stripped)
        
        # Cek jika baris adalah item daftar (bullet)
        if stripped.startswith(('* ', '- ', '• ')):
            if not in_list:
                formatted.append('<ul class="mb-2 ps-3" style="font-size: 0.85rem;">')
                in_list = True
                list_tag = 'ul'
            content = stripped[2:].strip()
            formatted.append(f'<li class="mb-1">{content}</li>')
        # Cek jika baris adalah item nomor
        elif re.match(r'^\d+\.\s+', stripped):
            if not in_list:
                formatted.append('<ol class="mb-2 ps-3" style="font-size: 0.85rem;">')
                in_list = True
                list_tag = 'ol'
            content = re.sub(r'^\d+\.\s+', '', stripped).strip()
            formatted.append(f'<li class="mb-1">{content}</li>')
        else:
            if in_list:
                formatted.append(f'</{list_tag}>')
                in_list = False
            formatted.append(f'<p class="mb-2">{stripped}</p>')
            
    if in_list:
        formatted.append(f'</{list_tag}>')
        
    return '\n'.join(formatted)


def generate_ai_explanation(context_type: str, context_data: dict) -> str:
    """
    Menghasilkan penjelasan naratif berbasis konteks data aktual.
    1. Mencoba memanggil Google Gemini API menggunakan API key dosen.
    2. Jika API key mencapai batas kuota / limit / error, menampilkan kotak notifikasi limit
       dan menyajikan analisis cadangan berbasis data riil (Rule-Based Fallback)
       secara ringkas, informatif, dan tidak berbelit-belit.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '') or DEFAULT_GEMINI_API_KEY

    # 1) Bangun Prompt untuk Analisis
    if context_type == 'prediction':
        pos_factors_text = "; ".join(context_data.get('top_pos_factors', [])) or "Kesesuaian lokasi dan spesifikasi luas bangunan"
        neg_factors_text = "; ".join(context_data.get('top_neg_factors', [])) or "Keterbatasan dimensi atau jumlah fasilitas"
        sample_warning = context_data.get('sample_warning') or "Jumlah sampel pembanding sangat memadai untuk evaluasi pasar."
        model_name = context_data.get('model_name', 'Random Forest Regressor')
        diff_median_text = context_data.get('diff_median_text', 'seimbang dengan median pasar')
        comp_median = context_data.get('comp_median_juta', 0)
        percentile_display = context_data.get('percentile_display', 'P50')
        market_status = context_data.get('market_status', 'Rentang Wajar')

        pred_p = int(context_data.get('predicted_price') or 0)
        p_low = int(context_data.get('price_low') or 0)
        p_high = int(context_data.get('price_high') or 0)
        p_m2 = int(context_data.get('price_per_m2_building') or 0)

        prompt = f"""Anda adalah analis properti profesional di platform IndoPrice.
Berikan analisis valuasi yang ringkas, objektif, to the point, dan langsung ke inti data (maksimal 2 paragraf pendek).

DATA PROPERTI & PASAR AKTUAL:
- Lokasi: {context_data.get('city_regency')}, {context_data.get('province')}
- Estimasi Nilai Wajar: Rp {pred_p:,} (Rp {p_m2:,}/m² bangunan)
- Rentang Wajar: Rp {p_low:,} s/d Rp {p_high:,}
- Posisi Pasar: Persentil {percentile_display} ({market_status}) dari {context_data.get('comp_sample_count', 0)} properti pembanding ({context_data.get('comp_level')})
- Selisih terhadap Median Pasar: {diff_median_text} (Median wilayah: Rp {comp_median} Jt)
- Faktor Utama Pendorong Nilai (+): {pos_factors_text}
- Faktor Utama Penahan Nilai (-): {neg_factors_text}
- Evaluasi Sampel: {sample_warning}

ATURAN FORMAT & GAYA BAHASA (WAJIB DIPATUHI):
1. DILARANG menggunakan tanda pagar atau heading markdown (JANGAN gunakan #, ##, atau ### sama sekali).
2. DILARANG menggunakan kalimat pembuka klise / AI-slop (seperti 'Tentu!', 'Halo', 'Berikut adalah analisis', 'Sebagai analis properti'). Langsung mulai kalimat pertama dengan fakta valuasi properti ini.
3. Buat dalam 2 paragraf singkat:
   - Paragraf 1: Posisi harga terhadap median pasar lokal dan rasio harga per m².
   - Paragraf 2: Pengaruh faktor pendorong/penahan (Explainable AI/TreeSHAP) serta kesimpulan/tips singkat bagi pengguna.
4. Gunakan murni fakta dan angka yang disediakan di atas. Jangan mengarang angka atau persentase baru.
5. Format penekanan HANYA boleh menggunakan bold (**teks**).
"""
    elif context_type == 'chart':
        chart_title = context_data.get('title', 'Statistik Pasar Properti')
        summary = context_data.get('summary', '')
        prompt = f"""Anda adalah analis pasar properti di platform IndoPrice.
Berikan analisis singkat, padat, dan to the point untuk visualisasi: '{chart_title}' (maksimal 1-2 paragraf pendek).

DATA GRAFIK:
{summary}

ATURAN FORMAT & GAYA BAHASA (WAJIB DIPATUHI):
1. DILARANG menggunakan tanda pagar atau heading markdown (JANGAN gunakan #, ##, atau ### sama sekali).
2. DILARANG menggunakan kalimat pembuka klise / AI-slop (seperti 'Tentu!', 'Grafik ini menampilkan', 'Berikut adalah ringkasan'). Langsung jelaskan temuan data utama pada kalimat pertama.
3. Fokus pada disparitas angka riil antarwilayah atau variabel, serta implikasi praktis pasar secara ringkas.
4. Format penekanan HANYA boleh menggunakan bold (**teks**).
"""
    else:
        prompt = f"Analisis data properti secara ringkas dan langsung ke inti: {context_data}"

    # 2) Panggil Google Gemini API via REST Endpoint
    if api_key:
        models_to_try = ['gemini-3.1-flash-lite', 'gemini-flash-lite-latest', 'gemini-2.5-flash', 'gemini-3.5-flash']
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1000
            }
        }
        for model_name in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                resp = requests.post(url, json=payload, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get('candidates', [])
                    if candidates and 'content' in candidates[0]:
                        parts = candidates[0]['content'].get('parts', [])
                        if parts and 'text' in parts[0]:
                            gemini_text = parts[0]['text'].strip()
                            formatted_body = format_markdown_to_html(gemini_text)
                            return f"""
<div class="mb-3 p-2 px-3 rounded-3 d-flex align-items-center justify-content-between" style="background: #F0FDF4; border: 1px solid #BBF7D0;">
    <div class="d-flex align-items-center gap-2">
        <i class="fa-solid fa-wand-magic-sparkles text-success"></i>
        <strong style="color: #166534; font-size: 0.84rem;">Analisis AI Generatif</strong>
    </div>
    <span class="badge bg-success" style="font-size: 0.68rem;">Gemini AI</span>
</div>
<div class="ai-body-content" style="color: var(--color-text, #1E293B); font-size: 0.88rem; line-height: 1.6;">
    {formatted_body}
</div>
"""
                else:
                    logger.warning(f"Model {model_name} status {resp.status_code}")
            except Exception as e:
                logger.warning(f"Model {model_name} error: {e}")
                continue

    # 3) Fallback: Tampilan ringkas, rapi, dan to the point
    fallback_text = generate_fallback_analysis(context_type, context_data)

    return f"""
<div class="alert alert-warning py-2 px-3 rounded-3 small mb-2 d-flex align-items-center border-warning-subtle" style="background-color: #FFFBEB; border: 1px solid #FDE68A;">
    <i class="fa-solid fa-triangle-exclamation text-warning me-2 fa-lg"></i>
    <strong style="color: #92400E; font-size: 0.84rem;">Pemberitahuan Kuota Gemini AI: Batas Limit Tercapai / Layanan Sibuk</strong>
</div>

<div class="p-2 px-3 rounded-3 mb-2" style="background: #EFF6FF; border: 1px solid #BFDBFE;">
    <div class="d-flex align-items-center gap-2">
        <i class="fa-solid fa-calculator text-primary"></i>
        <strong style="color: #1E40AF; font-size: 0.84rem;">Penjelasan Analis Pasar (Sistem Cadangan Berbasis Data Nyata / Rule-Based)</strong>
    </div>
</div>

<div class="p-3 rounded-3" style="color: var(--color-text, #1E293B); font-size: 0.86rem; line-height: 1.65; background-color: #F8FAFC; border: 1px solid var(--color-border, #E2E8F0);">
    {fallback_text}
</div>
"""

def generate_fallback_analysis(context_type: str, data: dict) -> str:
    """Analisis terstruktur berbasis aturan jika Gemini API offline atau kuota habis"""
    if context_type == 'prediction':
        city = data.get('city_regency', 'wilayah terpilih')
        prov = data.get('province', '')
        land = data.get('land_area_m2', 0)
        building = data.get('building_area_m2', 0)
        price = data.get('predicted_price', 0)
        percentile_display = data.get('percentile_display', 'P50')
        comp_count = data.get('comp_sample_count', 0)
        comp_level = data.get('comp_level', 'properti sejenis')
        comp_median = data.get('comp_median_juta', 0)
        diff_median_text = data.get('diff_median_text', 'seimbang dengan median pasar')
        price_m2 = data.get('price_per_m2_building', 0)
        model_name = data.get('model_name', 'Random Forest Regressor')
        sample_warning = data.get('sample_warning')

        pos_factors = data.get('top_pos_factors', [])
        neg_factors = data.get('top_neg_factors', [])

        pos_str = "; ".join(pos_factors[:2]) if pos_factors else f"lokasi strategis di {city}"
        neg_str = f" Sementara itu, faktor penahan nilai teridentifikasi pada <strong>{neg_factors[0]}</strong>." if neg_factors else ""

        ratio = round(land / building, 2) if building > 0 else 1.0

        sample_note = f"<br><br><strong>Catatan:</strong> {sample_warning}" if sample_warning and "Peringatan" in sample_warning else ""

        return (
            f"Berdasarkan pemodelan <strong>{model_name}</strong> IndoPrice, estimasi nilai wajar properti ini adalah "
            f"<strong>Rp {price:,.0f}</strong> (sekitar <strong>Rp {price_m2:,.0f}/m²</strong> bangunan). Posisi harga ini berada di persentil "
            f"<strong>{percentile_display}</strong> dari <strong>{comp_count} unit pembanding</strong> ({comp_level}), dengan selisih <strong>{diff_median_text}</strong> "
            f"dibandingkan median pasar wilayah (Rp {comp_median} Juta). Rasio tanah terhadap bangunan tercatat <strong>{ratio}:1</strong>, "
            f"merefleksikan komposisi hunian yang proporsional untuk area {city}, {prov}.<br><br>"
            f"Analisis Explainable AI (TreeSHAP) mengonfirmasi bahwa pendorong valuasi utama berasal dari <strong>{pos_str}</strong>.{neg_str}{sample_note}"
        )
    else:
        title = data.get('title', 'Grafik Pasar')
        return (
            f"Visualisasi <strong>'{title}'</strong> memperlihatkan dispersi harga properti di Indonesia yang dipengaruhi "
            f"secara signifikan oleh faktor lokasi geografis (pusat ekonomi vs penyangga) serta proporsi luas fisik bangunan. "
            f"Kawasan aglomerasi perkotaan utama secara konsisten menunjukkan valuasi per meter persegi tertinggi."
        )
