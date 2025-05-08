from PyQt5 import QtWidgets, QtGui, QtCore
import datetime, uuid, base64
from db_connector import DBConnector

def add_shadow(widget):
    """Áp dụng hiệu ứng đổ bóng cho widget (giúp card nổi bật hơn)"""
    shadow = QtWidgets.QGraphicsDropShadowEffect()
    shadow.setBlurRadius(15)
    shadow.setXOffset(3)
    shadow.setYOffset(3)
    shadow.setColor(QtGui.QColor(0, 0, 0, 80))
    widget.setGraphicsEffect(shadow)

class CustomerWindow(QtWidgets.QMainWindow):
    def __init__(self, db_connector, user, parent=None):
        super(CustomerWindow, self).__init__(parent)
        self.setWindowTitle("Khách hàng - Ứng dụng mua sắm")
        self.db_connector = db_connector
        self.user = user
        self.resize(1300, 750)
        
        self.tab_widget = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # Các tab cải tiến giao diện
        self.browse_tab = BrowseTab(self.db_connector, self.user, self)
        self.tab_widget.addTab(self.browse_tab, "Duyệt sản phẩm")
        
        self.cart_tab = CartTab(self.db_connector, self.user, self)
        self.tab_widget.addTab(self.cart_tab, "Giỏ hàng")
        
        self.order_tab = OrderTab(self.db_connector, self.user, self)
        self.tab_widget.addTab(self.order_tab, "Đơn hàng của tôi")
        
        self.chat_tab = ChatTab(self.db_connector, self.user, self)
        self.tab_widget.addTab(self.chat_tab, "Phản hồi của shop")
        
        # Style tổng thể: gradient nền, button với hiệu ứng gradient, font chữ hiện đại
        self.setStyleSheet("""
            QMainWindow {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                                  stop:0 #f1f8e9, stop:1 #aed581);
            }
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                                  stop:0 #66bb6a, stop:1 #43a047);
                color: white;
                padding: 8px;
                border: none;
                border-radius: 5px;
                font-family: "Segoe UI", sans-serif;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                                  stop:0 #81c784, stop:1 #66bb6a);
            }
            QLineEdit, QComboBox {
                padding: 6px;
                font-family: "Segoe UI", sans-serif;
                font-size: 13px;
            }
            QLabel {
                font-family: "Segoe UI", sans-serif;
            }
        """)

    # Thêm tính năng chuyển hướng về màn hình đăng nhập khi nhấn nút "X"
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
                    from admin_window import AdminWindow
                    new_window = AdminWindow(self.db_connector, user)
                elif role == "NguoiBan":
                    from seller_window import SellerWindow
                    new_window = SellerWindow(self.db_connector, user)
                elif role == "NguoiTieuDung":
                    new_window = CustomerWindow(self.db_connector, user)
                elif role == "Distributor":
                    from distributor_window import DistributorWindow
                    new_window = DistributorWindow(self.db_connector, user)
                else:
                    QtWidgets.QMessageBox.critical(self, "Lỗi", "Role không xác định!")
                    event.ignore()
                    return
                new_window.show()
            event.accept()  # Cho phép đóng cửa sổ hiện tại
        else:
            event.ignore()  # Hủy việc đóng cửa sổ

