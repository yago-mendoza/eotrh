import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                           QPushButton, QRadioButton, QButtonGroup, QMessageBox,
                           QScrollArea, QMainWindow, QFrame)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from manual_clinical_layer import ask_clinical_signs
from manual_radiographic_layer import ask_radiographic_signs
from automatic_analysis import automatic_analysis

# Global variables
clinical_score = 0
radio_score = 0

def interpret_clinical(p):
    if p == 0:
        return ("Clinical stage: 0",
                "No clinical signs/healthy",
                "Subclinical involvement cannot be excluded.",
                "Routine monitoring recommended.")
    elif p <= 2:
        return ("Clinical stage: 1",
                "Suspicious",
                "Minimal clinical signs. May correspond to very early stages.",
                "6-month follow-up recommended.")
    elif p <= 5:
        return ("Clinical stage: 2",
                "Mild",
                "Clear but localized clinical signs present.",
                "3-6 month follow-up recommended.")
    elif p <= 9:
        return ("Clinical stage: 3",
                "Moderate",
                "Multiple clinical signs of medium intensity.",
                "1-3 month follow-up recommended.")
    else:
        return ("Clinical stage: 4",
                "Severe",
                "Generalized and severe clinical involvement.",
                "Immediate evaluation recommended.")

def interpret_radiographic(p):
    if p == 0:
        return ("Radiographic stage: 0",
                "Normal",
                "No abnormal radiographic findings. Does not exclude mild EOTRH.",
                "Routine monitoring recommended.")
    elif p <= 2:
        return ("Radiographic stage: 1",
                "Suspicious",
                "Dental shape preserved but sporadic deviations.",
                "6-month follow-up recommended.")
    elif p <= 5:
        return ("Radiographic stage: 2",
                "Mild",
                "Dental shape preserved, slightly blunted root tip.",
                "3-6 month follow-up recommended.")
    elif p <= 9:
        return ("Radiographic stage: 3",
                "Moderate",
                "Dental shape largely preserved, clearly blunted root tip.",
                "1-3 month follow-up recommended.")
    else:
        return ("Radiographic stage: 4",
                "Severe",
                "Loss of dental shape, severely altered dental structure.",
                "Immediate evaluation recommended.")

def interpret_final(p):
    if p <= 4:
        return ("Low suspicion of EOTRH",
                "Routine monitoring recommended.")
    elif p <= 9:
        return ("Mild suspicion of EOTRH",
                "6-month follow-up recommended.")
    elif p <= 15:
        return ("Moderate suspicion of EOTRH",
                "3-6 month follow-up recommended.")
    elif p <= 21:
        return ("High suspicion of severe EOTRH",
                "1-3 month follow-up recommended.")
    else:
        return ("Very high suspicion of severe EOTRH",
                "Immediate evaluation recommended.")

# ───── INTERFACE ─────
class WelcomeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EOTRH Detect")
        self.setStyleSheet("background-color: #f0fef0;")
        self.clinical_window = None
        layout = QVBoxLayout()

        title = QLabel("Welcome to EOTRH Detect: EOTRH diagnostic software")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #0A3D2E; font-family: Arial")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        img = QLabel()
        try:
            logo_path = "../assets/logo.png"
            logo_pixmap = QPixmap(logo_path)
            if not logo_pixmap.isNull():
                logo_pixmap = logo_pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img.setPixmap(logo_pixmap)
                img.setAlignment(Qt.AlignCenter)
                layout.addWidget(img)
        except Exception as e:
            print(f"Error loading logo: {e}")

        button = QPushButton("Start Diagnosis")
        button.setStyleSheet("""
            QPushButton {
                background-color: #8fc98f;
                font-size: 16px;
                padding: 10px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #7ab97a;
            }
        """)
        button.clicked.connect(self.start)
        layout.addWidget(button)

        # Footer message
        footer = QLabel("Version 1.0 · Developed by Martina · 2025")
        footer.setStyleSheet("font-size: 10px; color: #555")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

        self.setLayout(layout)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

    def start(self):
        self.clinical_window = ClinicalLayer()
        self.clinical_window.show()
        self.close()

class ClinicalLayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manual Clinical Signs Layer")
        self.setStyleSheet("""
            QWidget {
                background-color: #f0fef0;
            }
            QLabel {
                margin-top: 10px;
            }
            QRadioButton {
                margin-left: 20px;
                padding: 5px;
                min-width: 600px;
                max-width: 900px;
                padding-right: 20px;
            }
        """)
        self.radio_window = None
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Clinical Signs Evaluation")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0A3D2E; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(15)
        
        self.titles = [
            ("Fistulae", [
                ("1 purulent or up to 3 serous (1 point)", 1),
                ("2-3 purulent or 4-6 serous (2 points)", 2),
                (">3 purulent or >6 serous (3 points)", 3)
            ]),
            ("Gingival recession", [
                ("<1/3 of the root exposed (1 point)", 1),
                ("<2/3 of the root exposed (2 points)", 2),
                ("Whole root exposed (3 points)", 3)
            ]),
            ("Subgingival bulbous enlargement", [
                ("No (0 points)", 0),
                ("Yes (1 point)", 1)
            ]),
            ("Gingivitis", [
                ("Focal (1 point)", 1),
                ("Widespread (2 points)", 2),
                ("Blueish colour (3 points)", 3)
            ]),
            ("Bite angle not correlated with age", [
                ("15 years old and pincer-like (1 point)", 1),
                ("Over 15 years old and bisection angle (2 points)", 2),
                ("Over 15 years old and pincer-like (3 points)", 3)
            ])
        ]

        self.groups = []
        for title, options in self.titles:
            group_widget = QWidget()
            group_layout = QVBoxLayout()
            group_layout.setSpacing(8)
            
            label = QLabel(f"<b>{title}</b>")
            label.setFont(QFont('Arial', 14))
            label.setStyleSheet("color: #0A3D2E;")
            label.setWordWrap(True)
            group_layout.addWidget(label)
            
            group = QButtonGroup(self)
            for text, value in options:
                rb = QRadioButton(text)
                rb.setProperty("value", value)
                rb.setFont(QFont('Arial', 12))
                group.addButton(rb)
                group_layout.addWidget(rb)
            
            group_widget.setLayout(group_layout)
            scroll_layout.addWidget(group_widget)
            self.groups.append(group)

        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        button = QPushButton("Next")
        button.setStyleSheet("""
            QPushButton {
                background-color: #8fc98f;
                font-size: 16px;
                padding: 10px;
                border-radius: 5px;
                border: none;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #7ab97a;
            }
        """)
        button.clicked.connect(self.next)
        layout.addWidget(button)

        self.setLayout(layout)
        self.setMinimumWidth(1000)
        self.setMinimumHeight(800)

    def next(self):
        global clinical_score
        clinical_score = 0
        
        # Check if all options are selected
        for group in self.groups:
            if not group.checkedButton():
                QMessageBox.warning(self, "Warning", "Please select an option for all categories before proceeding.")
                return
                
        # Calculate score
        for group in self.groups:
            selected_button = group.checkedButton()
            clinical_score += selected_button.property("value")

        QMessageBox.information(self, "Information", "Now we will analyze the radiographic signs.")
        self.radio_window = RadioLayer()
        self.radio_window.show()
        self.close()

class RadioLayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manual Radiographic Signs Layer")
        self.setStyleSheet("""
            QWidget {
                background-color: #f0fef0;
            }
            QLabel {
                margin-top: 10px;
            }
            QRadioButton {
                margin-left: 20px;
                padding: 5px;
                min-width: 600px;
                max-width: 900px;
                padding-right: 20px;
            }
        """)
        self.result_window = None
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Radiographic Signs Evaluation")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0A3D2E; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(15)

        self.titles = [
            ("Number of affected teeth", [
                ("0 (0 points)", 0),
                ("1-4 (1 point)", 1),
                ("5-8 (2 points)", 2),
                ("≥9 (3 points)", 3)
            ]),
            ("Missing teeth/extractions", [
                ("None (0 points)", 0),
                ("One or more incisors already missing/extracted (1 point)", 1)
            ]),
            ("Tooth structure", [
                ("Regular (0 points)", 0),
                ("Preserved: slightly blunted root tip, increased periodontal space (1 point)", 1),
                ("Largely preserved: circumferential increase of the root tip (2 points)", 2),
                ("Largely lost: intra-alveolar tooth part=clinical crown (3 points)", 3),
                ("Lost: intra-alveolar tooth part > clinical crown (4 points)", 4)
            ]),
            ("Tooth structure alterations", [
                ("No radiological findings (0 points)", 0),
                ("Mild: single area of increased radiolucency (1 point)", 1),
                ("Moderate: multiple areas of increased radiolucency (2 points)", 2),
                ("Severe: large areas of increased radiolucency (3 points)", 3)
            ]),
            ("Tooth surface", [
                ("No radiological findings (0 points)", 0),
                ("1 irregularity (up to max 1/3 root length) (1 point)", 1),
                ("2 irregularities / rough surface (2 points)", 2),
                ("Clearly irregular (sunken surface)/ rough (3 points)", 3)
            ])
        ]

        self.groups = []
        for title, options in self.titles:
            group_widget = QWidget()
            group_layout = QVBoxLayout()
            group_layout.setSpacing(8)
            
            label = QLabel(f"<b>{title}</b>")
            label.setFont(QFont('Arial', 14))
            label.setStyleSheet("color: #0A3D2E;")
            label.setWordWrap(True)
            group_layout.addWidget(label)
            
            group = QButtonGroup(self)
            for text, value in options:
                rb = QRadioButton(text)
                rb.setProperty("value", value)
                rb.setFont(QFont('Arial', 12))
                group.addButton(rb)
                group_layout.addWidget(rb)
            
            group_widget.setLayout(group_layout)
            scroll_layout.addWidget(group_widget)
            self.groups.append(group)

        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        button = QPushButton("Show Results")
        button.setStyleSheet("""
            QPushButton {
                background-color: #8fc98f;
                font-size: 16px;
                padding: 10px;
                border-radius: 5px;
                border: none;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #7ab97a;
            }
        """)
        button.clicked.connect(self.results)
        layout.addWidget(button)

        self.setLayout(layout)
        self.setMinimumWidth(1000)
        self.setMinimumHeight(800)

    def results(self):
        global radio_score
        radio_score = 0
        
        # Check if all options are selected
        for group in self.groups:
            if not group.checkedButton():
                QMessageBox.warning(self, "Warning", "Please select an option for all categories before proceeding.")
                return
                
        # Calculate score
        for group in self.groups:
            selected_button = group.checkedButton()
            radio_score += selected_button.property("value")

        self.result_window = ResultWindow()
        self.result_window.show()
        self.close()

class ResultWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Final Result")
        self.setStyleSheet("""
            QWidget {
                background-color: #f0fef0;
            }
            QLabel {
                margin: 10px;
                padding: 10px;
                min-width: 800px;
            }
            QLabel[class="section-title"] {
                font-size: 24px;
                font-weight: bold;
                color: #0A3D2E;
                margin-top: 20px;
            }
            QLabel[class="score"] {
                font-size: 18px;
                color: #2E5A4A;
                margin-top: 15px;
            }
            QLabel[class="interpretation"] {
                font-size: 14px;
                color: #333;
                margin-left: 20px;
                margin-top: 5px;
                padding-right: 20px;
                line-height: 1.4;
            }
        """)
        
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        # Create content widget
        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Title
        title = QLabel("EOTRH Evaluation Results")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #0A3D2E; margin-bottom: 30px;")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        layout.addWidget(title)

        # Calculate normalized scores
        clinical_score_normal = clinical_score * (41 * 0.4 / 17)   # max 16.4
        radio_score_normal = radio_score * (41 * 0.4 / 14)       # max 16.4
        digital_score = 0  # Default value
        digital_score_normal = digital_score * (41 * 0.2 / 10)   # max 8.2

        total = clinical_score_normal + radio_score_normal + digital_score_normal
        total_rounded = round(total)

        # Calculate results
        c1, c2, c3, c4 = interpret_clinical(clinical_score)
        r1, r2, r3, r4 = interpret_radiographic(radio_score)

        # Determine final classification
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

        # Clinical Section
        clinical_title = QLabel("Clinical Results")
        clinical_title.setProperty("class", "section-title")
        clinical_title.setWordWrap(True)
        layout.addWidget(clinical_title)

        clinical_score_label = QLabel(f"Raw Score: {clinical_score} (Normalized: {clinical_score_normal:.1f})")
        clinical_score_label.setProperty("class", "score")
        clinical_score_label.setWordWrap(True)
        layout.addWidget(clinical_score_label)

        for text in [c1, c2, c3, c4]:
            label = QLabel(text)
            label.setProperty("class", "interpretation")
            label.setWordWrap(True)
            layout.addWidget(label)

        # Radiographic Section
        radio_title = QLabel("Radiographic Results")
        radio_title.setProperty("class", "section-title")
        radio_title.setWordWrap(True)
        layout.addWidget(radio_title)

        radio_score_label = QLabel(f"Raw Score: {radio_score} (Normalized: {radio_score_normal:.1f})")
        radio_score_label.setProperty("class", "score")
        radio_score_label.setWordWrap(True)
        layout.addWidget(radio_score_label)

        for text in [r1, r2, r3, r4]:
            label = QLabel(text)
            label.setProperty("class", "interpretation")
            label.setWordWrap(True)
            layout.addWidget(label)

        # Final Section
        final_title = QLabel("Final Classification")
        final_title.setProperty("class", "section-title")
        final_title.setWordWrap(True)
        layout.addWidget(final_title)

        final_score = QLabel(f"Total integrated score: {total_rounded}/41")
        final_score.setProperty("class", "score")
        final_score.setWordWrap(True)
        layout.addWidget(final_score)

        final_class = QLabel(classification)
        final_class.setProperty("class", "interpretation")
        final_class.setWordWrap(True)
        layout.addWidget(final_class)

        final_interp = QLabel(interpretation)
        final_interp.setProperty("class", "interpretation")
        final_interp.setWordWrap(True)
        layout.addWidget(final_interp)

        # Set the layout for the content widget
        content_widget.setLayout(layout)
        scroll_area.setWidget(content_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
        self.setMinimumWidth(1000)
        self.setMinimumHeight(800)

# ───── EXECUTION ─────
def main():
    app = QApplication(sys.argv)
    window = WelcomeWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()


