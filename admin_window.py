from PyQt5 import QtWidgets, QtGui, QtCore
from db_connector import DBConnector
import base64
from functools import partial

# Dialog sửa thông tin người dùng (không thay đổi)
class EditUserDialog(QtWidgets.QDialog):
    def __init__(self, parent, role, doc):
        super().__init__(parent)
        self.role = role
        self.doc = doc
        self.setWindowTitle("Sửa thông tin người dùng")
        self.initUI()
    
    def initUI(self):
        layout = QtWidgets.QFormLayout(self)
        self.fields = {}
        if self.role == "Admin":
            self.fields = {
                "MaAdmin": QtWidgets.QLineEdit(self.doc.get("MaAdmin", "")),
                "TenAdmin": QtWidgets.QLineEdit(self.doc.get("TenAdmin", "")),
                "Email": QtWidgets.QLineEdit(self.doc.get("Email", "")),
                "SDT": QtWidgets.QLineEdit(self.doc.get("SDT", ""))
            }
        elif self.role == "NguoiBan":
            self.fields = {
                "MaNguoiBan": QtWidgets.QLineEdit(self.doc.get("MaNguoiBan", "")),
                "TenNguoiBan": QtWidgets.QLineEdit(self.doc.get("TenNguoiBan", "")),
                "DiaChi": QtWidgets.QLineEdit(self.doc.get("DiaChi", "")),
                "SDT": QtWidgets.QLineEdit(self.doc.get("SDT", "")),
                "Email": QtWidgets.QLineEdit(self.doc.get("Email", ""))
            }
        elif self.role == "NguoiTieuDung":
            self.fields = {
                "MaKhachHang": QtWidgets.QLineEdit(self.doc.get("MaKhachHang", "")),
                "TenKhachHang": QtWidgets.QLineEdit(self.doc.get("TenKhachHang", "")),
                "DiaChi": QtWidgets.QLineEdit(self.doc.get("DiaChi", "")),
                "SDT": QtWidgets.QLineEdit(self.doc.get("SDT", "")),
                "Email": QtWidgets.QLineEdit(self.doc.get("Email", ""))
            }
        elif self.role == "Distributor":
            self.fields = {
                "MaDistributor": QtWidgets.QLineEdit(self.doc.get("MaDistributor", "")),
                "TenDistributor": QtWidgets.QLineEdit(self.doc.get("TenDistributor", "")),
                "DiaChi": QtWidgets.QLineEdit(self.doc.get("DiaChi", "")),
                "SDT": QtWidgets.QLineEdit(self.doc.get("SDT", "")),
                "Email": QtWidgets.QLineEdit(self.doc.get("Email", ""))
            }
        for key, widget in self.fields.items():
            if key.startswith("Ma"):
                widget.setReadOnly(True)
            layout.addRow(key, widget)
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)
    
    def getData(self):
        data = {}
        for key, widget in self.fields.items():
            data[key] = widget.text()
        return data

