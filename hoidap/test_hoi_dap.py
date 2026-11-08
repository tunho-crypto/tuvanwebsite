"""Hỏi đáp: phân quyền, gửi câu hỏi, tự trả lời khi ngoài phạm vi, chuyên gia trả lời, hoàn tác, tranh chấp."""
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest import mock

from django.db import connection
from django.urls import reverse
from django.utils import timezone

from hoidap import services
from hoidap.models import CauHoi, TraLoi
from taikhoan.kiem_thu_chung import TestCaseDuLieuChung, TransactionTestCaseDuLieuChung
from taikhoan.models import NhatKy
from taikhoan.services import NghiepVuError
from tuvan.services import THONG_BAO_NGOAI_PHAM_VI

CAU_TRONG = "Kỹ thuật tưới nước cho cà phê mùa khô thế nào?"
CAU_NGOAI = "giá cà phê ngày mai"
HOM_NAY = f"{timezone.localdate():%Y%m%d}"
XEM = {"ADMIN", "CHUYEN_GIA", "NONG_DAN"}


class TestPhanQuyenHoiDap(TestCaseDuLieuChung):
    def setUp(self):
        self.ch = services.gui_cau_hoi(self.dl.nguoi_dung["NONG_DAN"], CAU_TRONG)

    def test_danh_sach_va_chi_tiet(self):
        self.kiem_tra_phan_quyen(reverse("hoidap:ds"), XEM)  # BIEN_TAP bị 403
        self.kiem_tra_phan_quyen(reverse("hoidap:chi_tiet", args=[self.ch.pk]), XEM)

    def test_chi_nong_dan_duoc_dat_cau_hoi(self):
        self.kiem_tra_phan_quyen(reverse("hoidap:them"), {"NONG_DAN"})
        so_luong = CauHoi.objects.count()
        self.kiem_tra_phan_quyen(reverse("hoidap:them"), {"NONG_DAN"}, "post", {"noi_dung": CAU_TRONG}, chi_bi_chan=True)
        self.assertEqual(CauHoi.objects.count(), so_luong)

    def test_chi_chuyen_gia_duoc_tra_loi(self):
        url = reverse("hoidap:tra_loi", args=[self.ch.pk])
        self.kiem_tra_phan_quyen(url, {"CHUYEN_GIA"})
        self.kiem_tra_phan_quyen(url, {"CHUYEN_GIA"}, "post", {"noi_dung": "Trả lời thử"}, chi_bi_chan=True)
        self.ch.refresh_from_db()
        self.assertEqual(self.ch.trang_thai, CauHoi.CHO_TRA_LOI)
        self.assertFalse(TraLoi.objects.exists())


