"""Giao diện chạy được khi không có mạng: Bootstrap dự phòng cục bộ."""
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import override_settings
from django.urls import reverse

from taikhoan.kiem_thu_chung import TestCaseDuLieuChung

CDN = "cdn.jsdelivr.net"


class TestBootstrapDuPhong(TestCaseDuLieuChung):
    def setUp(self):
        self.dang_nhap_vai_tro("NONG_DAN")

    def test_file_cuc_bo_ton_tai_dung_phien_ban(self):
        for ten, dau in (("bootstrap.min.css", "Bootstrap  v5.3.3"), ("bootstrap.bundle.min.js", "Bootstrap v5.3.3")):
            duong_dan = finders.find(f"vendor/bootstrap/{ten}")
            self.assertIsNotNone(duong_dan, ten)
            noi_dung = Path(duong_dan).read_text(encoding="utf-8")
            self.assertGreater(len(noi_dung), 50_000, ten)
            self.assertIn(dau, noi_dung[:400], ten)
        self.assertTrue(Path(finders.find("vendor/bootstrap/LICENSE")).read_text().startswith("The MIT License"))

    def test_mac_dinh_dung_cdn_kem_du_phong_khi_loi(self):
        html = self.client.get(reverse("trang_chu")).content.decode()
        self.assertFalse(settings.BOOTSTRAP_CUC_BO)
        self.assertIn(f"https://{CDN}/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css", html)  # đúng ràng buộc «Bootstrap qua CDN»
        self.assertIn(f"https://{CDN}/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js", html)
        self.assertEqual(html.count(" onerror=\""), 2)  # cả CSS lẫn JS đều có đường lui (không đếm «this.onerror=null»)
        self.assertEqual(html.count("/static/vendor/bootstrap/"), 2)

    @override_settings(BOOTSTRAP_CUC_BO=True)
    def test_che_do_cuc_bo_khong_goi_cdn(self):
        html = self.client.get(reverse("trang_chu")).content.decode()
        self.assertNotIn(CDN, html)
        self.assertIn('href="/static/vendor/bootstrap/bootstrap.min.css"', html)
        self.assertIn('src="/static/vendor/bootstrap/bootstrap.bundle.min.js"', html)
        self.assertNotIn("onerror=", html)

    @override_settings(BOOTSTRAP_CUC_BO=True)
    def test_trang_dang_nhap_cung_khong_goi_cdn(self):
        self.client.logout()
        self.assertNotIn(CDN, self.client.get(reverse("dang_nhap")).content.decode())

    def test_moi_trang_chinh_render_duoc_voi_base_moi(self):
        for ten in ("trang_chu", "doi_mat_khau", "tuvan:tu_van", "tuvan:lich_su", "timkiem:tim_kiem", "truyxuat:truy_xuat", "hoidap:ds", "hoidap:them"):
            self.assertEqual(self.client.get(reverse(ten)).status_code, 200, ten)
