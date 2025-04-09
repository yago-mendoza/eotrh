import cv2
import numpy as np
from skimage.transform import resize
from skimage import exposure, draw
from EntropyHub import DistEn2D
import io
import json

def extract_roi_pixels(image: np.ndarray, roi_vertices: list) -> np.ndarray:
    """
    Extreu els píxels dins d'una ROI poligonal d'una imatge.
    Retorna un array pla dels píxels dins la ROI.
    """
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    if not roi_vertices:
        return np.array([]) # Retorna array buit si no hi ha vèrtexs

    # Assegurar que els vèrtexs són enters
    polygon = np.array(roi_vertices, dtype=np.int32)

    # Comprovar si és un polígon vàlid (mínim 3 vèrtexs)
    if polygon.shape[0] < 3:
         print("Advertència: ROI amb menys de 3 vèrtexs, ignorant.")
         return np.array([])

    # Dibuixar el polígon omplert a la màscara
    cv2.fillPoly(mask, [polygon], 255)

    # Aplicar la màscara i extreure píxels (només canals grisos si n'hi ha)
    img_gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    roi_pixels = img_gray[mask == 255]

    return roi_pixels

async def analyze_rois_texture(file_content: bytes, rois_json: str):
    """
    Analitza la textura dins de múltiples ROIs definides per l'usuari.

    Args:
        file_content: Contingut binari de la imatge.
        rois_json: String JSON amb les definicions de les ROIs (llista de llistes de vèrtexs).

    Returns:
        Tuple (float, int): Valor DistEn2D MÀXIM trobat i puntuació digital corresponent (0, 5 o 10).
                           Retorna (0.0, 0) si hi ha error o no hi ha ROIs vàlides.
    """
    max_dist_en_value = 0.0
    digital_score = 0
    all_rois_data = []

    try:
        # 1. Carregar la imatge original
        nparr = np.frombuffer(file_content, np.uint8)
        # Carreguem en color per si necessitem visualitzar, però l'anàlisi serà en gris
        img_color = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_color is None:
            print("❌ Error: No s'ha pogut decodificar la imatge.")
            return 0.0, 0, []
        img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
        img_rescaled = exposure.rescale_intensity(img_gray, in_range='image', out_range=(0, 255))

        # 2. Decodificar les ROIs
        rois = json.loads(rois_json)
        if not isinstance(rois, list) or not rois:
            print("⚠️ No s'han proporcionat ROIs vàlides.")
            return 0.0, 0, [] # Cap ROI per analitzar

        # 3. Analitzar cada ROI
        print(f"Analitzant {len(rois)} ROIs...")
        for i, roi_verts in enumerate(rois):
            print(f"  - Processant ROI {i+1}...")
            # Extreure píxels de la ROI actual
            roi_pixels = extract_roi_pixels(img_rescaled, roi_verts)

            if roi_pixels.size == 0:
                print(f"    - ROI {i+1} buida o invàlida, ignorant.")
                all_rois_data.append({"roi_index": i+1, "dist_en": None, "error": "ROI buida o invàlida"})
                continue

            current_dist_en = 0.0
            try:
                # Comprovar variància abans de calcular DistEn2D
                if np.std(roi_pixels) < 1e-6:
                    print(f"    - ROI {i+1} amb textura homogènia (STD ≈ 0). DistEn2D = 0.")
                    current_dist_en = 0.0
                else:
                    # Redimensionar i normalitzar per DistEn2D
                    print(f"    - Iniciant preparació de dades per DistEn2D per ROI {i+1}...")
                    target_size = (64, 64) # Mida més petita pot ser suficient i més ràpida
                    # Assegurar que tenim prou píxels per redimensionar
                    if roi_pixels.size < target_size[0] * target_size[1]:
                         # Si la ROI és molt petita, potser no redimensionar o fer-ho diferent
                         # Per ara, intentem redimensionar igualment
                          print(f"    - Advertència: ROI {i+1} petita ({roi_pixels.size} píxels), el redimensionament pot ser imprecís.")

                    # Cal normalitzar les dades abans de DistEn2D
                    # EntropyHub espera array 2D per DistEn2D, reshape si és necessari
                    # Primer, normalitzem el rang de píxels (0-1)
                    roi_norm_range = roi_pixels.astype(np.float32) / 255.0
                    print(f"    - ROI {i+1}: Normalització de rang feta.")
                    # Redimensionem a la mida objectiu
                    # Necessitem que sigui 2D per resize, fem un reshape temporal
                    # Determinar forma original aproximada no és trivial, fem reshape a quadrat si podem
                    dim = int(np.sqrt(roi_norm_range.size))
                    if dim * dim < roi_norm_range.size: dim += 1 # Ajustar per encabir tots els píxels
                    padded_size = dim*dim
                    if roi_norm_range.size < padded_size: # Afegir padding si cal
                        roi_padded = np.pad(roi_norm_range, (0, padded_size - roi_norm_range.size), 'constant')
                    else:
                        roi_padded = roi_norm_range
                    roi_reshaped = roi_padded.reshape((dim,dim))
                    print(f"    - ROI {i+1}: Reshape a ({dim},{dim}) fet.")

                    # Ara redimensionem
                    roi_resized = resize(roi_reshaped, target_size, anti_aliasing=True)
                    print(f"    - ROI {i+1}: Redimensionament a {target_size} fet.")

                    # Finalment, normalitzem Z-score per DistEn2D
                    mean_val = np.mean(roi_resized)
                    std_val = np.std(roi_resized)
                    print(f"    - ROI {i+1}: Abans de Z-score: mean={mean_val:.4f}, std={std_val:.4f}")
                    if std_val < 1e-8:
                        print(f"    - Advertència: ROI {i+1} amb STD molt baixa ({std_val:.2e}) després de resize. S'evitarà divisió per zero.")
                        roi_final_norm = roi_resized - mean_val
                    else:
                        roi_final_norm = (roi_resized - mean_val) / std_val

                    # Comprovar si hi ha NaNs o Infs després de normalitzar
                    if np.isnan(roi_final_norm).any() or np.isinf(roi_final_norm).any():
                        print(f"    - ❌ ERROR: ROI {i+1} conté NaN o Inf després de normalització. Saltant DistEn2D.")
                        raise ValueError("NaN or Inf detected after Z-score normalization")

                    print(f"    - ROI {i+1}: Normalització Z-score feta. Forma final: {roi_final_norm.shape}")

                    # Calcular DistEn2D
                    print(f"    - ROI {i+1}: Iniciant càlcul DistEn2D...")
                    dist_en_result = DistEn2D(roi_final_norm, m=2, tau=1)
                    print(f"    - ROI {i+1}: Càlcul DistEn2D completat.")

                    # Accedir al valor. DistEn2D retorna una tupla o llista, depenent versió? Comprovem
                    if isinstance(dist_en_result, (list, tuple)) and len(dist_en_result) > 0:
                         # Podria retornar (val, LOG) o [[val]]
                         if isinstance(dist_en_result[0], (list, tuple)):
                              current_dist_en = dist_en_result[0][0]
                         else:
                              current_dist_en = dist_en_result[0]
                    else:
                         # Si retorna directament el valor
                         current_dist_en = float(dist_en_result)

                    current_dist_en = round(current_dist_en, 4)
                    print(f"    - ROI {i+1} DistEn2D: {current_dist_en}")

            except ImportError:
                 print("❌ Error Fatal: La llibreria EntropyHub no està instal·lada o no es troba.")
                 raise # Rellancem l'error perquè el servidor el capturi
            except Exception as e:
                # Imprimir l'error específic que va passar
                import traceback
                print(f"❌ Error processant ROI {i+1} durant preparació o càlcul DistEn2D: {e}")
                print(traceback.format_exc())
                current_dist_en = 0.0 # Assignem 0 en cas d'error
                # Afegim al log de dades de ROI l'error específic
                all_rois_data.append({"roi_index": i+1, "dist_en": None, "error": f"Error en càlcul: {e}"})
                continue # Anem a la següent ROI

            # Només afegir si no hi ha hagut error abans (dins del try/except)
            if any(d['roi_index'] == i+1 and d['error'] for d in all_rois_data): # Comprova si ja s'ha registrat error
                 pass # Ja s'ha registrat l'error, no afegir 'None' error
            else:
                 all_rois_data.append({"roi_index": i+1, "dist_en": current_dist_en, "error": None})

            # Actualitzar el valor màxim trobat fins ara
            max_dist_en_value = max(max_dist_en_value, current_dist_en)

    except json.JSONDecodeError:
        print("❌ Error: El format de les dades ROI no és JSON vàlid.")
        return 0.0, 0, []
    except Exception as e:
        print(f"❌ Error general durant l'anàlisi de ROIs: {e}")
        return 0.0, 0, [] # Retorna 0 en cas d'error general

    # Determinar puntuació digital final basada en el valor MÀXIM
    if max_dist_en_value > 0.95:
        digital_score = 10
    elif 0.70 <= max_dist_en_value <= 0.95:
        digital_score = 5
    else: # < 0.70
        digital_score = 0

    print(f"📊 Anàlisi completada. Max DistEn2D: {max_dist_en_value}. Puntuació Digital Final: {digital_score}")
    # Retornem el DistEn2D màxim, la puntuació final i les dades de cada ROI per possible display
    return max_dist_en_value, digital_score, all_rois_data