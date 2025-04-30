# -*- coding: utf-8 -*-
import logging
from typing import Dict, Any, Tuple, List

# Importar configuración y schemas
import config
from schemas import ManualFormData, AnalysisResult
from utils.i18n import load_strings # Para obtener textos de interpretación

logger = logging.getLogger(__name__)

# Ya no necesitamos get_score_from_string si el frontend envía valores numéricos
# Ya no necesitamos get_score_prefix ni format_option (lógica de presentación)

def calculate_clinical_score(data: ManualFormData) -> int:
    """Calcula la puntuació clínica des d'un model validat."""
    total_score = (
        data.fistules +
        data.recessio +
        data.bulbos +
        data.gingivitis +
        data.mossegada
    )
    # Limitar al máximo definido en config
    max_score = config.MAX_RAW_SCORES.get('clinical', 17)
    final_score = min(total_score, max_score)
    logger.debug(f"Clinical score calculated: {final_score} (raw: {total_score}, max: {max_score})")
    return final_score

def calculate_radiographic_score(data: ManualFormData) -> int:
    """Calcula la puntuació radiogràfica des d'un model validat."""
    total_score = (
        data.dents_afectades +
        data.absents +
        data.forma +
        data.estructura +
        data.superficie
    )
    # Limitar al máximo definido en config
    max_score = config.MAX_RAW_SCORES.get('radio', 14)
    final_score = min(total_score, max_score)
    logger.debug(f"Radiographic score calculated: {final_score} (raw: {total_score}, max: {max_score})")
    return final_score

def _get_classification_and_interpretation(total_integrated_score: int) -> Tuple[str, str]:
    """Determina la clasificación y la interpretación basada en la puntuación integrada."""
    i18n_strings = load_strings(config.DEFAULT_LOCALE) # Carga los textos

    thresholds = config.CLASSIFICATION_THRESHOLDS
    
    if total_integrated_score <= thresholds['low']:
        classification_key = "classification_low"
        interpretation_key = "interpretation_low"
    elif total_integrated_score <= thresholds['moderate']:
        classification_key = "classification_moderate"
        interpretation_key = "interpretation_moderate"
    elif total_integrated_score <= thresholds['high']:
        classification_key = "classification_high"
        interpretation_key = "interpretation_high"
    else: # >= high threshold
        classification_key = "classification_very_high"
        interpretation_key = "interpretation_very_high"

    classification = i18n_strings.get(classification_key, classification_key) # Devuelve clave si no existe
    interpretation = i18n_strings.get(interpretation_key, interpretation_key)

    logger.debug(f"Score: {total_integrated_score} -> Classification: '{classification}', Interpretation: '{interpretation}'")
    return classification, interpretation


def calculate_integrated_score(
    clinical_score: int,
    radio_score: int,
    digital_score: int,
    max_dist_en_value: float,
    roi_analysis_details: list
) -> AnalysisResult:
    """
    Calcula la puntuación integrada final, la clasificación y la interpretación.
    Retorna un objeto AnalysisResult.
    """
    max_scores = config.MAX_RAW_SCORES
    weights = config.SCORE_WEIGHTS
    max_total = config.MAX_INTEGRATED_SCORE

    # Ponderación (con protección por si max_score es 0)
    score_clinica_pond = (clinical_score / max_scores['clinical']) * (max_total * weights['clinical']) if max_scores['clinical'] else 0
    score_radio_pond = (radio_score / max_scores['radio']) * (max_total * weights['radio']) if max_scores['radio'] else 0
    score_digital_pond = (digital_score / max_scores['digital']) * (max_total * weights['digital']) if max_scores['digital'] else 0

    total_integrat = score_clinica_pond + score_radio_pond + score_digital_pond
    total_integrat_arrodonit = round(total_integrat)
    # Asegurar que no exceda el máximo teórico (por redondeos)
    total_integrat_arrodonit = min(total_integrat_arrodonit, max_total)

    logger.info(f"Integrated score calculation: Clinical={clinical_score}, Radio={radio_score}, Digital={digital_score}")
    logger.info(f"Weighted scores: Clinical={score_clinica_pond:.2f}, Radio={score_radio_pond:.2f}, Digital={score_digital_pond:.2f}")
    logger.info(f"Total Integrated Score: {total_integrat:.2f} -> Rounded: {total_integrat_arrodonit}/{max_total}")

    classification, interpretation = _get_classification_and_interpretation(total_integrat_arrodonit)

    # Crear el objeto de resultado
    result = AnalysisResult(
        puntuacio_clinica=clinical_score,
        puntuacio_radio=radio_score,
        puntuacio_digital=digital_score,
        puntuacio_total_integrada=total_integrat_arrodonit,
        classificacio=classification,
        interpretacio=interpretation,
        max_dist_en_value=round(max_dist_en_value, 4), # Redondear para mostrar
        roi_analysis_details=roi_analysis_details
    )

    return result