# -*- coding: utf-8 -*-
import re # Per extreure punts ignorant emojis

# Defineix emojis/prefixos per puntuacions
SCORE_PREFIX = {
    0: "🟢", # Verd per 0 punts
    1: "🟡", # Groc per 1-2 punts
    2: "🟡",
    3: "🟠", # Taronja per 3 punts
    4: "🔴", # Vermell per 4+ punts
}
# Pots ajustar els llindars i colors/emojis

def get_score_prefix(score: int) -> str:
    """Retorna un prefix visual per a la puntuació."""
    if score >= 4:
        return SCORE_PREFIX.get(4, "")
    elif score == 3:
        return SCORE_PREFIX.get(3, "")
    elif 1 <= score <= 2:
         return SCORE_PREFIX.get(1, "") # Mateix color per 1 i 2
    else: # score == 0
        return SCORE_PREFIX.get(0, "")


def format_option(text: str, score: int) -> str:
     """Afegeix prefix visual i punts al text de l'opció."""
     prefix = get_score_prefix(score)
     return f"{prefix} {text} ({score} punts)"

def get_score_from_string(choice_string: str) -> int:
    """Extreu la puntuació ignorant possibles emojis/prefixos."""
    try:
        # Utilitza regex per trobar el número just abans de " punt"
        match = re.search(r'\((\d+)\s+punt', choice_string)
        if match:
            return int(match.group(1))
        # Fallback per si només és un número (cas '0')
        elif choice_string.strip().isdigit():
             return int(choice_string.strip())
        else:
             print(f"Advertència: No s'ha pogut extreure la puntuació de '{choice_string}'. Assignant 0.")
             return 0
    except (ValueError, TypeError, AttributeError):
        print(f"Advertència: Error en extreure la puntuació de '{choice_string}'. Assignant 0.")
        return 0


# Les funcions calculate_clinical_score i calculate_radiographic_score
# no necessiten canvis interns, ja que get_score_from_string ara ignora els prefixos.

def calculate_clinical_score(data: dict) -> int:
    """Calcula la puntuació clínica basada en les respostes del formulari."""
    total_score = 0
    total_score += get_score_from_string(data.get("fistules", "0"))
    total_score += get_score_from_string(data.get("recessio", "0"))
    total_score += get_score_from_string(data.get("bulbos", "0"))
    total_score += get_score_from_string(data.get("gingivitis", "0"))
    total_score += get_score_from_string(data.get("mossegada", "0"))
    return min(total_score, 17)

def calculate_radiographic_score(data: dict) -> int:
    """Calcula la puntuació radiogràfica basada en les respostes del formulari."""
    total_score = 0
    total_score += get_score_from_string(data.get("dents_afectades", "0"))
    total_score += get_score_from_string(data.get("absents", "0"))
    total_score += get_score_from_string(data.get("forma", "0"))
    total_score += get_score_from_string(data.get("estructura", "0"))
    total_score += get_score_from_string(data.get("superficie", "0"))
    return min(total_score, 14)

# calculate_integrated_score roman igual internament
def calculate_integrated_score(puntuacio_clinica: int, puntuacio_radio: int, puntuacio_digital: int) -> dict:
    MAX_CLINICA = 17
    MAX_RADIO = 14
    MAX_DIGITAL = 10
    PES_CLINICA = 0.40
    PES_RADIO = 0.40
    PES_DIGITAL = 0.20
    MAX_TOTAL = 41

    score_clinica_pond = (puntuacio_clinica / MAX_CLINICA) * (MAX_TOTAL * PES_CLINICA) if MAX_CLINICA else 0
    score_radio_pond = (puntuacio_radio / MAX_RADIO) * (MAX_TOTAL * PES_RADIO) if MAX_RADIO else 0
    score_digital_pond = (puntuacio_digital / MAX_DIGITAL) * (MAX_TOTAL * PES_DIGITAL) if MAX_DIGITAL else 0

    total_integrat = score_clinica_pond + score_radio_pond + score_digital_pond
    total_integrat_arrodonit = round(total_integrat)

    if total_integrat_arrodonit <= 12:
        classificacio = "Baixa sospita d'EOTRH"
        interpretacio = "No hi ha prou evidència clínica ni radiogràfica (corresponent a un grau 0). Es recomana seguiment i exploració rutinària."
    elif 13 <= total_integrat_arrodonit <= 25:
        classificacio = "Sospita moderada d'EOTRH"
        interpretacio = "Alguns indicis compatibles amb EOTRH (grau 1). Es recomana seguiment clínic periòdic per controlar l'evolució."
    elif 26 <= total_integrat_arrodonit <= 34:
        classificacio = "Alta sospita d'EOTRH"
        interpretacio = "Coincidència clara entre signes clínics, radiogràfics i digitals (grau 2). Avaluació immediata."
    else: # >= 35
        classificacio = "Molt alta sospita d'EOTRH greu"
        interpretacio = "Indicadors forts i coherents (grau 3). Es recomana actuació terapèutica urgent."

    return {
        "puntuacio_clinica": puntuacio_clinica,
        "puntuacio_radio": puntuacio_radio,
        "puntuacio_digital": puntuacio_digital,
        "puntuacio_total_integrada": total_integrat_arrodonit,
        "classificacio": classificacio,
        "interpretacio": interpretacio
    }

# --- Funcions helpers per passar opcions amb color a Jinja2 ---
# Aquestes funcions es cridaran des de main.py per preparar el context de la plantilla

def get_clinical_options():
    # Retorna llista de tuples: (text_visible, puntuacio)
    return {
        "fistules": [
            ("Sense fístules", 0),
            ("1 purulenta i fins a 3 seroses", 1),
            ("2-3 purulentes o 4-6 seroses", 2),
            (">3 purulentes o >6 seroses", 3),
        ],
        "recessio": [
            ("Sense recessió", 0),
            ("<1/3 de l'arrel exposada", 1),
            ("<2/3 de l'arrel exposada", 2),
            ("Tota l'arrel exposada", 3),
        ],
        "bulbos": [
             ("No", 0),
             ("Sí", 1)
        ],
         "gingivitis": [
            ("Sense gingivitis", 0),
            ("Focal", 1),
            ("Difusa", 2),
            ("Coloració blavosa", 3),
        ],
        "mossegada": [
             ("Normal o <15 anys", 0),
             ("15 anys amb angle pincer", 1),
             (">15 anys amb angle intermig", 2),
             (">15 anys amb angle pincer", 3),
        ]
    }

def get_radiographic_options():
     # Retorna llista de tuples: (text_visible, puntuacio)
     return {
        "dents_afectades": [
            ("0", 0),
            ("1-4", 1),
            ("5-8", 2),
            ("≥9", 3),
        ],
        "absents": [
            ("Cap", 0),
            ("≥1 incisiu perdut", 1),
        ],
         "forma": [ # Text simplificat per claredat
            ("Regular", 0),
            ("Conservació parcial", 2),
            ("Conservació majoritària", 3),
            ("Pèrdua completa", 4),
        ],
         "estructura": [ # Text simplificat
            ("Cap troballa", 0),
            ("Lleu", 1),
            ("Moderada", 2),
            ("Greu", 3),
        ],
        "superficie": [ # Text simplificat
             ("Cap troballa", 0),
            ("1 zona irregular", 1),
            ("2 irregularitats / rugosa", 2),
            ("Marcada / col·lapse", 3),
        ]
     }