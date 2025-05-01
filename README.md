# Assistent de Diagnòstic Precoç EOTRH
# Early EOTRH Diagnostic Assistant

This FastAPI web application provides a diagnostic aid tool for Equine Odontoclastic Tooth Resorption and Hypercementosis (EOTRH) in horses, based on the methodology described by Górski (2022) and Tretow et al. (2025). It integrates three layers of information: automated digital analysis (simplified), manual clinical signs, and manual radiological signs.

**IMPORTANT WARNING:** The automated digital analysis (Layer 1) in this web version is **simplified**. Unlike the original script that required manual selection of Regions of Interest (ROI), this version analyzes the **global texture of the uploaded image**. This is a significant limitation and the results from this layer should be interpreted with caution. The tool is intended as support and **does not replace professional veterinary clinical judgment**.

### System Requirements

- Python 3.9 or higher
- pip (Python package manager)
- 2GB RAM minimum
- 500MB disk space

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/eortrh_diagnosis_app.git
cd eortrh_diagnosis_app
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
.\venv\Scripts\activate   # On Windows
```

3. Install dependencies:

   This project relies on several Python libraries. Here's a breakdown of the key ones:

   **Core Web Framework & Server:**
   *   `fastapi`: A modern, fast (high-performance) web framework for building APIs.
   *   `uvicorn`: A lightning-fast ASGI (`Asynchronous Server Gateway Interface`) server, used to **run** the FastAPI application.
   *   `jinja2`: A templating engine used to render the HTML frontend.
   *   `python-multipart`: Required by FastAPI to handle file uploads (like the X-ray images).

   **Image Analysis & Scientific Computing:**
   *   `opencv-python`: A powerful library for computer vision tasks, used here for image processing.
   *   `scikit-image`: Another image processing library providing algorithms for segmentation, filtering, etc.
   *   `EntropyHub`: A toolkit for calculating entropy measures, likely used for texture analysis.

```bash
pip install fastapi uvicorn jinja2 python-multipart opencv-python scikit-image EntropyHub
```

### Running the Application

0. Make sure your virtual environment is activated and running.

```bash
.\venv\Scripts\activate
```

1. Start the server:
```bash
uvicorn main:app --reload
```
   This command starts the `uvicorn` development server:
   *   `main:app`: Tells `uvicorn` where to find the FastAPI application object. It looks for a variable named `app` inside the `main.py` file.
   *   `--reload`: Enables auto-reload. The server will automatically restart whenever it detects changes in the source code, which is very convenient during development.

2. Open your browser and navigate to:
```
http://localhost:8000
```

## Project Structure

```
eotrh_diagnosis_app/
├── .git/                 # Directorio de Git (ignorado generalmente)
├── .gitignore            # Archivos ignorados por Git
├── __pycache__/          # Caché de Python (ignorado generalmente)
├── config.py             # Archivo de configuración
├── locales/              # Archivos de internacionalización
│   └── ca.json
├── main.py               # Archivo principal de la aplicación FastAPI
├── README.md             # Archivo README
├── schemas.py            # Definiciones de esquemas (Pydantic, etc.)
├── services/             # Lógica de negocio o servicios
│   ├── __init__.py
│   ├── __pycache__/
│   ├── image_analysis.py
│   ├── options.py
│   └── scoring.py
├── static/               # Archivos estáticos para la web
│   ├── assets/           # (Contenido no listado)
│   ├── css/              # (Contenido no listado)
│   ├── img/              # (Contenido no listado)
│   └── js/               # (Contenido no listado)
├── templates/            # Plantillas HTML (Jinja2, etc.)
│   └── index.html
├── utils/                # Funciones de utilidad
│   ├── __init__.py
│   ├── __pycache__/
│   └── i18n.py
└── venv/                 # Entorno virtual de Python (ignorado generalmente)

```

## Arquitectura y Funcionamiento Técnico

### Tecnologías Backend
- **FastAPI**: Framework principal que gestiona rutas, validación y API REST
- **Uvicorn**: Servidor ASGI para ejecutar la aplicación
- **Jinja2**: Motor de plantillas para renderizar HTML
- **OpenCV + scikit-image**: Procesamiento y análisis de imágenes radiográficas
- **EntropyHub**: Cálculo de medidas de entropía para análisis de textura
- **Pydantic**: Validación de datos y definición de esquemas

### Tecnologías Frontend
- **Vanilla JavaScript**: Interacción con API y manipulación del DOM
- **Fetch API**: Comunicación con endpoints del backend
- **Chart.js**: Visualización gráfica de resultados del análisis

### Interacción Backend-Frontend
1. **Frontend** envía imágenes y datos clínicos mediante `fetch` a `/api/analyze`
2. **Backend** procesa la imagen con OpenCV/scikit-image y aplica algoritmos
3. **Backend** devuelve resultados en formato JSON
4. **Frontend** recibe la respuesta y actualiza la interfaz dinámicamente

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Citation

If you use this tool in your research, please cite:

```
Górski, K. (2022). [Title of the paper]
Tretow et al. (2025). [Title of the paper]
```