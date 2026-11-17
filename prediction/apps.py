from django.apps import AppConfig
import os
import json
import logging

logger = logging.getLogger(__name__)

class PredictionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'prediction'
    verbose_name = 'IndoPrice Prediction & Analytics'

    # Class level cache untuk model ML, hierarki lokasi, dan data pembanding
    model = None
    locations = None
    meta_info = None
    df_clean = None

    def ready(self):
        """
        Dijalankan sekali saat Django server menyala.
        Memuat model ke memori RAM untuk inference instan.
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_dir, 'models', 'best_model.joblib')
        loc_path = os.path.join(base_dir, 'models', 'locations_map.json')

        # 1) Load Model ML
        if os.path.exists(model_path):
            try:
                import joblib
                PredictionConfig.model = joblib.load(model_path)
                logger.info("Model Machine Learning 'models/best_model.joblib' berhasil dimuat.")
            except Exception as e:
                logger.warning(f"Gagal memuat best_model.joblib: {e}")
        else:
            logger.warning("File 'models/best_model.joblib' belum ditemukan. Jalankan 'python scripts/train_model.py' terlebih dahulu.")

        # 2) Load Hierarki Lokasi Dropdown
        if os.path.exists(loc_path):
            try:
                with open(loc_path, 'r', encoding='utf-8') as f:
                    PredictionConfig.locations = json.load(f)
                logger.info("Hierarki lokasi 'models/locations_map.json' berhasil dimuat.")
            except Exception as e:
                logger.warning(f"Gagal memuat locations_map.json: {e}")
        else:
            logger.warning("File 'models/locations_map.json' belum ditemukan. Jalankan 'python scripts/train_model.py' terlebih dahulu.")
