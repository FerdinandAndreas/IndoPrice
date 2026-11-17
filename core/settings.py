"""
Django settings for IndoPrice project.
"""

from pathlib import Path
import os

# Menentukan Path Root Direktori Proyek 
BASE_DIR = Path(__file__).resolve().parent.parent

# Membaca Variabel dari File .env jika ada
env_path = BASE_DIR / '.env'
if env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        pass

# Konfigurasi keamanan untuk SECRET_KEY, DEBUG, ALLOWED_HOSTS
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-indopriceai-sistem-cerdas-p14-secret-key-2024')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# Daftar aplikasi yang terpasang 
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # App Aplikasi utama IndoPrice
    'prediction.apps.PredictionConfig',
]

# Konfigurasi Middleware Keamanan dan Session
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Konfigurasi routing URL utama 
ROOT_URLCONF = 'core.urls'

# Konfigurasi template engine HTML 
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Konfigurasi server WSGI (WSGI_APPLICATION)
WSGI_APPLICATION = 'core.wsgi.application'

# Konfigurasi database lokal SQLite (DATABASES)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

database_url = os.getenv('DATABASE_URL')
if database_url:
    try:
        import dj_database_url  # type: ignore
        DATABASES['default'] = dj_database_url.config(default=database_url, conn_max_age=600)
    except ImportError:
        pass

# Konfigurasi validasi password pengguna
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Konfigurasi waktu dan bahasa 
LANGUAGE_CODE = 'id-id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True

# Konfigurasi file statis (CSS, JavaScript, dan Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Tipe field kunci utama default (Primary Key)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Konfigurasi Google Gemini API Key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