class TestGuiCauHoi(TestCaseDuLieuChung):
    def setUp(self):
        self.nong_dan = self.dang_nhap_vai_tro("NONG_DAN")
        NhatKy.objects.all().delete()

    def test_cau_hoi_trong_pham_vi_cho_chuyen_gia(self):
        r = self.client.post(reverse("hoidap:them"), {"noi_dung": CAU_TRONG})
        ch = CauHoi.objects.get()
        self.assertRedirects(r, reverse("hoidap:chi_tiet", args=[ch.pk]))
        self.assertEqual((ch.ma_ch, ch.trang_thai, ch.nguoi_dung, ch.noi_dung), (f"CH{HOM_NAY}-001", "CHO_TRA_LOI", self.nong_dan, CAU_TRONG))
        self.assertFalse(TraLoi.objects.exists())
        self.assertEqual(NhatKy.objects.get().hanh_dong, "Gửi câu hỏi")

    def test_cau_hoi_ngoai_pham_vi_duoc_tra_loi_tu_dong_bang_cau_tieu_chuan(self):
        r = self.client.post(reverse("hoidap:them"), {"noi_dung": CAU_NGOAI}, follow=True)
        ch = CauHoi.objects.get()
        self.assertEqual(ch.trang_thai, CauHoi.NGOAI_PHAM_VI)
        tl = ch.tra_loi
        self.assertEqual((tl.noi_dung, tl.la_tu_dong, tl.nguoi_tra_loi), (THONG_BAO_NGOAI_PHAM_VI, True, None))
        self.assertContains(r, "Hệ thống chưa đủ thông tin dữ liệu về nội dung này trong phạm vi hỗ trợ")
        self.assertContains(r, "Trả lời tự động")
        self.assertContains(r, "nằm ngoài phạm vi hỗ trợ")  # thông báo cho người hỏi

    def test_tinh_ngoai_tay_nguyen_cung_ngoai_pham_vi(self):
        self.client.post(reverse("hoidap:them"), {"noi_dung": "Trồng cà phê ở Bình Phước được không?"})
        self.assertEqual(CauHoi.objects.get().trang_thai, CauHoi.NGOAI_PHAM_VI)

    def test_cau_hoi_ve_gia_lai_van_trong_pham_vi(self):
        self.client.post(reverse("hoidap:them"), {"noi_dung": "Trồng hồ tiêu ở Gia Lai cần lưu ý gì?"})
        self.assertEqual(CauHoi.objects.get().trang_thai, CauHoi.CHO_TRA_LOI)

    def test_cau_hoi_qua_ngan_bi_tu_choi_giu_noi_dung(self):
        r = self.client.post(reverse("hoidap:them"), {"noi_dung": "cà"})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["form"].errors["noi_dung"])
        self.assertEqual(CauHoi.objects.count(), 0)
        r = self.client.post(reverse("hoidap:them"), {"noi_dung": "   "})
        self.assertTrue(r.context["form"].errors["noi_dung"])

    def test_cau_hoi_qua_dai_bi_tu_choi(self):
        r = self.client.post(reverse("hoidap:them"), {"noi_dung": "cà phê " * 200})
        self.assertTrue(r.context["form"].errors["noi_dung"])

    def test_ma_cau_hoi_tang_dan(self):
        for _ in range(3):
            self.client.post(reverse("hoidap:them"), {"noi_dung": CAU_TRONG})
        self.assertEqual(list(CauHoi.objects.order_by("id").values_list("ma_ch", flat=True)), [f"CH{HOM_NAY}-00{i}" for i in (1, 2, 3)])

    def test_hoan_tac_khi_ghi_nhat_ky_loi_o_buoc_cuoi_ca_hai_nhanh(self):
        for cau in (CAU_TRONG, CAU_NGOAI):
            with mock.patch("hoidap.services.NhatKy.ghi", side_effect=RuntimeError("lỗi giả lập")):
                with self.assertRaises(RuntimeError):
                    services.gui_cau_hoi(self.nong_dan, cau)
        self.assertEqual((CauHoi.objects.count(), TraLoi.objects.count()), (0, 0))  # kể cả câu trả lời tự động cũng hoàn tác


