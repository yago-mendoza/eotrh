# -*- coding: utf-8 -*-
import cv2
import numpy as np
from skimage.transform import resize
from skimage import exposure
import json
import logging
import traceback
from typing import List, Tuple, Dict, Any, Optional

# Intentar importar EntropyHub, manejar error si no está
try:
    from EntropyHub import DistEn2D
    ENTROPYHUB_AVAILABLE = True
except ImportError:
    ENTROPYHUB_AVAILABLE = False
    DistEn2D = None # Para evitar errores de NameError más adelante

# Importar configuración y schemas
import config
from schemas import RoiData, RoiAnalysisDetail
from utils.i18n import load_strings # Para mensajes de error

logger = logging.getLogger(__name__)
i18n_strings = load_strings(config.DEFAULT_LOCALE)

# --- Funciones Auxiliares (Descomposición Funcional) ---

def _extract_roi_pixels(image: np.ndarray, roi_vertices: List[Tuple[int, int]]) -> Optional[np.ndarray]:
    """
    Extrae los píxeles dentro de una ROI poligonal de una imagen en escala de grises.
    Retorna un array plano de píxeles o None si la ROI es inválida.
    """
    logger.debug(f"[DEBUG] _extract_roi_pixels: Input image shape={image.shape}, dtype={image.dtype}")
    logger.debug(f"[DEBUG] _extract_roi_pixels: Input roi_vertices={roi_vertices}")
    # La validación de >= 3 vértices ya se hace en el schema RoiData
    polygon = np.array(roi_vertices, dtype=np.int32)
    logger.debug(f"[DEBUG] _extract_roi_pixels: Polygon array shape={polygon.shape}, dtype={polygon.dtype}")

    # Eliminar la comprobación de bounding box que causaba problemas
    if polygon.shape[0] < 3:
        logger.warning(f"ROI has fewer than 3 vertices ({polygon.shape[0]}). Skipping.")
        return None # No se puede procesar

    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    # Dibujar el polígono relleno en la máscara
    cv2.fillPoly(mask, [polygon], 255)
    logger.debug(f"[DEBUG] _extract_roi_pixels: Mask created shape={mask.shape}, Non-zero after fillPoly={np.count_nonzero(mask)}")

    # Dilatar ligeramente la máscara para capturar píxeles en casos límite
    kernel = np.ones((3,3), np.uint8)
    mask_dilated = cv2.dilate(mask, kernel, iterations = 1)
    logger.debug(f"[DEBUG] _extract_roi_pixels: Non-zero in mask after dilation={np.count_nonzero(mask_dilated)}")

    # Extraer píxeles donde la máscara dilatada es blanca
    roi_pixels = image[mask_dilated == 255]
    logger.debug(f"[DEBUG] _extract_roi_pixels: Extracted roi_pixels size={roi_pixels.size}")

    if roi_pixels.size == 0:
        logger.warning(f"ROI with vertices {roi_vertices} resulted in zero pixels AFTER DILATION.")
        return None

    return roi_pixels

def _preprocess_roi_for_disten(roi_pixels: np.ndarray, roi_index: int) -> Optional[np.ndarray]:
    """
    Preprocesa los píxeles de una ROI para el cálculo de DistEn2D:
    1. Comprueba STD inicial.
    2. Normaliza rango a [0, 1].
    3. Redimensiona a tamaño objetivo (config.DISTEN_TARGET_SIZE).
    4. Normaliza Z-score.
    Retorna el array 2D preprocesado o None si falla.
    """
    target_size = config.DISTEN_TARGET_SIZE

    # 1. Comprobar STD inicial
    std_initial = np.std(roi_pixels)
    if std_initial < config.DISTEN_LOW_STD_THRESHOLD:
        logger.info(i18n_strings.get("warning_roi_std_zero", "warning_roi_std_zero").format(roi_index=roi_index))
        # En este caso, DistEn será 0, no necesitamos preprocesar más
        return np.zeros(target_size) # Devolvemos array de ceros como marcador

    # 2. Normalizar rango a [0, 1]
    # Asegurar float para la división
    roi_norm_range = roi_pixels.astype(np.float32) / 255.0
    logger.debug(f"ROI {roi_index}: Range normalization done.")

    # 3. Redimensionar a tamaño objetivo
    # Necesitamos que sea 2D para resize. Intentamos un reshape cuadrado.
    current_size = roi_norm_range.size
    if current_size < target_size[0] * target_size[1]:
         logger.warning(i18n_strings.get("warning_roi_small", "warning_roi_small").format(roi_index=roi_index, size=current_size))

    dim = int(np.sqrt(current_size))
    # Ajustar dimensión si no es cuadrado perfecto para incluir todos los píxeles
    if dim * dim < current_size: dim += 1
    padded_size = dim * dim

    # Añadir padding si es necesario para formar el cuadrado
    if current_size < padded_size:
        roi_padded = np.pad(roi_norm_range, (0, padded_size - current_size), 'constant')
    else:
        roi_padded = roi_norm_range
    roi_reshaped = roi_padded.reshape((dim, dim))
    logger.debug(f"ROI {roi_index}: Reshaped to ({dim},{dim}) for resizing.")

    try:
        # Usar anti_aliasing para mejor calidad
        roi_resized = resize(roi_reshaped, target_size, anti_aliasing=True, preserve_range=True)
        logger.debug(f"ROI {roi_index}: Resized to {target_size}.")
    except Exception as e:
        logger.error(f"Error resizing ROI {roi_index}: {e}")
        return None # Fallo en el redimensionamiento

    # 4. Normalizar Z-score
    mean_val = np.mean(roi_resized)
    std_val = np.std(roi_resized)
    logger.debug(f"ROI {roi_index}: Before Z-score: mean={mean_val:.4f}, std={std_val:.4f}")

    if std_val < config.DISTEN_LOW_STD_THRESHOLD_RESIZE:
        logger.warning(i18n_strings.get("warning_roi_low_std_resize", "warning_roi_low_std_resize").format(roi_index=roi_index, std_val=std_val))
        # Evitar división por cero, devolver array centrado en 0
        roi_final_norm = roi_resized - mean_val
    else:
        roi_final_norm = (roi_resized - mean_val) / std_val

    # Comprobar NaNs/Infs después de la normalización
    if np.isnan(roi_final_norm).any() or np.isinf(roi_final_norm).any():
        logger.error(i18n_strings.get("warning_roi_nan_inf", "warning_roi_nan_inf").format(roi_index=roi_index))
        return None # Datos inválidos para DistEn2D

    logger.debug(f"ROI {roi_index}: Z-score normalization done. Shape: {roi_final_norm.shape}")
    return roi_final_norm


