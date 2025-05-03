# -*- coding: utf-8 -*-
from typing import Dict, List, Tuple

# NOTE: The descriptive texts could be moved to locales/ca.json if complete
#       internationalization is desired, but for now we leave them here
#       as they seem quite tied to the scoring logic.

def get_clinical_options() -> Dict[str, List[Tuple[str, int]]]:
    """
    Returns the options and scores for clinical signs.
    Format: { 'question_key': [ ('Option text 1', score1), ('Option text 2', score2), ... ] }
    """
    return {
        "fistules": [
            ("No fistulas", 0),
            ("1 purulent and up to 3 serous", 1),
            ("2-3 purulent or 4-6 serous", 2),
            (">3 purulent or >6 serous", 3),
        ],
        "recessio": [
            ("No recession", 0),
            ("<1/3 of root exposed", 1),
            ("<2/3 of root exposed", 2),
            ("Entire root exposed", 3),
        ],
        "bulbos": [
             ("No", 0),
             ("Yes", 1)
        ],
         "gingivitis": [
            ("No gingivitis", 0),
            ("Focal", 1),
            ("Diffuse", 2),
            ("Bluish coloration", 3),
        ],
        "mossegada": [
             ("Normal or <15 years", 0),
             ("15 years with pincer angle", 1),
             (">15 years with intermediate angle", 2),
             (">15 years with pincer angle", 3),
        ]
    }

def get_radiographic_options() -> Dict[str, List[Tuple[str, int]]]:
    """
    Returns the options and scores for radiographic signs.
    Format: { 'question_key': [ ('Option text 1', score1), ('Option text 2', score2), ... ] }
    """
    return {
        "dents_afectades": [
            ("0", 0),
            ("1-4", 1),
            ("5-8", 2),
            ("≥9", 3),
        ],
        "absents": [
            ("None", 0),
            ("≥1 incisor lost", 1),
        ],
         "forma": [ # Simplified text for clarity
            ("Regular", 0),
            ("Partial conservation", 2), # NOTE: There was no score 1 here
            ("Majority conservation", 3),
            ("Complete loss", 4),
        ],
         "estructura": [ # Simplified text
            ("No findings", 0),
            ("Mild", 1),
            ("Moderate", 2),
            ("Severe", 3),
        ],
        "superficie": [ # Simplified text
             ("No findings", 0),
            ("1 irregular area", 1),
            ("2 irregularities / rough", 2),
            ("Marked / collapse", 3),
        ]
     }