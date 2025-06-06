# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
import json
from typing import Dict, Any, List, Tuple
import datetime

# Importar configuración, schemas y servicios
import config
from schemas import ManualFormData, RoiData, AnalysisResult, RoiAnalysisDetail
from services import scoring, image_analysis, options
from utils.i18n import load_strings

# --- Configuración de Logging ---
logging.basicConfig(level=config.LOGGING_LEVEL, format=config.LOGGING_FORMAT)
logger = logging.getLogger(__name__)

# --- Inicialización FastAPI ---
app = FastAPI(title="EOTRH Watch")

# Montar archivos estáticos (CSS, JS, Imágenes)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar plantillas Jinja2
templates = Jinja2Templates(directory="templates")

# --- Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Sirve la página principal HTML."""
    logger.info("Root endpoint requested. Serving index.html.")
    # Carga strings y opciones para la plantilla inicial
    i18n_strings = load_strings(config.DEFAULT_LOCALE)
    context = {
        "request": request,
        "clinical_options": options.get_clinical_options(),
        "radiographic_options": options.get_radiographic_options(),
        "explanations": { # Mover textos de explicación a i18n
            "upload": i18n_strings.get("upload_explanation", ""),
            "roi": i18n_strings.get("roi_explanation", ""),
            "manual": i18n_strings.get("manual_explanation", ""),
            "results": i18n_strings.get("results_explanation", ""),
        },
        "i18n": i18n_strings, # Pasar todos los strings a la plantilla
        "results": None, # Sin resultados al inicio
        "config": config  # AÑADIR ESTA LÍNEA
    }
    context["now"] = datetime.datetime.utcnow
    return templates.TemplateResponse("index.html", context)

@app.post("/api/calculate", response_class=JSONResponse)
async def api_calculate(
    # Datos del formulario manual (FastAPI los parsea automáticamente)
    fistulae: int = Form(...),
    gingival_recession: int = Form(...),
    subgingival_bulbous_enlargement: int = Form(...),
    gingivitis: int = Form(...),
    bite_angle_not_correlated_with_age: int = Form(...),
    teeth_affected: int = Form(...),
    missing_or_extracted_teeths: int = Form(...),
    tooth_shape: int = Form(...),
    tooth_structure: int = Form(...),
    tooth_surface: int = Form(...),
    # Datos ROI (como string JSON)
    roi_data: str = Form(...), # Recibimos como string
    # Archivo de imagen
    image: UploadFile = File(...)
):
    """
    API para procesar datos y devolver resultados como JSON.
    Esta función contiene la misma lógica que handle_calculation pero devuelve JSON.
    """
    logger.info("API calculation endpoint received request.")

    try:
        # 1. Validar datos manuales con Pydantic
        manual_data = ManualFormData(
            fistulae=fistulae, gingival_recession=gingival_recession, subgingival_bulbous_enlargement=subgingival_bulbous_enlargement,
            gingivitis=gingivitis, bite_angle_not_correlated_with_age=bite_angle_not_correlated_with_age,
            teeth_affected=teeth_affected, missing_or_extracted_teeths=missing_or_extracted_teeths, tooth_shape=tooth_shape,
            tooth_structure=tooth_structure, tooth_surface=tooth_surface
        )
        
        # 2. Validar y parsear datos ROI
        roi_model = RoiData.parse_raw(roi_data)
        validated_rois: List[List[Tuple[int, int]]] = roi_model.root
        
        # 3. Leer contenido de la imagen
        image_content: bytes = await image.read()
        
        # 4. Realizar análisis de textura
        max_disten, digital_score, roi_details = await image_analysis.analyze_rois_texture(
            image_content, validated_rois
        )

        # 5. Calcular puntuaciones manuales
        clinical_score = scoring.calculate_clinical_score(manual_data)
        radiographic_score = scoring.calculate_radiographic_score(manual_data)

        # 6. Calcular puntuación integrada y obtener resultados finales
        analysis_results: AnalysisResult = scoring.calculate_integrated_score(
            clinical_score=clinical_score,
            radio_score=radiographic_score,
            digital_score=digital_score,
            max_dist_en_value=max_disten,
            roi_analysis_details=roi_details
        )
        
        # Devolver los resultados como JSON
        return analysis_results.dict()
        
    except Exception as e:
        logger.error(f"API error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Error procesando los datos: {str(e)}"}
        )
    finally:
        await image.close()

