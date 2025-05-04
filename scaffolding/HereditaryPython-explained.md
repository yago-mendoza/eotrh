# Hereditary Python - EOTRH Diagnosis System

## Overview

Hereditary Python is a software system designed for diagnosing Equine Odontoclastic Tooth Resorption and Hypercementosis (EOTRH) in horses. This Python-based application integrates multiple diagnostic layers to provide a comprehensive evaluation system for veterinary use.

## Core Components

The system is structured into three main diagnostic layers:

1. **Automatic Digital Analysis** - Analyzes radiographic images using texture analysis algorithms
2. **Manual Clinical Evaluation** - Captures clinical signs observed by veterinarians
3. **Manual Radiographic Evaluation** - Records radiographic findings observed by veterinarians

## Workflow

The system follows this workflow:

1. Start the application via `menu_principal.py` or the main EOTRH Detect window
2. Complete clinical sign assessment
3. Complete radiographic sign assessment
4. (Optional) Perform automatic digital analysis of radiographs
5. Generate an integrated diagnosis based on all three layers

## Key Files

- **menu_principal.py**: Main application entry point with GUI implementation
- **eotrh_detect.py**: Core diagnostic algorithm and complete workflow implementation
- **manual_clinical_layer.py**: Implementation of clinical sign assessment
- **manual_radiographic_layer.py**: Implementation of radiographic sign assessment
- **automatic_analysis.py**: Implementation of digital image analysis

## Technical Details

### Automatic Digital Analysis

The digital analysis uses texture analysis based on 2D Distance Entropy (DistEn2D) from the EntropyHub library:

1. Loading and normalizing radiographic images
2. Allowing manual selection of Regions of Interest (ROI) through a polygon selection tool
3. Extracting the selected ROI and resizing to a standard size
4. Calculating the entropy distance using DistEn2D algorithm
5. Classifying the results based on entropy distance thresholds

### Clinical Evaluation

The clinical evaluation assesses:
- Fistulae presence and severity
- Gingival gingival_recession
- Subgingival bulbous enlargement
- Gingivitis
- Bite angle not correlated with age

Points are assigned based on severity, with a total score that maps to clinical stages from 0 (healthy) to 4 (severe).

### Radiographic Evaluation

The radiographic evaluation considers:
- Number of affected teeth
- Missing teeth/extractions
- Dental shape
- Dental structure
- Dental surface

Points are assigned based on severity, with a total score that maps to radiographic stages from 0 (normal) to 4 (severe).

### Integrated Scoring

The system combines scores from all three layers using a weighted algorithm:
- 40% weight for clinical score (normalized to 16.4 points maximum)
- 40% weight for radiographic score (normalized to 16.4 points maximum)
- 20% weight for digital analysis score (normalized to 8.2 points maximum)

The total integrated score (out of 41 points) is used to classify cases as:
- Low suspicion (≤12 points)
- Moderate suspicion (13-25 points)
- High suspicion (26-34 points)
- Very high suspicion (>34 points)

## User Interface

The system implements a PyQt5-based graphical user interface with:
- Welcome screen with logo
- Clinical evaluation questionnaire
- Radiographic evaluation questionnaire
- Interactive image selection and ROI definition tools
- Results display with interpretations

## Design Decisions

1. **Multi-layered approach**: Combining digital analysis with manual observations provides a more robust diagnostic approach than any single method alone.

2. **Standardized scoring**: Each diagnostic layer uses a standardized, evidence-based scoring system based on veterinary literature (Tretow et al., 2025).

3. **Weighted integration**: Different weights for each diagnostic layer reflect their relative importance in the diagnosis.

4. **Desktop GUI application**: Implemented using PyQt5 for cross-platform compatibility and user-friendly interface.

5. **Modular architecture**: Each diagnostic layer is implemented in a separate module, allowing for independent development and testing.

## Limitations and Future Development

1. Current digital analysis requires manual ROI selection, which introduces user variability.
2. The system could benefit from integration with DICOM and other veterinary imaging formats.
3. Future versions could incorporate machine learning for automated ROI detection and classification. 