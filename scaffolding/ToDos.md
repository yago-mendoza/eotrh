# EOTRH Diagnostic Assistant - Development Roadmap

## ✅ Core System Features

- [X] Initial application architecture setup with FastAPI
- [X] Responsive web interface with modern design
- [X] Multi-step workflow implementation (upload, ROI, manual data, results)
- [X] Progress bar navigation system
- [X] Error handling and validation system
- [X] Image upload and validation mechanism
- [X] Development of ROI (Region of Interest) selection tools
  - [X] Polygon drawing tool
  - [X] Freehand drawing tool
  - [X] Selection and movement tool
  - [X] Undo/redo functionality
  - [X] Delete functionality
- [X] Complete clinical and radiographic form design
- [X] Results visualization

## ✅ Diagnostic Analysis Components

- [X] Implementation of three-layer analysis system:
  - [X] Layer 1: Digital image analysis using texture algorithms
    - [X] Image preprocessing techniques
    - [X] ROI-based texture analysis with EntropyHub
    - [X] Calculation of Distance Entropy (DistEn) metrics
  - [X] Layer 2: Clinical signs assessment
    - [X] Scoring system for fistulae
    - [X] Scoring system for gingival gingival_recession
    - [X] Scoring system for bulbous appearance
    - [X] Scoring system for gingivitis
    - [X] Scoring system for bite angle
  - [X] Layer 3: Radiographic signs assessment
    - [X] Scoring system for affected teeth
    - [X] Scoring system for missing_or_extracted_teeth teeth
    - [X] Scoring system for tooth shape
    - [X] Scoring system for tooth structure
    - [X] Scoring system for tooth surface
- [X] Integrated scoring algorithm with configurable weights
- [X] Classification system based on thresholds
- [X] Interpretative comments for each diagnostic category

## ✅ User Interface Enhancements

- [X] Development of diagnostic results thermometer visualization
- [X] Loading screens with progress indicators
- [X] Tabbed interface for clinical vs radiographic data
- [X] Mobile-responsive design
- [X] Score breakdown visualization with color-coded bars
- [X] Tool tooltips and user guidance
- [X] Dynamic form validation

## 🔄 Ongoing Improvements & Future Enhancements

- [X] Consider interpretative comments that have been adapted for each state
- [X] Show the score corresponding to each sign in the forms
- [X] Add a "None" option to each question in the form
- [?] Remove final interpretative score - the software should only provide interpretation for each layer without a final interpretation (awaiting client approval)

## 📊 Performance Optimization

- [X] Image preprocessing optimization
- [X] Canvas rendering performance improvements
- [X] Asynchronous processing for computational tasks
- [ ] Server-side caching for faster repeated analyses
- [ ] Optimize mobile performance

## 📦 Packaging

## Deployment Options Overview

- [-] **Build Standalone Executable for Windows Users**  
  Custom executable tailored for offline desktop usage and ease of distribution.  
  **Estimated Cost:** €450

- [-] **Develop Docker Container for Cross-Platform Deployment**  
  Ideal for enterprise environments and CI/CD workflows.  
  **Estimated Cost:** €1220  

- [X] **Package Installers for All Major Operating Systems**  
  Native installers for Windows, macOS, and Linux.  
  - [ ] Include automatic update mechanism for desktop clients  
  **Estimated Cost:** €370  

- [ ] **Cloud-Based Web Deployment**  
  Fully hosted and managed solution with high scalability and minimal maintenance overhead.  
  **Estimated Cost:** €790  
  - Best suited for production environments and enterprise-level usage  

- [X] **Lightweight Self-Hosted Web Deployment**  
  Cost-effective and reliable option using a shared server infrastructure.  
  - [X] Custom domain registration included (€20)  
  - Minimal maintenance, suitable for MVPs and testing phases  
  **Total Estimated Cost:** **€279.99**  
  - ✅ *Excellent value for initial deployment without compromising accessibility*

## 📝 Documentation & Training

- [X] In-application tooltips and guidance
- [ ] README with installation instructions