from PyQt5 import QtWidgets, QtCore, QtGui
import datetime
from db_connector import DBConnector
from functools import partial

class DistributorWindow(QtWidgets.QMainWindow):
    def __init__(self, db_connector, user, parent=None):
        super(DistributorWindow, self).__init__(parent)
        self.setWindowTitle("Nhà phân phối - Quản lý vận chuyển")
        self.db_connector = db_connector
        self.user = user
        self.resize(1200, 700)
        
        self.tab_widget = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        self.create_shipping_tab()
        
        # Giao diện tối giản, hiện đại với flat design và font chữ hiện đại
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f9f9f9;
                font-family: "Segoe UI", sans-serif;
            }
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            QTabBar::tab {
                background: transparent;
                padding: 10px 20px;
                margin-right: 2px;
                font-size: 14px;
                color: #555;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom: 3px solid #8e24aa;
                color: #8e24aa;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QPushButton {
                background-color: #8e24aa;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #9c27b0;
            }
            QFrame.card {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
            }
        """)

    # Thêm phương thức closeEvent để chuyển hướng về màn hình đăng nhập khi nhấn nút "X"
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
                    from customer_window import CustomerWindow
                    new_window = CustomerWindow(self.db_connector, user)
                elif role == "Distributor":
                    new_window = DistributorWindow(self.db_connector, user)
                else:
                    QtWidgets.QMessageBox.critical(self, "Lỗi", "Role không xác định!")
                    event.ignore()
                    return
                new_window.show()
            event.accept()
        else:
            event.ignore()

    def create_shipping_tab(self):
        tab = QtWidgets.QWidget()
        vlayout = QtWidgets.QVBoxLayout(tab)
        vlayout.setContentsMargins(15, 15, 15, 15)
        vlayout.setSpacing(10)
        
        # Sử dụng QScrollArea chứa widget có QGridLayout để hiển thị các thẻ (3 thẻ/row)
        self.ship_container = QtWidgets.QScrollArea()
        self.ship_container.setWidgetResizable(True)
        self.ship_list_widget = QtWidgets.QWidget()
        self.ship_grid_layout = QtWidgets.QGridLayout(self.ship_list_widget)
        self.ship_grid_layout.setAlignment(QtCore.Qt.AlignTop)
        self.ship_container.setWidget(self.ship_list_widget)
        vlayout.addWidget(self.ship_container)
        
        self.tab_widget.addTab(tab, "Vận chuyển")
        self.load_shipping()
    
    def load_shipping(self):
        # Lấy các đơn vận chuyển của nhà phân phối hiện tại
        shippings = list(self.db_connector.van_chuyen_phan_phoi.find({
            "MaDistributor": self.user["MaDistributor"]
        }))
        # Xóa sạch các thẻ cũ trong grid layout
        for i in reversed(range(self.ship_grid_layout.count())):
            widgetToRemove = self.ship_grid_layout.itemAt(i).widget()
            if widgetToRemove:
                widgetToRemove.setParent(None)
        
        # Thêm các thẻ mới, sắp xếp 3 thẻ trên mỗi hàng
        for index, ship in enumerate(shippings):
            card = self.create_shipping_card(ship)
            row = index // 3
            col = index % 3
            self.ship_grid_layout.addWidget(card, row, col)
    
    def create_shipping_card(self, ship):
        card = QtWidgets.QFrame()
        card.setObjectName("card")
        card.setProperty("class", "card")
        # Dùng style đã được set trong stylesheet của QMainWindow
        card.setStyleSheet("QFrame.card { background-color: #ffffff; border: 1px solid #ddd; border-radius: 8px; padding: 10px; }")
        
        layout = QtWidgets.QVBoxLayout(card)
        layout.setSpacing(5)
        
        # Lấy thông tin vận chuyển
        maVanChuyen = ship.get("MaVanChuyen", "")
        maDonHang = ship.get("MaDonHang", "")
        trangThai = ship.get("TrangThai", "")
        ngay = ship.get("NgayGiao")
        ngay_str = ngay.strftime("%Y-%m-%d") if ngay else ""
        ghiChu = ship.get("GhiChu", "")
        
        # Lấy thông tin đơn hàng để hiển thị mã khách hàng và tên khách hàng
        don = self.db_connector.don_hang.find_one({"MaDonHang": maDonHang})
        if don:
            maKH = don.get("MaKhachHang", "")
            kh = self.db_connector.nguoi_tieu_dung.find_one({"MaKhachHang": maKH})
            tenKH = kh.get("TenKhachHang", "") if kh else ""
        else:
            maKH = ""
            tenKH = ""
        
        # Tạo các nhãn hiển thị thông tin
        label_vc = QtWidgets.QLabel(f"<b>Mã vận chuyển:</b> {maVanChuyen}")
        label_don = QtWidgets.QLabel(f"<b>Mã đơn hàng:</b> {maDonHang}")
        label_status = QtWidgets.QLabel(f"<b>Trạng thái:</b> {trangThai}")
        label_date = QtWidgets.QLabel(f"<b>Ngày giao:</b> {ngay_str}")
        label_maKH = QtWidgets.QLabel(f"<b>Mã KH:</b> {maKH}")
        label_tenKH = QtWidgets.QLabel(f"<b>Tên KH:</b> {tenKH}")
        label_ghichu = QtWidgets.QLabel(f"<b>Ghi chú:</b> {ghiChu}")
        
        # Thêm các nhãn vào layout của thẻ
        layout.addWidget(label_vc)
        layout.addWidget(label_don)
        layout.addWidget(label_status)
        layout.addWidget(label_date)
        layout.addWidget(label_maKH)
        layout.addWidget(label_tenKH)
        layout.addWidget(label_ghichu)
        
        # Nút "Cập nhật" để cập nhật trạng thái
        btn_update = QtWidgets.QPushButton("Cập nhật")
        btn_update.clicked.connect(partial(self.update_status, ship))
        layout.addWidget(btn_update)
        
        return card
    
    def update_status(self, ship):
        # Cho phép các trạng thái: "đang giao", "đã giao", "đã hủy"
        allowed_statuses = ["đang giao", "đã giao", "đã hủy"]
        current_status = ship.get("TrangThai", "đang giao")
        if current_status not in allowed_statuses:
            current_status = "đang giao"
        new_status, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Cập nhật trạng thái",
            "Chọn trạng thái mới:",
            allowed_statuses,
            allowed_statuses.index(current_status),
            False
        )
        if ok and new_status:
            update = {"TrangThai": new_status}
            if new_status == "đã giao":
                update["NgayGiao"] = datetime.datetime.now()
            self.db_connector.van_chuyen_phan_phoi.update_one(
                {"MaVanChuyen": ship["MaVanChuyen"]},
                {"$set": update}
            )
            self.db_connector.don_hang.update_one(
                {"MaDonHang": ship["MaDonHang"]},
                {"$set": {"TrangThai": new_status}}
            )
            QtWidgets.QMessageBox.information(self, "Thành công", "Trạng thái đã được cập nhật!")
            self.load_shipping()

if __name__ == "__main__":
    import sys
    db_connector = DBConnector()
    app = QtWidgets.QApplication(sys.argv)
    # Giả sử user là một dict chứa MaDistributor, ví dụ:
    user = {"MaDistributor": "D001"}
    window = DistributorWindow(db_connector, user)
    window.show()
    sys.exit(app.exec_())
