"""Kiểm thử toàn hệ thống theo mục 9 của đề cương: MỖI đường dẫn được thử với 4 vai trò và người chưa đăng nhập.

Ma trận bên dưới viết TAY từ mục 6 của đề cương (cộng các điểm đã thống nhất, xem RA_SOAT_UML.md), độc lập với mã nguồn.
Ba lớp bảo vệ:
1. Mọi đường dẫn trong URLconf phải có trong ma trận (thêm view mới mà quên test phân quyền thì test này đỏ).
2. Khai báo `vai_tro_cho_phep` của từng view phải khớp ma trận.
3. Hành vi thật: trang công khai xem được khi chưa đăng nhập; đường dẫn riêng tư chuyển về /dang-nhap/, sai vai trò 403, đúng vai trò thành công.
"""
from io import StringIO

from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import URLResolver, get_resolver, reverse

from danhmuc.models import CayTrong
from hoidap.services import gui_cau_hoi
from taikhoan.models import NguoiDung
from tuvan.models import LuatTuVan
from tuvan.services import tu_van_va_luu

TAT_CA = {"ADMIN", "BIEN_TAP", "CHUYEN_GIA", "NONG_DAN"}
AD, BT, CG, ND = "ADMIN", "BIEN_TAP", "CHUYEN_GIA", "NONG_DAN"
DONG_Y = {"nhu_cau": "Cây giá trị kinh tế cao", "tinh_thanh": "DAK_LAK", "mua_vu": "MUA_MUA"}

# (tên url, khóa tham số, phương thức, vai trò được phép, mã thành công, dữ liệu gửi kèm)
MA_TRAN = [
    ("doi_mat_khau", None, "get", TAT_CA, 200, None),
    ("nguoi_dung_ds", None, "get", {AD}, 200, None),
    ("nguoi_dung_them", None, "get", {AD}, 200, None),
    ("nguoi_dung_sua", "nguoi_dung", "get", {AD}, 200, None),
    ("nguoi_dung_khoa", "nguoi_dung", "post", {AD}, 302, None),
    ("nhat_ky", None, "get", {AD}, 200, None),
    ("danhmuc:ds", "danh_muc", "get", TAT_CA, 200, None),
    ("danhmuc:them", "danh_muc", "get", {AD, BT}, 200, None),
    ("danhmuc:sua", "danh_muc_pk", "get", {AD, BT}, 200, None),
    ("danhmuc:xoa", "danh_muc_pk", "get", {AD, BT}, 200, None),
    ("tuvan:tu_van", None, "get", TAT_CA, 200, None),
    ("tuvan:api_tinh_diem", None, "post", TAT_CA, 200, DONG_Y),
    ("tuvan:lich_su", None, "get", TAT_CA, 200, None),
    ("tuvan:lich_su_chi_tiet", "lich_su", "get", TAT_CA, 200, None),
    ("tuvan:luat_ds", None, "get", {AD, BT}, 200, None),
    ("tuvan:luat_them", None, "get", {AD, BT}, 200, None),
    ("tuvan:luat_sua", "luat", "get", {AD, BT}, 200, None),
    ("tuvan:luat_xoa", "luat", "get", {AD, BT}, 200, None),
    ("tuvan:luat_bat_tat", "luat", "post", {AD, BT}, 302, None),
    ("timkiem:tim_kiem", None, "get", TAT_CA, 200, None),
    ("truyxuat:truy_xuat", None, "get", TAT_CA, 200, None),
    ("hoidap:ds", None, "get", {AD, CG, ND}, 200, None),
    ("hoidap:them", None, "get", {ND}, 200, None),
    ("hoidap:chi_tiet", "cau_hoi", "get", {AD, CG, ND}, 200, None),
    ("hoidap:tra_loi", "cau_hoi", "get", {CG}, 200, None),
    ("cauhinh:trong_so", None, "get", {AD}, 200, None),
    ("thongke:thong_ke", None, "get", {AD}, 200, None),
    ("baocao:bao_cao", None, "get", {AD}, 200, None),
    ("baocao:cay_trong", None, "get", {AD}, 200, None),
    ("baocao:luat", None, "get", {AD}, 200, None),
    ("baocao:lich_su", None, "get", {AD}, 200, None),
]
CONG_KHAI = {
    "trang_chu", "gioi_thieu", "dang_nhap", "dang_ky", "dang_xuat",
    "quen_mat_khau", "quen_mat_khau_done", "quen_mat_khau_ma", "quen_mat_khau_complete",
}  # không cần đăng nhập; kiểm tra riêng


def tat_ca_ten_url():
    def duyet(mau, ns=""):
        for p in mau:
            if isinstance(p, URLResolver):
                yield from duyet(p.url_patterns, f"{ns}{p.namespace}:" if p.namespace else ns)
            else:
                yield f"{ns}{p.name}", p
    return dict(duyet(get_resolver().url_patterns))


