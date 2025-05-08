# main.py
import sys
from PyQt5 import QtWidgets
from db_connector import DBConnector
from login import LoginDialog
from admin_window import AdminWindow
from seller_window import SellerWindow
from customer_window import CustomerWindow
from distributor_window import DistributorWindow

def main():
    app = QtWidgets.QApplication(sys.argv)
    db_connector = DBConnector()
    login_dialog = LoginDialog(db_connector)
    if login_dialog.exec_() == QtWidgets.QDialog.Accepted:
        role = login_dialog.role
        user = login_dialog.user
        if role == "Admin":
            main_window = AdminWindow(db_connector, user)
        elif role == "NguoiBan":
            main_window = SellerWindow(db_connector, user)
        elif role == "NguoiTieuDung":
            main_window = CustomerWindow(db_connector, user)
        elif role == "Distributor":
            main_window = DistributorWindow(db_connector, user)
        else:
            QtWidgets.QMessageBox.critical(None, "Lỗi", "Role không xác định!")
            sys.exit(1)
        main_window.show()
        sys.exit(app.exec_())

if __name__ == '__main__':
    main()
