# -*- coding: utf-8 -*-
import cv2
import numpy as np
from skimage.transform import resize
from skimage import exposure
import json
import logging
import traceback
from typing import List, Tuple, Dict, Any, Optional

# --- Dependencia Externa Clave: EntropyHub ---
# OBJETIVO: Utilizar la función DistEn2D para cuantificar la complejidad textural.
# MANEJO DE ERROR: Si EntropyHub no está instalado, el análisis fallará pero
#                 la aplicación lo manejará mostrando un error al usuario.
try:
    from EntropyHub import DistEn2D
    ENTROPYHUB_AVAILABLE = True
except ImportError:
    ENTROPYHUB_AVAILABLE = False
    DistEn2D = None # Define DistEn2D como None para evitar NameError más adelante si falla la importación.

# --- Importaciones Internas ---
import config # Archivo de configuración (umbrales, tamaño de ROI, mapeo de puntuación).
from schemas import RoiData, RoiAnalysisDetail # Modelos Pydantic para validación y estructura de datos.
from utils.i18n import load_strings # Para cargar mensajes de error traducibles.

logger = logging.getLogger(__name__) # Logger estándar de Python.
# Cargar cadenas de texto (mensajes de error, etc.) para el idioma por defecto.
i18n_strings = load_strings(config.DEFAULT_LOCALE)

# --- Funciones Auxiliares (Descomposición Funcional) ---
# Dividir el proceso en funciones más pequeñas mejora la legibilidad y mantenibilidad.

# --- PASO 3 (por ROI): Extracción de Píxeles ---
def _extract_roi_pixels(image: np.ndarray, roi_vertices: List[Tuple[int, int]]) -> Optional[np.ndarray]:
    """
    Extrae los píxeles de la imagen que caen dentro de una ROI poligonal.

    OBJETIVO: Aislar los píxeles específicos que el usuario ha seleccionado para analizar.
    ORIGEN: `image` es la imagen original en escala de grises (`img_prepared`).
            `roi_vertices` son las coordenadas [x, y] de UN polígono ROI, provenientes
            del frontend (transformadas a coordenadas originales).
    DESTINO: El array 1D de valores de píxeles (uint8) de la ROI, que se pasará a `_preprocess_roi_for_disten`.

    Args:
        image: Imagen NumPy en escala de grises (preparada).
        roi_vertices: Lista de tuplas (x, y) definiendo los vértices de la ROI en coordenadas de la imagen original.

    Returns:
        Array NumPy 1D con los valores de los píxeles de la ROI, o None si la ROI es inválida o no contiene píxeles.
    """
    logger.debug(f"[DEBUG] _extract_roi_pixels: Input image shape={image.shape}, dtype={image.dtype}")
    # Los vértices vienen del frontend (JSON), ya validados >= 3 puntos por `RoiData` schema.
    logger.debug(f"[DEBUG] _extract_roi_pixels: Input roi_vertices={roi_vertices}")
    polygon = np.array(roi_vertices, dtype=np.int32) # OpenCV necesita int32.
    logger.debug(f"[DEBUG] _extract_roi_pixels: Polygon array shape={polygon.shape}, dtype={polygon.dtype}")

    # Validación básica (aunque redundante si el schema funcionó).
    if polygon.shape[0] < 3:
        logger.warning(f"ROI has fewer than 3 vertices ({polygon.shape[0]}). Skipping.")
        return None # No se puede procesar un polígono con menos de 3 vértices.

    # --- Creación de Máscara ---
    # CÓMO: Crear una imagen negra (máscara) del mismo tamaño que la imagen original.
    #       Dibujar el polígono ROI relleno de blanco sobre esta máscara.
    mask = np.zeros(image.shape[:2], dtype=np.uint8) # Máscara 8-bit (0 o 255).
    cv2.fillPoly(mask, [polygon], 255) # Dibuja el polígono relleno.
    logger.debug(f"[DEBUG] _extract_roi_pixels: Mask created shape={mask.shape}, Non-zero after fillPoly={np.count_nonzero(mask)}")

    # --- Dilatación Opcional de la Máscara ---
    # POR QUÉ: A veces, especialmente con ROIs pequeñas o delgadas, `fillPoly` puede no capturar
    #         todos los píxeles deseados, especialmente en los bordes. Una ligera dilatación
    #         de la máscara blanca puede ayudar a incluir estos píxeles límite.
    # CÓMO: Se usa un kernel pequeño (3x3) para expandir ligeramente el área blanca.
    kernel = np.ones((3,3), np.uint8)
    mask_dilated = cv2.dilate(mask, kernel, iterations = 1) # 1 iteración es suficiente para una expansión mínima.
    logger.debug(f"[DEBUG] _extract_roi_pixels: Non-zero in mask after dilation={np.count_nonzero(mask_dilated)}")

    # --- Extracción Final ---
    # CÓMO: Usar la máscara dilatada (donde los píxeles son 255) como índice booleano
    #       para seleccionar los píxeles correspondientes de la imagen en escala de grises.
    roi_pixels = image[mask_dilated == 255]
    logger.debug(f"[DEBUG] _extract_roi_pixels: Extracted roi_pixels size={roi_pixels.size}")

    # Validación post-extracción.
    if roi_pixels.size == 0:
        # Esto puede ocurrir si la ROI es extremadamente pequeña o cae fuera de la imagen.
        logger.warning(f"ROI with vertices {roi_vertices} resulted in zero pixels AFTER DILATION.")
        return None # No hay píxeles para analizar.

    # Devuelve un array 1D plano con los valores de intensidad de los píxeles.
    return roi_pixels