class TestMaTranHeThong(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("nap_du_lieu_mau", stdout=StringIO())
        nong_dan = NguoiDung.objects.get(username="nongdan")
        # Tài khoản mục tiêu riêng cho «sửa / khóa người dùng»: ADMIN khóa nó cũng không ảnh hưởng 4 tài khoản dùng để đăng nhập
        muc_tieu = NguoiDung.objects.create_user("muctieu", password="Mat-khau-manh-2026", vai_tro=nong_dan.vai_tro)
        cay = CayTrong.objects.get(ma_cay="CAO_SU")
        cls.tham_so = {
            "nguoi_dung": {"pk": muc_tieu.pk},
            "danh_muc": {"muc": "cay-trong"},
            "danh_muc_pk": {"muc": "cay-trong", "pk": cay.pk},
            "lich_su": {"pk": tu_van_va_luu(nong_dan, "Cây giá trị kinh tế cao", "DAK_LAK", "MUA_MUA").pk},
            "luat": {"pk": LuatTuVan.objects.get(rule_id="LT20260101-001").pk},
            "cau_hoi": {"pk": gui_cau_hoi(nong_dan, "Kỹ thuật tưới nước cho cà phê mùa khô thế nào?").pk},
        }
        cls.nguoi = {v: NguoiDung.objects.get(username={AD: "admin", BT: "bientap", CG: "chuyengia", ND: "nongdan"}[v]) for v in TAT_CA}

    def duong_dan(self, ten, khoa):
        return reverse(ten, kwargs=self.tham_so[khoa] if khoa else None)

    # ---- lớp bảo vệ 1
    def test_moi_duong_dan_co_trong_ma_tran(self):
        trong_ma_tran = {m[0] for m in MA_TRAN}
        co_that = set(tat_ca_ten_url())
        self.assertEqual(sorted(co_that - trong_ma_tran - CONG_KHAI), [], "Đường dẫn chưa có trong ma trận phân quyền: thêm vào MA_TRAN")
        self.assertEqual(sorted(trong_ma_tran - co_that), [], "Ma trận có đường dẫn không còn tồn tại")
        self.assertEqual(len(MA_TRAN) + len(CONG_KHAI), 40)

    # ---- lớp bảo vệ 2
    def test_khai_bao_vai_tro_cua_view_khop_ma_tran(self):
        view_theo_ten = tat_ca_ten_url()
        for ten, _, _, duoc_phep, _, _ in MA_TRAN:
            khai_bao = view_theo_ten[ten].callback.view_class.vai_tro_cho_phep
            self.assertEqual(set(khai_bao) if khai_bao else TAT_CA, duoc_phep, ten)

    # ---- lớp bảo vệ 3
    def test_chua_dang_nhap_deu_bi_chuyen_ve_dang_nhap(self):
        for ten, khoa, phuong_thuc, _, _, du_lieu in MA_TRAN:
            url = self.duong_dan(ten, khoa)
            with self.subTest(url=url):
                r = getattr(Client(), phuong_thuc)(url, du_lieu or {})
                self.assertEqual(r.status_code, 302)
                self.assertTrue(r["Location"].startswith("/dang-nhap/?next="), r["Location"])

    def test_sai_vai_tro_403_dung_vai_tro_thanh_cong(self):
        for ten, khoa, phuong_thuc, duoc_phep, thanh_cong, du_lieu in MA_TRAN:
            url = self.duong_dan(ten, khoa)
            for vai_tro in sorted(TAT_CA):
                with self.subTest(url=url, vai_tro=vai_tro):
                    c = Client()
                    c.force_login(self.nguoi[vai_tro])
                    r = getattr(c, phuong_thuc)(url, du_lieu or {})
                    self.assertEqual(r.status_code, thanh_cong if vai_tro in duoc_phep else 403)

    def test_view_chi_nhan_post_tu_choi_get(self):
        for ten, khoa, phuong_thuc, duoc_phep, _, _ in MA_TRAN:
            if phuong_thuc != "post":
                continue
            c = Client()
            c.force_login(self.nguoi[sorted(duoc_phep)[0]])
            self.assertEqual(c.get(self.duong_dan(ten, khoa)).status_code, 405, ten)

    def test_duong_dan_cong_khai(self):
        c = Client()
        self.assertEqual(c.get(reverse("trang_chu")).status_code, 200)
        self.assertContains(c.get(reverse("trang_chu")), "Đăng nhập sử dụng")
        self.assertEqual(c.get(reverse("gioi_thieu")).status_code, 200)
        self.assertEqual(c.get(reverse("dang_nhap")).status_code, 200)
        self.assertEqual(c.get(reverse("dang_ky")).status_code, 200)
        self.assertEqual(c.get(reverse("quen_mat_khau")).status_code, 200)
        self.assertEqual(c.get(reverse("quen_mat_khau_done")).status_code, 200)
        self.assertEqual(c.get(reverse("quen_mat_khau_complete")).status_code, 200)
        self.assertEqual(c.get(reverse("quen_mat_khau_ma")).status_code, 200)
        self.assertEqual(c.post(reverse("dang_xuat")).status_code, 302)  # chưa đăng nhập vẫn đăng xuất được, không lỗi
        c.force_login(self.nguoi[ND])
        self.assertContains(c.get(reverse("trang_chu")), "Thông tin thiết yếu cho nhà nông")
        self.assertEqual(c.get(reverse("dang_xuat")).status_code, 405)  # đăng xuất chỉ nhận POST

    def test_duong_dan_khong_ton_tai_la_404(self):
        c = Client()
        c.force_login(self.nguoi[AD])
        for url in ("/khong-co-trang-nay/", "/danh-muc/khong-co/", "/tu-van/lich-su/999999/", "/hoi-dap/999999/", "/nguoi-dung/999999/sua/"):
            self.assertEqual(c.get(url).status_code, 404, url)

    def test_nguoi_dung_bi_khoa_khong_vao_duoc_bat_ky_trang_nao(self):
        c = Client()
        c.force_login(self.nguoi[ND])
        self.nguoi[ND].is_active = False
        self.nguoi[ND].save()
        for ten, khoa, phuong_thuc, _, _, du_lieu in MA_TRAN:
            r = getattr(c, phuong_thuc)(self.duong_dan(ten, khoa), du_lieu or {})
            self.assertEqual(r.status_code, 302, ten)
            self.assertTrue(r["Location"].startswith("/dang-nhap/"), ten)
