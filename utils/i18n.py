# -*- coding: utf-8 -*-
import json
import os
from functools import lru_cache
import logging
from typing import Dict, Any

# Importar config para saber dónde buscar los archivos
from config import LOCALES_PATH, DEFAULT_LOCALE

logger = logging.getLogger(__name__)

# Usamos lru_cache para no leer el archivo JSON en cada petición
@lru_cache(maxsize=10)
def load_strings(locale: str = DEFAULT_LOCALE) -> Dict[str, Any]:
    """
    Carga el archivo JSON de strings para el locale especificado.
    """
    filepath = os.path.join(LOCALES_PATH, f"{locale}.json")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            strings = json.load(f)
            logger.debug(f"Strings loaded successfully for locale '{locale}' from {filepath}")
            return strings
    except FileNotFoundError:
        logger.error(f"Locale file not found: {filepath}. Falling back to empty dict.")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from file: {filepath}. Falling back to empty dict.")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading strings for locale '{locale}': {e}")
        return {}

# Podrías añadir una función gettext o _ para facilitar la obtención de strings
# def get_string(key: str, locale: str = DEFAULT_LOCALE, **kwargs) -> str:
#     strings = load_strings(locale)
#     template = strings.get(key, key) # Devuelve la clave si no se encuentra
#     try:
#         return template.format(**kwargs) if kwargs else template
#     except KeyError as e:
#         logger.warning(f"Missing format key '{e}' for string key '{key}' in locale '{locale}'")
#         return template # Devuelve la plantilla sin formato