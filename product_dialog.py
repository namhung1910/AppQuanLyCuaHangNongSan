# product_dialog.py
import os
import base64
from PyQt5 import QtWidgets, QtGui, QtCore

class ProductDialogSeller(QtWidgets.QDialog):
    def __init__(self, db_connector, ma_nguoi_ban, product=None, parent=None):
        super(ProductDialogSeller, self).__init__(parent)
        self.setWindowTitle("Thêm/Sửa Sản phẩm")
        self.db_connector = db_connector
        self.ma_nguoi_ban = ma_nguoi_ban
        self.product = product
        
        form = QtWidgets.QFormLayout()
        self.txt_ma = QtWidgets.QLineEdit()
        self.txt_ten = QtWidgets.QLineEdit()
        # Thay đổi: dùng QComboBox cho Danh mục từ DB
        self.cmb_dm = QtWidgets.QComboBox()
        self.load_categories()
        
        self.txt_gia = QtWidgets.QLineEdit()
        self.txt_sl = QtWidgets.QLineEdit()
        self.txt_chat = QtWidgets.QLineEdit()
        self.txt_mota = QtWidgets.QLineEdit()
        self.txt_hinhanh = QtWidgets.QLineEdit()
        btn_browse = QtWidgets.QPushButton("Chọn ảnh")
        btn_browse.clicked.connect(self.browse_image)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.txt_hinhanh)
        hlayout.addWidget(btn_browse)
        
        form.addRow("Mã nông sản:", self.txt_ma)
        form.addRow("Tên nông sản:", self.txt_ten)
        form.addRow("Danh mục:", self.cmb_dm)
        form.addRow("Giá:", self.txt_gia)
        form.addRow("Số lượng:", self.txt_sl)
        form.addRow("Chất lượng:", self.txt_chat)
        form.addRow("Mô tả:", self.txt_mota)
        form.addRow("Ảnh sản phẩm:", hlayout)
        
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        form.addRow(btn_box)
        self.setLayout(form)
        
        if product:
            self.txt_ma.setText(product.get("MaNongSan", ""))
            self.txt_ten.setText(product.get("TenNongSan", ""))
            index = self.cmb_dm.findData(product.get("MaDanhMuc", ""))
            if index >= 0:
                self.cmb_dm.setCurrentIndex(index)
            self.txt_gia.setText(str(product.get("Gia", "")))
            self.txt_sl.setText(str(product.get("SoLuong", "")))
            self.txt_chat.setText(product.get("ChatLuong", ""))
            self.txt_mota.setText(product.get("MoTa", ""))
            self.txt_hinhanh.setText(product.get("HinhAnh", ""))
            self.txt_ma.setDisabled(True)
    
    def load_categories(self):
        self.cmb_dm.clear()
        cats = list(self.db_connector.danh_muc_nong_san.find())
        for c in cats:
            self.cmb_dm.addItem(c.get("TenDanhMuc", ""), c.get("MaDanhMuc", ""))
    
    def browse_image(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Chọn ảnh sản phẩm", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.txt_hinhanh.setText(path)
    
    def accept(self):
        img_str = ""
        path = self.txt_hinhanh.text().strip()
        try:
            if path and os.path.exists(path):
                with open(path, "rb") as f:
                    img_bytes = f.read()
                    img_str = base64.b64encode(img_bytes).decode("utf-8")
            else:
                img_str = self.txt_hinhanh.text().strip()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Không thể đọc ảnh: {e}")
            return
        
        try:
            data = {
                "MaNongSan": self.txt_ma.text().strip(),
                "TenNongSan": self.txt_ten.text().strip(),
                "MaDanhMuc": self.cmb_dm.currentData(),
                "MaNguoiBan": self.ma_nguoi_ban,
                "Gia": float(self.txt_gia.text().strip()),
                "SoLuong": int(self.txt_sl.text().strip()),
                "ChatLuong": self.txt_chat.text().strip(),
                "MoTa": self.txt_mota.text().strip(),
                "HinhAnh": img_str
            }
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi nhập liệu: {e}")
            return
        
        if self.product:
            self.db_connector.nong_san.update_one({"MaNongSan": self.product["MaNongSan"]}, {"$set": data})
        else:
            self.db_connector.nong_san.insert_one(data)
        super(ProductDialogSeller, self).accept()
