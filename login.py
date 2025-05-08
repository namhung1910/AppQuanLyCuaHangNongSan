# login.py
from PyQt5 import QtWidgets, QtCore
from db_connector import DBConnector
from register import RegistrationDialog

class LoginDialog(QtWidgets.QDialog):
    def __init__(self, db_connector, parent=None):
        super(LoginDialog, self).__init__(parent)
        self.setWindowTitle("Đăng nhập")
        self.resize(1200, 700)
        self.db_connector = db_connector
        self.user = None
        self.role = None

        # Tiêu đề
        header_label = QtWidgets.QLabel("Đăng nhập")
        header_label.setAlignment(QtCore.Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin-bottom: 20px;")

        # Layout cho các trường nhập liệu sử dụng QFormLayout
        form_layout = QtWidgets.QFormLayout()
        self.email_input = QtWidgets.QLineEdit()
        self.email_input.setPlaceholderText("Email")
        form_layout.addRow("Email:", self.email_input)

        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("Mật khẩu")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        form_layout.addRow("Mật khẩu:", self.password_input)

        self.role_combo = QtWidgets.QComboBox()
        self.role_combo.addItems(["Admin", "NguoiBan", "NguoiTieuDung", "Distributor"])
        form_layout.addRow("Vai trò:", self.role_combo)

        # Layout cho các nút bấm
        button_layout = QtWidgets.QHBoxLayout()
        self.login_button = QtWidgets.QPushButton("Đăng nhập")
        self.login_button.clicked.connect(self.handle_login)
        self.register_button = QtWidgets.QPushButton("Đăng ký")
        self.register_button.clicked.connect(self.open_registration)
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.register_button)

        # Layout chính
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(20)
        main_layout.addWidget(header_label)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # Áp dụng style đơn giản và hiện đại
        self.setStyleSheet("""
            QDialog { background-color: #f0f8ff; }
            QLabel { color: #333; }
            QLineEdit, QComboBox { padding: 8px; font-size: 16px; }
            QPushButton { background-color: #4682b4; color: white; padding: 10px; border-radius: 5px; font-size: 16px; }
            QPushButton:hover { background-color: #5a9bd4; }
        """)

    def handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_combo.currentText()

        query = {"Email": email, "MatKhau": password}
        
        collection = None
        if role == "Admin":
            collection = self.db_connector.admin
        elif role == "NguoiBan":
            collection = self.db_connector.nguoi_ban
        elif role == "NguoiTieuDung":
            collection = self.db_connector.nguoi_tieu_dung
        elif role == "Distributor":
            collection = self.db_connector.distributor
        
        if collection is not None:
            user = collection.find_one(query)
            if user is not None:
                self.user = user
                self.role = role
                QtWidgets.QMessageBox.information(self, "Thành công", f"Đăng nhập {role} thành công!")
                self.accept()
                return
        QtWidgets.QMessageBox.warning(self, "Lỗi", "Sai thông tin đăng nhập!")

    def open_registration(self):
        reg_dialog = RegistrationDialog(self.db_connector, self)
        reg_dialog.exec_()
