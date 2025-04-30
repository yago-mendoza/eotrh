import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import PolygonSelector
from matplotlib.path import Path as MplPath
from skimage.transform import resize
from skimage import exposure
from EntropyHub import DistEn2D

# ────────────────────────────────
# AUXILIARY FUNCTIONS
# ────────────────────────────────

def distEn2D_screening_classification(distance):
    if distance <= 0.2:
        return "No digital alterations", "No significant alterations detected in image texture."
    elif 0.2 < distance <= 0.4:
        return "Mild suspicion of EOTRH", "Mild texture alterations that may correspond to early stages."
    elif 0.4 < distance <= 0.6:
        return "Moderate suspicion of EOTRH", "Moderate texture alterations compatible with EOTRH."
    else:
        return "Strong suspicion of EOTRH", "Severe texture alterations coinciding with advanced EOTRH."

def load_and_prepare_image(image_path):
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image from {image_path}")
    
    # Convert to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Normalize the image
    norm_image = cv2.normalize(gray_image, None, 0, 255, cv2.NORM_MINMAX)
    
    return norm_image

def select_polygon_roi(image):
    fig, ax = plt.subplots()
    ax.imshow(image, cmap='gray')
    ax.set_title("Select ROI with polygon (close polygon with right click)")
    
    selector = PolygonSelector(ax, lambda *args: None)
    plt.show()
    
    return selector.verts

def extract_polygonal_roi(image, vertices):
    # Create polygon mask
    h, w = image.shape
    x, y = np.meshgrid(np.arange(w), np.arange(h))
    x, y = x.flatten(), y.flatten()
    points = np.vstack((x, y)).T
    
    path = MplPath(vertices)
    mask = path.contains_points(points)
    mask = mask.reshape(h, w)
    
    # Apply mask
    roi = np.zeros_like(image)
    roi[mask] = image[mask]
    
    return roi

def calculate_entropy_distance(roi):
    # Resize ROI to standard size
    roi_resized = resize(roi, (100, 100))
    
    # Normalize image
    roi_norm = exposure.equalize_hist(roi_resized)
    
    # Calculate DistEn2D
    _, dist = DistEn2D(roi_norm, m=2, tau=1)
    
    return dist

def automatic_analysis():
    print("\n--- Automatic Digital Analysis ---")
    print("This analysis evaluates digital alterations in radiographic images.")
    
    # Request image path
    image_path = input("Enter the path to the radiographic image: ")
    
    try:
        # Load and prepare image
        image = load_and_prepare_image(image_path)
        
        # Select ROI for each tooth
        print("\nSelect ROI for tooth 101:")
        vertices_101 = select_polygon_roi(image)
        roi_101 = extract_polygonal_roi(image, vertices_101)
        
        print("\nSelect ROI for tooth 201:")
        vertices_201 = select_polygon_roi(image)
        roi_201 = extract_polygonal_roi(image, vertices_201)
        
        # Calculate entropy distances
        dist_101 = calculate_entropy_distance(roi_101)
        dist_201 = calculate_entropy_distance(roi_201)
        
        # Classify results
        classif_101, interp_101 = distEn2D_screening_classification(dist_101)
        classif_201, interp_201 = distEn2D_screening_classification(dist_201)
        
        # Show results
        print("\n--- Digital Analysis Results ---")
        print(f"\nTooth 101:")
        print(f"Entropy distance: {dist_101:.3f}")
        print(f"Classification: {classif_101}")
        print(f"Interpretation: {interp_101}")
        
        print(f"\nTooth 201:")
        print(f"Entropy distance: {dist_201:.3f}")
        print(f"Classification: {classif_201}")
        print(f"Interpretation: {interp_201}")
        
        # Return average score
        score = (dist_101 + dist_201) / 2
        return score
        
    except Exception as e:
        print(f"Error in automatic analysis: {str(e)}")
        return 0

if __name__ == "__main__":
    automatic_analysis()