def _calculate_disten_safe(processed_roi: np.ndarray, roi_index: int) -> Tuple[Optional[float], Optional[str]]:
    """
    Calcula DistEn2D de forma segura sobre una ROI preprocesada.
    Retorna (valor_disten, error_msg | None).
    """
    if not ENTROPYHUB_AVAILABLE:
        error_msg = i18n_strings.get("error_entropyhub_missing", "error_entropyhub_missing")
        logger.critical(error_msg)
        return None, error_msg

    # Si la ROI era homogénea (marcador de ceros)
    if np.all(processed_roi == 0):
         return 0.0, None # DistEn es 0 por definición

    try:
        logger.info(f"Calculating DistEn2D for ROI {roi_index}...")
        # Parámetros m y tau fijos según el código original
        dist_en_result = DistEn2D(processed_roi, m=2, tau=1) # CORREGIT: Assignar a una sola variable
        logger.info(f"DistEn2D calculation for ROI {roi_index} complete.")

        # El resultado suele ser una lista con un solo valor
        if isinstance(dist_en_result, list) and len(dist_en_result) > 0:
             current_dist_en = float(dist_en_result[0])
        else: # Por si acaso cambia el formato de retorno
             current_dist_en = float(dist_en_result)

        # Asegurar que no sea NaN o Inf (aunque la validación anterior debería prevenirlo)
        if not np.isfinite(current_dist_en):
             raise ValueError("DistEn2D calculation resulted in NaN or Inf")

        dist_en_value = round(current_dist_en, 4)
        logger.info(f"ROI {roi_index} DistEn2D value: {dist_en_value}")
        return dist_en_value, None

    except Exception as e:
        error_msg = i18n_strings.get("error_calculating_roi", "error_calculating_roi").format(roi_index=roi_index, error=str(e))
        logger.error(error_msg)
        logger.debug(traceback.format_exc()) # Log completo en debug
        return None, error_msg


def _calculate_digital_score(max_dist_en_value: float) -> int:
    """Determina la puntuación digital final basada en el valor máximo de DistEn2D."""
    if max_dist_en_value > config.DISTEN_HIGH_THRESHOLD:
        score = config.DIGITAL_SCORE_MAPPING['high']
    elif config.DISTEN_MEDIUM_THRESHOLD <= max_dist_en_value <= config.DISTEN_HIGH_THRESHOLD:
        score = config.DIGITAL_SCORE_MAPPING['medium']
    else: # < DISTEN_MEDIUM_THRESHOLD
        score = config.DIGITAL_SCORE_MAPPING['low']

    logger.info(f"Max DistEn2D: {max_dist_en_value:.4f} -> Digital Score: {score}")
    return score


# --- Función Principal del Servicio ---

