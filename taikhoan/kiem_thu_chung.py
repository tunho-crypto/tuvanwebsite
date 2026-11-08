"""Dữ liệu dùng chung cho test (độc lập với nap_du_lieu_mau để số liệu tính tay không bị đổi theo dữ liệu mẫu).

Bộ luật (trọng số mặc định w1=0.5, w2=0.3, w3=0.2):
- LT-SR  Sầu riêng, Đăk Lăk, mùa mưa, từ khóa [gia tri cao, kinh te cao]
- LT-CF  Cà phê,   Đăk Lăk, mùa mưa, từ khóa [gia tri cao, kinh te cao, gia tri kinh te, cay cong nghiep]
- LT-HT  Hồ tiêu,  luật chung (tỉnh, mùa để trống), từ khóa [gia tri cao, kinh te cao]
- LT-BO  Bơ,       Lâm Đồng, mùa khô, từ khóa [gia tri cao, an qua]
- LT-OFF Chanh dây, Lâm Đồng, mùa khô, từ khóa [gia tri cao], is_active=False
"""
from datetime import datetime
from types import SimpleNamespace

from django.test import Client, TestCase, TransactionTestCase
from django.utils import timezone

from cauhinh.models import CauHinhHeThong
from danhmuc.models import CayTrong, KyThuat, MuaVu, TaiLieu, TinhThanh
from taikhoan import du_lieu_mau as dl
from taikhoan.models import NguoiDung, VaiTro
from tuvan.models import LuatTuVan

MAT_KHAU = "123456"
TAT_CA_VAI_TRO = ("ADMIN", "BIEN_TAP", "CHUYEN_GIA", "NONG_DAN")


def tao_du_lieu_chung():
    """Tạo 4 vai trò + 4 người dùng, 12 cây, 5 tỉnh, 2 mùa, tài liệu, trọng số, bộ luật mẫu."""
    vai_tro = {ma: VaiTro.objects.create(ma_vai_tro=ma, ten_vai_tro=ten, mo_ta=mo_ta) for ma, ten, mo_ta in dl.VAI_TRO}
    nguoi_dung = {}
    for username, ho, ten, ma_vt in dl.TAI_KHOAN:
        nd = NguoiDung(username=username, last_name=ho, first_name=ten, vai_tro=vai_tro[ma_vt])
        nd.set_password(MAT_KHAU)
        nd.save()
        nguoi_dung[ma_vt] = nd

    cay = {m: CayTrong.objects.create(ma_cay=m, ten_cay=t, nhom_cay=n, dac_diem=d) for m, t, n, d in dl.CAY_TRONG}
    tinh = {m: TinhThanh.objects.create(ma_tinh=m, ten_tinh=t) for m, t in dl.TINH_THANH}
    mua = {m: MuaVu.objects.create(ma_mua=m, ten_mua=t, thoi_gian_tu=a, thoi_gian_den=b) for m, t, a, b in dl.MUA_VU}
    tai_lieu = TaiLieu.objects.create(ma_tl="TL_TEST", ten_tl="Tài liệu kiểm thử", nguon_tham_chieu="WASI")

    ky_thuat = KyThuat.objects.create(ma_kt="KT_TEST", ten_kt="Kỹ thuật kiểm thử", loai_kt="Tưới nước", noi_dung="...")

    for ten, gia_tri in (("w1", "0.5"), ("w2", "0.3"), ("w3", "0.2")):
        CauHinhHeThong.objects.create(ten_cau_hinh=ten, gia_tri=gia_tri)

    def luat(rule_id, ma_cay, ma_tinh, ma_mua, tu_khoa, kich_hoat=True):
        return LuatTuVan.objects.create(
            rule_id=rule_id,
            cay_tro=cay[ma_cay],
            tinh_thanh=tinh[ma_tinh] if ma_tinh else None,
            mua_vu=mua[ma_mua] if ma_mua else None,
            condition_json={"tu_khoa": tu_khoa},
            score_weight="1.00",
            tai_lieu=tai_lieu,
            is_active=kich_hoat,
        )

    luat("LT-SR", "SAU_RIENG", "DAK_LAK", "MUA_MUA", ["gia tri cao", "kinh te cao"])
    luat("LT-CF", "CA_PHE", "DAK_LAK", "MUA_MUA", ["gia tri cao", "kinh te cao", "gia tri kinh te", "cay cong nghiep"])
    luat("LT-HT", "HO_TIEU", None, None, ["gia tri cao", "kinh te cao"])
    luat("LT-BO", "BO", "LAM_DONG", "MUA_KHO", ["gia tri cao", "an qua"])
    luat("LT-OFF", "CHANH_DAY", "LAM_DONG", "MUA_KHO", ["gia tri cao"], kich_hoat=False)

    return SimpleNamespace(
        vai_tro=vai_tro, nguoi_dung=nguoi_dung, cay=cay, tinh=tinh, mua=mua, tai_lieu=tai_lieu, ky_thuat=ky_thuat
    )


