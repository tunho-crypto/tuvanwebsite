"""Cấu hình trọng số w1, w2, w3 (quy tắc 5): chỉ ADMIN, tổng bằng 1, trong transaction, ảnh hưởng kết quả tư vấn."""
import threading
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from unittest import mock

from django.db import connection
from django.urls import reverse

from cauhinh.models import CauHinhHeThong
from cauhinh.services import cap_nhat_trong_so, chuoi_trong_so
from taikhoan.kiem_thu_chung import TestCaseDuLieuChung, TransactionTestCaseDuLieuChung
from taikhoan.models import NhatKy
from tuvan.services import TrongSoKhongHopLe, lay_trong_so, tinh_diem_tu_van

URL = "/cau-hinh/"


def gia_tri():
    return dict(CauHinhHeThong.objects.values_list("ten_cau_hinh", "gia_tri"))


class TestPhanQuyenTrongSo(TestCaseDuLieuChung):
    def test_trang_chi_admin(self):
        self.kiem_tra_phan_quyen(URL, {"ADMIN"})

    def test_post_cua_vai_tro_khac_bi_chan_khong_doi_gi(self):
        self.kiem_tra_phan_quyen(URL, {"ADMIN"}, "post", {"w1": "0,8", "w2": "0,1", "w3": "0,1"}, chi_bi_chan=True)
        self.assertEqual(gia_tri(), {"w1": "0.5", "w2": "0.3", "w3": "0.2"})


class TestServiceTrongSo(TestCaseDuLieuChung):
    def setUp(self):
        self.admin = self.dl.nguoi_dung["ADMIN"]

    def test_cap_nhat_thanh_cong_va_ghi_nhat_ky_cu_moi(self):
        cap_nhat_trong_so(self.admin, "0.8", "0,1", Decimal("0.1"))
        self.assertEqual(gia_tri(), {"w1": "0.8", "w2": "0.1", "w3": "0.1"})
        nk = NhatKy.objects.get(hanh_dong="Sửa trọng số")
        self.assertEqual(nk.nguoi_dung, self.admin)
        self.assertEqual(nk.chi_tiet, "w1: 0.5 → 0.8; w2: 0.3 → 0.1; w3: 0.2 → 0.1")

    def test_tong_khac_1_bi_tu_choi_khong_doi_gi_khong_ghi_nhat_ky(self):
        for sai in (("0.5", "0.5", "0.5"), ("0.5", "0.3", "0.1"), ("1", "1", "-1")):
            with self.assertRaises(TrongSoKhongHopLe, msg=str(sai)):
                cap_nhat_trong_so(self.admin, *sai)
        self.assertEqual(gia_tri(), {"w1": "0.5", "w2": "0.3", "w3": "0.2"})
        self.assertEqual(NhatKy.objects.filter(hanh_dong="Sửa trọng số").count(), 0)

    def test_gia_tri_khong_phai_so_bi_tu_choi(self):
        with self.assertRaises(TrongSoKhongHopLe):
            cap_nhat_trong_so(self.admin, "abc", "0.5", "0.5")

    def test_chap_nhan_bien_hop_le(self):
        cap_nhat_trong_so(self.admin, "1", "0", "0")
        self.assertEqual(gia_tri(), {"w1": "1", "w2": "0", "w3": "0"})
        cap_nhat_trong_so(self.admin, "0.33", "0.33", "0.34")
        self.assertEqual(sum(lay_trong_so().values()), 1)

    def test_tao_moi_neu_thieu_dong_cau_hinh(self):
        CauHinhHeThong.objects.all().delete()
        cap_nhat_trong_so(self.admin, "0.6", "0.2", "0.2")
        self.assertEqual(gia_tri(), {"w1": "0.6", "w2": "0.2", "w3": "0.2"})

    def test_hoan_tac_khi_loi_o_buoc_cuoi(self):
        with mock.patch("cauhinh.services.NhatKy.ghi", side_effect=RuntimeError("lỗi giả lập")):
            with self.assertRaises(RuntimeError):
                cap_nhat_trong_so(self.admin, "0.8", "0.1", "0.1")
        self.assertEqual(gia_tri(), {"w1": "0.5", "w2": "0.3", "w3": "0.2"})  # cả ba giá trị đều quay về như cũ

    def test_chuoi_trong_so_gon(self):
        self.assertEqual([chuoi_trong_so(Decimal(x)) for x in ("0.80", "1.0", "0", "0.5")], ["0.8", "1", "0", "0.5"])

    def test_doi_trong_so_lam_doi_ket_qua_tu_van(self):
        args = ("Cây giá trị kinh tế cao", "Đăk Lăk", "Mùa mưa")
        truoc = tinh_diem_tu_van(*args)
        cap_nhat_trong_so(self.admin, "0.8", "0.1", "0.1")
        sau = tinh_diem_tu_van(*args)
        self.assertEqual([x["ma_cay"] for x in truoc["de_xuat"]], ["SAU_RIENG", "CA_PHE", "HO_TIEU"])
        self.assertEqual([(x["ma_cay"], x["diem"]) for x in sau["de_xuat"]], [("SAU_RIENG", 1.0), ("HO_TIEU", 0.9), ("CA_PHE", 0.8)])
        self.assertEqual(sau["trong_so"], {"w1": 0.8, "w2": 0.1, "w3": 0.1})


