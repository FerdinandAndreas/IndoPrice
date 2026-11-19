from django.urls import path
from . import views

# Namespace Aplikasi
app_name = 'prediction'

# Daftar Rute Halaman Utama Website
urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('predict/', views.predict_view, name='predict'),
    path('subsidi/', views.subsidi_view, name='subsidi'),
    path('history/', views.history_view, name='history'),
    path('visualisasi/', views.visualization_view, name='visualisasi'),

    # Daftar Endpoint API AJAX 
    path('api/cities/', views.api_get_cities, name='api_cities'),
    path('api/districts/', views.api_get_districts, name='api_districts'),
    path('api/ai-explain/', views.api_ai_explain, name='api_ai_explain'),
    path('api/ai-predict-explain/', views.api_ai_predict_explain, name='api_ai_predict_explain'),
    path('api/chatbot/', views.api_chatbot, name='api_chatbot'),
]
