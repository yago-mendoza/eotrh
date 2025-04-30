# This layer allows the veterinarian to manually input the clinical signs observed in the patient.
# Clinical signs are evaluated according to Tretow et al. (2025) table

import questionary

def ask_clinical_signs():
    total_score = 0
    
    # Fistulas
    fistulae_response = questionary.select(
        "Fistulae:",
        choices=[
            "1 purulent or up to 3 serous (1 point)",
            "2-3 purulent or 4-6 serous (2 points)",
            ">3 purulent or >6 serous (3 points)"
        ]).ask()
    total_score += int(fistulae_response[fistulae_response.find('(')+1])

    # Gingival recession
    recession_response = questionary.select(
        "Gingival recession:",
        choices=[
            "<1/3 of the root exposed (1 point)",
            "<2/3 of the root exposed (2 points)",
            "Whole root exposed (3 points)"
        ]).ask()
    total_score += int(recession_response[recession_response.find('(')+1])

    # Bulbous thickening of the alveolar region
    bulbous_response = questionary.select(
        "Subgingival vulbous enlargement:",
        choices=[
            "No (0 points)",
            "Yes (1 point)"
        ]).ask()
    total_score += int(bulbous_response[bulbous_response.find('(')+1])

    # Gingivitis
    gingivitis_response = questionary.select(
        "Gingivitis:",
        choices=[
            "Focal (1 point)",
            "Widespread (2 points)",
            "Blueish colour (3 points)"
        ]).ask()
    total_score += int(gingivitis_response[gingivitis_response.find('(')+1])

    # Bite angle
    bite_response = questionary.select(
        "Bite angle not correlated with age:",
        choices=[
            "15 years old and pincer-like (1 point)",
            "Over 15 years old and bisection angle (2 points)",
            "Over 15 years old and pincer-like (3 points)"
        ]).ask()
    total_score += int(bite_response[bite_response.find('(')+1])

    # Classification based on total score
    if total_score == 0:
        stage, comment = "0 - No clinical signs/healthy",  "Subclinical involvement cannot be excluded."
    elif 1 <= total_score <= 2:
        stage, comment = "1 - Suspicious", "Minimal clinical signs. May correspond to very early stages."
    elif 3 <= total_score <= 5:
        stage, comment = "2 - Mild", "Clear but localized clinical signs present."
    elif 6 <= total_score <= 9:
        stage, comment = "3 - Moderate", "Multiple clinical signs of medium intensity."
    else:
        stage, comment = "4 - Severe", "Generalized and severe clinical involvement."

    # Final results
    print("\n--- Clinical questionnaire results ---")
    print(f"Total score: {total_score}")
    print(f"Clinical stage: {stage}")
    print(f"Interpretation: {comment}")
    return total_score

if __name__ == "__main__":
    ask_clinical_signs()
   

