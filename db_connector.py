# db_connector.py
from pymongo import MongoClient

class DBConnector:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="AgricultureDB"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
    
    def get_collection(self, collection_name):
        return self.db[collection_name]

    # Thuộc tính truy cập nhanh các collection:
    @property
    def admin(self):
        return self.get_collection("Admin")
    
    @property
    def nguoi_ban(self):
        return self.get_collection("NguoiBan")
    
    @property
    def nguoi_tieu_dung(self):
        return self.get_collection("NguoiTieuDung")
    
    @property
    def distributor(self):
        return self.get_collection("Distributor")
    
    @property
    def danh_muc_nong_san(self):
        return self.get_collection("DanhMucNongSan")
    
    @property
    def nong_san(self):
        return self.get_collection("NongSan")
    
    @property
    def don_hang(self):
        return self.get_collection("DonHang")
    
    @property
    def chi_tiet_don_hang(self):
        return self.get_collection("ChiTietDonHang")
    
    @property
    def gio_hang(self):
        return self.get_collection("GioHang")
    
    @property
    def phuong_thuc_thanh_toan(self):
        return self.get_collection("PhuongThucThanhToan")
    
    @property
    def danh_gia(self):
        return self.get_collection("DanhGia")
    
    @property
    def van_chuyen_phan_phoi(self):
        return self.get_collection("VanChuyenPhanPhoi")
    
    # Collection để lưu chat giữa khách hàng và shop (nếu cần)
    @property
    def chat_shop(self):
        return self.get_collection("ChatShop")
