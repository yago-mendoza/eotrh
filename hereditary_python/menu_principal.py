import os
import sys
from PyQt5.QtWidgets import (QApplication, QLabel, QVBoxLayout, QWidget, QMainWindow, 
                           QPushButton, QMessageBox, QFrame)
from PyQt5.QtGui import QPixmap, QFont, QPalette, QColor
from PyQt5.QtCore import Qt, QTimer

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from manual_clinical_layer import ask_clinical_signs
from manual_radiographic_layer import ask_radiographic_signs
from automatic_analysis import automatic_analysis

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EOTRH Detect")
        
        # Set window size and position
        self.setFixedSize(800, 600)
        self.center()
        
        # Set green theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f8f0;
            }
            QLabel {
                color: #2e7d32;
            }
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 16px;
                border-radius: 6px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
            QMessageBox {
                background-color: #f0f8f0;
            }
        """)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Add title
        title_label = QLabel("Welcome to EOTRH Detect")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #2e7d32;")
        layout.addWidget(title_label)
        
        # Add subtitle
        subtitle_label = QLabel("Diagnostic Software of EOTRH")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("font-size: 20px; color: #2e7d32;")
        layout.addWidget(subtitle_label)
        
        # Add logo
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            logo_path = os.path.join(project_root, 'resources', 'logo.png')
            
            if not os.path.exists(logo_path):
                error_label = QLabel(f"Error: Logo file not found at {logo_path}")
                error_label.setStyleSheet("color: red; font-weight: bold;")
                layout.addWidget(error_label)
                return
            
            pixmap = QPixmap(logo_path)
            if pixmap.isNull():
                error_label = QLabel(f"Error: Could not load logo from {logo_path}")
                error_label.setStyleSheet("color: red; font-weight: bold;")
                layout.addWidget(error_label)
                return
            
            # Create a frame for the logo
            logo_frame = QFrame()
            logo_frame.setStyleSheet("background-color: white; border-radius: 10px; padding: 20px;")
            logo_layout = QVBoxLayout(logo_frame)
            
            label = QLabel()
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignCenter)
            logo_layout.addWidget(label)
            
            layout.addWidget(logo_frame)
            
        except Exception as e:
            error_label = QLabel(f"Error displaying logo: {str(e)}")
            error_label.setStyleSheet("color: red; font-weight: bold;")
            layout.addWidget(error_label)
        
        # Add spacer
        layout.addStretch()
        
        # Add start button
        start_button = QPushButton("Initiate Diagnosis")
        start_button.setCursor(Qt.PointingHandCursor)
        layout.addWidget(start_button, alignment=Qt.AlignCenter)
        start_button.clicked.connect(self.start_diagnosis)
        
        # Add spacer
        layout.addStretch()
    
    def center(self):
        frame = self.frameGeometry()
        screen = QApplication.primaryScreen().geometry()
        frame.moveCenter(screen.center())
        self.move(frame.topLeft())
    
    def start_diagnosis(self):
        # Run clinical evaluation
        clinical_score = ask_clinical_signs()
        
        # Show message about radiographic evaluation
        msg = QMessageBox()
        msg.setWindowTitle("Next Step")
        msg.setText("Clinical evaluation completed.\n\nProceeding to radiographic evaluation...")
        msg.setIcon(QMessageBox.Information)
        msg.exec_()
        
        # Run radiographic evaluation
        radio_score = ask_radiographic_signs()
        
        # Show final results
        digital_score = 0  # Default value
        integrated_score(clinical_score, radio_score, digital_score)
        
        # Show completion message
        msg = QMessageBox()
        msg.setWindowTitle("Diagnosis Complete")
        msg.setText("The diagnosis process has been completed.\n\nThank you for using EOTRH Detect!")
        msg.setIcon(QMessageBox.Information)
        msg.exec_()

def integrated_score(clinical_score, radio_score, digital_score):
    # Apply specific weights for each layer (normalized to 41 points)
    clinical_score_normal = clinical_score * (41 * 0.4 / 17)   # max 16.4
    radio_score_normal = radio_score * (41 * 0.4 / 14)       # max 16.4
    digital_score_normal = digital_score * (41 * 0.2 / 10)   # max 8.2

    total = clinical_score_normal + radio_score_normal + digital_score_normal
    total_rounded = round(total)

    if total_rounded <= 12:
        classification = "Low suspicion of EOTRH"
        interpretation = "Not enough clinical or radiographic evidence. Routine monitoring and examination recommended."
    elif 13 <= total_rounded <= 25:
        classification = "Moderate suspicion of EOTRH"
        interpretation = "Some signs compatible with EOTRH. Periodic clinical follow-up recommended to monitor progression."
    elif 26 <= total_rounded <= 34:
        classification = "High suspicion of EOTRH"
        interpretation = "Clear correlation between clinical, radiographic and digital signs. Immediate evaluation."
    else:
        classification = "Very high suspicion of severe EOTRH"
        interpretation = "Strong and consistent indicators. Urgent therapeutic intervention recommended."

    print("\n--- INTEGRATED FINAL RESULT ---")
    print(f"Total integrated score: {total_rounded}/41")
    print(f"Classification: {classification}")
    print(f"Interpretation: {interpretation}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
