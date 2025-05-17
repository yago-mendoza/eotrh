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
            ("1 purulent or up to 3 serous", 1),
            ("2-3 purulent or 4-6 serous", 2),
            (">3 purulent or >6 serous", 3),
        ],
        "gingival_recession": [
            ("No gingival recession", 0),
            ("<1/3 of the root exposed", 1),
            ("<2/3 of the root exposed", 2),
            ("Whole root exposed", 3),
        ],
        "subgingival_bulbous_enlargement": [
             ("No", 0),
             ("Yes", 1)
        ],
         "gingivitis": [
            ("No gingivitis", 0),
            ("Focal", 1),
            ("Widespread", 2),
            ("Blueish color", 3),
        ],
        "bite_angle_not_correlated_with_age": [
             ("Normal or <15 years", 0),
             ("15 years and pincer-like", 1),
             ("Over 15 years old and bisection angle", 2),
             ("Over 15 years old and pincer-like", 3),
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
            ("One or more incisors already missing/extracted", 1),
        ],
         "tooth_shape": [
            ("Regular", 0),
            ("Preserved: slightly blunted root tip, enlargement of the periodontal space", 1),
            ("Largely preserved: circumferential increase of the root tip or the more occlusal part of the tooth, intra-alveolar tooth part < clinical crown", 2),
            ("Largely lost: intra-alveolar tooth part = clinical crown", 3),
            ("Lost: intra-alveolar tooth part > clinical crown", 4),
        ],
         "tooth_structure": [
            ("No radiological findings", 0),
            ("Mild: single area of increased radiolucency (up to max. 1/3 of the root width)", 1),
            ("Moderate: multiple areas of increased radiolucency (up to max. 1/3) or two (up to 2/3)", 2),
            ("Severe: large areas of increased radiolucency", 3),
        ],
        "tooth_surface": [
            ("No radiological findings", 0),
            ("1 irregularity (up to max 1/3 root length)", 1),
            ("2 irregularities/surface rough", 2),
            ("Obviously irregular (surface slumps)/ rough", 3),
        ]
     }