# -*- coding: utf-8 -*-
import logging

# --- Logging Configuration ---
LOGGING_LEVEL = logging.DEBUG  # INFO para producción, DEBUG para desarrollo
LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# --- Image Analysis Configuration ---
DISTEN_HIGH_THRESHOLD: float = 0.95
DISTEN_MEDIUM_THRESHOLD: float = 0.70
DISTEN_TARGET_SIZE: tuple[int, int] = (64, 64) # Tamaño objetivo para resize antes de DistEn2D
DISTEN_LOW_STD_THRESHOLD: float = 1e-6 # Umbral STD para considerar textura homogénea antes de DistEn
DISTEN_LOW_STD_THRESHOLD_RESIZE: float = 1e-8 # Umbral STD después de resize

# --- Scoring Configuration ---
MAX_RAW_SCORES: dict[str, int] = {
    'clinical': 17,
    'radio': 14,
    'digital': 10
}

SCORE_WEIGHTS: dict[str, float] = {
    'clinical': 0.40,
    'radio': 0.40,
    'digital': 0.20
}

MAX_INTEGRATED_SCORE: int = 41

# Umbrales para la clasificación final integrada (límite superior inclusivo)
CLASSIFICATION_THRESHOLDS: dict[str, int] = {
    'low': 12,
    'moderate': 25,
    'high': 34,
    # 'very_high' es implícito (> high)
}

# Puntuaciones Digitales asignadas según DistEn2D
DIGITAL_SCORE_MAPPING: dict[str, int] = {
    'high': 10,      # si DistEn > DISTEN_HIGH_THRESHOLD
    'medium': 5,     # si DISTEN_MEDIUM_THRESHOLD <= DistEn <= DISTEN_HIGH_THRESHOLD
    'low': 0         # si DistEn < DISTEN_MEDIUM_THRESHOLD
}

# --- i18n Configuration ---
DEFAULT_LOCALE: str = "ca"
LOCALES_PATH: str = "locales" # Ruta a la carpeta con archivos JSON

# --- Form Option Keys (para asegurar consistencia) ---
# Se podrían definir aquí si se quiere mayor robustez, o confiar en los tests
# CLINICAL_KEYS = ["fistules", "recessio", "bulbos", "gingivitis", "mossegada"]
# RADIOGRAPHIC_KEYS = ["dents_afectades", "absents", "forma", "estructura", "superficie"]