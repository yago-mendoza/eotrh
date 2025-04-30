# Hypotheses on Dist2D Library Malfunction

## Context
This document outlines potential reasons why the automatic layer of our EOTRH diagnostic software isn't functioning as expected. The software uses distribution entropy (DistEn2D) for texture analysis of equine dental radiographs to detect EOTRH.

## Potential Issues

### Standardization Problems
- In the reference article, all radiographs followed the same mA and kV parameters
- Our software cannot enforce this standardization across different clinical settings

### ROI Selection Differences
The reference study used a specific ROI selection method:
- Each ROI was manually annotated to cover the largest possible area of both tooth crown and root
- ROIs were individually fitted to separate teeth
- Each ROI was bounded by four high-radiodensity lines representing:
  1. Occlusal side of the incisor tooth
  2. Medial side of the incisor tooth
  3. Apical side of the incisor tooth
  4. Lateral side of the incisor tooth
- ROIs were annotated using ImageJ software and saved as PNG files

Our implementation may differ significantly from this approach.

### Threshold Selection
The criteria I initially used for determining affected/unaffected status was based on the regression graph (Figure 2), but Table 3 in the study provides sensitivity, specificity, etc. for different reference values:
- Mean
- Mean + SD
- Mean + 2 SD

The study indicates that using the **mean** value provides the most balanced results:
- Sensitivity: 0.50
- Specificity: 0.95
- Positive Predictive Value (PPV): 0.67
- Negative Predictive Value (NPV): 0.90

### Suggested Approach
Based on this information, we should:
1. Calculate DistEn2D for each ROI
2. Store the value + known EOTRH grade
3. Analyze the values to find our own mean from our dataset
4. Use that mean as a cutoff in the diagnosis logic
5. Update the cutoff as our dataset grows

The reference study suggests an approximate threshold of DistEn2D = 0.65, but this should be validated with our own data.

## Technical Implementation Notes
The reference study processed images in two steps:
1. Input image filtering (Figure 1D)
2. Output image texture analysis (Figure 1E)

They used:
- Three filtering algorithms implemented with SimpleITK toolkit in Python
- Five entropy-based texture analyses conducted separately using Python 3.8.5 64-bit with the EntropyHub package

## Next Steps
- Determine specific recommendations for each layer of the software
- Consider implementing automatic ROI detection if feasible
- Validate our own threshold values with local data
