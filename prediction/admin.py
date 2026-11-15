from django.contrib import admin
from .models import PredictionHistory, AIAnalysisLog

@admin.register(PredictionHistory)
class PredictionHistoryAdmin(admin.ModelAdmin):
    list_display = ('city_regency', 'province', 'land_area_m2', 'building_area_m2', 'bedrooms', 'bathrooms', 'predicted_price', 'created_at')
    list_filter = ('province', 'city_regency', 'created_at')
    search_fields = ('city_regency', 'province', 'district')
    readonly_fields = ('created_at',)

@admin.register(AIAnalysisLog)
class AIAnalysisLogAdmin(admin.ModelAdmin):
    list_display = ('topic', 'created_at')
    search_fields = ('topic', 'prompt', 'response')
    readonly_fields = ('created_at',)
