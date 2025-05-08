# register.py
import uuid
from PyQt5 import QtWidgets, QtCore
from db_connector import DBConnector

class RegistrationDialog(QtWidgets.QDialog):
    def __init__(self, db_connector, parent=None):
        super(RegistrationDialog, self).__init__(parent)
        self.setWindowTitle("Đăng ký tài khoản")
        self.resize(1200, 700)
        self.db_connector = db_connector

        # Tiêu đề dialog
        header_label = QtWidgets.QLabel("Đăng ký tài khoản")
        header_label.setAlignment(QtCore.Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin-bottom: 20px;")

        # Thành phần nhập liệu
        self.role_combo = QtWidgets.QComboBox()
        self.role_combo.addItems(["Admin", "NguoiBan", "NguoiTieuDung", "Distributor"])
        self.role_combo.currentIndexChanged.connect(self.update_form_fields)

        self.name_input = QtWidgets.QLineEdit()
        self.address_input = QtWidgets.QLineEdit()
        self.phone_input = QtWidgets.QLineEdit()
        self.email_input = QtWidgets.QLineEdit()
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.name_label = QtWidgets.QLabel("Tên:")

        # Nút đăng ký
        self.register_button = QtWidgets.QPushButton("Đăng ký")
        self.register_button.clicked.connect(self.register_account)

        # Layout form sử dụng QFormLayout cho việc căn chỉnh nhãn và trường nhập liệu
        form_layout = QtWidgets.QFormLayout()
        form_layout.setLabelAlignment(QtCore.Qt.AlignRight)
        form_layout.setHorizontalSpacing(20)
        form_layout.setVerticalSpacing(15)
        form_layout.addRow("Role:", self.role_combo)
        form_layout.addRow(self.name_label, self.name_input)
        form_layout.addRow("Địa chỉ:", self.address_input)
        form_layout.addRow("Số điện thoại:", self.phone_input)
        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("Mật khẩu:", self.password_input)

        # Layout cho nút đăng ký, căn giữa
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.register_button)
        button_layout.addStretch()

        # Layout chính
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(20)
        main_layout.addWidget(header_label)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # Cập nhật label dựa theo role chọn
        self.update_form_fields()

        # Áp dụng style cho giao diện
        self.setStyleSheet("""
            QDialog { background-color: #f0f8ff; }
            QLabel { color: #333; font-size: 16px; }
            QLineEdit, QComboBox { padding: 8px; font-size: 16px; }
            QPushButton { background-color: #4682b4; color: white; padding: 10px; border-radius: 5px; font-size: 16px; }
            QPushButton:hover { background-color: #5a9bd4; }
        """)

    def update_form_fields(self):
        role = self.role_combo.currentText()
        if role == "Admin":
            self.name_label.setText("Tên Admin:")
        elif role == "NguoiBan":
            self.name_label.setText("Tên Người bán:")
        elif role == "NguoiTieuDung":
            self.name_label.setText("Tên Khách hàng:")
        elif role == "Distributor":
            self.name_label.setText("Tên Distributor:")

    def register_account(self):
        role = self.role_combo.currentText()
        name = self.name_input.text().strip()
        address = self.address_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()

        if not all([name, address, phone, email, password]):
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng điền đầy đủ thông tin!")
            return

        id_value = str(uuid.uuid4())
        doc = {}

        if role == "Admin":
            doc = {
                "MaAdmin": id_value,
                "TenAdmin": name,
                "Email": email,
                "MatKhau": password,
                "SoDienThoai": phone
            }
            collection = self.db_connector.admin
        elif role == "NguoiBan":
            doc = {
                "MaNguoiBan": id_value,
                "TenNguoiBan": name,
                "DiaChi": address,
                "SoDienThoai": phone,
                "Email": email,
                "MatKhau": password,
                "HinhAnhGianHang": ""
            }
            collection = self.db_connector.nguoi_ban
        elif role == "NguoiTieuDung":
            doc = {
                "MaKhachHang": id_value,
                "TenKhachHang": name,
                "DiaChi": address,
                "SoDienThoai": phone,
                "Email": email,
                "MatKhau": password
            }
            collection = self.db_connector.nguoi_tieu_dung
        elif role == "Distributor":
            doc = {
                "MaDistributor": id_value,
                "TenDistributor": name,
                "DiaChi": address,
                "SoDienThoai": phone,
                "Email": email,
                "MatKhau": password
            }
            collection = self.db_connector.distributor
        else:
            QtWidgets.QMessageBox.critical(self, "Lỗi", "Role không hợp lệ!")
            return

        # Kiểm tra email đã tồn tại hay chưa
        if collection.find_one({"Email": email}):
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Email đã tồn tại!")
            return

        result = collection.insert_one(doc)
        if result.inserted_id:
            QtWidgets.QMessageBox.information(self, "Thành công", "Đăng ký thành công!")
            self.accept()
        else:
            QtWidgets.QMessageBox.critical(self, "Lỗi", "Đăng ký thất bại!")