async def analyze_rois_texture(
    file_content: bytes,
    rois: List[List[Tuple[int, int]]] # Espera la lista validada por RoiData
) -> Tuple[float, int, List[RoiAnalysisDetail]]:
    """
    Analiza la textura dentro de múltiples ROIs definidas por el usuario.

    Args:
        file_content: Contenido binari de la imagen.
        rois: Lista de ROIs validadas (lista de listas de vértices).

    Returns:
        Tuple (max_disten, digital_score, details_list):
            - max_disten: Valor DistEn2D MÀXIM encontrado.
            - digital_score: Puntuación digital correspondiente.
            - details_list: Lista con detalles de cada ROI analizada.
        Retorna (0.0, 0, []) si hay errores irrecuperables o no hay ROIs.
    """
    max_dist_en_value = 0.0
    all_rois_data: List[RoiAnalysisDetail] = []
    error_occurred = False # Flag para errores generales

    if not ENTROPYHUB_AVAILABLE:
         error_msg = i18n_strings.get("error_entropyhub_missing", "error_entropyhub_missing")
         logger.critical(error_msg)
         # Añadir un detalle de error general si no hay ROIs para iterar
         if not rois:
              all_rois_data.append(RoiAnalysisDetail(roi_index=0, error=error_msg))
         error_occurred = True # Marcar que hubo un error fatal

    # 1. Cargar y preparar la imagen
    try:
        nparr = np.frombuffer(file_content, np.uint8)
        img_color = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_color is None:
            logger.error(i18n_strings.get("error_decoding_image", "error_decoding_image"))
            return 0.0, 0, [RoiAnalysisDetail(roi_index=0, error=i18n_strings.get("error_decoding_image"))]

        img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
        # Reescalar intensidad para asegurar rango 0-255 consistente
        img_prepared = exposure.rescale_intensity(img_gray, in_range='image', out_range=(0, 255)).astype(np.uint8)
        logger.info("Image loaded and prepared successfully.")
        logger.debug(f"[DEBUG] Prepared image shape: {img_prepared.shape}, dtype: {img_prepared.dtype}") # Log Imatge preparada

    except Exception as e:
        logger.error(f"Error loading/preparing image: {e}")
        logger.debug(traceback.format_exc())
        return 0.0, 0, [RoiAnalysisDetail(roi_index=0, error=f"Image loading error: {e}")]

    # Si no hay ROIs, no hay nada más que hacer
    if not rois:
        logger.warning("No valid ROIs provided for analysis.")
        # Devolver el error de EntropyHub si fue el caso, o simplemente lista vacía
        return 0.0, 0, all_rois_data if error_occurred else []

    # 2. Analizar cada ROI
    logger.info(f"Analyzing {len(rois)} ROIs...")
    for i, roi_verts in enumerate(rois):
        roi_index = i + 1
        dist_en_value: Optional[float] = None
        error_msg: Optional[str] = None

        # Log de les coordenades rebudes per a aquesta ROI
        logger.debug(f"[DEBUG] Processing ROI {roi_index} with vertices: {roi_verts}")

        # Si ya hubo error fatal (EntropyHub), no procesar más ROIs
        if error_occurred:
             error_msg = i18n_strings.get("error_entropyhub_missing", "error_entropyhub_missing")
             all_rois_data.append(RoiAnalysisDetail(roi_index=roi_index, error=error_msg))
             continue

        try:
            logger.info(f"Processing ROI {roi_index}...")
            # 3. Extraer píxeles
            roi_pixels = _extract_roi_pixels(img_prepared, roi_verts)

            if roi_pixels is None:
                error_msg = "ROI resulted in zero pixels or was invalid" # No traducir, es técnico
                logger.warning(f"ROI {roi_index}: {error_msg}")
            else:
                logger.debug(f"[DEBUG] ROI {roi_index}: Successfully extracted {roi_pixels.size} pixels.") # Log èxit extracció
                # 4. Preprocesar para DistEn2D
                processed_roi = _preprocess_roi_for_disten(roi_pixels, roi_index)

                if processed_roi is None:
                    error_msg = "Failed during preprocessing (resize/normalize)" # No traducir
                    logger.error(f"ROI {roi_index}: {error_msg}")
                else:
                    # 5. Calcular DistEn2D
                    dist_en_value, error_msg = _calculate_disten_safe(processed_roi, roi_index)

        except Exception as e:
            # Captura errores inesperados en el flujo de una ROI
            error_msg = i18n_strings.get("error_processing_roi", "error_processing_roi").format(roi_index=roi_index, error=str(e))
            logger.error(error_msg)
            logger.debug(traceback.format_exc())

        # Registrar resultado de esta ROI
        all_rois_data.append(RoiAnalysisDetail(roi_index=roi_index, dist_en=dist_en_value, error=error_msg))

        # Actualizar el valor máximo si el cálculo fue exitoso
        if dist_en_value is not None:
            max_dist_en_value = max(max_dist_en_value, dist_en_value)

    # 6. Calcular puntuación digital final
    # Solo calcular si no hubo error fatal (como EntropyHub ausente)
    digital_score = _calculate_digital_score(max_dist_en_value) if not error_occurred else 0

    logger.info("ROI texture analysis completed.")
    return max_dist_en_value, digital_score, all_rois_data