@app.post("/calculate", response_class=HTMLResponse)
async def handle_calculation(
    request: Request,
    # Datos del formulario manual (FastAPI los parsea automáticamente)
    fistulae: int = Form(...),
    gingival_recession: int = Form(...),
    subgingival_bulbous_enlargement: int = Form(...),
    gingivitis: int = Form(...),
    bite_angle_not_correlated_with_age: int = Form(...),
    teeth_affected: int = Form(...),
    missing_or_extracted_teeths: int = Form(...),
    tooth_shape: int = Form(...),
    tooth_structure: int = Form(...),
    tooth_surface: int = Form(...),
    # Datos ROI (como string JSON)
    roi_data: str = Form(...), # Recibimos como string
    # Archivo de imagen
    image: UploadFile = File(...)
):
    """
    Recibe los datos del formulario, la imagen y las ROIs, realiza los cálculos
    y devuelve la página de resultados.
    """
    logger.info("Calculation endpoint received request.")

    # 1. Validar datos manuales con Pydantic
    try:
        manual_data = ManualFormData(
            fistulae=fistulae, gingival_recession=gingival_recession, subgingival_bulbous_enlargement=subgingival_bulbous_enlargement,
            gingivitis=gingivitis, bite_angle_not_correlated_with_age=bite_angle_not_correlated_with_age,
            teeth_affected=teeth_affected, missing_or_extracted_teeths=missing_or_extracted_teeths, tooth_shape=tooth_shape,
            tooth_structure=tooth_structure, tooth_surface=tooth_surface
        )
        logger.debug("Manual form data validated successfully.")
    except ValidationError as e:
        logger.error(f"Manual form data validation failed: {e}")
        # Idealmente, devolverías un error más específico al usuario
        raise HTTPException(status_code=422, detail=f"Error en datos manuales: {e}")

    # 2. Validar y parsear datos ROI
    try:
        # Directamente parsear y validar usando el RootModel desde el string JSON
        roi_model = RoiData.parse_raw(roi_data)
        # Acceder a los datos validados via el atributo .root
        validated_rois: List[List[Tuple[int, int]]] = roi_model.root
        logger.debug(f"ROI data validated successfully. Found {len(validated_rois)} ROIs.")
    except ValidationError as e:
        logger.error(f"ROI data validation/parsing failed: {e}")
        logger.debug(f"Received ROI data string: {roi_data}")
        # Extraer detalles del error para mejor feedback
        error_details = e.errors()
        raise HTTPException(status_code=422, detail=f"Error en datos ROI: {error_details}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format for ROI data: {e}")
        logger.debug(f"Received ROI data string: {roi_data}")
        raise HTTPException(status_code=422, detail="Error en datos ROI: Formato JSON inválido.")

    # 3. Leer contenido de la imagen
    try:
        image_content: bytes = await image.read()
        logger.info(f"Image '{image.filename}' read successfully ({len(image_content)} bytes).")
    except Exception as e:
        logger.error(f"Failed to read uploaded image file: {e}")
        raise HTTPException(status_code=400, detail=f"Error al leer el archivo de imagen: {e}")
    finally:
        await image.close() # Siempre cerrar el archivo

    # 4. Realizar análisis de textura (puede ser largo)
    # Considerar ejecutar en threadpool si es necesario: asyncio.to_thread(image_analysis.analyze_rois_texture, ...)
    try:
        max_disten, digital_score, roi_details = await image_analysis.analyze_rois_texture(
            image_content, validated_rois
        )
    except Exception as e:
        # Captura errores inesperados del propio servicio de análisis
        logger.error(f"Unexpected error during texture analysis: {e}", exc_info=True)
        # Podríamos definir un error específico o usar los detalles devueltos
        max_disten = 0.0
        digital_score = 0
        roi_details = [RoiAnalysisDetail(roi_index=0, error=f"Analysis service error: {e}")]


    # 5. Calcular puntuaciones manuales
    clinical_score = scoring.calculate_clinical_score(manual_data)
    radiographic_score = scoring.calculate_radiographic_score(manual_data)

    # 6. Calcular puntuación integrada y obtener resultados finales
    analysis_results: AnalysisResult = scoring.calculate_integrated_score(
        clinical_score=clinical_score,
        radio_score=radiographic_score,
        digital_score=digital_score,
        max_dist_en_value=max_disten,
        roi_analysis_details=roi_details
    )

    logger.info(f"Final integrated score: {analysis_results.puntuacio_total_integrada}, Classification: {analysis_results.classificacio}")

    # Redirigir a la ruta raíz con los resultados en la sesión
    # Pero volver a TemplateResponse para mantener compatibilidad mientras añadimos el endpoint API
    i18n_strings = load_strings(config.DEFAULT_LOCALE)
    context = {
        "request": request,
        "results": analysis_results.dict(), # Pasar como diccionario a la plantilla
        "clinical_options": options.get_clinical_options(), # Necesario si volvemos atrás
        "radiographic_options": options.get_radiographic_options(), # Necesario si volvemos atrás
        "explanations": { # Mover textos de explicación a i18n
            "upload": i18n_strings.get("upload_explanation", ""),
            "roi": i18n_strings.get("roi_explanation", ""),
            "manual": i18n_strings.get("manual_explanation", ""),
            "results": i18n_strings.get("results_explanation", ""),
        },
         "i18n": i18n_strings, # Pasar todos los strings a la plantilla
         "config": config  # AÑADIR ESTA LÍNEA
    }
    context["now"] = datetime.datetime.utcnow
    return templates.TemplateResponse("index.html", context)

# --- Entry point (si se ejecuta directamente con uvicorn) ---
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server...")
    # Reload=True es útil para desarrollo
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)