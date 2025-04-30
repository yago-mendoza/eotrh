# This layer allows the veterinarian to manually input the radiographic signs observed in the patient.
# It is based on a standardized scale specific for radiographic signs (according to Tretow et al., 2025).

import questionary

def ask_radiographic_signs():
    total_score = 0

    # Number of affected teeth
    teeth_response = questionary.select(
        "Number of affected teeth:",
        choices=[
            "0 (0 points)",
            "1-4 (1 point)",
            "5-8 (2 points)",
            "≥9 (3 points)"
        ]).ask()
    total_score += int(teeth_response[teeth_response.find('(')+1])

    # Missing teeth/extractions
    missing_response = questionary.select(
        "Missing teeth/extractions:",
        choices=[
            "None (0 points)",
            "One or more incisors already missing/extracted (1 point)"
        ]).ask()
    total_score += int(missing_response[missing_response.find('(')+1])

    # Dental shape
    shape_response = questionary.select(
        "Tooth structure:",
        choices=[
            "Regular (0 points)",
            "Preserved: slightly blunted root tip, increased periodontal space (1 point)",
            "Largely preserved: circumferential increase of the root tip or the more occlusal part of the tooth, intra-alveolar tooth part < clinical crown (2 points)",
            "Largely lost: intra-alveolar tooth part=clinical crown (3 points)",
            "Lost: intra-alveolar tooth part > clinical crown (4 points)"
        ]).ask()
    total_score += int(shape_response[shape_response.find('(')+1])

    # Dental structure
    structure_response = questionary.select(
        "Tooth structure:",
        choices=[
            "No radiological findings (0 points)",
            "Mild: single area of increased radiolucency (up to max. 1/3 of root width)(1 point)",
            "Moderate: multiple areas of increased radiolucency (up to max. 1/3) or two (up to 2/3) (2 points)",
            "Severe: large areas of increased radiolucency (3 points)"
        ]).ask()
    total_score += int(structure_response[structure_response.find('(')+1])

    # Dental surface
    surface_response = questionary.select(
        "Tooth surface:",
        choices=[
            "No radiological findings (0 points)",
            "1 irregularity (up to max 1/3 root length) (1 point)",
            "2 irregularities / rough surface (2 points)",
            "Clearly irregular (sunken surface)/ rough (3 points)"
        ]).ask()
    total_score += int(surface_response[surface_response.find('(')+1])

    # Classification based on total score
    if total_score == 0:
        stage = "0 - Normal"
        interpretation = "No abnormal radiographic findings. Does not exclude mild EOTRH."
    elif 1 <= total_score <= 2:
        stage = "1 - Suspicious"
        interpretation = "Dental shape preserved but sporadic deviations: slightly blunted root tip, irregular/rough surface, slightly altered tooth structure"
    elif 3 <= total_score <= 5:
        stage = "2 - Mild"
        interpretation = "Dental shape preserved, slightly blunted root tip, irregular/rough surface, slightly altered tooth structure"
    elif 6 <= total_score <= 9:
        stage = "3 - Moderate"
        interpretation = "Dental shape largely preserved, intra-alveolar part of tooth is not wider than clinical crown, clearly blunted root tip, irregular/rough surface, moderately altered dental structure"
    else:
        stage = "4 - Severe"
        interpretation = "Loss of dental shape, intra-alveolar part of tooth wider than clinical crown, clearly irregular/rough surface, severely altered dental structure."

    # Final results
    print("\n--- Radiographic questionnaire results ---")
    print(f"Total radiographic score: {total_score}")
    print(f"Radiographic stage: {stage}")
    print(f"Interpretation: {interpretation}")
    return total_score

if __name__ == "__main__":
    ask_radiographic_signs()
    