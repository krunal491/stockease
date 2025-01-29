from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel,
    QMessageBox, QGraphicsOpacityEffect, QFrame
)
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt, QPropertyAnimation, QFile, QTextStream

from database import authenticate_user, register_user
from main import MainWindow
import sys

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login-page")

        self.is_signup_mode = False  

        screen_geometry = QApplication.primaryScreen().geometry()
        self.resize(screen_geometry.width(), screen_geometry.height())

        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)

        self.opacity_effect = QGraphicsOpacityEffect()
        self.opacity_effect.setOpacity(0.27)
        self.bg_label.setGraphicsEffect(self.opacity_effect)

        self.frame_bg = QLabel(self)
        self.frame_bg.setStyleSheet("background-color: rgba(200,200,200, 0.29); border-radius: 15px;")
        self.frame_bg.setGeometry(300, 150, 750, 450)

        self.frame = QFrame(self)
        self.frame.setGeometry(0, 0, 400, 400)
        self.frame.setStyleSheet("border-radius: 15px;")

        self.layout = QVBoxLayout(self.frame)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel("Optimize Your Stock with Ease")
        self.title_label.setFont(QFont("Poppins", 32, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: rgb(36,36,36); text-align: center; padding: 15px;")
        self.layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        input_style = """
            QLineEdit {
                padding: 10px;
                min-width: 250px;
                border: 2px solid #4C566A;
                border-radius: 8px;
                font-size: 16px;
                color: rgb(255, 255, 255);
                background-color: rgb(36, 36, 36);
            }
            QLineEdit:focus {
                border: 2px solid #5E81AC;
                background-color: rgb(36, 36, 36);
            }
        """

        self.email_input = QLineEdit(self)
        self.email_input.setPlaceholderText("Email")
        self.email_input.setStyleSheet(input_style)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(input_style)

        self.mobile_input = QLineEdit(self)
        self.mobile_input.setPlaceholderText("Mobile Number")
        self.mobile_input.setStyleSheet(input_style)
        self.mobile_input.setVisible(False)  

        button_style = """
            QPushButton {
                background-color:rgb(41, 88, 146);
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
                color: white;
                min-width: 140px;
            }
            QPushButton:hover {
                background-color:rgb(93, 136, 179);
            }
            QPushButton:pressed {
                background-color: #BF616A;
            }
        """

        self.login_button = QPushButton("Login")
        self.signup_button = QPushButton("Sign Up")
        self.login_button.setStyleSheet(button_style)
        self.signup_button.setStyleSheet(button_style)

        self.login_button.clicked.connect(self.login)
        self.signup_button.clicked.connect(self.handle_signup_click)

        self.layout.addWidget(self.email_input, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.password_input, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.mobile_input, alignment=Qt.AlignmentFlag.AlignCenter)  # added but hidden initially
        self.layout.addSpacing(4)
        self.layout.addWidget(self.login_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.signup_button, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.frame, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(main_layout)

        self.bg_label.lower()
        self.frame_bg.lower()
        self.frame.raise_()
        self.update_background()
        self.start_text_animation()

    def update_background(self):
        pixmap = QPixmap("backg.png")
        if not pixmap.isNull():
            self.bg_label.setPixmap(
                pixmap.scaled(
                    self.size(),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
            self.bg_label.setGeometry(0, 0, self.width(), self.height())

    def resizeEvent(self, event):
        if hasattr(self, "bg_label"):
            self.update_background()
        super().resizeEvent(event)

    def start_text_animation(self):
        opacity_effect = QGraphicsOpacityEffect()
        self.title_label.setGraphicsEffect(opacity_effect)
        self.animation = QPropertyAnimation(opacity_effect, b"opacity")
        self.animation.setDuration(1200)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()

    def login(self):
        email = self.email_input.text()
        password = self.password_input.text()
        user, requires_otp = authenticate_user(email, password)
        if user:
            self.open_dashboard()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid email or password.")

    def handle_signup_click(self):
        if not self.is_signup_mode:
            self.is_signup_mode = True
            self.mobile_input.setVisible(True)
            self.signup_button.setText("Submit")
        else:
            self.signup()  

    def signup(self):
        email = self.email_input.text()
        password = self.password_input.text()
        mobile = self.mobile_input.text()

        if not mobile.strip():
            QMessageBox.warning(self, "Missing Info", "Please enter your mobile number.")
            return

        if register_user(email, password, mobile=mobile):
            QMessageBox.information(self, "Sign Up Success", "Account created successfully!")
            self.is_signup_mode = False
            self.mobile_input.setVisible(False)
            self.signup_button.setText("Sign Up")
        else:
            QMessageBox.warning(self, "Sign Up Failed", "Email already exists!")

    def open_dashboard(self):
        qss_file = QFile("style.qss")
        if qss_file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            stream = QTextStream(qss_file)
            style_sheet = stream.readAll()
            qss_file.close()
        else:
            style_sheet = ""

        self.dashboard = MainWindow()
        self.dashboard.setStyleSheet(style_sheet)
        self.dashboard.showMaximized()
        self.close()


if __name__ == "__main__":
    app = QApplication([])
    window = LoginWindow()
    window.show()
    app.exec()



