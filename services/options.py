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
        "fistulae": [
            ("No fistulae", 0),
            ("1 purulent and up to 3 serous", 1),
            ("2-3 purulent or 4-6 serous", 2),
            (">3 purulent or >6 serous", 3),
        ],
        "gingival_recession": [
            ("No gingival recession", 0),
            ("<1/3 of root exposed", 1),
            ("<2/3 of root exposed", 2),
            ("Entire root exposed", 3),
        ],
        "subgingival_bulbous_enlargement": [
             ("No", 0),
             ("Yes", 1)
        ],
         "gingivitis": [
            ("No gingivitis", 0),
            ("Focal", 1),
            ("Diffuse", 2),
            ("Bluish coloration", 3),
        ],
        "bite_angle_not_correlated_with_age": [
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
        "teeth_affected": [
            ("0", 0),
            ("1-4", 1),
            ("5-8", 2),
            ("≥9", 3),
        ],
        "missing_or_extracted_teeths": [
            ("None", 0),
            ("≥1 incisor lost", 1),
        ],
         "tooth_shape": [ # Simplified text for clarity
            ("Regular", 0),
            ("Partial conservation", 2), # NOTE: There was no score 1 here
            ("Majority conservation", 3),
            ("Complete loss", 4),
        ],
         "tooth_structure": [ # Simplified text
            ("No findings", 0),
            ("Mild", 1),
            ("Moderate", 2),
            ("Severe", 3),
        ],
        "tooth_surface": [ # Simplified text
             ("No findings", 0),
            ("1 irregular area", 1),
            ("2 irregularities / rough", 2),
            ("Marked / collapse", 3),
        ]
     }