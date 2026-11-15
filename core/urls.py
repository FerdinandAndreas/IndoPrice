"""
URL configuration for IndoPrice AI project.
"""
# Import modul admin dan routing URL Django
from django.contrib import admin
from django.urls import path, include

# Daftar rute utama proyek 
urlpatterns = [
    # Rute ke panel admin Django
    path('admin/', admin.site.urls),
    # Teruskan seluruh rute publik ke aplikasi prediction
    path('', include('prediction.urls')),
]
