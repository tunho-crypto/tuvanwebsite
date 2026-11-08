"""Kiểm chứng TỰ ĐỘNG từng test case thủ công trong danh_sach.py, trên dữ liệu thật của nap_du_lieu_mau.

Mỗi test case có đúng một hàm test_tc_<use_case>_<số>. Mục đích: khi bạn làm tay theo bảng, kết quả mong đợi đã được
chứng minh là đúng với hệ thống. Riêng UI-01 (không mạng) và phần nhìn bằng mắt (màu sắc, bố cục) cần tự kiểm tra trên trình duyệt.
"""
import html as html_lib
import re
from io import BytesIO, StringIO

import openpyxl
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from danhmuc.models import CayTrong, MuaVu, TaiLieu, TinhThanh
from hoidap.models import CauHoi, TraLoi
from kiem_thu_thu_cong.danh_sach import HAM_NGOAI_PHAM_VI, NHU_CAU_CHINH
from taikhoan.models import NguoiDung, NhatKy
from timkiem.models import LichSuTimKiem
from tuvan.models import LichSuTuVan, LuatTuVan

MK = "123456"
HOM_NAY = f"{timezone.localdate():%Y%m%d}"
MENU_AD = ["Trang chủ", "Giới thiệu", "Danh mục", "Tra cứu", "Tư vấn", "Hỏi đáp", "Báo cáo", "Quản trị"]
MENU_BT = ["Trang chủ", "Giới thiệu", "Danh mục", "Tra cứu", "Tư vấn"]
MENU_CG = MENU_ND = ["Trang chủ", "Giới thiệu", "Danh mục", "Tra cứu", "Tư vấn", "Hỏi đáp"]


def vao(ten, mat_khau=MK, **them):
    """Đăng nhập bằng form thật (không dùng force_login) và trả về client."""
    c = Client()
    r = c.post("/dang-nhap/", {"username": ten, "password": mat_khau, **them})
    assert r.status_code == 302, f"đăng nhập {ten} thất bại"
    return c


def van_ban(r):
    """Văn bản hiển thị của trang (bỏ thẻ HTML, script, gộp khoảng trắng) để so khớp câu thông báo."""
    t = re.sub(r"<script.*?</script>", " ", r.content.decode(), flags=re.S)
    t = html_lib.unescape(re.sub(r"<[^>]+>", " ", t))
    return " ".join(t.split())


def loi_form(r):
    return [html_lib.unescape(re.sub(r"<[^>]+>", "", m)).strip() for m in re.findall(r"(?:invalid-feedback d-block|alert alert-danger)[^>]*>(.*?)</div>", r.content.decode(), flags=re.S)]


def tu_van(c, nhu_cau=NHU_CAU_CHINH, tinh="DAK_LAK", mua="MUA_MUA"):
    return c.post("/tu-van/", {"nhu_cau": nhu_cau, "tinh_thanh": tinh, "mua_vu": mua}, follow=True)


def de_xuat(r):
    return [(x["ten_cay"], round(x["diem"], 3)) for x in r.context["ket_qua"]["de_xuat"]]


def hoi(c, noi_dung):
    return c.post("/hoi-dap/them/", {"noi_dung": noi_dung}, follow=True)


def ten_menu(c):
    return [m["ten"] for m in c.get("/").context["menu"]]


def xlsx(r):
    return openpyxl.load_workbook(BytesIO(r.content))


def bang(ws, o_dau):
    dong = [[c.value for c in r] for r in ws.iter_rows()]
    i = next(k for k, r in enumerate(dong) if r[0] == o_dau)
    return dong[i], dong[i + 1 :]