# --- PASO 4 (por ROI): Preprocesamiento para DistEn2D ---
def _preprocess_roi_for_disten(roi_pixels: np.ndarray, roi_index: int) -> Optional[np.ndarray]:
    """
    Prepara los píxeles extraídos de una ROI para el cálculo de DistEn2D.

    OBJETIVO: Acondicionar los datos de la ROI para que cumplan los requisitos y
              mejoren la robustez del cálculo de entropía (DistEn2D).
    ORIGEN: `roi_pixels` es el array 1D de píxeles de `_extract_roi_pixels`.
    DESTINO: Un array NumPy 2D normalizado y redimensionado, listo para `_calculate_disten_safe`,
             o un array 2D de ceros si la ROI es homogénea, o None si hay error.

    Pasos del Preprocesamiento:
    1. Comprobar Desviación Estándar (STD) inicial: Si es muy baja, la ROI es homogénea, DistEn será 0.
    2. Normalizar Rango [0, 1]: Poner todos los valores en una escala comparable.
    3. Redimensionar a Tamaño Fijo: DistEn2D puede ser sensible al tamaño de la entrada. Redimensionar
       a un tamaño estándar (`config.DISTEN_TARGET_SIZE`) asegura comparabilidad entre ROIs de diferentes tamaños.
    4. Normalizar Z-score: Centrar los datos en media 0 y STD 1. Ayuda a estabilizar el cálculo de DistEn.

    Args:
        roi_pixels: Array 1D NumPy con los píxeles de la ROI.
        roi_index: Índice numérico de la ROI (para logging).

    Returns:
        Array 2D NumPy preprocesado (float32), o array de ceros, o None si falla.
    """
    # Tamaño objetivo para redimensionar la ROI (ej. 64x64), definido en config.py.
    target_size = config.DISTEN_TARGET_SIZE

    # --- 1. Comprobar STD Inicial ---
    # POR QUÉ: Si la ROI es casi completamente homogénea (todos los píxeles casi iguales),
    #         su entropía/complejidad es intrínsecamente muy baja (o cero).
    #         Calcular DistEn puede dar problemas numéricos o ser innecesario.
    std_initial = np.std(roi_pixels)
    if std_initial < config.DISTEN_LOW_STD_THRESHOLD: # Umbral bajo definido en config.py.
        logger.info(i18n_strings.get("warning_roi_std_zero", "warning_roi_std_zero").format(roi_index=roi_index))
        # En este caso, consideramos DistEn = 0. Devolvemos un array de ceros del tamaño objetivo
        # como señal para `_calculate_disten_safe`.
        return np.zeros(target_size, dtype=np.float32)

    # --- 2. Normalizar Rango a [0, 1] ---
    # POR QUÉ: Asegura que los valores de píxeles (originalmente 0-255) estén en una escala estándar.
    # CÓMO: Dividir por 255. Convertir a float32 para precisión.
    roi_norm_range = roi_pixels.astype(np.float32) / 255.0
    logger.debug(f"ROI {roi_index}: Range normalization done.")

    # --- 3. Redimensionar a Tamaño Fijo (target_size x target_size) ---
    # POR QUÉ: Comparar DistEn entre ROIs de tamaños muy diferentes puede ser problemático.
    #         Se estandariza el tamaño para que la métrica sea más comparable.
    # CÓMO:
    #   a. Necesitamos una matriz 2D para redimensionar. Convertimos el array 1D `roi_norm_range`
    #      a una matriz lo más cuadrada posible.
    #   b. Se calcula la dimensión `dim` de un cuadrado que contenga al menos `current_size` píxeles.
    #   c. Se añade padding (ceros) si `roi_norm_range` tiene menos píxeles que `dim*dim`.
    #   d. Se redimensiona (`reshape`) a `(dim, dim)`.
    #   e. Se usa `skimage.transform.resize` para redimensionar la matriz `(dim, dim)` a `target_size`.
    #      - `anti_aliasing=True`: Suaviza para evitar artefactos.
    #      - `preserve_range=True`: Mantiene el rango [0, 1] tras redimensionar.

    current_size = roi_norm_range.size
    # Advertir si la ROI original es mucho más pequeña que el tamaño objetivo.
    if current_size < target_size[0] * target_size[1]:
         logger.warning(i18n_strings.get("warning_roi_small", "warning_roi_small").format(roi_index=roi_index, size=current_size))

    # Calcular dimensión del cuadrado intermedio.
    dim = int(np.sqrt(current_size))
    if dim * dim < current_size: dim += 1 # Asegurar que quepan todos los píxeles.
    padded_size = dim * dim

    # Añadir padding si es necesario.
    if current_size < padded_size:
        # `np.pad` añade ceros al final del array 1D.
        roi_padded = np.pad(roi_norm_range, (0, padded_size - current_size), 'constant')
    else:
        roi_padded = roi_norm_range
    # Convertir a matriz 2D cuadrada.
    roi_reshaped = roi_padded.reshape((dim, dim))
    logger.debug(f"ROI {roi_index}: Reshaped to ({dim},{dim}) for resizing.")

    try:
        # Redimensionar a la forma objetivo (ej. 64x64).
        roi_resized = resize(roi_reshaped, target_size, anti_aliasing=True, preserve_range=True)
        logger.debug(f"ROI {roi_index}: Resized to {target_size}.")
    except Exception as e:
        # El redimensionamiento puede fallar por diversas razones (ej. memoria).
        logger.error(f"Error resizing ROI {roi_index}: {e}")
        return None # Indica fallo en el preprocesamiento.

    # --- 4. Normalizar Z-score ---
    # POR QUÉ: Centrar los datos (media=0) y escalarlos (STD=1) puede mejorar la
    #         estabilidad numérica y el rendimiento de algoritmos como DistEn.
    # CÓMO: `(valor - media) / std`. Se maneja el caso de STD muy baja para evitar división por cero.
    mean_val = np.mean(roi_resized)
    std_val = np.std(roi_resized)
    logger.debug(f"ROI {roi_index}: Before Z-score: mean={mean_val:.4f}, std={std_val:.4f}")

    # Comprobar STD después de redimensionar (podría bajar).
    if std_val < config.DISTEN_LOW_STD_THRESHOLD_RESIZE: # Umbral puede ser diferente al inicial.
        logger.warning(i18n_strings.get("warning_roi_low_std_resize", "warning_roi_low_std_resize").format(roi_index=roi_index, std_val=std_val))
        # Si la STD es casi cero, evitamos división por cero. Devolvemos la ROI solo centrada.
        roi_final_norm = roi_resized - mean_val
    else:
        # Aplicar normalización Z-score estándar.
        roi_final_norm = (roi_resized - mean_val) / std_val

    # Comprobación final de validez numérica.
    if np.isnan(roi_final_norm).any() or np.isinf(roi_final_norm).any():
        logger.error(i18n_strings.get("warning_roi_nan_inf", "warning_roi_nan_inf").format(roi_index=roi_index))
        return None # Datos inválidos.

    logger.debug(f"ROI {roi_index}: Z-score normalization done. Shape: {roi_final_norm.shape}")
    # Devuelve la matriz 2D preprocesada, lista para DistEn2D.
    return roi_final_norm


