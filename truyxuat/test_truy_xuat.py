"""Truy xuất nguồn gốc: kết quả tư vấn -> luật -> tài liệu (quy tắc 10)."""
import html as html_lib
import re

from django.urls import reverse

from taikhoan.kiem_thu_chung import TAT_CA_VAI_TRO, TestCaseDuLieuChung
from tuvan import services
from tuvan.models import LuatTuVan

URL = "/truy-xuat/"
NHU_CAU = "Cây giá trị kinh tế cao"


class TestPhanQuyenTruyXuat(TestCaseDuLieuChung):
    def test_moi_vai_tro_duoc_truy_xuat(self):
        self.kiem_tra_phan_quyen(URL, set(TAT_CA_VAI_TRO))
        self.kiem_tra_phan_quyen(URL + "?ma=LT-SR", set(TAT_CA_VAI_TRO))


class TestTruyXuat(TestCaseDuLieuChung):
    def setUp(self):
        self.dang_nhap_vai_tro("NONG_DAN")

    def test_khong_nhap_ma_hien_form(self):
        r = self.client.get(URL)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Nhập mã luật")

    def test_hien_luat_va_tai_lieu(self):
        html = self.client.get(URL, {"ma": "LT-SR"}).content.decode()
        for cum in ("Luật LT-SR", "Sầu riêng", "Đăk Lăk", "Mùa mưa", "gia tri cao, kinh te cao", "Đang áp dụng", "Tài liệu kiểm thử", "WASI", "TL_TEST"):
            self.assertIn(cum, html, cum)

    def test_he_so_uu_tien_chi_hien_cho_admin_va_bien_tap(self):
        self.assertNotContains(self.client.get(URL, {"ma": "LT-SR"}), "Hệ số ưu tiên")
        for ma in ("ADMIN", "BIEN_TAP"):
            self.dang_nhap_vai_tro(ma)
            self.assertContains(self.client.get(URL, {"ma": "LT-SR"}), "Hệ số ưu tiên")

    def test_luat_chung_va_luat_tat(self):
        html = self.client.get(URL, {"ma": "LT-OFF"}).content.decode()
        self.assertIn("Đã ngừng áp dụng", html)
        html = self.client.get(URL, {"ma": "LT-HT"}).content.decode()
        self.assertIn("Mọi tỉnh", html)
        self.assertIn("Mọi mùa", html)

    def test_luat_khong_co_tai_lieu(self):
        LuatTuVan.objects.filter(rule_id="LT-SR").update(tai_lieu=None)
        self.assertContains(self.client.get(URL, {"ma": "LT-SR"}), "chưa được gắn tài liệu")

    def test_ma_khong_ton_tai_tra_404_co_thong_bao(self):
        r = self.client.get(URL, {"ma": "LT-KHONG-CO"})
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, "Không tìm thấy luật có mã", status_code=404)

    def test_ma_chua_ky_tu_la_duoc_escape(self):
        r = self.client.get(URL, {"ma": "<script>alert(1)</script>"})
        self.assertEqual(r.status_code, 404)
        self.assertNotContains(r, "<script>alert(1)", status_code=404)


