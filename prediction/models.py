from django.db import models

class PredictionHistory(models.Model):
    """Mencatat riwayat prediksi harga yang dilakukan pengguna"""
    province = models.CharField(max_length=100, verbose_name="Provinsi")
    city_regency = models.CharField(max_length=100, verbose_name="Kabupaten/Kota")
    district = models.CharField(max_length=100, blank=True, null=True, verbose_name="Kecamatan")
    land_area_m2 = models.FloatField(verbose_name="Luas Tanah (m²)")
    building_area_m2 = models.FloatField(verbose_name="Luas Bangunan (m²)")
    bedrooms = models.IntegerField(verbose_name="Kamar Tidur")
    bathrooms = models.IntegerField(verbose_name="Kamar Mandi")
    floors = models.IntegerField(default=1, verbose_name="Lantai")

    predicted_price = models.BigIntegerField(verbose_name="Estimasi Harga (Rp)")
    price_low = models.BigIntegerField(blank=True, null=True, verbose_name="Batas Bawah (Rp)")
    price_high = models.BigIntegerField(blank=True, null=True, verbose_name="Batas Atas (Rp)")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Prediksi")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Riwayat Prediksi"
        verbose_name_plural = "Riwayat Prediksi"

    def __str__(self):
        return f"{self.city_regency} ({self.land_area_m2}m²/{self.building_area_m2}m²) - Rp {self.predicted_price:,.0f}"

class AIAnalysisLog(models.Model):
    """Mencatat interaksi analisis dari Gemini AI"""
    topic = models.CharField(max_length=200, verbose_name="Topik Analisis")
    prompt = models.TextField(verbose_name="Pertanyaan/Konteks")
    response = models.TextField(verbose_name="Respon AI")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Analisis")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Log Analisis AI"
        verbose_name_plural = "Log Analisis AI"

    def __str__(self):
        return f"{self.topic} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