# Main window sử dụng card thay vì table
class AdminWindow(QtWidgets.QMainWindow):
    def __init__(self, db_connector, user, parent=None):
        super(AdminWindow, self).__init__(parent)
        self.setWindowTitle("Admin - Quản lý hệ thống")
        self.db_connector = db_connector
        self.user = user
        self.resize(1200, 700)
        
        self.tab_widget = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        self.create_user_tab()
        self.create_category_tab()
        self.create_product_tab()
        self.create_order_tab()
        
        # Style tổng thể – flat design, bo tròn nhẹ
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
                font-family: "Segoe UI", sans-serif;
            }
            QTabWidget::pane { border: none; background-color: transparent; }
            QTabBar::tab {
                background-color: transparent; padding: 10px 20px; margin-right: 2px;
                font-size: 14px; color: #555;
            }
            QTabBar::tab:selected {
                background-color: #ffffff; border-bottom: 3px solid #4682b4;
                color: #4682b4; border-top-left-radius: 8px; border-top-right-radius: 8px;
            }
            QFrame.card {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton {
                background-color: #4682b4; color: #ffffff;
                border: none; padding: 6px 12px; border-radius: 6px; font-size: 13px;
            }
            QPushButton:hover { background-color: #5a9bd4; }
        """)
        
        # Ban đầu hiển thị danh sách Admin
        self.load_user_data("Admin")
        self.load_products()
        self.load_orders()

    # --- Tính năng chuyển hướng khi nhấn nút X ---
    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(
            self,
            "Đăng xuất",
            "Bạn có chắc chắn muốn đăng xuất không?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            self.hide()  # Ẩn cửa sổ hiện tại
            from login import LoginDialog
            login_dialog = LoginDialog(self.db_connector)
            if login_dialog.exec_() == QtWidgets.QDialog.Accepted:
                role = login_dialog.role
                user = login_dialog.user
                if role == "Admin":
                    new_window = AdminWindow(self.db_connector, user)
                elif role == "NguoiBan":
                    from seller_window import SellerWindow
                    new_window = SellerWindow(self.db_connector, user)
                elif role == "NguoiTieuDung":
                    from customer_window import CustomerWindow
                    new_window = CustomerWindow(self.db_connector, user)
                elif role == "Distributor":
                    from distributor_window import DistributorWindow
                    new_window = DistributorWindow(self.db_connector, user)
                else:
                    QtWidgets.QMessageBox.critical(self, "Lỗi", "Role không xác định!")
                    event.ignore()
                    return
                new_window.show()
            event.accept()
        else:
            event.ignore()
    # --- Kết thúc tính năng chuyển hướng ---

    # ------------------ TAB NGƯỜI DÙNG ------------------
    def create_user_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # Nút chuyển đổi vai trò
        hlayout = QtWidgets.QHBoxLayout()
        self.btn_admin = QtWidgets.QPushButton("Quản lý Admin")
        self.btn_seller = QtWidgets.QPushButton("Quản lý Người bán")
        self.btn_customer = QtWidgets.QPushButton("Quản lý Khách hàng")
        self.btn_distributor = QtWidgets.QPushButton("Quản lý Distributor")
        for btn, role in [(self.btn_admin, "Admin"),
                          (self.btn_seller, "NguoiBan"),
                          (self.btn_customer, "NguoiTieuDung"),
                          (self.btn_distributor, "Distributor")]:
            btn.clicked.connect(lambda _, r=role: self.load_user_data(r))
            hlayout.addWidget(btn)
        layout.addLayout(hlayout)
        # Container dạng scroll chứa các card (sắp xếp theo chiều dọc)
        self.user_container = QtWidgets.QScrollArea()
        self.user_container.setWidgetResizable(True)
        self.user_list_widget = QtWidgets.QWidget()
        self.user_list_layout = QtWidgets.QVBoxLayout(self.user_list_widget)
        self.user_list_layout.setAlignment(QtCore.Qt.AlignTop)
        self.user_container.setWidget(self.user_list_widget)
        layout.addWidget(self.user_container)
        self.tab_widget.addTab(tab, "Người dùng")
    
    def load_user_data(self, role):
        if role == "Admin":
            coll = self.db_connector.admin
            keys = ["MaAdmin", "TenAdmin", "Email", "SDT"]
            mapping = {"MaAdmin": "Mã Admin", "TenAdmin": "Tên Admin", "Email": "Email", "SDT": "SĐT"}
        elif role == "NguoiBan":
            coll = self.db_connector.nguoi_ban
            keys = ["MaNguoiBan", "TenNguoiBan", "DiaChi", "SDT", "Email"]
            mapping = {"MaNguoiBan": "Mã Người bán", "TenNguoiBan": "Tên Người bán", "DiaChi": "Địa chỉ", "SDT": "SĐT", "Email": "Email"}
        elif role == "NguoiTieuDung":
            coll = self.db_connector.nguoi_tieu_dung
            keys = ["MaKhachHang", "TenKhachHang", "DiaChi", "SDT", "Email"]
            mapping = {"MaKhachHang": "Mã Khách hàng", "TenKhachHang": "Tên Khách hàng", "DiaChi": "Địa chỉ", "SDT": "SĐT", "Email": "Email"}
        elif role == "Distributor":
            coll = self.db_connector.distributor
            keys = ["MaDistributor", "TenDistributor", "DiaChi", "SDT", "Email"]
            mapping = {"MaDistributor": "Mã Distributor", "TenDistributor": "Tên Distributor", "DiaChi": "Địa chỉ", "SDT": "SĐT", "Email": "Email"}
        else:
            return
        
        data = list(coll.find())
        # Xóa nội dung cũ của layout
        for i in reversed(range(self.user_list_layout.count())):
            widgetToRemove = self.user_list_layout.itemAt(i).widget()
            if widgetToRemove:
                widgetToRemove.setParent(None)
        for doc in data:
            card = self.create_user_card(doc, keys, mapping, role)
            self.user_list_layout.addWidget(card)
    
    def create_user_card(self, doc, keys, mapping, role):
        card = QtWidgets.QFrame()
        card.setObjectName("card")
        card.setProperty("class", "card")
        card.setStyleSheet("QFrame.card { background-color: #ffffff; border: 1px solid #ddd; border-radius: 8px; padding: 10px; }")
        vlayout = QtWidgets.QVBoxLayout(card)
        for key in keys:
            text = f"<b>{mapping.get(key, key)}:</b> {doc.get(key, '')}"
            label = QtWidgets.QLabel(text)
            vlayout.addWidget(label)
        btn_layout = QtWidgets.QHBoxLayout()
        btn_edit = QtWidgets.QPushButton("Sửa")
        btn_edit.clicked.connect(partial(self.edit_user, doc, role))
        btn_del = QtWidgets.QPushButton("Xóa")
        btn_del.clicked.connect(partial(self.delete_user, doc, role))
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_del)
        btn_layout.addStretch()
        vlayout.addLayout(btn_layout)
        return card

    def edit_user(self, doc, role):
        dialog = EditUserDialog(self, role, doc)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            new_data = dialog.getData()
            if role == "Admin":
                coll = self.db_connector.admin
                id_field = "MaAdmin"
            elif role == "NguoiBan":
                coll = self.db_connector.nguoi_ban
                id_field = "MaNguoiBan"
            elif role == "NguoiTieuDung":
                coll = self.db_connector.nguoi_tieu_dung
                id_field = "MaKhachHang"
            elif role == "Distributor":
                coll = self.db_connector.distributor
                id_field = "MaDistributor"
            coll.update_one({id_field: doc.get(id_field)}, {"$set": new_data})
            QtWidgets.QMessageBox.information(self, "Sửa", "Cập nhật thông tin thành công.")
            self.load_user_data(role)
    
    def delete_user(self, doc, role):
        confirm = QtWidgets.QMessageBox.question(self, "Xác nhận", "Bạn có muốn xóa user này?")
        if confirm == QtWidgets.QMessageBox.Yes:
            if role == "Admin":
                coll = self.db_connector.admin
                id_field = "MaAdmin"
            elif role == "NguoiBan":
                coll = self.db_connector.nguoi_ban
                id_field = "MaNguoiBan"
            elif role == "NguoiTieuDung":
                coll = self.db_connector.nguoi_tieu_dung
                id_field = "MaKhachHang"
            elif role == "Distributor":
                coll = self.db_connector.distributor
                id_field = "MaDistributor"
            coll.delete_one({id_field: doc.get(id_field)})
            QtWidgets.QMessageBox.information(self, "Xóa", "User đã được xóa.")
            self.load_user_data(role)
    
    # ------------------ TAB DANH MỤC ------------------
    def create_category_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        btn_add = QtWidgets.QPushButton("Thêm danh mục nông sản")
        btn_add.clicked.connect(self.add_category)
        layout.addWidget(btn_add)
        # Sử dụng QScrollArea chứa container với QGridLayout (3 thẻ/row)
        self.category_container = QtWidgets.QScrollArea()
        self.category_container.setWidgetResizable(True)
        self.category_list_widget = QtWidgets.QWidget()
        self.category_list_layout = QtWidgets.QGridLayout(self.category_list_widget)
        self.category_list_layout.setAlignment(QtCore.Qt.AlignTop)
        self.category_container.setWidget(self.category_list_widget)
        layout.addWidget(self.category_container)
        self.tab_widget.addTab(tab, "Danh mục")
        self.load_categories()
    
    def add_category(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Thêm danh mục", "Nhập tên danh mục:")
        if ok and name:
            desc, _ = QtWidgets.QInputDialog.getText(self, "Mô tả", "Nhập mô tả:")
            doc = {"MaDanhMuc": name.upper(), "TenDanhMuc": name, "MoTa": desc}
            self.db_connector.danh_muc_nong_san.insert_one(doc)
            self.load_categories()
    
    def load_categories(self):
        cats = list(self.db_connector.danh_muc_nong_san.find())
        # Xóa nội dung cũ của grid layout
        for i in reversed(range(self.category_list_layout.count())):
            widgetToRemove = self.category_list_layout.itemAt(i).widget()
            if widgetToRemove:
                widgetToRemove.setParent(None)
        # Thêm card vào grid layout (3 card/row)
        for index, cat in enumerate(cats):
            card = self.create_category_card(cat)
            row = index // 3
            col = index % 3
            self.category_list_layout.addWidget(card, row, col)
    
    def create_category_card(self, cat):
        card = QtWidgets.QFrame()
        card.setObjectName("card")
        card.setProperty("class", "card")
        card.setStyleSheet("QFrame.card { background-color: #ffffff; border: 1px solid #ddd; border-radius: 8px; padding: 10px; }")
        vlayout = QtWidgets.QVBoxLayout(card)
        label1 = QtWidgets.QLabel(f"<b>Mã danh mục:</b> {cat.get('MaDanhMuc', '')}")
        label2 = QtWidgets.QLabel(f"<b>Tên danh mục:</b> {cat.get('TenDanhMuc', '')}")
        label3 = QtWidgets.QLabel(f"<b>Mô tả:</b> {cat.get('MoTa', '')}")
        count = self.db_connector.nong_san.count_documents({"MaDanhMuc": cat.get("MaDanhMuc", "")})
        label4 = QtWidgets.QLabel(f"<b>Sản phẩm:</b> {count}")
        vlayout.addWidget(label1)
        vlayout.addWidget(label2)
        vlayout.addWidget(label3)
        vlayout.addWidget(label4)
        return card

    # ------------------ TAB SẢN PHẨM ------------------
    def create_product_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        self.product_container = QtWidgets.QScrollArea()
        self.product_container.setWidgetResizable(True)
        self.product_list_widget = QtWidgets.QWidget()
        self.product_list_layout = QtWidgets.QGridLayout(self.product_list_widget)
        self.product_list_layout.setAlignment(QtCore.Qt.AlignTop)
        self.product_container.setWidget(self.product_list_widget)
        layout.addWidget(self.product_container)
        self.tab_widget.addTab(tab, "Sản phẩm")
        self.load_products()
    
    def load_products(self):
        products = list(self.db_connector.nong_san.find())
        for i in reversed(range(self.product_list_layout.count())):
            widgetToRemove = self.product_list_layout.itemAt(i).widget()
            if widgetToRemove:
                widgetToRemove.setParent(None)
        for index, prod in enumerate(products):
            card = self.create_product_card(prod)
            row = index // 3
            col = index % 3
            self.product_list_layout.addWidget(card, row, col)
    
    def create_product_card(self, prod):
        card = QtWidgets.QFrame()
        card.setObjectName("card")
        card.setProperty("class", "card")
        card.setStyleSheet("QFrame.card { background-color: #ffffff; border: 1px solid #ddd; border-radius: 8px; padding: 10px; }")
        hlayout = QtWidgets.QHBoxLayout(card)
        lbl_img = QtWidgets.QLabel()
        lbl_img.setFixedSize(150, 150)
        b64 = prod.get("HinhAnh", "")
        if b64:
            try:
                img_data = base64.b64decode(b64)
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(img_data)
                lbl_img.setPixmap(pixmap.scaled(150, 150, QtCore.Qt.KeepAspectRatio))
            except Exception as e:
                lbl_img.setText("Lỗi ảnh")
        else:
            lbl_img.setText("Không có ảnh")
        hlayout.addWidget(lbl_img)
        vlayout = QtWidgets.QVBoxLayout()
        info_lines = [
            f"<b>Mã nông sản:</b> {prod.get('MaNongSan', '')}",
            f"<b>Tên:</b> {prod.get('TenNongSan', '')}",
            f"<b>Danh mục:</b> {prod.get('MaDanhMuc', '')}",
            f"<b>Giá:</b> {prod.get('Gia', '')}",
            f"<b>Số lượng:</b> {prod.get('SoLuong', '')}",
            f"<b>Chất lượng:</b> {prod.get('ChatLuong', '')}",
            f"<b>Mô tả:</b> {prod.get('MoTa', '')}"
        ]
        for line in info_lines:
            lbl = QtWidgets.QLabel(line)
            lbl.setWordWrap(True)
            vlayout.addWidget(lbl)
        hlayout.addLayout(vlayout)
        return card

    # ------------------ TAB ĐƠN HÀNG ------------------
    def create_order_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        self.order_container = QtWidgets.QScrollArea()
        self.order_container.setWidgetResizable(True)
        self.order_list_widget = QtWidgets.QWidget()
        self.order_list_layout = QtWidgets.QGridLayout(self.order_list_widget)
        self.order_list_layout.setAlignment(QtCore.Qt.AlignTop)
        self.order_container.setWidget(self.order_list_widget)
        layout.addWidget(self.order_container)
        self.tab_widget.addTab(tab, "Đơn hàng")
        self.load_orders()
    
    def load_orders(self):
        orders = list(self.db_connector.don_hang.find())
        for i in reversed(range(self.order_list_layout.count())):
            widgetToRemove = self.order_list_layout.itemAt(i).widget()
            if widgetToRemove:
                widgetToRemove.setParent(None)
        for index, order in enumerate(orders):
            card = self.create_order_card(order)
            row = index // 3
            col = index % 3
            self.order_list_layout.addWidget(card, row, col)
    
    def create_order_card(self, order):
        card = QtWidgets.QFrame()
        card.setObjectName("card")
        card.setProperty("class", "card")
        card.setStyleSheet("QFrame.card { background-color: #ffffff; border: 1px solid #ddd; border-radius: 8px; padding: 10px; }")
        vlayout = QtWidgets.QVBoxLayout(card)
        maDonHang = order.get("MaDonHang", "")
        ngay = order.get("NgayDatHang")
        ngay_str = ngay.strftime("%Y-%m-%d %H:%M:%S") if ngay else ""
        tongTien = order.get("TongTien", "")
        trangThai = order.get("TrangThai", "")
        pttt = order.get("PhuongThucThanhToan", "")
        maKH = order.get("MaKhachHang", "")
        kh = self.db_connector.nguoi_tieu_dung.find_one({"MaKhachHang": maKH})
        tenKH = kh.get("TenKhachHang", "") if kh else ""
        details = list(self.db_connector.chi_tiet_don_hang.find({"MaDonHang": maDonHang}))
        sellerNames = set()
        for d in details:
            prod = self.db_connector.nong_san.find_one({"MaNongSan": d.get("MaNongSan")})
            if prod:
                nvb = self.db_connector.nguoi_ban.find_one({"MaNguoiBan": prod.get("MaNguoiBan", "")})
                if nvb:
                    sellerNames.add(nvb.get("TenNguoiBan", ""))
        tenNVB = ", ".join(sellerNames)
        vc = self.db_connector.van_chuyen_phan_phoi.find_one({"MaDonHang": maDonHang})
        distributorName = ""
        if vc:
            dstr = self.db_connector.distributor.find_one({"MaDistributor": vc.get("MaDistributor", "")})
            distributorName = dstr.get("TenDistributor", "") if dstr else ""
        
        info_lines = [
            f"<b>Mã đơn hàng:</b> {maDonHang}",
            f"<b>Ngày đặt:</b> {ngay_str}",
            f"<b>Tổng tiền:</b> {tongTien}",
            f"<b>Trạng thái:</b> {trangThai}",
            f"<b>PTTT:</b> {pttt}",
            f"<b>Mã KH:</b> {maKH}",
            f"<b>Tên KH:</b> {tenKH}",
            f"<b>Tên NVB:</b> {tenNVB}",
            f"<b>Distributor:</b> {distributorName}"
        ]
        for line in info_lines:
            lbl = QtWidgets.QLabel(line)
            lbl.setWordWrap(True)
            vlayout.addWidget(lbl)
        return card

if __name__ == "__main__":
    import sys
    # Giả sử DBConnector được cấu hình đúng
    db_connector = DBConnector()
    app = QtWidgets.QApplication(sys.argv)
    window = AdminWindow(db_connector, user="admin")
    window.show()
    sys.exit(app.exec_())
