"""Phân loại câu hỏi trong/ngoài phạm vi (quy tắc 9)."""
from danhmuc.models import TinhThanh
from hoidap.pham_vi import LY_DO_CHU_DE, LY_DO_KHONG_CO_DANH_MUC, LY_DO_TINH, phan_loai_cau_hoi
from taikhoan.kiem_thu_chung import TestCaseDuLieuChung


class TestPhanLoaiCauHoi(TestCaseDuLieuChung):
    def kiem_tra(self, cau, trong, ly_do=""):
        self.assertEqual(phan_loai_cau_hoi(cau), (trong, ly_do), cau)

    def test_trong_pham_vi_khi_nhac_cay_trong(self):
        for cau in (
            "Kỹ thuật tưới nước cho cà phê mùa khô thế nào?",
            "Cách trồng sầu riêng ở Đăk Lăk",
            "HỒ TIÊU bị vàng lá phải làm sao",
            "trong ca phe o dak lak",  # không dấu
        ):
            self.kiem_tra(cau, True)

    def test_trong_pham_vi_khi_nhac_ky_thuat_trong_danh_muc(self):
        self.kiem_tra("Cho tôi hỏi về tưới nước vào mùa khô", True)  # loại kỹ thuật «Tưới nước»

    def test_gia_the_va_gia_tri_khong_bi_nham_voi_gia_ca(self):
        self.kiem_tra("Giá thể trồng sầu riêng nên dùng loại nào", True)
        self.kiem_tra("Sầu riêng có giá trị dinh dưỡng gì", True)

    def test_ngoai_pham_vi_vi_hoi_gia_hoac_du_doan(self):
        for cau in ("giá cà phê ngày mai", "Giá cà phê hôm nay là bao nhiêu", "Dự đoán cà phê năm sau", "Thị trường sầu riêng thế nào", "dự báo mưa cho cà phê"):
            self.kiem_tra(cau, False, LY_DO_CHU_DE)

    def test_ngoai_pham_vi_vi_tinh_ngoai_tay_nguyen(self):
        for cau in ("Trồng cà phê ở Bình Phước được không", "Sầu riêng ở Tiền Giang", "Cà phê ở Hà Nội", "cà phê tại tp Hồ Chí Minh", "ho tieu o Phu Quoc Kien Giang"):
            self.kiem_tra(cau, False, LY_DO_TINH)

    def test_tinh_ngoai_vung_them_vao_danh_muc_cung_bi_nhan_ra(self):
        TinhThanh.objects.create(ma_tinh="NGOAI_LE", ten_tinh="Ngoại Lệ", vung_mien="Khác")
        self.kiem_tra("Trồng cà phê ở Ngoại Lệ", False, LY_DO_TINH)

    def test_tinh_tay_nguyen_trong_danh_muc_khong_bi_chan(self):
        for cau in ("Cà phê ở Kon Tum", "Cà phê ở Gia Lai", "Cà phê ở Đăk Nông", "Cà phê ở Lâm Đồng", "ca phe o gia lai", "Cà phê ở Đăk Lăk"):
            self.kiem_tra(cau, True)

    def test_gia_lai_khong_bi_nham_voi_hoi_gia(self):
        self.kiem_tra("Trồng hồ tiêu ở Gia Lai", True)
        self.kiem_tra("giá cà phê ở Gia Lai", False, LY_DO_CHU_DE)  # «giá» có dấu thì vẫn là hỏi giá
        self.kiem_tra("gia ca phe ngay mai", False, LY_DO_CHU_DE)  # gõ không dấu: «gia cà phê» vẫn bị nhận ra

    def test_ngoai_pham_vi_vi_khong_nhac_cay_hay_ky_thuat(self):
        for cau in ("Hôm nay trời đẹp quá", "Làm sao để nấu phở ngon", "Thời tiết Đăk Lăk ngày mai", "", "   ", "???"):
            self.kiem_tra(cau, False, LY_DO_KHONG_CO_DANH_MUC)

    def test_ten_cay_phai_nhac_dung_cum_lien_tiep(self):
        self.kiem_tra("phê này cà gì vậy", False, LY_DO_KHONG_CO_DANH_MUC)  # đủ từ nhưng sai thứ tự
        self.kiem_tra("trồng cà phê", True)

    def test_uu_tien_tinh_roi_den_chu_de_roi_den_danh_muc(self):
        self.kiem_tra("giá cà phê ở Bình Phước", False, LY_DO_TINH)

    def test_them_cay_moi_vao_danh_muc_thi_cau_hoi_ve_cay_do_trong_pham_vi(self):
        self.kiem_tra("Cách trồng mắc ca", False, LY_DO_KHONG_CO_DANH_MUC)
        from danhmuc.models import CayTrong

        CayTrong.objects.create(ma_cay="MAC_CA", ten_cay="Mắc ca", nhom_cay="CONG_NGHIEP")
        self.kiem_tra("Cách trồng mắc ca", True)