class TestViewTrongSo(TestCaseDuLieuChung):
    def setUp(self):
        self.dang_nhap_vai_tro("ADMIN")

    def test_form_hien_gia_tri_hien_tai_kieu_viet_nam(self):
        r = self.client.get(URL)
        self.assertEqual(r.context["form"].initial, {"w1": "0,5", "w2": "0,3", "w3": "0,2"})
        self.assertContains(r, "w1 - Trọng số nhu cầu")

    def test_luu_thanh_cong_chap_nhan_dau_phay(self):
        r = self.client.post(URL, {"w1": "0,8", "w2": "0,1", "w3": "0,1"}, follow=True)
        self.assertContains(r, "Đã cập nhật trọng số")
        self.assertEqual(gia_tri(), {"w1": "0.8", "w2": "0.1", "w3": "0.1"})

    def test_tong_khac_1_hien_loi_va_giu_gia_tri_da_nhap(self):
        r = self.client.post(URL, {"w1": "0,8", "w2": "0,3", "w3": "0,1"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Tổng w1 + w2 + w3 phải bằng 1")
        self.assertContains(r, 'value="0,8"')
        self.assertEqual(gia_tri(), {"w1": "0.5", "w2": "0.3", "w3": "0.2"})

    def test_khong_phai_so_bao_loi_tai_truong(self):
        r = self.client.post(URL, {"w1": "abc", "w2": "0,5", "w3": "0,5"})
        self.assertTrue(r.context["form"].errors["w1"])
        self.assertEqual(gia_tri(), {"w1": "0.5", "w2": "0.3", "w3": "0.2"})

    def test_truong_de_trong_bao_loi(self):
        r = self.client.post(URL, {"w1": "", "w2": "0,5", "w3": "0,5"})
        self.assertTrue(r.context["form"].errors["w1"])

    def test_cau_hinh_dang_hong_van_mo_duoc_trang_de_sua(self):
        CauHinhHeThong.objects.all().delete()
        r = self.client.get(URL)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["form"].initial, {})
        self.client.post(URL, {"w1": "0,5", "w2": "0,3", "w3": "0,2"})
        self.assertEqual(sum(lay_trong_so().values()), 1)


class TestTranhChapTrongSo(TransactionTestCaseDuLieuChung):
    def test_nhieu_admin_sua_cung_luc_ket_qua_luon_la_mot_bo_ba_nguyen_ven(self):
        cac_bo = [("0.5", "0.3", "0.2"), ("0.8", "0.1", "0.1"), ("0.2", "0.5", "0.3"), ("0.6", "0.2", "0.2"), ("0.1", "0.1", "0.8"), ("0.4", "0.4", "0.2")]
        admin_id = self.dl.nguoi_dung["ADMIN"].pk
        rao = threading.Barrier(len(cac_bo))

        def chay(bo):
            try:
                from taikhoan.models import NguoiDung

                rao.wait(timeout=15)
                for _ in range(3):
                    cap_nhat_trong_so(NguoiDung.objects.get(pk=admin_id), *bo)
                return bo
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=len(cac_bo)) as ex:
            list(ex.map(chay, cac_bo))
        cuoi = lay_trong_so()  # không ném lỗi nghĩa là tổng vẫn bằng 1
        self.assertIn(tuple(str(cuoi[k]) for k in ("w1", "w2", "w3")), cac_bo)  # không bao giờ trộn nửa bộ này nửa bộ kia
        nhat_ky = list(NhatKy.objects.filter(hanh_dong="Sửa trọng số").order_by("id"))
        self.assertEqual(len(nhat_ky), len(cac_bo) * 3)

        # Chuỗi nhật ký phải liền mạch: «mới» của lần trước đúng bằng «cũ» của lần sau (các lần sửa thật sự xếp hàng,
        # không có hai lần cùng đọc một giá trị cũ). Đây là điều khóa dòng (FOR UPDATE) bảo đảm.
        def doc(chi_tiet, vi_tri):
            return tuple(phan.split(": ")[1].split(" → ")[vi_tri] for phan in chi_tiet.split("; "))

        truoc = ("0.5", "0.3", "0.2")  # giá trị ban đầu của dữ liệu chung
        for nk in nhat_ky:
            self.assertEqual(doc(nk.chi_tiet, 0), truoc, nk.chi_tiet)
            truoc = doc(nk.chi_tiet, 1)
        self.assertEqual(truoc, tuple(str(cuoi[k]) for k in ("w1", "w2", "w3")))
