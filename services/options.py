# -*- coding: utf-8 -*-
from typing import Dict, List, Tuple

# NOTA: Los textos descriptivos podrían moverse a locales/ca.json si se desea
#       una internacionalización completa, pero por ahora los dejamos aquí
#       ya que parecen bastante ligados a la lógica de puntuación.

def get_clinical_options() -> Dict[str, List[Tuple[str, int]]]:
    """
    Retorna las opciones y puntuaciones para los signos clínicos.
    Formato: { 'clave_pregunta': [ ('Texto opción 1', score1), ('Texto opción 2', score2), ... ] }
    """
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

def get_radiographic_options() -> Dict[str, List[Tuple[str, int]]]:
    """
    Retorna las opciones y puntuaciones para los signos radiográficos.
    Formato: { 'clave_pregunta': [ ('Texto opción 1', score1), ('Texto opción 2', score2), ... ] }
    """
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
            ("Conservació parcial", 2), # OJO: No había puntuación 1 aquí
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