# --- PASO 5 (por ROI): Cálculo de Entropía ---
def _calculate_disten_safe(processed_roi: np.ndarray, roi_index: int) -> Tuple[Optional[float], Optional[str]]:
    """
    Calcula la Entropía de Distribución 2D (DistEn2D) de forma segura para una ROI preprocesada.

    OBJETIVO: Cuantificar la complejidad o irregularidad de la textura espacial de la ROI.
    ORIGEN: `processed_roi` es la matriz 2D resultante de `_preprocess_roi_for_disten`.
    DESTINO: El valor numérico de DistEn2D (float) o None si hay error.

    Args:
        processed_roi: Matriz 2D NumPy preprocesada.
        roi_index: Índice numérico de la ROI (para logging).

    Returns:
        Tupla (valor_disten, error_msg):
            - valor_disten: Float con el valor de DistEn2D redondeado, o 0.0 si la ROI era homogénea, o None si hubo error.
            - error_msg: String con mensaje de error si lo hubo, None si éxito.
    """
    # Comprobación crítica: ¿Está disponible EntropyHub?
    if not ENTROPYHUB_AVAILABLE:
        error_msg = i18n_strings.get("error_entropyhub_missing", "error_entropyhub_missing")
        logger.critical(error_msg)
        return None, error_msg # Error fatal, no se puede calcular.

    # Comprobar si la ROI fue marcada como homogénea en el preprocesamiento.
    if np.all(processed_roi == 0):
         logger.info(f"ROI {roi_index}: Marked as homogeneous (std near zero). DistEn set to 0.")
         return 0.0, None # DistEn es 0 por definición para datos constantes.

    # --- Llamada a EntropyHub.DistEn2D ---
    try:
        logger.info(f"Calculating DistEn2D for ROI {roi_index} with shape {processed_roi.shape}...")
        # Parámetros `m` y `tau`:
        #   - `m=2`: Dimensión de los patrones a comparar (vectores de 2x2 en este caso, común para 2D).
        #   - `tau=1`: Retraso entre píxeles al formar los patrones (adyacentes).
        # Estos valores son típicos pero podrían ajustarse según estudios específicos.
        dist_en_result = DistEn2D(processed_roi, m=2, tau=1)
        logger.info(f"DistEn2D calculation for ROI {roi_index} complete.")

        # Procesar resultado:
        # EntropyHub a veces devuelve una lista con un solo elemento.
        if isinstance(dist_en_result, list) and len(dist_en_result) > 0:
             current_dist_en = float(dist_en_result[0])
        else:
             current_dist_en = float(dist_en_result) # Asumir que es un float directamente.

        # Validación numérica del resultado.
        if not np.isfinite(current_dist_en):
             # Puede ocurrir en casos extremos o por bugs en la librería.
             raise ValueError("DistEn2D calculation resulted in NaN or Inf")

        # Redondear para presentación.
        dist_en_value = round(current_dist_en, 4)
        logger.info(f"ROI {roi_index} DistEn2D value: {dist_en_value}")
        return dist_en_value, None # Éxito.

    except Exception as e:
        # Capturar cualquier error durante el cálculo de DistEn.
        error_msg = i18n_strings.get("error_calculating_roi", "error_calculating_roi").format(roi_index=roi_index, error=str(e))
        logger.error(error_msg)
        logger.debug(traceback.format_exc()) # Log completo de la excepción en modo debug.
        return None, error_msg # Indicar fallo.