class TestCaseDuLieuChung(TestCase):
    """Lớp cơ sở: tạo dữ liệu chung một lần cho cả lớp test, có sẵn self.dl."""

    @classmethod
    def setUpTestData(cls):
        cls.dl = tao_du_lieu_chung()

    def dang_nhap_vai_tro(self, ma_vai_tro):
        """Đăng nhập self.client bằng tài khoản mẫu của vai trò, trả về người dùng đó."""
        self.client.force_login(self.dl.nguoi_dung[ma_vai_tro])
        return self.dl.nguoi_dung[ma_vai_tro]

    def kiem_tra_phan_quyen(self, url, cho_phep, phuong_thuc="get", du_lieu=None, ma_thanh_cong=200, chi_bi_chan=False):
        """Ma trận phân quyền cho một URL.

        - Chưa đăng nhập: 302 về /dang-nhap/.
        - Vai trò KHÔNG thuộc cho_phep: 403.
        - Vai trò thuộc cho_phep: ma_thanh_cong (bỏ qua nếu chi_bi_chan=True, dùng cho view POST làm thay đổi dữ liệu).
        """
        c = Client()
        phan_hoi = getattr(c, phuong_thuc)(url, du_lieu or {})
        self.assertEqual(phan_hoi.status_code, 302, f"Ẩn danh {url}")
        self.assertIn("/dang-nhap/", phan_hoi["Location"], f"Ẩn danh {url}")
        for ma in TAT_CA_VAI_TRO:
            if ma in cho_phep and chi_bi_chan:
                continue
            c = Client()
            c.force_login(self.dl.nguoi_dung[ma])
            phan_hoi = getattr(c, phuong_thuc)(url, du_lieu or {})
            mong_doi = ma_thanh_cong if ma in cho_phep else 403
            self.assertEqual(phan_hoi.status_code, mong_doi, f"{ma} {phuong_thuc.upper()} {url}")


class TransactionTestCaseDuLieuChung(TransactionTestCase):
    """Dùng cho test đa luồng (tranh chấp dữ liệu): dữ liệu phải được COMMIT thật để các luồng khác nhìn thấy."""

    def setUp(self):
        self.dl = tao_du_lieu_chung()


# ---------------------------------------------------------------------------------------------
# Dữ liệu thống kê tính tay được (dùng cho test thống kê và báo cáo). Mọi mốc thời gian là 12:00 giờ địa phương.
#
#  Tư vấn (5 lượt)        ngày    tỉnh      mùa        kết quả   đề xuất (hạng 1 đứng trước)
#   LS-T1  nongdan        01/10   Đăk Lăk   Mùa mưa    có        Sầu riêng, Cà phê
#   LS-T2  nongdan        01/10   Đăk Lăk   Mùa mưa    có        Sầu riêng, Hồ tiêu
#   LS-T3  admin          02/10   Lâm Đồng  Mùa khô    có        Bơ, Hồ tiêu
#   LS-T4  nongdan        05/10   Đăk Lăk   (không)    ngoài     -
#   LS-T5  chuyengia      05/10   Gia Lai   Mùa mưa    ngoài     -
#  Hỏi đáp (6 câu): 01/10 DA + NGOAI; 02/10 DA + NGOAI; 05/10 CHO + NGOAI
#  Tìm kiếm (10 dòng): 01/10 «ca phe», «ca phe», «sau rieng», «!!!»; 02/10 «Cà phê», «sau rieng», «mua mua»;
#                      05/10 «ca phe», «ho tieu», «ho tieu»
# ---------------------------------------------------------------------------------------------
def gio(thang, ngay, nam=2026):
    return timezone.make_aware(datetime(nam, thang, ngay, 12, 0))


