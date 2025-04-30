# Assistent de Diagnòstic Precoç EOTRH
# Early EOTRH Diagnostic Assistant

Aquesta aplicació web implementada amb FastAPI proporciona una eina d'ajuda al diagnòstic d'Equine Odontoclastic Tooth Resorption and Hypercementosis (EOTRH) en cavalls, basada en la metodologia descrita per Górski (2022) i Tretow et al. (2025). Integra tres capes d'informació: anàlisi digital automàtica (simplificada), signes clínics manuals i signes radiològics manuals.

**ADVERTÈNCIA IMPORTANT:** L'anàlisi digital automàtica (Capa 1) en aquesta versió web està **simplificada**. A diferència del script original que requeria selecció manual de Regions d'Interès (ROI), aquesta versió analitza la **textura global de la imatge** carregada. Això és una limitació significativa i els resultats d'aquesta capa han d'interpretar-se amb precaució. L'eina està pensada com un suport i **no substitueix el judici clínic veterinari professional**.

### Requisits del Sistema

- Python 3.9 o superior
- pip (gestor de paquets de Python)
- 2GB RAM mínim
- 500MB espai en disc

### Instal·lació

1. Clona el repositori:
```bash
git clone https://github.com/your-username/eortrh_diagnosis_app.git
cd eortrh_diagnosis_app
```

2. Crea un entorn virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Linux/Mac
.\venv\Scripts\activate   # En Windows
```

3. Instal·la les dependències:
```bash
pip install pyqt5 opencv-python questionary matplotlib scikit-image EntropyHub fastapi python-multipart jinja2 uvicorn
```

### Execució

1. Inicia el servidor:
```bash
uvicorn app.main:app --reload
```

2. Obre el navegador i accedeix a:
```
http://localhost:8000
```

## English

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
```bash
pip install -r requirements.txt
```

### Running the Application

1. Start the server:
```bash
uvicorn app.main:app --reload
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

## Project Structure

```
eortrh_diagnosis_app/
├── app/
│   ├── main.py           # Main application file
│   ├── models/           # Data models
│   ├── routers/          # API routes
│   ├── static/           # Static files (CSS, JS)
│   └── templates/        # HTML templates
├── tests/                # Test files
├── requirements.txt      # Project dependencies
└── README.md            # This file
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributors

- [Your Name]
- [Other Contributors]

## Citation

If you use this tool in your research, please cite:

```
Górski, K. (2022). [Title of the paper]
Tretow et al. (2025). [Title of the paper]
```