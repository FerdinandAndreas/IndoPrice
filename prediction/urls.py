from django.urls import path
from . import views

app_name = 'prediction'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('predict/', views.predict_view, name='predict'),
    path('subsidi/', views.subsidi_view, name='subsidi'),
    path('history/', views.history_view, name='history'),

    # AJAX API Endpoints
    path('api/cities/', views.api_get_cities, name='api_cities'),
    path('api/districts/', views.api_get_districts, name='api_districts'),
    path('api/ai-explain/', views.api_ai_explain, name='api_ai_explain'),
    path('api/ai-predict-explain/', views.api_ai_predict_explain, name='api_ai_predict_explain'),
]