def tao_du_lieu_thong_ke(dl):
    from hoidap.models import CauHoi
    from timkiem.models import LichSuTimKiem
    from tuvan.models import LichSuTuVan
    from tuvan.services import THONG_BAO_NGOAI_PHAM_VI

    ten_cay = {"SAU_RIENG": "Sầu riêng", "CA_PHE": "Cà phê", "HO_TIEU": "Hồ tiêu", "BO": "Bơ"}

    def lich_su(ma, nguoi, nhu_cau, tinh, ma_tinh, mua, ma_mua, de_xuat, ngay):
        trong = bool(de_xuat)
        ket_qua = {
            "trong_pham_vi": trong,
            "thong_bao": "" if trong else THONG_BAO_NGOAI_PHAM_VI,
            "dau_vao": {"nhu_cau": nhu_cau, "tinh_thanh": ma_tinh, "mua_vu": ma_mua},
            "trong_so": {"w1": 0.5, "w2": 0.3, "w3": 0.2},
            "de_xuat": [
                {"thu_hang": i, "ma_cay": ma_cay, "ten_cay": ten_cay[ma_cay], "diem": diem, "chi_tiet": {}, "ly_do": "", "rule_id": "", "tai_lieu": None}
                for i, (ma_cay, diem) in enumerate(de_xuat, start=1)
            ],
        }
        doi_tuong = LichSuTuVan.objects.create(
            ma_lstv=ma, nguoi_dung=dl.nguoi_dung[nguoi], nhu_cau=nhu_cau, tinh_thanh=tinh, mua_vu=mua,
            ket_qua_json=ket_qua, thoi_gian=ngay
        )

    lich_su("LS-T1", "NONG_DAN", "Cây giá trị kinh tế cao", "Đăk Lăk", "DAK_LAK", "Mùa mưa", "MUA_MUA", [("SAU_RIENG", 1.0), ("CA_PHE", 0.875)], gio(10, 1))
    lich_su("LS-T2", "NONG_DAN", "Cây giá trị kinh tế cao", "Đăk Lăk", "DAK_LAK", "Mùa mưa", "MUA_MUA", [("SAU_RIENG", 1.0), ("HO_TIEU", 0.75)], gio(10, 1))
    lich_su("LS-T3", "ADMIN", "Cây ăn quả giá trị cao", "Lâm Đồng", "LAM_DONG", "Mùa khô", "MUA_KHO", [("BO", 1.0), ("HO_TIEU", 0.5)], gio(10, 2))
    lich_su("LS-T4", "NONG_DAN", "giá cà phê ngày mai", "Đăk Lăk", "DAK_LAK", "", "", [], gio(10, 5))
    lich_su("LS-T5", "CHUYEN_GIA", "thời tiết", "Gia Lai", "GIA_LAI", "Mùa mưa", "MUA_MUA", [], gio(10, 5))

    for ma, trang_thai, ngay in (
        ("CH-T1", CauHoi.DA_TRA_LOI, gio(10, 1)), ("CH-T2", CauHoi.NGOAI_PHAM_VI, gio(10, 1)),
        ("CH-T3", CauHoi.DA_TRA_LOI, gio(10, 2)), ("CH-T4", CauHoi.NGOAI_PHAM_VI, gio(10, 2)),
        ("CH-T5", CauHoi.CHO_TRA_LOI, gio(10, 5)), ("CH-T6", CauHoi.NGOAI_PHAM_VI, gio(10, 5)),
    ):
        CauHoi.objects.create(ma_ch=ma, nguoi_dung=dl.nguoi_dung["NONG_DAN"], noi_dung="Câu hỏi " + ma, trang_thai=trang_thai, thoi_gian=ngay)

    for i, (tu_khoa, ngay) in enumerate((
        ("ca phe", gio(10, 1)), ("ca phe", gio(10, 1)), ("sau rieng", gio(10, 1)), ("!!!", gio(10, 1)),
        ("Cà phê", gio(10, 2)), ("sau rieng", gio(10, 2)), ("mua mua", gio(10, 2)),
        ("ca phe", gio(10, 5)), ("ho tieu", gio(10, 5)), ("ho tieu", gio(10, 5)),
    ), start=1):
        LichSuTimKiem.objects.create(ma_ls=f"TK-T{i}", tu_khoa=tu_khoa, thoi_gian=ngay)
