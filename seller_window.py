from PyQt5 import QtWidgets, QtGui, QtCore
import os, base64
from db_connector import DBConnector
from product_dialog import ProductDialogSeller
from login import LoginDialog  # Import LoginDialog để mở lại màn hình đăng nhập

def add_shadow(widget):
    """Áp dụng hiệu ứng đổ bóng cho widget (giúp card nổi bật hơn)"""
    shadow = QtWidgets.QGraphicsDropShadowEffect()
    shadow.setBlurRadius(15)
    shadow.setXOffset(3)
    shadow.setYOffset(3)
    shadow.setColor(QtGui.QColor(0, 0, 0, 80))
    widget.setGraphicsEffect(shadow)

# ==================== Cửa sổ Người bán ====================
class SellerWindow(QtWidgets.QMainWindow):
    def __init__(self, db_connector, user, parent=None):
        super(SellerWindow, self).__init__(parent)
        self.setWindowTitle("Người bán - Quản lý gian hàng và sản phẩm")
        self.db_connector = db_connector
        self.user = user
        self.resize(1200, 750)
        
        self.tab_widget = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # Tạo các tab với giao diện cải tiến
        self.create_product_tab()
        self.create_order_tab()
        self.create_review_tab()  # Giao diện chat giữa shop và khách hàng
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                                  stop:0 #fffde7, stop:1 #ffd54f);
            }
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                                  stop:0 #ffb74d, stop:1 #ff8f00);
                color: white;
                padding: 8px;
                border: none;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                                  stop:0 #ffcc80, stop:1 #ffb74d);
            }
            QLineEdit, QComboBox {
                padding: 6px;
                font-size: 13px;
            }
            QLabel {
                font-size: 13px;
            }
        """)

    # Override hàm closeEvent để chuyển hướng về màn hình đăng nhập
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
            login_dialog = LoginDialog(self.db_connector)
            if login_dialog.exec_() == QtWidgets.QDialog.Accepted:
                role = login_dialog.role
                user = login_dialog.user
                # Mở cửa sổ mới dựa theo vai trò đăng nhập
                if role == "NguoiBan":
                    new_window = SellerWindow(self.db_connector, user)
                elif role == "Admin":
                    from admin_window import AdminWindow
                    new_window = AdminWindow(self.db_connector, user)
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
            event.accept()  # Chấp nhận việc đóng cửa sổ hiện tại
        else:
            event.ignore()  # Hủy việc đóng cửa sổ nếu không đồng ý

    # --------- Tab Sản phẩm ---------
    def create_product_tab(self):
        self.product_tab = ProductTabSeller(self.db_connector, self.user, self)
        self.tab_widget.addTab(self.product_tab, "Sản phẩm")
    
    # --------- Tab Đơn hàng ---------
    def create_order_tab(self):
        self.order_tab = OrderTabSeller(self.db_connector, self.user, self)
        self.tab_widget.addTab(self.order_tab, "Đơn hàng")
    
    # --------- Tab Chat với KH ---------
    def create_review_tab(self):
        self.chat_tab = ChatTabSeller(self.db_connector, self.user, self)
        self.tab_widget.addTab(self.chat_tab, "Chat với KH")

# ==================== Các class Tab và Card như cũ ====================
class ProductTabSeller(QtWidgets.QWidget):
    def __init__(self, db_connector, user, main_window, parent=None):
        super(ProductTabSeller, self).__init__(parent)
        self.db_connector = db_connector
        self.user = user
        self.main_window = main_window
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Thanh công cụ: nút Thêm sản phẩm
        tool_layout = QtWidgets.QHBoxLayout()
        btn_add = QtWidgets.QPushButton("Thêm sản phẩm")
        btn_add.clicked.connect(self.add_product)
        tool_layout.addWidget(btn_add)
        tool_layout.addStretch()
        main_layout.addLayout(tool_layout)
        
        # Scroll area chứa các card sản phẩm
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        main_layout.addWidget(self.scroll_area)
        
        self.content_widget = QtWidgets.QWidget()
        self.grid_layout = QtWidgets.QGridLayout(self.content_widget)
        self.grid_layout.setSpacing(20)
        self.scroll_area.setWidget(self.content_widget)
        
        self.load_products()
    
    def load_products(self):
        products = list(self.db_connector.nong_san.find({"MaNguoiBan": self.user["MaNguoiBan"]}))
        # Xóa hết card cũ
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        cols = 3
        for idx, prod in enumerate(products):
            row = idx // cols
            col = idx % cols
            card = ProductCardSeller(prod, self.edit_product, self.delete_product)
            self.grid_layout.addWidget(card, row, col)
    
    def add_product(self):
        dialog = ProductDialogSeller(self.db_connector, self.user["MaNguoiBan"])
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.load_products()
    
    def edit_product(self, prod):
        dialog = ProductDialogSeller(self.db_connector, self.user["MaNguoiBan"], prod)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.load_products()
    
    def delete_product(self, prod):
        confirm = QtWidgets.QMessageBox.question(self, "Xác nhận", "Bạn có muốn xóa sản phẩm này?")
        if confirm == QtWidgets.QMessageBox.Yes:
            self.db_connector.nong_san.delete_one({"MaNongSan": prod.get("MaNongSan", "")})
            self.load_products()

class ProductCardSeller(QtWidgets.QFrame):
    def __init__(self, prod, edit_callback, delete_callback, parent=None):
        super(ProductCardSeller, self).__init__(parent)
        self.prod = prod
        self.edit_callback = edit_callback
        self.delete_callback = delete_callback
        self.setFixedSize(350, 380)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 10px;
            }
            QLabel {
                color: #424242;
            }
        """)
        add_shadow(self)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Ảnh sản phẩm
        self.image_label = QtWidgets.QLabel()
        self.image_label.setFixedSize(320, 180)
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        b64 = prod.get("HinhAnh", "")
        if b64:
            try:
                img_data = base64.b64decode(b64)
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(img_data)
                self.image_label.setPixmap(pixmap.scaled(320, 180, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
            except:
                self.image_label.setText("Lỗi ảnh")
        else:
            self.image_label.setText("Không có ảnh")
        layout.addWidget(self.image_label)
        
        # Thông tin sản phẩm
        name = prod.get("TenNongSan", "Sản phẩm")
        self.name_label = QtWidgets.QLabel(name)
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)
        
        # Thông tin cơ bản
        info = f"Danh mục: {prod.get('MaDanhMuc', '')}\nGiá: {prod.get('Gia', 0)}\nSL: {prod.get('SoLuong', 0)}\nChất lượng: {prod.get('ChatLuong', '')}"
        self.info_label = QtWidgets.QLabel(info)
        self.info_label.setAlignment(QtCore.Qt.AlignLeft)
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        # Mô tả sản phẩm
        mota = prod.get("MoTa", "")
        if len(mota) > 60:
            mota = mota[:60] + "..."
        self.mota_label = QtWidgets.QLabel(f"Mô tả: {mota}")
        self.mota_label.setAlignment(QtCore.Qt.AlignLeft)
        self.mota_label.setWordWrap(True)
        layout.addWidget(self.mota_label)
        
        # Nút Sửa và Xóa
        btn_layout = QtWidgets.QHBoxLayout()
        btn_edit = QtWidgets.QPushButton("Sửa")
        btn_edit.clicked.connect(lambda: self.edit_callback(self.prod))
        btn_delete = QtWidgets.QPushButton("Xóa")
        btn_delete.clicked.connect(lambda: self.delete_callback(self.prod))
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
        layout.addLayout(btn_layout)

class OrderTabSeller(QtWidgets.QWidget):
    def __init__(self, db_connector, user, main_window, parent=None):
        super(OrderTabSeller, self).__init__(parent)
        self.db_connector = db_connector
        self.user = user
        self.main_window = main_window
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Scroll area chứa các card đơn hàng
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        main_layout.addWidget(self.scroll_area)
        
        self.content_widget = QtWidgets.QWidget()
        self.vbox = QtWidgets.QVBoxLayout(self.content_widget)
        self.vbox.setSpacing(15)
        self.scroll_area.setWidget(self.content_widget)
        
        self.load_orders()
    
    def load_orders(self):
        products = list(self.db_connector.nong_san.find({"MaNguoiBan": self.user["MaNguoiBan"]}))
        ids = [p["MaNongSan"] for p in products]
        details = list(self.db_connector.chi_tiet_don_hang.find({"MaNongSan": {"$in": ids}}))
        
        for i in reversed(range(self.vbox.count())):
            widget = self.vbox.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        for d in details:
            card = OrderDetailCardSeller(d, self.db_connector)
            self.vbox.addWidget(card)
        self.vbox.addStretch()

class OrderDetailCardSeller(QtWidgets.QFrame):
    def __init__(self, order_detail, db_connector, parent=None):
        super(OrderDetailCardSeller, self).__init__(parent)
        self.order_detail = order_detail
        self.db_connector = db_connector
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        add_shadow(self)
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(20)
        
        # Ảnh sản phẩm
        self.image_label = QtWidgets.QLabel()
        self.image_label.setFixedSize(110, 110)
        prod = self.db_connector.nong_san.find_one({"MaNongSan": order_detail.get("MaNongSan", "")})
        if prod and prod.get("HinhAnh", ""):
            try:
                img_data = base64.b64decode(prod.get("HinhAnh", ""))
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(img_data)
                self.image_label.setPixmap(pixmap.scaled(110, 110, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
            except:
                self.image_label.setText("Lỗi ảnh")
        else:
            self.image_label.setText("Không có ảnh")
        layout.addWidget(self.image_label)
        
        # Thông tin đơn hàng
        info_layout = QtWidgets.QVBoxLayout()
        ten_sp = prod.get("TenNongSan", "") if prod else ""
        lbl_sp = QtWidgets.QLabel(f"Sản phẩm: {ten_sp}")
        lbl_sl = QtWidgets.QLabel(f"Số lượng: {order_detail.get('SoLuong', '')}")
        lbl_dg = QtWidgets.QLabel(f"Đơn giá: {order_detail.get('DonGia', '')}")
        don = self.db_connector.don_hang.find_one({"MaDonHang": order_detail.get("MaDonHang", "")})
        makh = don.get("MaKhachHang", "") if don else ""
        lbl_makh = QtWidgets.QLabel(f"Mã KH: {makh}")
        kh = self.db_connector.nguoi_tieu_dung.find_one({"MaKhachHang": makh})
        tenkh = kh.get("TenKhachHang", "") if kh else ""
        lbl_tenkh = QtWidgets.QLabel(f"Tên KH: {tenkh}")
        info_layout.addWidget(lbl_sp)
        info_layout.addWidget(lbl_sl)
        info_layout.addWidget(lbl_dg)
        info_layout.addWidget(lbl_makh)
        info_layout.addWidget(lbl_tenkh)
        layout.addLayout(info_layout)

class ChatTabSeller(QtWidgets.QWidget):
    def __init__(self, db_connector, user, main_window, parent=None):
        super(ChatTabSeller, self).__init__(parent)
        self.db_connector = db_connector
        self.user = user
        self.main_window = main_window
        
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Danh sách khách hàng
        self.customer_list = QtWidgets.QListWidget()
        self.customer_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #ffe082;
            }
        """)
        self.customer_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.customer_list.itemClicked.connect(self.load_chat_history)
        main_layout.addWidget(self.customer_list, 1)
        
        # Khu vực chat
        chat_layout = QtWidgets.QVBoxLayout()
        self.chat_history = QtWidgets.QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        chat_layout.addWidget(self.chat_history)
        input_layout = QtWidgets.QHBoxLayout()
        self.chat_input = QtWidgets.QLineEdit()
        self.chat_input.setPlaceholderText("Nhập tin nhắn...")
        btn_send = QtWidgets.QPushButton("Gửi")
        btn_send.clicked.connect(self.send_chat)
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(btn_send)
        chat_layout.addLayout(input_layout)
        main_layout.addLayout(chat_layout, 2)
        
        self.load_customers_for_chat()
        current_item = self.customer_list.currentItem()
        if current_item:
            self.load_chat_history(current_item)
    
    def load_customers_for_chat(self):
        chats = list(self.db_connector.chat_shop.find({
            "MaNguoiBan": self.user["MaNguoiBan"]
        }))
        customer_ids = set()
        for chat in chats:
            if chat.get("MaKhachHang"):
                customer_ids.add(chat.get("MaKhachHang"))
        self.customer_list.clear()
        for cid in customer_ids:
            customer = self.db_connector.nguoi_tieu_dung.find_one({"MaKhachHang": cid})
            if customer:
                name = customer.get("TenKhachHang", "")
                item_text = f"{name} ({cid})"
            else:
                item_text = cid
            item = QtWidgets.QListWidgetItem(item_text)
            item.setData(QtCore.Qt.UserRole, cid)
            self.customer_list.addItem(item)
    
    def load_chat_history(self, item):
        self.chat_history.clear()
        if item is None:
            return
        cid = item.data(QtCore.Qt.UserRole)
        chats = list(self.db_connector.chat_shop.find({
            "MaNguoiBan": self.user["MaNguoiBan"],
            "MaKhachHang": cid
        }).sort("ThoiGian", 1))
        for chat in chats:
            sender = chat.get("Sender", "")
            time = chat.get("ThoiGian").strftime("%Y-%m-%d %H:%M") if chat.get("ThoiGian") else ""
            content = chat.get("NoiDung", "")
            self.chat_history.append(f"[{time}] {sender}: {content}")
    
    def send_chat(self):
        current_item = self.customer_list.currentItem()
        if current_item is None:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Chưa chọn khách hàng để gửi tin!")
            return
        cid = current_item.data(QtCore.Qt.UserRole)
        content = self.chat_input.text().strip()
        if not content:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Nội dung tin nhắn không được để trống!")
            return
        chat_doc = {
            "MaNguoiBan": self.user["MaNguoiBan"],
            "MaKhachHang": cid,
            "ThoiGian": QtCore.QDateTime.currentDateTime().toPyDateTime(),
            "NoiDung": content,
            "Sender": "Shop"
        }
        self.db_connector.chat_shop.insert_one(chat_doc)
        self.chat_input.clear()
        self.load_chat_history(current_item)
