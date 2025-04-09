from fastapi import FastAPI, Request, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
# Importar funcions de càlcul i les noves helpers per opcions
from logic.calculation import (
    calculate_clinical_score,
    calculate_radiographic_score,
    calculate_integrated_score,
    get_clinical_options,
    get_radiographic_options
)
# Importar la funció d'anàlisi de ROIs
from logic.image_analysis import analyze_rois_texture
import shutil
import os
import base64 # Per enviar la imatge al frontend si cal

# Crear directori per pujades temporals si no existeix (si decidim guardar imatges)
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


app = FastAPI(title="EOTRH Diagnosis Assistant v2")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Defineix els textos explicatius per passar a la plantilla
EXPLANATIONS = {
     "upload": "Pugeu la radiografia dental (.jpg, .png). Assegureu-vos que la imatge sigui clara i estigui ben enfocada.",
     "roi": "Dibuixeu rectangles (Regions d'Interès o ROI) sobre les zones sospitoses de les genives o dents a la imatge. L'anàlisi de textura es farà dins d'aquestes àrees.",
     "manual": "Introduïu les observacions clíniques i radiogràfiques manuals seleccionant les opcions que millor descriguin el cas.",
     "results": "A continuació es presenta el diagnòstic integrat basat en l'anàlisi digital (textura ROIs), les observacions clíniques i les radiogràfiques."
}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Mostra la pàgina inicial amb el formulari."""
    # Passem les opcions (ara tuples) i explicacions
    context = {
        "request": request,
        "clinical_options": get_clinical_options(),
        "radiographic_options": get_radiographic_options(),
        "results": None,
        "image_data": None, # Per si volem mostrar la imatge després de pujar
        "explanations": EXPLANATIONS # Afegeix explicacions
    }
    return templates.TemplateResponse("index.html", context)

@app.post("/calculate", response_class=HTMLResponse)
async def handle_calculation(
    request: Request,
    image: UploadFile = File(...),
    roi_data: str = Form(...), # Rep les dades ROI com a string JSON
    # Clinical Data
    fistules: str = Form(...),
    recessio: str = Form(...),
    bulbos: str = Form(...),
    gingivitis: str = Form(...),
    mossegada: str = Form(...),
    # Radiographic Data
    dents_afectades: str = Form(...),
    absents: str = Form(...),
    forma: str = Form(...),
    estructura: str = Form(...),
    superficie: str = Form(...),
):
    """Processa imatge, ROIs, dades manuals i calcula el diagnòstic."""

    # Llegir el contingut de la imatge
    image_content = await image.read()
    if not image_content:
        raise HTTPException(status_code=400, detail="No s'ha pujat cap imatge o està buida.")

    # --- CAPA 1: Anàlisi Digital amb ROIs ---
    # L'anàlisi ara necessita el contingut de la imatge i les ROIs
    max_dist_en, digital_score, roi_details = await analyze_rois_texture(image_content, roi_data)
    # Podem afegir max_dist_en i roi_details als resultats finals si volem mostrar-los

    # --- CAPA 2: Puntuació Clínica ---
    clinical_data = {
        "fistules": fistules, "recessio": recessio, "bulbos": bulbos,
        "gingivitis": gingivitis, "mossegada": mossegada
    }
    clinical_score = calculate_clinical_score(clinical_data)

    # --- CAPA 3: Puntuació Radiològica ---
    radiographic_data = {
        "dents_afectades": dents_afectades, "absents": absents, "forma": forma,
        "estructura": estructura, "superficie": superficie
    }
    radiographic_score = calculate_radiographic_score(radiographic_data)

    # --- Càlcul Integrat ---
    final_results = calculate_integrated_score(
        puntuacio_clinica=clinical_score,
        puntuacio_radio=radiographic_score,
        puntuacio_digital=digital_score # La puntuació basada en el DistEn màxim
    )

    # Afegir detalls extra als resultats per mostrar a la plantilla
    final_results["max_dist_en_value"] = round(max_dist_en, 4) # El valor DistEn màxim trobat
    final_results["roi_analysis_details"] = roi_details # Detalls de cada ROI analitzada

    # Convertir la imatge a Base64 per mostrar-la de nou amb els resultats
    image_b64 = base64.b64encode(image_content).decode("utf-8")
    image_data_uri = f"data:{image.content_type};base64,{image_b64}"


    # Retornar resultats a la plantilla
    # Passem de nou les opcions i explicacions per si el formulari es renderitza
    context = {
        "request": request,
        "clinical_options": get_clinical_options(),
        "radiographic_options": get_radiographic_options(),
        "results": final_results,
        "image_data": image_data_uri, # Passa la imatge per mostrar-la
        "explanations": EXPLANATIONS # Afegeix explicacions
    }

    return templates.TemplateResponse("index.html", context)


if __name__ == "__main__":
    import uvicorn
    print("Iniciant servidor Uvicorn a http://127.0.0.1:8000")
    print("Utilitza `Ctrl+C` per aturar.")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)