class TestChuyenGiaTraLoi(TestCaseDuLieuChung):
    def setUp(self):
        self.nong_dan = self.dl.nguoi_dung["NONG_DAN"]
        self.chuyen_gia = self.dl.nguoi_dung["CHUYEN_GIA"]
        self.ch = services.gui_cau_hoi(self.nong_dan, CAU_TRONG)
        NhatKy.objects.all().delete()

    def test_tra_loi_thanh_cong_nong_dan_thay_cau_tra_loi(self):
        self.dang_nhap_vai_tro("CHUYEN_GIA")
        r = self.client.post(reverse("hoidap:tra_loi", args=[self.ch.pk]), {"noi_dung": "Tưới 3-4 đợt mỗi mùa khô."}, follow=True)
        self.assertContains(r, "Đã trả lời câu hỏi")
        self.ch.refresh_from_db()
        self.assertEqual(self.ch.trang_thai, CauHoi.DA_TRA_LOI)
        tl = self.ch.tra_loi
        self.assertEqual((tl.nguoi_tra_loi, tl.la_tu_dong), (self.chuyen_gia, False))
        self.assertEqual(NhatKy.objects.get(hanh_dong="Trả lời câu hỏi").nguoi_dung, self.chuyen_gia)
        self.dang_nhap_vai_tro("NONG_DAN")
        html = self.client.get(reverse("hoidap:chi_tiet", args=[self.ch.pk])).content.decode()
        self.assertIn("Tưới 3-4 đợt mỗi mùa khô.", html)
        self.assertIn("Lê Chuyên Gia", html)

    def test_tra_loi_rong_bi_tu_choi(self):
        self.dang_nhap_vai_tro("CHUYEN_GIA")
        r = self.client.post(reverse("hoidap:tra_loi", args=[self.ch.pk]), {"noi_dung": "   "})
        self.assertTrue(r.context["form"].errors["noi_dung"])
        self.assertFalse(TraLoi.objects.exists())

    def test_khong_tra_loi_hai_lan(self):
        services.tra_loi_cau_hoi(self.chuyen_gia, self.ch, "Lần một")
        with self.assertRaisesMessage(NghiepVuError, "đã được xử lý"):
            services.tra_loi_cau_hoi(self.chuyen_gia, self.ch, "Lần hai")
        self.assertEqual(TraLoi.objects.get().noi_dung, "Lần một")

    def test_khong_tra_loi_cau_ngoai_pham_vi_da_tu_dong_tra_loi(self):
        ngoai = services.gui_cau_hoi(self.nong_dan, CAU_NGOAI)
        with self.assertRaises(NghiepVuError):
            services.tra_loi_cau_hoi(self.chuyen_gia, ngoai, "Thử ghi đè")
        self.assertEqual(ngoai.tra_loi.noi_dung, THONG_BAO_NGOAI_PHAM_VI)

    def test_mo_trang_tra_loi_cho_cau_da_xu_ly_bi_chuyen_ve_chi_tiet(self):
        services.tra_loi_cau_hoi(self.chuyen_gia, self.ch, "Đã xong")
        self.dang_nhap_vai_tro("CHUYEN_GIA")
        r = self.client.get(reverse("hoidap:tra_loi", args=[self.ch.pk]), follow=True)
        self.assertContains(r, "đã được xử lý")

    def test_post_tra_loi_cho_cau_da_xu_ly_bao_loi_khong_them_ban_ghi(self):
        services.tra_loi_cau_hoi(self.chuyen_gia, self.ch, "Đã xong")
        self.dang_nhap_vai_tro("CHUYEN_GIA")
        r = self.client.post(reverse("hoidap:tra_loi", args=[self.ch.pk]), {"noi_dung": "Thêm"}, follow=True)
        self.assertContains(r, "đã được xử lý")
        self.assertEqual(TraLoi.objects.count(), 1)

    def test_nut_tra_loi_chi_hien_cho_chuyen_gia_khi_dang_cho(self):
        url = reverse("hoidap:chi_tiet", args=[self.ch.pk])
        self.dang_nhap_vai_tro("CHUYEN_GIA")
        self.assertContains(self.client.get(url), "/tra-loi/")
        self.dang_nhap_vai_tro("ADMIN")
        self.assertNotContains(self.client.get(url), "/tra-loi/")
        self.dang_nhap_vai_tro("NONG_DAN")
        self.assertNotContains(self.client.get(url), "/tra-loi/")

    def test_hoan_tac_khi_tra_loi_loi_o_buoc_cuoi(self):
        with mock.patch("hoidap.services.NhatKy.ghi", side_effect=RuntimeError("lỗi giả lập")):
            with self.assertRaises(RuntimeError):
                services.tra_loi_cau_hoi(self.chuyen_gia, self.ch, "Sẽ mất")
        self.ch.refresh_from_db()
        self.assertEqual(self.ch.trang_thai, CauHoi.CHO_TRA_LOI)
        self.assertFalse(TraLoi.objects.exists())