class TestTruyXuatTuLichSu(TestCaseDuLieuChung):
    def setUp(self):
        self.nong_dan = self.dl.nguoi_dung["NONG_DAN"]
        self.ls = services.tu_van_va_luu(self.nong_dan, NHU_CAU, "DAK_LAK", "MUA_MUA")

    def test_di_tu_ket_qua_tu_van_den_tai_lieu_bang_link_xem_nguon(self):
        self.dang_nhap_vai_tro("NONG_DAN")
        trang = self.client.get(reverse("tuvan:lich_su_chi_tiet", args=[self.ls.pk])).content.decode()
        links = [html_lib.unescape(h) for h in re.findall(r'href="(/truy-xuat/\?[^"]+)"', trang)]
        self.assertEqual(len(links), 3)  # 3 đề xuất -> 3 link
        self.assertIn(f"/truy-xuat/?ma=LT-SR&ls={self.ls.ma_lstv}", links)
        r = self.client.get(links[0])
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "WASI")
        self.assertContains(r, self.ls.ma_lstv)  # có đường quay lại lần tư vấn
        self.assertContains(r, reverse("tuvan:lich_su_chi_tiet", args=[self.ls.pk]))

    def test_ban_xem_truoc_cung_co_link_xem_nguon_khong_kem_lich_su(self):
        self.dang_nhap_vai_tro("NONG_DAN")
        d = self.client.post(reverse("tuvan:api_tinh_diem"), {"nhu_cau": NHU_CAU, "tinh_thanh": "DAK_LAK", "mua_vu": "MUA_MUA"}).json()
        self.assertIn("/truy-xuat/?ma=LT-SR", d["html"])
        self.assertNotIn("&amp;ls=", d["html"])

    def test_khong_lo_lich_su_cua_nguoi_khac(self):
        self.dang_nhap_vai_tro("ADMIN")
        ls_admin = services.tu_van_va_luu(self.dl.nguoi_dung["ADMIN"], NHU_CAU, "DAK_LAK", "MUA_MUA")
        self.dang_nhap_vai_tro("NONG_DAN")
        r = self.client.get(URL, {"ma": "LT-SR", "ls": ls_admin.ma_lstv})
        self.assertEqual(r.status_code, 200)  # thông tin luật không bí mật
        self.assertNotContains(r, ls_admin.ma_lstv)  # nhưng lần tư vấn của người khác thì không hiện
        self.dang_nhap_vai_tro("CHUYEN_GIA")
        self.assertContains(self.client.get(URL, {"ma": "LT-SR", "ls": ls_admin.ma_lstv}), ls_admin.ma_lstv)

    def test_luat_da_bi_xoa_van_truy_xuat_duoc_nguon_tu_ban_chup(self):
        LuatTuVan.objects.filter(rule_id="LT-SR").delete()
        self.dang_nhap_vai_tro("NONG_DAN")
        r = self.client.get(URL, {"ma": "LT-SR", "ls": self.ls.ma_lstv})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "đã bị xóa khỏi hệ thống")
        self.assertContains(r, "WASI")
        self.assertContains(r, "Tài liệu kiểm thử")

    def test_luat_da_xoa_nhung_khong_co_lich_su_thi_404(self):
        LuatTuVan.objects.filter(rule_id="LT-SR").delete()
        self.dang_nhap_vai_tro("NONG_DAN")
        self.assertEqual(self.client.get(URL, {"ma": "LT-SR"}).status_code, 404)
        ls_khac = services.tu_van_va_luu(self.dl.nguoi_dung["ADMIN"], NHU_CAU, "DAK_LAK", "MUA_MUA")  # không phải của nông dân
        self.assertEqual(self.client.get(URL, {"ma": "LT-SR", "ls": ls_khac.ma_lstv}).status_code, 404)

    def test_canh_bao_khi_tai_lieu_da_doi_sau_lan_tu_van(self):
        LuatTuVan.objects.filter(rule_id="LT-SR").update(tai_lieu=None)
        self.dang_nhap_vai_tro("NONG_DAN")
        r = self.client.get(URL, {"ma": "LT-SR", "ls": self.ls.ma_lstv})
        self.assertContains(r, "đã được cập nhật sau lần tư vấn")
        self.assertContains(r, "Tài liệu kiểm thử (WASI)")  # nguồn tại thời điểm tư vấn

    def test_khong_canh_bao_khi_tai_lieu_khong_doi(self):
        self.dang_nhap_vai_tro("NONG_DAN")
        self.assertNotContains(self.client.get(URL, {"ma": "LT-SR", "ls": self.ls.ma_lstv}), "đã được cập nhật sau lần tư vấn")