# --- PASO 6: Cálculo de la Puntuación Digital Final ---
def _calculate_digital_score(max_dist_en_value: float) -> int:
    """Determina la puntuación digital final basada en el valor MÁXIMO de DistEn2D encontrado entre todas las ROIs.

    OBJETIVO: Traducir la métrica técnica de máxima complejidad textural (`max_dist_en_value`)
              a una categoría clínica simplificada (puntuación numérica).
    ORIGEN: `max_dist_en_value` es el valor más alto de DistEn2D obtenido de todas las ROIs válidas.
    DESTINO: La puntuación entera final que se mostrará al usuario y se usará en la evaluación global.

    RAZONAMIENTO (INFERIDO): Se asume que la presencia de *al menos una* región con alta complejidad
                           textural (DistEn alta) es el indicador clínicamente más relevante.
                           Por eso se usa el MÁXIMO valor encontrado.

    UMBRALES Y MAPEO:
        - Los umbrales `DISTEN_HIGH_THRESHOLD` y `DISTEN_MEDIUM_THRESHOLD` se definen en `config.py`.
          Estos valores deben determinarse EMPÍRICAMENTE mediante estudios clínicos que correlacionen
          los valores de DistEn2D con diagnósticos conocidos.
        - El mapeo `DIGITAL_SCORE_MAPPING` (también en `config.py`) asigna una puntuación entera
          (ej., 0, 1, 3) a las categorías 'low', 'medium', 'high' definidas por los umbrales.
          La elección de los valores de puntuación (ej. por qué 3 y no 2) dependerá de cómo esta
          puntuación digital se integre con otras puntuaciones manuales del sistema EOTRH.
    """
    # Comparar el máximo DistEn con los umbrales definidos en config.py.
    if max_dist_en_value > config.DISTEN_HIGH_THRESHOLD:
        # Si supera el umbral alto -> categoría 'high'.
        score = config.DIGITAL_SCORE_MAPPING['high']
    elif config.DISTEN_MEDIUM_THRESHOLD <= max_dist_en_value <= config.DISTEN_HIGH_THRESHOLD:
        # Si está entre medio y alto (inclusive) -> categoría 'medium'.
        score = config.DIGITAL_SCORE_MAPPING['medium']
    else: # Si es menor que el umbral medio (< DISTEN_MEDIUM_THRESHOLD).
        # -> categoría 'low'.
        score = config.DIGITAL_SCORE_MAPPING['low']

    logger.info(f"Max DistEn2D: {max_dist_en_value:.4f} -> Digital Score: {score} (Thresholds: M={config.DISTEN_MEDIUM_THRESHOLD}, H={config.DISTEN_HIGH_THRESHOLD})")
    return score