class TestDanhSachHoiDap(TestCaseDuLieuChung):
    def setUp(self):
        nd = self.dl.nguoi_dung
        self.a = services.gui_cau_hoi(nd["NONG_DAN"], CAU_TRONG)
        self.b = services.gui_cau_hoi(nd["NONG_DAN"], CAU_NGOAI)
        self.c = services.gui_cau_hoi(nd["ADMIN"], "Cách trồng sầu riêng ở Đăk Lăk")
        services.tra_loi_cau_hoi(nd["CHUYEN_GIA"], self.c, "Đã trả lời")

    def ds(self, ma_vai_tro, **loc):
        self.dang_nhap_vai_tro(ma_vai_tro)
        return {c.ma_ch for c in self.client.get(reverse("hoidap:ds"), loc).context["ds_cau_hoi"]}

    def test_nong_dan_chi_thay_cau_hoi_cua_minh(self):
        self.assertEqual(self.ds("NONG_DAN"), {self.a.ma_ch, self.b.ma_ch})

    def test_chuyen_gia_va_admin_thay_tat_ca(self):
        tat_ca = {self.a.ma_ch, self.b.ma_ch, self.c.ma_ch}
        self.assertEqual(self.ds("CHUYEN_GIA"), tat_ca)
        self.assertEqual(self.ds("ADMIN"), tat_ca)

    def test_loc_theo_trang_thai_va_tu_khoa(self):
        self.assertEqual(self.ds("CHUYEN_GIA", trang_thai="CHO_TRA_LOI"), {self.a.ma_ch})
        self.assertEqual(self.ds("CHUYEN_GIA", trang_thai="NGOAI_PHAM_VI"), {self.b.ma_ch})
        self.assertEqual(self.ds("CHUYEN_GIA", trang_thai="DA_TRA_LOI"), {self.c.ma_ch})
        self.assertEqual(self.ds("CHUYEN_GIA", q="sầu riêng"), {self.c.ma_ch})
        self.assertEqual(self.ds("CHUYEN_GIA", q=self.b.ma_ch), {self.b.ma_ch})
        self.assertEqual(len(self.ds("CHUYEN_GIA", trang_thai="khong-hop-le")), 3)  # giá trị lạ bị bỏ qua

    def test_dem_cau_hoi_cho_tra_loi(self):
        self.dang_nhap_vai_tro("CHUYEN_GIA")
        r = self.client.get(reverse("hoidap:ds"))
        self.assertEqual(r.context["so_cho_tra_loi"], 1)
        self.assertContains(r, "1 chờ trả lời")

    def test_nong_dan_khong_xem_duoc_cau_hoi_cua_nguoi_khac(self):
        self.dang_nhap_vai_tro("NONG_DAN")
        self.assertEqual(self.client.get(reverse("hoidap:chi_tiet", args=[self.c.pk])).status_code, 404)

    def test_cau_hoi_khong_ton_tai_404(self):
        self.dang_nhap_vai_tro("CHUYEN_GIA")
        self.assertEqual(self.client.get(reverse("hoidap:chi_tiet", args=[999999])).status_code, 404)
        self.assertEqual(self.client.get(reverse("hoidap:tra_loi", args=[999999])).status_code, 404)

    def test_chi_nong_dan_thay_nut_dat_cau_hoi(self):
        self.dang_nhap_vai_tro("NONG_DAN")
        self.assertContains(self.client.get(reverse("hoidap:ds")), "Đặt câu hỏi")
        self.dang_nhap_vai_tro("CHUYEN_GIA")
        self.assertNotContains(self.client.get(reverse("hoidap:ds")), "+ Đặt câu hỏi")


class TestTranhChapHoiDap(TransactionTestCaseDuLieuChung):
    def test_nhieu_chuyen_gia_cung_tra_loi_mot_cau_chi_mot_nguoi_thanh_cong(self):
        ch = services.gui_cau_hoi(self.dl.nguoi_dung["NONG_DAN"], CAU_TRONG)
        chuyen_gia_id = self.dl.nguoi_dung["CHUYEN_GIA"].pk
        so_luong = 5
        rao = threading.Barrier(so_luong)

        def chay(i):
            from taikhoan.models import NguoiDung

            try:
                rao.wait(timeout=15)
                services.tra_loi_cau_hoi(NguoiDung.objects.get(pk=chuyen_gia_id), ch, f"Trả lời số {i}")
                return "ok"
            except NghiepVuError:
                return "tu_choi"
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=so_luong) as ex:
            ket_qua = list(ex.map(chay, range(so_luong)))
        self.assertEqual(sorted(ket_qua), ["ok"] + ["tu_choi"] * (so_luong - 1))
        self.assertEqual(TraLoi.objects.count(), 1)
        ch.refresh_from_db()
        self.assertEqual(ch.trang_thai, CauHoi.DA_TRA_LOI)
        self.assertEqual(NhatKy.objects.filter(hanh_dong="Trả lời câu hỏi").count(), 1)

    def test_nhieu_nong_dan_cung_gui_cau_hoi_ma_khong_trung(self):
        nong_dan_id = self.dl.nguoi_dung["NONG_DAN"].pk
        so_luong, moi_luong = 5, 3
        rao = threading.Barrier(so_luong)

        def chay(i):
            from taikhoan.models import NguoiDung

            try:
                rao.wait(timeout=15)
                nd = NguoiDung.objects.get(pk=nong_dan_id)
                return [services.gui_cau_hoi(nd, CAU_TRONG if (i + j) % 2 else CAU_NGOAI).ma_ch for j in range(moi_luong)]
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=so_luong) as ex:
            cac_ma = [m for ds in ex.map(chay, range(so_luong)) for m in ds]
        tong = so_luong * moi_luong
        self.assertEqual(set(cac_ma), {f"CH{HOM_NAY}-{n:03d}" for n in range(1, tong + 1)})
        self.assertEqual(CauHoi.objects.count(), tong)
        # mỗi câu ngoài phạm vi có đúng một câu trả lời tự động
        self.assertEqual(TraLoi.objects.count(), CauHoi.objects.filter(trang_thai=CauHoi.NGOAI_PHAM_VI).count())