# ----------------- Tab Duyệt Sản phẩm -----------------
class BrowseTab(QtWidgets.QWidget):
    def __init__(self, db_connector, user, main_window, parent=None):
        super(BrowseTab, self).__init__(parent)
        self.db_connector = db_connector
        self.user = user
        self.main_window = main_window
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Thanh tìm kiếm với màu sắc nổi bật
        search_layout = QtWidgets.QHBoxLayout()
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Tìm theo tên nông sản...")
        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.addItem("Tất cả", "")
        cats = list(self.db_connector.danh_muc_nong_san.find())
        for c in cats:
            self.category_combo.addItem(c.get("TenDanhMuc", ""), c.get("MaDanhMuc", ""))
        btn_search = QtWidgets.QPushButton("Tìm")
        btn_search.clicked.connect(self.load_products)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.category_combo)
        search_layout.addWidget(btn_search)
        layout.addLayout(search_layout)
        
        # Scroll area chứa các card sản phẩm
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
        
        self.content_widget = QtWidgets.QWidget()
        self.grid_layout = QtWidgets.QGridLayout(self.content_widget)
        self.grid_layout.setSpacing(20)
        self.scroll_area.setWidget(self.content_widget)
        
        self.load_products()
    
    def load_products(self):
        query = {}
        key = self.search_input.text().strip()
        if key:
            query["TenNongSan"] = {"$regex": key, "$options": "i"}
        cat = self.category_combo.currentData()
        if cat:
            query["MaDanhMuc"] = cat
        products = list(self.db_connector.nong_san.find(query))
        
        # Xóa hết card cũ
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
                
        cols = 3  # Số cột hiển thị
        for idx, prod in enumerate(products):
            row = idx // cols
            col = idx % cols
            card = ProductCard(prod, self.add_product_to_cart, self.db_connector)
            self.grid_layout.addWidget(card, row, col)
    
    def add_product_to_cart(self, prod):
        qty, ok = QtWidgets.QInputDialog.getInt(self, "Số lượng", "Nhập số lượng:", value=1, min=1)
        if not ok:
            return
        self.db_connector.gio_hang.insert_one({
            "MaGioHang": f"{self.user['MaKhachHang']}_{prod.get('MaNongSan', '')}",
            "MaKhachHang": self.user["MaKhachHang"],
            "MaNongSan": prod.get("MaNongSan", ""),
            "SoLuong": qty
        })
        QtWidgets.QMessageBox.information(self, "Thành công", "Đã thêm vào giỏ hàng!")
        self.main_window.cart_tab.load_cart()