# --- Función Principal del Servicio de Análisis de Textura ---
# Esta es la función que será llamada por la ruta de la API (ej. en main.py).

async def analyze_rois_texture(
    file_content: bytes,                 # Contenido binario de la imagen subida.
    rois: List[List[Tuple[int, int]]]  # Lista de ROIs [[(x,y), ...], [(x,y), ...]] en COORDS ORIGINALES.
                                         # Se asume que viene validada por el schema `RoiData`.
) -> Tuple[float, int, List[RoiAnalysisDetail]]: # Retorna: (Max DistEn, Puntuación Final, Detalles por ROI)
    """
    Analiza la textura (usando DistEn2D) dentro de múltiples ROIs definidas por el usuario en una imagen.

    FLUJO PRINCIPAL:
    1. Cargar y preparar la imagen (decode, grayscale, rescale intensity).
    2. Iterar sobre cada ROI recibida del frontend.
    3. Para cada ROI:
        a. Extraer los píxeles correspondientes (`_extract_roi_pixels`).
        b. Preprocesar los píxeles para DistEn2D (`_preprocess_roi_for_disten`).
        c. Calcular DistEn2D de forma segura (`_calculate_disten_safe`).
        d. Registrar el resultado (valor o error) para esta ROI.
        e. Actualizar el valor máximo de DistEn2D encontrado hasta ahora.
    4. Calcular la puntuación digital final basada en el máximo DistEn2D (`_calculate_digital_score`).
    5. Retornar el máximo DistEn, la puntuación final, y la lista de detalles de cada ROI.

    Args:
        file_content: Contenido binario de la imagen (bytes).
        rois: Lista de listas de vértices [(x, y), ...], donde cada lista interna representa una ROI
              en las coordenadas originales de la imagen.

    Returns:
        Tupla (max_disten, digital_score, details_list):
            - max_disten: El valor MÁXIMO de DistEn2D encontrado entre todas las ROIs procesadas con éxito.
            - digital_score: La puntuación digital final (entero) calculada a partir de `max_disten`.
            - details_list: Una lista de objetos `RoiAnalysisDetail`, uno por cada ROI procesada,
                            conteniendo su índice, valor DistEn (si se calculó) y/o mensaje de error.
        Retorna (0.0, 0, [detalles_error]) o (0.0, 0, []) si hay errores irrecuperables (ej. carga de imagen,
        EntropyHub no disponible) o si no se proporcionan ROIs.
    """
    max_dist_en_value = 0.0 # Inicializar el máximo encontrado.
    all_rois_data: List[RoiAnalysisDetail] = [] # Lista para almacenar detalles de cada ROI.
    error_occurred = False # Flag para errores globales que impiden el cálculo.

    # Comprobación inicial crucial: ¿Está EntropyHub disponible?
    if not ENTROPYHUB_AVAILABLE:
         error_msg = i18n_strings.get("error_entropyhub_missing", "error_entropyhub_missing")
         logger.critical(error_msg)
         # Si no hay ROIs para iterar, añadir un error general.
         if not rois:
              all_rois_data.append(RoiAnalysisDetail(roi_index=0, error=error_msg))
         # Marcar error fatal. El bucle for añadirá este error a cada ROI si se itera.
         error_occurred = True

    # --- PASO 1: Cargar y Preparar Imagen ---
    try:
        # Decodificar los bytes de la imagen usando OpenCV.
        nparr = np.frombuffer(file_content, np.uint8)
        img_color = cv2.imdecode(nparr, cv2.IMREAD_COLOR | cv2.IMREAD_IGNORE_ORIENTATION)
        if img_color is None:
            # Error si OpenCV no puede decodificar la imagen.
            logger.error(i18n_strings.get("error_decoding_image", "error_decoding_image"))
            # Devolver valores por defecto y un detalle de error.
            return 0.0, 0, [RoiAnalysisDetail(roi_index=0, error=i18n_strings.get("error_decoding_image"))]

        # Convertir a escala de grises para análisis de textura.
        img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)

        # Reescalar intensidad a 0-255.
        # POR QUÉ: Asegura un rango de valores consistente independientemente del rango original
        #         de la imagen (que podría variar), antes de pasar a la extracción/normalización.
        img_prepared = exposure.rescale_intensity(img_gray, in_range='image', out_range=(0, 255)).astype(np.uint8)
        logger.info("Image loaded and prepared successfully.")
        logger.debug(f"[DEBUG] Prepared image shape: {img_prepared.shape}, dtype: {img_prepared.dtype}")

    except Exception as e:
        # Capturar cualquier error durante la carga/preparación inicial.
        logger.error(f"Error loading/preparing image: {e}")
        logger.debug(traceback.format_exc())
        # Error fatal, devolver valores por defecto y detalle de error.
        return 0.0, 0, [RoiAnalysisDetail(roi_index=0, error=f"Image loading error: {e}")]

    # --- Manejo del caso sin ROIs ---
    if not rois:
        logger.warning("No valid ROIs provided for analysis. Returning score 0.")
        # Si no hay ROIs, la puntuación es 0. Devolver la lista de detalles
        # (que podría contener el error de EntropyHub si ocurrió).
        return 0.0, 0, all_rois_data

    # --- PASO 2: Analizar Cada ROI (Iteración) ---
    logger.info(f"Analyzing {len(rois)} ROIs...")
    for i, roi_verts in enumerate(rois):
        roi_index = i + 1 # Índice 1-based para mostrar al usuario.
        dist_en_value: Optional[float] = None # Resultado de DistEn para esta ROI.
        error_msg: Optional[str] = None # Mensaje de error para esta ROI.

        # Log de las coordenadas originales recibidas del frontend para esta ROI.
        logger.debug(f"[DEBUG] Processing ROI {roi_index} with vertices: {roi_verts}")

        # Si ya hubo un error fatal (EntropyHub ausente), no intentar procesar.
        # Simplemente registrar el error para esta ROI también.
        if error_occurred:
             error_msg = i18n_strings.get("error_entropyhub_missing", "error_entropyhub_missing")
             all_rois_data.append(RoiAnalysisDetail(roi_index=roi_index, error=error_msg))
             continue # Pasar a la siguiente ROI.

        # --- Flujo de Procesamiento por ROI (Try/Except para errores específicos de ROI) ---
        try:
            logger.info(f"Processing ROI {roi_index}...")

            # PASO 3: Extraer píxeles.
            roi_pixels = _extract_roi_pixels(img_prepared, roi_verts)

            if roi_pixels is None:
                # Error si no se pudieron extraer píxeles (ROI inválida/vacía).
                error_msg = "ROI resulted in zero pixels or was invalid" # Mensaje técnico.
                logger.warning(f"ROI {roi_index}: {error_msg}")
            else:
                logger.debug(f"[DEBUG] ROI {roi_index}: Successfully extracted {roi_pixels.size} pixels.")

                # PASO 4: Preprocesar píxeles para DistEn.
                processed_roi = _preprocess_roi_for_disten(roi_pixels, roi_index)

                if processed_roi is None:
                    # Error durante el preprocesamiento (resize, normalize, NaN/Inf).
                    error_msg = "Failed during preprocessing (resize/normalize)" # Mensaje técnico.
                    logger.error(f"ROI {roi_index}: {error_msg}")
                else:
                    # PASO 5: Calcular DistEn2D.
                    dist_en_value, error_msg = _calculate_disten_safe(processed_roi, roi_index)
                    # `dist_en_value` será float, 0.0, o None.
                    # `error_msg` será None si el cálculo fue exitoso.

        except Exception as e:
            # Captura cualquier error inesperado durante el procesamiento de ESTA ROI.
            error_msg = i18n_strings.get("error_processing_roi", "error_processing_roi").format(roi_index=roi_index, error=str(e))
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            # Asegurar que dist_en_value sea None si hubo una excepción aquí.
            dist_en_value = None

        # --- Registrar resultado de esta ROI ---.
        # Añadir los detalles (índice, valor DistEn, error) a la lista de resultados.
        all_rois_data.append(RoiAnalysisDetail(roi_index=roi_index, dist_en=dist_en_value, error=error_msg))

        # --- Actualizar Máximo DistEn ---.
        # Si el cálculo fue exitoso (dist_en_value no es None) Y no hubo error fatal previo.
        if dist_en_value is not None and not error_occurred:
            max_dist_en_value = max(max_dist_en_value, dist_en_value)
            logger.debug(f"ROI {roi_index}: DistEn = {dist_en_value:.4f}. Current max_dist_en = {max_dist_en_value:.4f}")

    # --- PASO 6: Calcular Puntuación Digital Final ---
    # Solo calcular si no hubo un error fatal inicial (ej. EntropyHub).
    # Si hubo error, la puntuación se queda en 0 (inicializada).
    digital_score = _calculate_digital_score(max_dist_en_value) if not error_occurred else 0

    logger.info(f"ROI texture analysis completed. Max DistEn: {max_dist_en_value:.4f}, Final Score: {digital_score}")
    # --- Retorno Final ---
    return max_dist_en_value, digital_score, all_rois_data