class KichBan(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("nap_du_lieu_mau", stdout=StringIO())

    def setUp(self):
        self.ad, self.bt, self.cg, self.nd = (vao(t) for t in ("admin", "bientap", "chuyengia", "nongdan"))

    def da_thay(self, r, *cum):
        t = van_ban(r)
        for c in cum:
            self.assertIn(c, t, c)


# ======================================================================================= Đăng nhập
class TestDangNhap(KichBan):
    def test_tc_dn_01(self):
        c = Client()
        r = c.post("/dang-nhap/", {"username": "nongdan", "password": MK}, follow=True)
        self.assertRedirects(r, "/")
        self.da_thay(r, "Xin chào, Phạm Nông Dân", "Vai trò: Nông dân")
        self.assertEqual(ten_menu(c), MENU_ND)
        self.assertTrue(NhatKy.objects.filter(hanh_dong="Đăng nhập", nguoi_dung__username="nongdan").exists())

    def test_tc_dn_02(self):
        c = Client()
        for username in ("nongdan", "khongco"):
            r = c.post("/dang-nhap/", {"username": username, "password": "sai-mat-khau" if username == "nongdan" else MK})
            self.assertEqual(r.status_code, 200)
            self.assertEqual(loi_form(r), ["Tên đăng nhập hoặc mật khẩu không đúng."])
        self.assertEqual(NhatKy.objects.filter(hanh_dong="Đăng nhập thất bại").count(), 2)
        self.assertFalse(NhatKy.objects.filter(chi_tiet__icontains="sai-mat-khau").exists())
        r = c.post("/dang-nhap/", {"username": "", "password": ""})
        self.assertEqual(loi_form(r), ["Trường này là bắt buộc."] * 2)
        self.assertNotIn("_auth_user_id", c.session)

    def test_tc_dn_03(self):
        r = self.nd.post("/dang-xuat/")
        self.assertRedirects(r, "/dang-nhap/")
        self.assertEqual(self.nd.get("/").status_code, 200)
        self.assertEqual(self.nd.get("/doi-mat-khau/").status_code, 302)
        self.assertTrue(NhatKy.objects.filter(hanh_dong="Đăng xuất", nguoi_dung__username="nongdan").exists())
        c = vao("nongdan")
        self.assertEqual(c.get("/dang-xuat/").status_code, 405)
        self.assertEqual(c.get("/").status_code, 200)  # GET không đăng xuất được

    def test_tc_dn_04(self):
        r = self.nd.post("/doi-mat-khau/", {"old_password": MK, "new_password1": "Mat-khau-moi-2026", "new_password2": "Mat-khau-moi-2026"}, follow=True)
        self.assertRedirects(r, "/")
        self.da_thay(r, "Đã đổi mật khẩu.")
        self.assertEqual(self.nd.get("/").status_code, 200)  # vẫn đang đăng nhập
        self.assertEqual(Client().post("/dang-nhap/", {"username": "nongdan", "password": MK}).status_code, 200)
        self.assertEqual(Client().post("/dang-nhap/", {"username": "nongdan", "password": "Mat-khau-moi-2026"}).status_code, 302)
        self.assertTrue(NhatKy.objects.filter(hanh_dong="Đổi mật khẩu").exists())

    def test_tc_dn_05(self):
        def thu(cu, moi, nhap_lai=None):
            nd = vao("nongdan")
            return loi_form(nd.post("/doi-mat-khau/", {"old_password": cu, "new_password1": moi, "new_password2": nhap_lai or moi}))

        self.assertEqual(thu("sai", "Mat-khau-moi-2026"), ["Mật khẩu cũ không chính xác. Hãy nhập lại lần nữa"])
        self.assertEqual(thu(MK, "12345678"), ["Mật khẩu này quá phổ biến.", "Mật khẩu này hoàn toàn là số."])
        self.assertEqual(thu(MK, "Ab1!xyz"), ["Mật khẩu quá ngắn: cần có ít nhất 8 ký tự."])
        self.assertEqual(len(thu(MK, "Mat-khau-moi-2026", "Mat-khau-khac-2026")), 1)  # hai mật khẩu mới khác nhau
        self.assertTrue(NguoiDung.objects.get(username="nongdan").check_password(MK))


# ======================================================================================= Quản lý người dùng
class TestQuanLyNguoiDung(KichBan):
    def test_tc_nd_01(self):
        r = self.ad.get("/nguoi-dung/")
        self.assertEqual([u.username for u in r.context["ds_nguoi_dung"]], ["admin", "bientap", "chuyengia", "nongdan"])
        ds = lambda **q: [u.username for u in self.ad.get("/nguoi-dung/", q).context["ds_nguoi_dung"]]
        self.assertEqual(ds(q="chuyen"), ["chuyengia"])
        self.assertEqual(ds(vai_tro="NONG_DAN"), ["nongdan"])
        r = self.ad.get("/nguoi-dung/", {"trang_thai": "khoa"})
        self.assertEqual(ds(trang_thai="khoa"), [])
        self.da_thay(r, "Không có người dùng nào.")

    def test_tc_nd_02(self):
        vt = self.ad.get("/nguoi-dung/them/").context["form"].fields["vai_tro"].queryset.get(ma_vai_tro="CHUYEN_GIA")
        r = self.ad.post("/nguoi-dung/them/", {"username": "nvmoi", "ho": "Nguyễn", "ten": "Mới", "email": "nv@example.com", "vai_tro": vt.pk,
                                               "mat_khau": "Mat-khau-manh-2026", "nhap_lai_mat_khau": "Mat-khau-manh-2026", "is_active": "on"}, follow=True)
        self.assertRedirects(r, "/nguoi-dung/")
        self.da_thay(r, "Đã tạo người dùng nvmoi.", "nvmoi")
        nd = NguoiDung.objects.get(username="nvmoi")
        self.assertEqual((nd.vai_tro.ma_vai_tro, nd.is_active), ("CHUYEN_GIA", True))
        vao("nvmoi", "Mat-khau-manh-2026")
        self.assertTrue(NhatKy.objects.filter(hanh_dong="Tạo người dùng").exists())

    def test_tc_nd_03(self):
        vt = NguoiDung.objects.get(username="nongdan").vai_tro.pk
        def thu(**d):
            goc = {"username": "zz_moi", "vai_tro": vt, "mat_khau": "Mat-khau-manh-2026", "nhap_lai_mat_khau": "Mat-khau-manh-2026"}
            return loi_form(self.ad.post("/nguoi-dung/them/", {**goc, **d}))

        self.assertEqual(thu(username="NONGDAN"), ["Tên đăng nhập đã tồn tại."])
        self.assertEqual(thu(mat_khau="123456", nhap_lai_mat_khau="123456"),
                         ["Mật khẩu quá ngắn: cần có ít nhất 8 ký tự.", "Mật khẩu này quá phổ biến.", "Mật khẩu này hoàn toàn là số."])
        self.assertEqual(thu(nhap_lai_mat_khau="Mat-khau-khac-2026"), ["Hai mật khẩu không khớp."])
        self.assertFalse(NguoiDung.objects.filter(username="zz_moi").exists())

    def test_tc_nd_04(self):
        pk = NguoiDung.objects.get(username="nongdan").pk
        r = self.ad.post(f"/nguoi-dung/{pk}/khoa/", follow=True)
        self.da_thay(r, "Đã khóa tài khoản nongdan.", "Đã khóa", "Mở khóa")
        self.assertEqual(self.nd.get("/doi-mat-khau/").status_code, 302)  # tài khoản bị khóa bị đăng xuất; trang chủ vẫn công khai
        r = Client().post("/dang-nhap/", {"username": "nongdan", "password": MK})
        self.assertEqual(loi_form(r), ["Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên."])
        r = self.ad.post(f"/nguoi-dung/{pk}/khoa/", follow=True)
        self.da_thay(r, "Đã mở khóa tài khoản nongdan.")
        vao("nongdan")
        self.assertEqual(list(NhatKy.objects.filter(hanh_dong__in=["Khóa tài khoản", "Mở khóa tài khoản"]).order_by("id").values_list("hanh_dong", flat=True)),
                         ["Khóa tài khoản", "Mở khóa tài khoản"])

    def test_tc_nd_05(self):
        admin = NguoiDung.objects.get(username="admin")
        html = self.ad.get("/nguoi-dung/").content.decode()
        self.assertNotIn(f"/nguoi-dung/{admin.pk}/khoa/", html)  # không có nút Khóa ở dòng của chính mình
        self.assertIn(f"/nguoi-dung/{admin.pk}/sua/", html)
        r = self.ad.post(f"/nguoi-dung/{admin.pk}/sua/", {"ho": "Nguyễn Quản", "ten": "Trị", "email": "", "vai_tro": admin.vai_tro_id})  # không gửi is_active = bỏ chọn
        self.assertEqual(loi_form(r), ["Không thể tự khóa tài khoản của chính mình."])
        admin.refresh_from_db()
        self.assertTrue(admin.is_active)

    def test_tc_nd_06(self):
        admin = NguoiDung.objects.get(username="admin")
        vt = NguoiDung.objects.get(username="nongdan").vai_tro.pk
        r = self.ad.post(f"/nguoi-dung/{admin.pk}/sua/", {"ho": "A", "ten": "B", "email": "", "vai_tro": vt, "is_active": "on"})
        self.assertEqual(loi_form(r), ["Không thể tự bỏ quyền ADMIN của chính mình."])
        admin.refresh_from_db()
        self.assertEqual(admin.vai_tro.ma_vai_tro, "ADMIN")

    def test_tc_nd_07(self):
        bt = NguoiDung.objects.get(username="bientap")
        vt = NguoiDung.objects.get(username="chuyengia").vai_tro.pk
        r = self.ad.post(f"/nguoi-dung/{bt.pk}/sua/", {"ho": "Trần Biên", "ten": "Tập", "email": "", "vai_tro": vt, "is_active": "on", "mat_khau_moi": "Mat-khau-manh-2026"}, follow=True)
        self.da_thay(r, "Đã cập nhật người dùng bientap.")
        bt.refresh_from_db()
        self.assertEqual(bt.vai_tro.ma_vai_tro, "CHUYEN_GIA")
        vao("bientap", "Mat-khau-manh-2026")
        nk = NhatKy.objects.get(hanh_dong="Sửa người dùng")
        self.assertIn("đặt lại mật khẩu", nk.chi_tiet)
        self.assertNotIn("Mat-khau-manh-2026", nk.chi_tiet)


class TestNhatKy(KichBan):
    def test_tc_nk_01(self):
        r = self.ad.get("/nhat-ky/")
        ds = list(r.context["ds_nhat_ky"])
        self.assertEqual(ds, sorted(ds, key=lambda n: (n.thoi_gian, n.id), reverse=True))  # mới nhất ở trên
        self.assertRegex(r.content.decode(), r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}")
        loc = self.ad.get("/nhat-ky/", {"nguoi_dung": "nongdan"}).context["ds_nhat_ky"]
        self.assertTrue(loc and all(n.nguoi_dung.username == "nongdan" for n in loc))
        r = self.ad.get("/nhat-ky/", {"tu_ngay": "2999-01-01"})
        self.da_thay(r, "Chưa có nhật ký.")
        self.assertEqual(r.context["paginator"].per_page, 20)


# ======================================================================================= Danh mục
class TestDanhMuc(KichBan):
    def test_tc_dm_01(self):
        r = self.nd.get("/danh-muc/cay-trong/")
        self.assertEqual((r.context["paginator"].count, len(r.context["page_obj"])), (12, 10))
        self.assertEqual(len(self.nd.get("/danh-muc/cay-trong/", {"page": 2}).context["page_obj"]), 2)
        self.da_thay(r, "Cây công nghiệp", "Cây ăn quả", "Cây ngắn ngày")
        html = r.content.decode()
        for nut in ("+ Thêm mới", "/sua/", "/xoa/"):
            self.assertNotIn(nut, html)
        html = self.bt.get("/danh-muc/cay-trong/").content.decode()
        for nut in ("+ Thêm mới", "/sua/", "/xoa/"):
            self.assertIn(nut, html)

    def test_tc_dm_02(self):
        ds = lambda q: [c.ma_cay for c in self.bt.get("/danh-muc/cay-trong/", {"q": q}).context["page_obj"]]
        self.assertEqual(ds("sầu"), ["SAU_RIENG"])
        self.assertEqual(ds("đậu"), ["LAC"])
        self.assertEqual(ds("sau"), ["SAU_RIENG"])  # khớp theo MÃ SAU_RIENG, không phải theo tên
        self.assertEqual(ds("dau"), [])  # Đậu phộng có mã LAC; tên có dấu nên không khớp «dau»
        self.da_thay(self.bt.get("/danh-muc/cay-trong/", {"q": "dau"}), "Chưa có dữ liệu.")
        self.assertEqual(ds("ho_tieu"), ["HO_TIEU"])

    def test_tc_dm_03(self):
        r = self.bt.post("/danh-muc/cay-trong/them/", {"ma_cay": "  mac_ca  ", "ten_cay": "Mắc ca", "nhom_cay": "CONG_NGHIEP", "dac_diem": ""}, follow=True)
        self.da_thay(r, "Đã lưu cây trồng «Mắc ca».", "MAC_CA")
        self.assertTrue(CayTrong.objects.filter(ma_cay="MAC_CA").exists())
        self.assertTrue(NhatKy.objects.filter(hanh_dong="Thêm danh mục").exists())

    def test_tc_dm_04(self):
        r = self.bt.post("/danh-muc/cay-trong/them/", {"ma_cay": " ca_phe", "ten_cay": "Cà phê trùng", "nhom_cay": "AN_QUA"})
        self.assertEqual(loi_form(r), ["Cây trồng có Mã cây đã tồn tại."])
        self.assertEqual(CayTrong.objects.filter(ma_cay="CA_PHE").count(), 1)

    def test_tc_dm_05(self):
        cay = CayTrong.objects.get(ma_cay="CAO_SU")
        r = self.bt.post(f"/danh-muc/cay-trong/{cay.pk}/sua/", {"ma_cay": "CAO_SU", "ten_cay": "Cao su (đã sửa)", "nhom_cay": "CONG_NGHIEP", "dac_diem": ""}, follow=True)
        self.da_thay(r, "Đã lưu cây trồng «Cao su (đã sửa)».")
        self.da_thay(self.bt.get(f"/danh-muc/cay-trong/{cay.pk}/xoa/"), "Xác nhận xóa")
        r = self.bt.post(f"/danh-muc/cay-trong/{cay.pk}/xoa/", follow=True)
        self.da_thay(r, "Đã xóa cây trồng «Cao su (đã sửa)».")
        self.assertFalse(CayTrong.objects.filter(pk=cay.pk).exists())
        self.assertEqual(set(NhatKy.objects.filter(hanh_dong__in=["Sửa danh mục", "Xóa danh mục"]).values_list("hanh_dong", flat=True)), {"Sửa danh mục", "Xóa danh mục"})

    def test_tc_dm_06(self):
        cay = CayTrong.objects.get(ma_cay="CA_PHE")
        NhatKy.objects.all().delete()
        r = self.bt.post(f"/danh-muc/cay-trong/{cay.pk}/xoa/", follow=True)
        self.da_thay(r, "Không thể xóa «Cà phê» vì đang được sử dụng bởi 1 luật tư vấn.")
        self.assertTrue(CayTrong.objects.filter(pk=cay.pk).exists())
        self.assertFalse(NhatKy.objects.filter(hanh_dong="Xóa danh mục").exists())

    def test_tc_dm_07(self):
        tinh = TinhThanh.objects.get(ma_tinh="DAK_LAK")
        r = self.bt.post(f"/danh-muc/tinh-thanh/{tinh.pk}/xoa/", follow=True)
        self.da_thay(r, "Không thể xóa «Đăk Lăk» vì đang được sử dụng bởi 2 luật tư vấn.")
        tl = TaiLieu.objects.get(ma_tl="TL_WASI_01")
        r = self.bt.post(f"/danh-muc/tai-lieu/{tl.pk}/xoa/", follow=True)
        self.da_thay(r, "Không thể xóa «Quy trình kỹ thuật trồng trọt cây công nghiệp và cây ăn quả Tây Nguyên» vì đang được sử dụng bởi 6 luật tư vấn.")
        self.assertTrue(TinhThanh.objects.filter(pk=tinh.pk).exists() and TaiLieu.objects.filter(pk=tl.pk).exists())

    def test_tc_dm_08(self):
        r = self.bt.post("/danh-muc/mua-vu/them/", {"ma_mua": "MUA_X", "ten_mua": "Mùa X", "thoi_gian_tu": 0, "thoi_gian_den": 13})
        self.assertEqual(loi_form(r), ["Đảm bảo giá trị này lớn hơn hoặc bằng với 1 .", "Đảm bảo giá trị này là nhỏ hơn hoặc bằng với 12 ."])
        self.assertFalse(MuaVu.objects.filter(ma_mua="MUA_X").exists())
        r = self.bt.post("/danh-muc/mua-vu/them/", {"ma_mua": "mua_thu", "ten_mua": "Mùa thu", "thoi_gian_tu": 1, "thoi_gian_den": 12}, follow=True)
        self.da_thay(r, "MUA_THU")
        self.assertTrue(MuaVu.objects.filter(ma_mua="MUA_THU").exists())


# ======================================================================================= Tư vấn
class TestTuVan(KichBan):
    def test_tc_tv_01(self):
        r = tu_van(self.nd)
        ls = LichSuTuVan.objects.get()
        self.assertRedirects(r, f"/tu-van/lich-su/{ls.pk}/")
        self.assertRegex(ls.ma_lstv, rf"^LS{HOM_NAY}-001$")
        t = van_ban(r)
        self.da_thay(r, f"Đã lưu vào lịch sử: {ls.ma_lstv}", "#1 · Sầu riêng Điểm 1,00", "#2 · Cà phê Điểm 0,88", "#3 · Hồ tiêu Điểm 0,75",
                     "Nhu cầu khớp 100% từ khóa của luật; luật áp dụng đúng cho Đăk Lăk; đúng Mùa mưa.", "100%",
                     "Quy trình kỹ thuật trồng trọt cây công nghiệp và cây ăn quả Tây Nguyên (WASI)",
                     "Hướng dẫn cơ cấu cây trồng theo mùa vụ tỉnh Đăk Lăk (Sở Nông nghiệp và Môi trường Đăk Lăk)")
        self.assertEqual(de_xuat(r), [("Sầu riêng", 1.0), ("Cà phê", 0.875), ("Hồ tiêu", 0.75)])
        html = r.content.decode()
        self.assertIn('value="DAK_LAK" selected', html)
        self.assertIn('value="MUA_MUA" selected', html)
        self.assertIn(NHU_CAU_CHINH, html)

    def test_tc_tv_02(self):
        t = van_ban(tu_van(self.nd))
        the_ca_phe = t[t.index("#2 · Cà phê") : t.index("#3 · Hồ tiêu")]
        for dong in ("Nhu cầu 0,5 0,75 0,375", "Tỉnh thành 0,3 1,00 0,300", "Mùa vụ 0,2 1,00 0,200", "Điểm phù hợp 0,875"):
            self.assertIn(dong, the_ca_phe)

    def test_tc_tv_03(self):
        tu_van(self.nd)
        truoc = LichSuTuVan.objects.count()
        r = self.nd.post("/tu-van/api-tinh-diem/", {"nhu_cau": NHU_CAU_CHINH, "tinh_thanh": "DAK_LAK", "mua_vu": "MUA_MUA"})
        d = r.json()
        self.assertEqual([x["ma_cay"] for x in d["ket_qua"]["de_xuat"]], ["SAU_RIENG", "CA_PHE", "HO_TIEU"])
        self.assertIn("Bản xem trước", d["html"])
        self.assertIn("chưa lưu", d["html"])
        self.assertEqual(LichSuTuVan.objects.count(), truoc)

    def test_tc_tv_04(self):
        r = tu_van(self.nd, mua="")
        self.assertEqual(de_xuat(r), [("Sầu riêng", 0.8), ("Hồ tiêu", 0.75), ("Cà phê", 0.675)])
        self.da_thay(r, "Điểm 0,80", "Điểm 0,75", "Điểm 0,68")

    def test_tc_tv_05(self):
        self.assertEqual(de_xuat(tu_van(self.nd, "Cây ăn quả giá trị cao", "LAM_DONG", "MUA_KHO")), [("Bơ", 1.0), ("Hồ tiêu", 0.5)])

    def test_tc_tv_06(self):
        self.assertEqual(de_xuat(tu_van(self.nd, "Cây ngắn ngày lương thực", "DAK_NONG")), [("Ngô", 1.0)])
        self.assertEqual(de_xuat(tu_van(self.nd, "Cây ngắn ngày lương thực", "GIA_LAI")), [("Sắn", 1.0)])

    def test_tc_tv_07(self):
        r = tu_van(self.nd, "giá cà phê ngày mai")
        self.da_thay(r, HAM_NGOAI_PHAM_VI)
        self.assertNotIn("Lý do:", van_ban(r))
        self.assertEqual(de_xuat(r), [])
        ds = self.nd.get("/tu-van/lich-su/")
        self.da_thay(ds, "Ngoài phạm vi")
        self.assertFalse(LichSuTuVan.objects.get().ket_qua_json["trong_pham_vi"])

    def test_tc_tv_08(self):
        self.bt.post("/danh-muc/tinh-thanh/them/", {"ma_tinh": "ha_noi", "ten_tinh": "Hà Nội", "vung_mien": "Đồng bằng sông Hồng"})
        self.assertTrue(TinhThanh.objects.filter(ma_tinh="HA_NOI").exists())
        r = tu_van(self.nd, tinh="HA_NOI")
        self.da_thay(r, HAM_NGOAI_PHAM_VI)
        self.assertEqual(de_xuat(r), [])

    def test_tc_tv_09(self):
        goc = {"nhu_cau": NHU_CAU_CHINH, "tinh_thanh": "DAK_LAK", "mua_vu": "MUA_MUA"}
        for ghi_de, mong in (({"tinh_thanh": ""}, "Trường này là bắt buộc."), ({"nhu_cau": "     "}, "Trường này là bắt buộc."),
                             ({"nhu_cau": "a" * 501}, "Giá trị này chỉ có tối đa 500 kí tự (hiện có 501)")):
            r = self.nd.post("/tu-van/", {**goc, **ghi_de})
            self.assertEqual(r.status_code, 200)
            self.assertEqual(loi_form(r), [mong])
        r = self.nd.post("/tu-van/", {**goc, "tinh_thanh": ""})
        self.assertIn('value="MUA_MUA" selected', r.content.decode())
        self.assertEqual(self.nd.post("/tu-van/", {**goc, "nhu_cau": "a" * 500}).status_code, 302)  # biên 500 hợp lệ
        self.assertEqual(LichSuTuVan.objects.count(), 1)  # chỉ lần hợp lệ duy nhất

    def test_tc_tv_10(self):
        tu_van(self.nd)
        tu_van(self.nd, "giá cà phê ngày mai")
        r = self.nd.get("/tu-van/lich-su/")
        self.assertEqual(len(r.context["ds_lich_su"]), 2)
        self.assertNotIn("<th>Người dùng</th>", r.content.decode())
        loc = self.nd.get("/tu-van/lich-su/", {"ket_qua": "ngoai"}).context["ds_lich_su"]
        self.assertEqual([x.nhu_cau for x in loc], ["giá cà phê ngày mai"])
        ls = LichSuTuVan.objects.get(nhu_cau=NHU_CAU_CHINH)
        r = self.nd.get(f"/tu-van/lich-su/{ls.pk}/")
        self.assertEqual(de_xuat(r), [("Sầu riêng", 1.0), ("Cà phê", 0.875), ("Hồ tiêu", 0.75)])
        self.assertIn('value="DAK_LAK" selected', r.content.decode())

    def test_tc_tv_11(self):
        tu_van(self.nd)
        tu_van(self.ad)
        ls_ad = LichSuTuVan.objects.get(nguoi_dung__username="admin")
        r = self.cg.get("/tu-van/lich-su/")
        self.assertEqual(len(r.context["ds_lich_su"]), 2)
        self.assertIn("<th>Người dùng</th>", r.content.decode())
        self.assertEqual(self.nd.get(f"/tu-van/lich-su/{ls_ad.pk}/").status_code, 404)
        self.assertEqual(self.cg.get(f"/tu-van/lich-su/{ls_ad.pk}/").status_code, 200)


# ======================================================================================= Truy xuất nguồn
class TestTruyXuat(KichBan):
    def link_nguon(self, r, ma_luat):
        h = re.search(rf'href="(/truy-xuat/\?ma={ma_luat}[^"]*)"', r.content.decode())
        self.assertIsNotNone(h, ma_luat)
        return html_lib.unescape(h.group(1))

    def test_tc_tx_01(self):
        r = tu_van(self.nd)
        ls = LichSuTuVan.objects.get()
        sr = self.nd.get(self.link_nguon(r, "LT20260101-001"))
        self.da_thay(sr, f"Truy xuất từ lần tư vấn {ls.ma_lstv}", "Luật LT20260101-001", "Đang áp dụng", "Sầu riêng", "Đăk Lăk", "Mùa mưa", "gia tri cao, kinh te cao",
                     "Quy trình kỹ thuật trồng trọt cây công nghiệp và cây ăn quả Tây Nguyên", "WASI", "TL_WASI_01")
        self.assertNotIn("Hệ số ưu tiên", van_ban(sr))
        cf = self.nd.get(self.link_nguon(r, "LT20260101-002"))
        self.da_thay(cf, "Sở Nông nghiệp và Môi trường Đăk Lăk", "Cà phê")
        self.da_thay(self.ad.get(self.link_nguon(r, "LT20260101-001")), "Hệ số ưu tiên")

    def test_tc_tx_02(self):
        r = self.nd.get("/truy-xuat/", {"ma": "LT-KHONG-CO"})
        self.assertEqual(r.status_code, 404)
        self.assertIn("Không tìm thấy luật có mã «LT-KHONG-CO».", van_ban(r))
        r = self.nd.get("/truy-xuat/")
        self.assertEqual(r.status_code, 200)
        self.assertIn('placeholder="Nhập mã luật, ví dụ LT20260101-001"', r.content.decode())
        self.assertNotIn("Luật LT", van_ban(r))


# ======================================================================================= Quản lý luật
class TestQuanLyLuat(KichBan):
    def form_luat(self, **ghi_de):
        d = {"cay_tro": CayTrong.objects.get(ma_cay="MIT").pk, "tinh_thanh": TinhThanh.objects.get(ma_tinh="DAK_LAK").pk,
             "mua_vu": MuaVu.objects.get(ma_mua="MUA_MUA").pk, "tu_khoa": "giá trị cao\nkinh tế cao", "score_weight": "1,5",
             "tai_lieu": TaiLieu.objects.get(ma_tl="TL_WASI_01").pk, "is_active": "on"}
        d.update(ghi_de)
        return d

    def test_tc_lu_01(self):
        ds = lambda **q: sorted(l.rule_id for l in self.bt.get("/tu-van/luat/", q).context["ds_luat"])
        self.assertEqual(ds(), [f"LT20260101-00{i}" for i in range(1, 8)])
        self.assertEqual(ds(trang_thai="tat"), ["LT20260101-007"])
        self.assertEqual(ds(cay="CA_PHE"), ["LT20260101-002"])
        self.assertEqual(ds(q="an qua"), ["LT20260101-004"])

    def test_tc_lu_02(self):
        r = self.bt.post("/tu-van/luat/them/", self.form_luat(), follow=True)
        self.da_thay(r, f"Đã lưu luật LT{HOM_NAY}-001.")
        r = tu_van(self.nd)
        self.assertEqual(de_xuat(r), [("Mít", 1.0), ("Sầu riêng", 1.0), ("Cà phê", 0.875), ("Hồ tiêu", 0.75)])  # bằng điểm: hệ số 1,5 > 1,00
        self.da_thay(r, "Điểm 1,00")

    def test_tc_lu_03(self):
        pk = LuatTuVan.objects.get(rule_id="LT20260101-001").pk
        r = self.bt.post(f"/tu-van/luat/{pk}/bat-tat/", follow=True)
        self.da_thay(r, "Đã tắt luật LT20260101-001.")
        self.assertEqual(de_xuat(tu_van(self.nd)), [("Cà phê", 0.875), ("Hồ tiêu", 0.75)])
        r = self.bt.post(f"/tu-van/luat/{pk}/bat-tat/", follow=True)
        self.da_thay(r, "Đã bật luật LT20260101-001.")
        self.assertEqual(de_xuat(tu_van(self.nd)), [("Sầu riêng", 1.0), ("Cà phê", 0.875), ("Hồ tiêu", 0.75)])
        self.assertTrue(NhatKy.objects.filter(hanh_dong="Tắt luật tư vấn").exists() and NhatKy.objects.filter(hanh_dong="Bật luật tư vấn").exists())

    def test_tc_lu_04(self):
        so_luat = LuatTuVan.objects.count()
        self.assertEqual(loi_form(self.bt.post("/tu-van/luat/them/", self.form_luat(tu_khoa=" , ;  "))), ["Nhập ít nhất một cụm từ khóa."])
        self.assertEqual(loi_form(self.bt.post("/tu-van/luat/them/", self.form_luat(score_weight="-1"))), ["Đảm bảo giá trị này lớn hơn hoặc bằng với 0 ."])
        r = self.bt.post("/tu-van/luat/them/", self.form_luat(score_weight="abc"))
        self.assertTrue(r.context["form"].errors["score_weight"])
        self.assertEqual(LuatTuVan.objects.count(), so_luat)

    def test_tc_lu_05(self):
        self.bt.post("/tu-van/luat/them/", self.form_luat())
        luat = LuatTuVan.objects.get(rule_id=f"LT{HOM_NAY}-001")
        r = tu_van(self.nd)
        self.assertIn("Mít", [x[0] for x in de_xuat(r)])
        ls = LichSuTuVan.objects.get()
        r = self.bt.post(f"/tu-van/luat/{luat.pk}/xoa/", follow=True)
        self.da_thay(r, f"Đã xóa luật LT{HOM_NAY}-001.")
        self.assertNotIn("Mít", [x[0] for x in de_xuat(tu_van(self.nd))])
        cu = self.nd.get(f"/tu-van/lich-su/{ls.pk}/")
        self.assertIn("Mít", [x[0] for x in de_xuat(cu)])
        nguon = self.nd.get(f"/truy-xuat/?ma=LT{HOM_NAY}-001&ls={ls.ma_lstv}")
        self.assertEqual(nguon.status_code, 200)
        self.da_thay(nguon, f"Luật LT{HOM_NAY}-001 đã bị xóa khỏi hệ thống. Dưới đây là nguồn đã lưu trong lịch sử tư vấn.", "WASI")
        self.assertTrue(NhatKy.objects.filter(hanh_dong="Xóa luật tư vấn").exists())


# ======================================================================================= Cấu hình trọng số
class TestCauHinhTrongSo(KichBan):
    def test_tc_ch_01(self):
        r = self.ad.get("/cau-hinh/")
        self.assertEqual(r.context["form"].initial, {"w1": "0,5", "w2": "0,3", "w3": "0,2"})
        self.da_thay(r, "w1 - Trọng số nhu cầu", "w2 - Trọng số tỉnh thành", "w3 - Trọng số mùa vụ")

    def test_tc_ch_02(self):
        truoc = de_xuat(tu_van(self.ad))
        for w in (("0,8", "0,1", "0,1"), ("0.8", "0.1", "0.1")):
            r = self.ad.post("/cau-hinh/", dict(zip(("w1", "w2", "w3"), w)), follow=True)
            self.da_thay(r, "Đã cập nhật trọng số.")
        sau = de_xuat(tu_van(self.ad))
        self.assertEqual(truoc, [("Sầu riêng", 1.0), ("Cà phê", 0.875), ("Hồ tiêu", 0.75)])
        self.assertEqual(sau, [("Sầu riêng", 1.0), ("Hồ tiêu", 0.9), ("Cà phê", 0.8)])
        nk = NhatKy.objects.filter(hanh_dong="Sửa trọng số").order_by("id").first()
        self.assertEqual(nk.chi_tiet, "w1: 0.5 → 0.8; w2: 0.3 → 0.1; w3: 0.2 → 0.1")

    def test_tc_ch_03(self):
        for w in (("0,8", "0,3", "0,1"), ("0,5", "0,3", "0,1")):
            r = self.ad.post("/cau-hinh/", dict(zip(("w1", "w2", "w3"), w)))
            self.assertEqual(loi_form(r), ["Tổng w1 + w2 + w3 phải bằng 1"])
            self.assertIn(f'value="{w[0]}"', r.content.decode())
        self.assertEqual(self.ad.get("/cau-hinh/").context["form"].initial, {"w1": "0,5", "w2": "0,3", "w3": "0,2"})

    def test_tc_ch_04(self):
        thu = lambda w1, w2, w3: loi_form(self.ad.post("/cau-hinh/", {"w1": w1, "w2": w2, "w3": w3}))
        self.assertEqual(thu("abc", "0,5", "0,5"), ["Phải là số, ví dụ 0,5."])
        self.assertEqual(thu("1,5", "-0,5", "0"), ["Trọng số w2 không được âm"])
        self.assertEqual(thu("", "0,5", "0,5"), ["Trường này là bắt buộc."])
        r = self.ad.post("/cau-hinh/", {"w1": "1", "w2": "0", "w3": "0"}, follow=True)
        self.da_thay(r, "Đã cập nhật trọng số.")

    def test_tc_ch_05(self):
        ls = tu_van(self.nd).context["lich_su"]
        self.ad.post("/cau-hinh/", {"w1": "0,8", "w2": "0,1", "w3": "0,1"})
        r = self.nd.get(f"/tu-van/lich-su/{ls.pk}/")
        self.assertEqual(de_xuat(r), [("Sầu riêng", 1.0), ("Cà phê", 0.875), ("Hồ tiêu", 0.75)])
        self.assertEqual(r.context["ket_qua"]["trong_so"], {"w1": 0.5, "w2": 0.3, "w3": 0.2})


# ======================================================================================= Tìm kiếm
class TestTimKiem(KichBan):
    def test_tc_tk_01(self):
        r = self.nd.get("/tim-kiem/", {"q": "ca phe"})
        self.da_thay(r, "Tìm thấy 2 kết quả cho «ca phe».", "Cây trồng (1)", "Cà phê", "Cây công nghiệp", "Kỹ thuật (1)", "Kỹ thuật tưới tiết kiệm nước cho cà phê")
        self.assertNotIn("Mùa vụ (", van_ban(r))
        self.assertEqual(LichSuTimKiem.objects.get().tu_khoa, "ca phe")

    def test_tc_tk_02(self):
        r = self.nd.get("/tim-kiem/", {"q": "mùa mưa"})
        kq = r.context["ket_qua"]
        self.assertEqual([m.ma_mua for m in kq["mua_vu"]], ["MUA_MUA"])
        self.assertEqual([k.ma_kt for k in kq["ky_thuat"]], ["KT_THOAT_SR"])
        self.assertEqual(sorted(c.ma_cay for c in kq["cay_trong"]), ["NGO", "SAU_RIENG"])
        self.da_thay(r, "từ tháng 5 đến tháng 10", "Làm rãnh thoát nước cho sầu riêng mùa mưa")
        r = self.nd.get("/tim-kiem/", {"q": "mua"})
        self.assertEqual(sorted(m.ma_mua for m in r.context["ket_qua"]["mua_vu"]), ["MUA_KHO", "MUA_MUA"])

    def test_tc_tk_03(self):
        r = self.nd.get("/tim-kiem/", {"q": "khong co gi het"})
        self.da_thay(r, "Không tìm thấy kết quả nào cho «khong co gi het». Thử từ khóa ngắn hơn hoặc viết không dấu.")
        self.assertEqual(LichSuTimKiem.objects.get().tu_khoa, "khong co gi het")

    def test_tc_tk_04(self):
        self.da_thay(self.nd.get("/tim-kiem/", {"q": "!!!"}), "Từ khóa phải có ít nhất một chữ cái hoặc chữ số.")
        self.assertEqual(LichSuTimKiem.objects.count(), 0)
        self.da_thay(self.nd.get("/tim-kiem/", {"q": ""}), "Nhập từ khóa để tra cứu. Không cần gõ dấu tiếng Việt.")
        r = self.nd.get("/tim-kiem/", {"q": "<script>alert(1)</script>"})
        self.assertNotIn("<script>alert(1)", r.content.decode())
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", r.content.decode())


# ======================================================================================= Hỏi đáp
class TestHoiDap(KichBan):
    def test_tc_hd_01(self):
        r = hoi(self.nd, "Kỹ thuật tưới nước cho cà phê mùa khô thế nào?")
        ch = CauHoi.objects.get()
        self.da_thay(r, f"Đã gửi câu hỏi {ch.ma_ch}. Chuyên gia sẽ trả lời sớm.", "Chờ trả lời", "Câu hỏi đang chờ chuyên gia trả lời.")
        self.assertEqual((ch.trang_thai, ch.ma_ch), ("CHO_TRA_LOI", f"CH{HOM_NAY}-001"))

    def test_tc_hd_02(self):
        hoi(self.nd, "Kỹ thuật tưới nước cho cà phê mùa khô thế nào?")
        ch = CauHoi.objects.get()
        self.da_thay(self.cg.get("/hoi-dap/"), "1 chờ trả lời")
        r = self.cg.post(f"/hoi-dap/{ch.pk}/tra-loi/", {"noi_dung": "Tưới 3-4 đợt mỗi mùa khô, mỗi đợt 450-600 lít/gốc."}, follow=True)
        self.da_thay(r, f"Đã trả lời câu hỏi {ch.ma_ch}.", "Đã trả lời")
        r = self.nd.get(f"/hoi-dap/{ch.pk}/")
        self.da_thay(r, "Tưới 3-4 đợt mỗi mùa khô, mỗi đợt 450-600 lít/gốc.", "Trả lời của Lê Chuyên Gia")
        self.assertTrue(NhatKy.objects.filter(hanh_dong="Trả lời câu hỏi").exists())

    def kiem_tra_ngoai(self, cau):
        r = hoi(self.nd, cau)
        ch = CauHoi.objects.get(noi_dung=cau)
        self.assertEqual(ch.trang_thai, "NGOAI_PHAM_VI")
        self.assertEqual((ch.tra_loi.noi_dung, ch.tra_loi.la_tu_dong), (HAM_NGOAI_PHAM_VI, True))
        self.da_thay(r, "Câu hỏi nằm ngoài phạm vi hỗ trợ nên đã được trả lời tự động.", "Ngoài phạm vi", "Trả lời tự động", HAM_NGOAI_PHAM_VI)

    def test_tc_hd_03(self):
        self.kiem_tra_ngoai("giá cà phê ngày mai")

    def test_tc_hd_04(self):
        self.kiem_tra_ngoai("Trồng cà phê ở Bình Phước được không?")
        self.kiem_tra_ngoai("Cà phê ở Hà Nội")

    def test_tc_hd_05(self):
        self.kiem_tra_ngoai("Hôm nay trời đẹp quá")
        self.kiem_tra_ngoai("Thời tiết Đăk Lăk ngày mai")

    def test_tc_hd_06(self):
        for cau in ("Trồng hồ tiêu ở Gia Lai cần lưu ý gì?", "Giá thể trồng sầu riêng nên dùng loại nào"):
            r = hoi(self.nd, cau)
            self.assertEqual(CauHoi.objects.get(noi_dung=cau).trang_thai, "CHO_TRA_LOI", cau)
            self.da_thay(r, "Chờ trả lời")

    def test_tc_hd_07(self):
        thu = lambda cau: loi_form(self.nd.post("/hoi-dap/them/", {"noi_dung": cau}))
        self.assertEqual(thu("cà"), ["Câu hỏi quá ngắn, vui lòng mô tả rõ hơn (ít nhất 5 ký tự)."])
        self.assertEqual(thu("      "), ["Trường này là bắt buộc."])
        self.assertEqual(thu("a" * 1001), ["Giá trị này chỉ có tối đa 1000 kí tự (hiện có 1001)"])
        self.assertEqual(CauHoi.objects.count(), 0)
        hoi(self.nd, "cà phê " * 143)  # 1001 ký tự nhưng dấu cách cuối bị cắt -> đúng 1000 ký tự, hợp lệ (biên)
        self.assertEqual(CauHoi.objects.count(), 1)

    def test_tc_hd_08(self):
        hoi(self.nd, "Kỹ thuật tưới nước cho cà phê mùa khô thế nào?")
        hoi(self.nd, "giá cà phê ngày mai")
        da_tra_loi, ngoai = CauHoi.objects.get(trang_thai="CHO_TRA_LOI"), CauHoi.objects.get(trang_thai="NGOAI_PHAM_VI")
        self.cg.post(f"/hoi-dap/{da_tra_loi.pk}/tra-loi/", {"noi_dung": "Đã xong"})
        for ch in (da_tra_loi, ngoai):
            r = self.cg.get(f"/hoi-dap/{ch.pk}/tra-loi/", follow=True)
            self.assertRedirects(r, f"/hoi-dap/{ch.pk}/")
            self.da_thay(r, "Câu hỏi này đã được xử lý, không thể trả lời nữa.")
            r = self.cg.post(f"/hoi-dap/{ch.pk}/tra-loi/", {"noi_dung": "Thêm"}, follow=True)
            self.da_thay(r, "Câu hỏi này đã được xử lý, không thể trả lời nữa.")
        self.assertEqual(TraLoi.objects.count(), 2)  # 1 của chuyên gia + 1 tự động, không có thêm


# ======================================================================================= Báo cáo, thống kê
class TestBaoCao(KichBan):
    def test_tc_bc_01(self):
        tu_van(self.nd)
        self.da_thay(self.ad.get("/bao-cao/"), "12 cây trồng", "6 luật đang bật", "Tổng 1 lần tư vấn")
        r = self.ad.get("/bao-cao/cay-trong/")
        self.assertRegex(r["Content-Disposition"], rf'filename="cay-trong_{HOM_NAY}\.xlsx"')
        tieu_de, dong = bang(xlsx(r)["Cây trồng"], "Mã cây")
        self.assertEqual(len(dong), 12)
        so_luat = {d[0]: d[4] for d in dong}
        self.assertEqual([so_luat[m] for m in ("SAU_RIENG", "CA_PHE", "HO_TIEU", "BO", "CHANH_DAY", "CAO_SU")], [1, 1, 1, 1, 0, 0])
        self.assertEqual({d[2] for d in dong}, {"Cây công nghiệp", "Cây ăn quả", "Cây ngắn ngày"})

    def test_tc_bc_02(self):
        ws = xlsx(self.ad.get("/bao-cao/luat-tu-van/"))["Luật tư vấn hiện hành"]
        _, dong = bang(ws, "Mã luật")
        self.assertEqual(len(dong), 6)
        self.assertNotIn("LT20260101-007", [d[0] for d in dong])
        ht = next(d for d in dong if d[0] == "LT20260101-003")
        self.assertEqual(ht[3:5], ["Mọi tỉnh", "Mọi mùa"])
        self.assertIsInstance(ht[6], (int, float))
        self.assertTrue(all(d[7] and d[8] for d in dong))

    def test_tc_bc_03(self):
        tu_van(self.nd)
        tu_van(self.nd, "giá cà phê ngày mai")
        hom_nay = f"{timezone.localdate():%Y-%m-%d}"
        ws = xlsx(self.ad.get("/bao-cao/lich-su-tu-van/", {"tu_ngay": hom_nay, "den_ngay": hom_nay}))["Lịch sử tư vấn"]
        d = f"{timezone.localdate():%d/%m/%Y}"
        self.assertEqual(ws["A1"].value, f"Khoảng thời gian: từ {d} đến {d}")
        _, dong = bang(ws, "Mã")
        self.assertEqual((len(dong), [x[6] for x in dong]), (2, ["Có đề xuất", "Ngoài phạm vi"]))
        self.assertTrue(hasattr(dong[0][1], "year"))  # ngày giờ thật
        r = self.ad.get("/bao-cao/lich-su-tu-van/", {"tu_ngay": "2026-10-10", "den_ngay": "2026-10-01"}, follow=True)
        self.assertRedirects(r, "/bao-cao/")
        self.da_thay(r, "Khoảng ngày không hợp lệ. Vui lòng chọn lại.")

    def test_tc_bc_04(self):
        tu_van(self.nd)
        tu_van(self.nd, "giá cà phê ngày mai")
        for q in ("ca phe", "ca phe", "sau rieng"):
            self.nd.get("/tim-kiem/", {"q": q})
        hoi(self.nd, "Kỹ thuật tưới nước cho cà phê mùa khô thế nào?")
        r = self.ad.get("/bao-cao/thong-ke/")
        self.assertEqual(r.context["tk"]["tu_van"]["tong"], 2)
        self.da_thay(r, "Lượt tư vấn", "50,0%", "Từ khóa tìm kiếm nhiều nhất", "ca phe", "Sầu riêng")
        _, dong = bang(xlsx(self.ad.get("/bao-cao/lich-su-tu-van/"))["Lịch sử tư vấn"], "Mã")
        self.assertEqual(len(dong), r.context["tk"]["tu_van"]["tong"])  # khớp số dòng Excel lịch sử
        x = self.ad.get("/bao-cao/thong-ke/", {"xuat": "xlsx"})
        wb = xlsx(x)
        self.assertEqual(len(wb.sheetnames), 6)
        o = {row[0].value: row[1] for row in wb["Tổng quan"].iter_rows() if row[0].value}
        self.assertEqual(o["Tỷ lệ tư vấn có đề xuất"].number_format, "0.0%")
        r = self.ad.get("/bao-cao/thong-ke/", {"tu_ngay": "2026-10-05", "den_ngay": "2026-10-01"})
        self.da_thay(r, "«Từ ngày» phải trước hoặc bằng «Đến ngày».")
        self.assertNotIn("tk", r.context)
        r = self.ad.get("/bao-cao/thong-ke/", {"tu_ngay": "2027-01-01", "den_ngay": "2027-01-31"})
        self.assertEqual(r.context["tk"]["tu_van"]["ty_le_trong_pham_vi"], None)
        self.assertIn("—", van_ban(r))
        self.assertNotIn("0,0%", van_ban(r))

    def test_tc_bc_05(self):
        for nhu_cau in ("=1+1 giá trị cao", "+1+1 giá trị cao", "-2+3 giá trị cao", "@SUM(A1) giá trị cao"):
            tu_van(self.nd, nhu_cau)
        ws = xlsx(self.ad.get("/bao-cao/lich-su-tu-van/"))["Lịch sử tư vấn"]
        o = [r[3] for r in ws.iter_rows(min_row=3)]
        self.assertEqual([x.value for x in o], ["=1+1 giá trị cao", "+1+1 giá trị cao", "-2+3 giá trị cao", "@SUM(A1) giá trị cao"])
        self.assertEqual({x.data_type for x in o}, {"s"})

    def test_tc_bc_06(self):
        NhatKy.objects.all().delete()
        self.ad.get("/bao-cao/thong-ke/")  # chỉ xem, không xuất
        self.assertFalse(NhatKy.objects.filter(hanh_dong="Xuất báo cáo").exists())
        for url in ("/bao-cao/cay-trong/", "/bao-cao/luat-tu-van/", "/bao-cao/lich-su-tu-van/", "/bao-cao/thong-ke/?xuat=xlsx"):
            self.ad.get(url)
        r = self.ad.get("/nhat-ky/", {"q": "Xuất báo cáo"})
        nk = {n.doi_tuong: n.chi_tiet for n in r.context["ds_nhat_ky"]}
        self.assertEqual(set(nk), {"BaoCao: cay-trong", "BaoCao: luat-tu-van", "BaoCao: lich-su-tu-van", "BaoCao: thong-ke"})
        self.assertEqual(nk["BaoCao: cay-trong"], "12 dòng")
        self.assertEqual(nk["BaoCao: luat-tu-van"], "6 dòng")


# ======================================================================================= Phân quyền tổng hợp
class TestPhanQuyen(KichBan):
    def test_tc_pq_01(self):
        self.assertEqual(ten_menu(self.ad), MENU_AD)
        self.assertEqual(ten_menu(self.bt), MENU_BT)
        self.assertEqual(ten_menu(self.cg), MENU_CG)
        self.assertEqual(ten_menu(self.nd), MENU_ND)
        con = lambda c: [x["ten"] for m in c.get("/").context["menu"] if m["ten"] == "Tư vấn" for x in m["nhom"]]
        self.assertEqual(con(self.ad), ["Tư vấn cây trồng", "Lịch sử tư vấn", "Luật tư vấn"])
        self.assertEqual(con(self.bt), ["Tư vấn cây trồng", "Lịch sử tư vấn", "Luật tư vấn"])
        self.assertEqual(con(self.cg), ["Tư vấn cây trồng", "Lịch sử tư vấn"])
        self.assertEqual(con(self.nd), ["Tư vấn cây trồng", "Lịch sử tư vấn"])

    def test_tc_pq_02(self):
        urls = ["/nguoi-dung/", "/nguoi-dung/them/", "/nhat-ky/", "/cau-hinh/", "/bao-cao/", "/bao-cao/thong-ke/", "/bao-cao/cay-trong/"]
        for c in (self.bt, self.cg, self.nd):
            for u in urls:
                r = c.get(u)
                self.assertEqual(r.status_code, 403, u)
        self.da_thay(self.nd.get("/nhat-ky/"), "Bạn không có quyền truy cập chức năng này.", "Về trang chủ")
        for u in urls:
            self.assertEqual(self.ad.get(u).status_code, 200, u)

    def test_tc_pq_03(self):
        pk = CayTrong.objects.first().pk
        for c in (self.cg, self.nd, self.bt):
            self.assertEqual(c.get("/danh-muc/cay-trong/").status_code, 200)
        for u in ("/danh-muc/cay-trong/them/", f"/danh-muc/cay-trong/{pk}/sua/", f"/danh-muc/cay-trong/{pk}/xoa/"):
            self.assertEqual([c.get(u).status_code for c in (self.cg, self.nd, self.bt)], [403, 403, 200], u)

    def test_tc_pq_04(self):
        for u in ("/tu-van/luat/", "/tu-van/luat/them/"):
            self.assertEqual([c.get(u).status_code for c in (self.cg, self.nd, self.bt, self.ad)], [403, 403, 200, 200], u)
        for u in ("/tu-van/", "/tu-van/lich-su/"):
            self.assertEqual([c.get(u).status_code for c in (self.cg, self.nd, self.bt, self.ad)], [200] * 4, u)

    def test_tc_pq_05(self):
        hoi(self.nd, "Kỹ thuật tưới nước cho cà phê mùa khô thế nào?")
        ch = CauHoi.objects.get()
        ng_khac = CauHoi.objects.create(ma_ch="CH-NK", nguoi_dung=NguoiDung.objects.get(username="admin"), noi_dung="Câu hỏi của người khác")
        self.assertEqual(self.bt.get("/hoi-dap/").status_code, 403)
        self.assertEqual(self.cg.get("/hoi-dap/them/").status_code, 403)
        self.assertEqual(self.ad.get("/hoi-dap/them/").status_code, 403)
        self.assertEqual(self.nd.get(f"/hoi-dap/{ch.pk}/tra-loi/").status_code, 403)
        self.assertEqual(self.nd.get(f"/hoi-dap/{ng_khac.pk}/").status_code, 404)
        r = self.ad.get(f"/hoi-dap/{ch.pk}/")
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("/tra-loi/", r.content.decode())

    def test_tc_pq_06(self):
        c = Client()
        self.assertEqual(c.get("/").status_code, 200)
        for u in ("/tu-van/", "/hoi-dap/", "/nguoi-dung/", "/bao-cao/", "/danh-muc/cay-trong/"):
            r = c.get(u)
            self.assertEqual((r.status_code, r["Location"]), (302, f"/dang-nhap/?next={u}"), u)
        r = c.post("/dang-nhap/?next=/nguoi-dung/", {"username": "admin", "password": MK, "next": "/nguoi-dung/"})
        self.assertRedirects(r, "/nguoi-dung/")


# ======================================================================================= Giao diện không mạng
class TestGiaoDienOffline(KichBan):
    def test_tc_ui_01(self):
        with override_settings(BOOTSTRAP_CUC_BO=True):
            html = self.nd.get("/").content.decode()
            self.assertNotIn("cdn.jsdelivr.net", html)
            self.assertIn("/static/vendor/bootstrap/bootstrap.min.css", html)
            self.assertNotIn("cdn.jsdelivr.net", Client().get("/dang-nhap/").content.decode())