class ProductCard(QtWidgets.QFrame):
    def __init__(self, prod, add_to_cart_callback, db_connector, parent=None):
        super(ProductCard, self).__init__(parent)
        self.prod = prod
        self.add_to_cart_callback = add_to_cart_callback
        self.db_connector = db_connector

        # Responsive card: sử dụng minimum size và size policy
        self.setMinimumSize(250, 330)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        
        # Nền gradient xanh lá nhẹ với border tinh tế
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e8f5e9, stop:1 #c8e6c9);
                border: 1px solid #66bb6a;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        add_shadow(self)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Ảnh sản phẩm
        self.image_label = QtWidgets.QLabel()
        self.image_label.setFixedSize(220, 180)
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.setStyleSheet("border-radius: 8px;")
        b64 = prod.get("HinhAnh", "")
        if b64:
            try:
                img_data = base64.b64decode(b64)
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(img_data)
                self.image_label.setPixmap(pixmap.scaled(220, 180, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
            except Exception as e:
                self.image_label.setText("Lỗi ảnh")
        else:
            self.image_label.setText("Không có ảnh")
        layout.addWidget(self.image_label)
        
        # Tên sản phẩm
        self.name_label = QtWidgets.QLabel(prod.get("TenNongSan", "Sản phẩm"))
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setFont(QtGui.QFont("Segoe UI", 12, QtGui.QFont.Bold))
        layout.addWidget(self.name_label)
        
        # Tên người bán
        seller_id = prod.get("MaNguoiBan", "")
        seller_name = "Không xác định"
        if seller_id:
            seller = self.db_connector.nguoi_ban.find_one({"MaNguoiBan": seller_id})
            if seller:
                seller_name = seller.get("TenNguoiBan", "Không xác định")
        self.seller_label = QtWidgets.QLabel(f"Người bán: {seller_name}")
        self.seller_label.setAlignment(QtCore.Qt.AlignCenter)
        self.seller_label.setFont(QtGui.QFont("Segoe UI", 10))
        layout.addWidget(self.seller_label)
        
        # Giá sản phẩm
        self.price_label = QtWidgets.QLabel(f"Giá: {prod.get('Gia', 0)}")
        self.price_label.setAlignment(QtCore.Qt.AlignCenter)
        self.price_label.setFont(QtGui.QFont("Segoe UI", 11, QtGui.QFont.DemiBold))
        layout.addWidget(self.price_label)
        
        # Nút thêm vào giỏ
        btn = QtWidgets.QPushButton("Thêm vào giỏ")
        btn.setFont(QtGui.QFont("Segoe UI", 11))
        btn.clicked.connect(lambda: self.add_to_cart_callback(self.prod))
        layout.addWidget(btn)

# ----------------- Tab Giỏ hàng -----------------
class CartTab(QtWidgets.QWidget):
    def __init__(self, db_connector, user, main_window, parent=None):
        super(CartTab, self).__init__(parent)
        self.db_connector = db_connector
        self.user = user
        self.main_window = main_window
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Scroll area chứa card các mặt hàng trong giỏ (hiển thị dạng grid 3 cột)
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
        
        self.content_widget = QtWidgets.QWidget()
        self.grid_layout = QtWidgets.QGridLayout(self.content_widget)
        self.grid_layout.setSpacing(15)
        self.scroll_area.setWidget(self.content_widget)
        
        # Nút Đặt hàng nổi bật
        self.btn_order = QtWidgets.QPushButton("Đặt hàng")
        self.btn_order.setFixedHeight(40)
        self.btn_order.setFont(QtGui.QFont("Segoe UI", 11))
        self.btn_order.clicked.connect(self.place_order)
        layout.addWidget(self.btn_order)
        
        self.load_cart()
    
    def load_cart(self):
        # Xóa các widget cũ
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        items = list(self.db_connector.gio_hang.find({"MaKhachHang": self.user["MaKhachHang"]}))
        cols = 3
        for idx, it in enumerate(items):
            row = idx // cols
            col = idx % cols
            card = CartItemCard(it, self.db_connector)
            self.grid_layout.addWidget(card, row, col)
    
    def place_order(self):
        items = list(self.db_connector.gio_hang.find({"MaKhachHang": self.user["MaKhachHang"]}))
        if not items:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Giỏ hàng trống!")
            return
        total = 0.0
        for it in items:
            prod = self.db_connector.nong_san.find_one({"MaNongSan": it["MaNongSan"]})
            if prod:
                total += float(prod.get("Gia", 0)) * int(it.get("SoLuong", 1))
        ma_don = str(uuid.uuid4())
        order = {
            "MaDonHang": ma_don,
            "MaKhachHang": self.user["MaKhachHang"],
            "NgayDatHang": datetime.datetime.now(),
            "TongTien": total,
            "TrangThai": "Đang giao",
            "PhuongThucThanhToan": "COD"
        }
        self.db_connector.don_hang.insert_one(order)
        for it in items:
            prod = self.db_connector.nong_san.find_one({"MaNongSan": it["MaNongSan"]})
            if prod:
                detail = {
                    "MaChiTiet": str(uuid.uuid4()),
                    "MaDonHang": ma_don,
                    "MaNongSan": it["MaNongSan"],
                    "SoLuong": it["SoLuong"],
                    "DonGia": float(prod.get("Gia", 0))
                }
                self.db_connector.chi_tiet_don_hang.insert_one(detail)
        self.db_connector.gio_hang.delete_many({"MaKhachHang": self.user["MaKhachHang"]})
        distributor = self.db_connector.distributor.find_one()
        if distributor:
            vc = {
                "MaVanChuyen": str(uuid.uuid4()),
                "MaDonHang": ma_don,
                "MaDistributor": distributor.get("MaDistributor", ""),
                "TrangThai": "Đang giao"
            }
            self.db_connector.van_chuyen_phan_phoi.insert_one(vc)
        QtWidgets.QMessageBox.information(self, "Thành công", "Đơn hàng đã được đặt!")
        self.load_cart()
        self.main_window.order_tab.load_orders()

class CartItemCard(QtWidgets.QFrame):
    def __init__(self, cart_item, db_connector, parent=None):
        super(CartItemCard, self).__init__(parent)
        self.cart_item = cart_item
        self.db_connector = db_connector

        # Responsive: sử dụng minimum size và size policy
        self.setMinimumSize(250, 150)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        
        # Nền gradient xanh lá nhẹ
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e8f5e9, stop:1 #c8e6c9);
                border: 1px solid #66bb6a;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        add_shadow(self)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Ảnh sản phẩm trong giỏ
        self.image_label = QtWidgets.QLabel()
        self.image_label.setFixedSize(110, 110)
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.setStyleSheet("border-radius: 8px;")
        prod = self.db_connector.nong_san.find_one({"MaNongSan": cart_item.get("MaNongSan", "")})
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
        
        # Thông tin sản phẩm
        info_layout = QtWidgets.QVBoxLayout()
        name_label = QtWidgets.QLabel(prod.get("TenNongSan", "Sản phẩm"))
        name_label.setFont(QtGui.QFont("Segoe UI", 12, QtGui.QFont.Bold))
        qty_label = QtWidgets.QLabel(f"Số lượng: {cart_item.get('SoLuong', 1)}")
        qty_label.setFont(QtGui.QFont("Segoe UI", 11))
        unit_label = QtWidgets.QLabel(f"Đơn giá: {prod.get('Gia', 0)}")
        unit_label.setFont(QtGui.QFont("Segoe UI", 11))
        total = float(prod.get("Gia", 0)) * int(cart_item.get("SoLuong", 1))
        total_label = QtWidgets.QLabel(f"Tổng: {total}")
        total_label.setFont(QtGui.QFont("Segoe UI", 11, QtGui.QFont.DemiBold))
        info_layout.addWidget(name_label)
        info_layout.addWidget(qty_label)
        info_layout.addWidget(unit_label)
        info_layout.addWidget(total_label)
        layout.addLayout(info_layout)

# ----------------- Tab Đơn hàng của tôi -----------------
class OrderTab(QtWidgets.QWidget):
    def __init__(self, db_connector, user, main_window, parent=None):
        super(OrderTab, self).__init__(parent)
        self.db_connector = db_connector
        self.user = user
        self.main_window = main_window
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
        
        self.content_widget = QtWidgets.QWidget()
        self.grid_layout = QtWidgets.QGridLayout(self.content_widget)
        self.grid_layout.setSpacing(15)
        self.scroll_area.setWidget(self.content_widget)
        
        self.load_orders()
    
    def load_orders(self):
        # Xóa nội dung cũ
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        orders = list(self.db_connector.don_hang.find({"MaKhachHang": self.user["MaKhachHang"]}))
        cols = 3
        for idx, order in enumerate(orders):
            row = idx // cols
            col = idx % cols
            card = OrderCard(order, self.db_connector)
            self.grid_layout.addWidget(card, row, col)

class OrderCard(QtWidgets.QFrame):
    def __init__(self, order, db_connector, parent=None):
        super(OrderCard, self).__init__(parent)
        self.order = order
        self.db_connector = db_connector

        # Responsive: đặt minimum size và size policy
        self.setMinimumSize(250, 200)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        
        # Nền gradient xanh lá nhẹ với border tinh tế
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e8f5e9, stop:1 #c8e6c9);
                border: 1px solid #66bb6a;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        add_shadow(self)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(15)
        
        # Ảnh sản phẩm (lấy ảnh của sản phẩm đầu tiên trong đơn)
        self.image_label = QtWidgets.QLabel()
        self.image_label.setFixedSize(110, 110)
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.setStyleSheet("border-radius: 8px;")
        details = list(self.db_connector.chi_tiet_don_hang.find({"MaDonHang": order.get("MaDonHang", "")}))
        if details:
            first = details[0]
            prod = self.db_connector.nong_san.find_one({"MaNongSan": first.get("MaNongSan", "")})
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
        else:
            self.image_label.setText("Không có ảnh")
        layout.addWidget(self.image_label)
        
        # Thông tin đơn hàng
        info_layout = QtWidgets.QVBoxLayout()
        order_id = order.get("MaDonHang", "")
        id_label = QtWidgets.QLabel(f"Đơn hàng: {order_id}")
        id_label.setFont(QtGui.QFont("Segoe UI", 11, QtGui.QFont.Bold))
        ngay = order.get("NgayDatHang")
        ngay_str = ngay.strftime("%Y-%m-%d %H:%M") if ngay else ""
        date_label = QtWidgets.QLabel(f"Ngày: {ngay_str}")
        date_label.setFont(QtGui.QFont("Segoe UI", 10))
        total_label = QtWidgets.QLabel(f"Tổng tiền: {order.get('TongTien', 0)}")
        total_label.setFont(QtGui.QFont("Segoe UI", 11, QtGui.QFont.DemiBold))
        status_label = QtWidgets.QLabel(f"Trạng thái: {order.get('TrangThai', '')}")
        status_label.setFont(QtGui.QFont("Segoe UI", 10))
        pttt_label = QtWidgets.QLabel(f"PTTT: {order.get('PhuongThucThanhToan', '')}")
        pttt_label.setFont(QtGui.QFont("Segoe UI", 10))
        info_layout.addWidget(id_label)
        info_layout.addWidget(date_label)
        info_layout.addWidget(total_label)
        info_layout.addWidget(status_label)
        info_layout.addWidget(pttt_label)
        
        # Thông tin các sản phẩm trong đơn
        prod_info = []
        for d in details:
            prod = self.db_connector.nong_san.find_one({"MaNongSan": d.get("MaNongSan", "")})
            if prod:
                name = prod.get("TenNongSan", "")
                qty = d.get("SoLuong", 0)
                prod_info.append(f"{name} x {qty}")
        prod_label = QtWidgets.QLabel("; ".join(prod_info))
        prod_label.setWordWrap(True)
        prod_label.setFont(QtGui.QFont("Segoe UI", 10))
        info_layout.addWidget(prod_label)
        
        layout.addLayout(info_layout)

# ----------------- Tab Phản hồi của shop -----------------
class ChatTab(QtWidgets.QWidget):
    def __init__(self, db_connector, user, main_window, parent=None):
        super(ChatTab, self).__init__(parent)
        self.db_connector = db_connector
        self.user = user
        self.main_window = main_window
        
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Danh sách shop (màu nền nhẹ, viền bo tròn)
        self.shop_list = QtWidgets.QListWidget()
        self.shop_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 5px;
                font-family: "Segoe UI", sans-serif;
                font-size: 12px;
            }
            QListWidget::item:selected {
                background-color: #c5e1a5;
            }
        """)
        self.shop_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.shop_list.itemClicked.connect(self.load_chat_history)
        main_layout.addWidget(self.shop_list, 1)
        
        # Khu vực chat với background nhẹ, cuộn mượt
        chat_layout = QtWidgets.QVBoxLayout()
        self.chat_history = QtWidgets.QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                font-family: "Segoe UI", sans-serif;
                font-size: 12px;
            }
        """)
        chat_layout.addWidget(self.chat_history)
        input_layout = QtWidgets.QHBoxLayout()
        self.chat_input = QtWidgets.QLineEdit()
        self.chat_input.setPlaceholderText("Nhập tin nhắn...")
        self.chat_input.setFont(QtGui.QFont("Segoe UI", 12))
        btn_send = QtWidgets.QPushButton("Gửi")
        btn_send.setFont(QtGui.QFont("Segoe UI", 12))
        btn_send.clicked.connect(self.send_chat)
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(btn_send)
        chat_layout.addLayout(input_layout)
        main_layout.addLayout(chat_layout, 2)
        
        self.load_shops_for_chat()
        current_item = self.shop_list.currentItem()
        if current_item:
            self.load_chat_history(current_item)
    
    def load_shops_for_chat(self):
        orders = list(self.db_connector.don_hang.find({"MaKhachHang": self.user["MaKhachHang"]}))
        shop_ids = set()
        for order in orders:
            details = list(self.db_connector.chi_tiet_don_hang.find({"MaDonHang": order.get("MaDonHang", "")}))
            for d in details:
                prod = self.db_connector.nong_san.find_one({"MaNongSan": d.get("MaNongSan", "")})
                if prod:
                    shop_ids.add(prod.get("MaNguoiBan", ""))
        self.shop_list.clear()
        for sid in shop_ids:
            shop = self.db_connector.nguoi_ban.find_one({"MaNguoiBan": sid})
            if shop:
                item = QtWidgets.QListWidgetItem(f"{shop.get('TenNguoiBan', '')} ({sid})")
                item.setData(QtCore.Qt.UserRole, sid)
                self.shop_list.addItem(item)
    
    def load_chat_history(self, item):
        self.chat_history.clear()
        if item is None:
            return
        sid = item.data(QtCore.Qt.UserRole)
        chats = list(self.db_connector.chat_shop.find({
            "MaNguoiBan": sid,
            "MaKhachHang": self.user["MaKhachHang"]
        }).sort("ThoiGian", 1))
        for chat in chats:
            sender = chat.get("Sender", "")
            time = chat.get("ThoiGian").strftime("%Y-%m-%d %H:%M") if chat.get("ThoiGian") else ""
            content = chat.get("NoiDung", "")
            self.chat_history.append(f"[{time}] {sender}: {content}")
    
    def send_chat(self):
        if self.shop_list.currentItem() is None:
            return
        sid = self.shop_list.currentItem().data(QtCore.Qt.UserRole)
        content = self.chat_input.text().strip()
        if content:
            chat_doc = {
                "MaKhachHang": self.user["MaKhachHang"],
                "MaNguoiBan": sid,
                "ThoiGian": QtCore.QDateTime.currentDateTime().toPyDateTime(),
                "NoiDung": content,
                "Sender": "Khách hàng"
            }
            self.db_connector.chat_shop.insert_one(chat_doc)
            self.chat_input.clear()
            self.load_chat_history(self.shop_list.currentItem())
            
# Nếu chạy file này độc lập để kiểm tra
if __name__ == "__main__":
    import sys
    db_connector = DBConnector()
    app = QtWidgets.QApplication(sys.argv)
    # Giả sử user là một document của khách hàng (NguoiTieuDung)
    # Ví dụ: {"MaKhachHang": "KH001", ...}
    user = {"MaKhachHang": "KH001"}
    window = CustomerWindow(db_connector, user)
    window.show()
    sys.exit(app.exec_())
