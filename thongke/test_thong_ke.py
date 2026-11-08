"""Thống kê với số liệu tính tay (xem tao_du_lieu_thong_ke trong taikhoan/kiem_thu_chung.py)."""
from datetime import date
from decimal import Decimal
from io import BytesIO

import openpyxl
from django.urls import reverse

from baocao.excel import MIME_XLSX
from taikhoan.kiem_thu_chung import TestCaseDuLieuChung, tao_du_lieu_thong_ke
from taikhoan.models import NhatKy
from thongke import services

D = Decimal
URL = "/bao-cao/thong-ke/"
THANG_10 = lambda ngay: date(2026, 10, ngay)


class TestThongKeTuVan(TestCaseDuLieuChung):
    def setUp(self):
        tao_du_lieu_thong_ke(self.dl)

    def test_tong_hop_toan_bo(self):
        tv = services.thong_ke_tu_van()
        self.assertEqual((tv["tong"], tv["trong_pham_vi"], tv["ngoai_pham_vi"]), (5, 3, 2))
        self.assertEqual(tv["ty_le_trong_pham_vi"], D("0.6"))

    def test_theo_tinh_theo_mua_theo_ngay(self):
        tv = services.thong_ke_tu_van()
        self.assertEqual(tv["theo_tinh"], [("Đăk Lăk", 3), ("Gia Lai", 1), ("Lâm Đồng", 1)])
        self.assertEqual(tv["theo_mua"], [("Mùa mưa", 3), ("Không chọn mùa", 1), ("Mùa khô", 1)])
        self.assertEqual(tv["theo_ngay"], [(THANG_10(1), 2), (THANG_10(2), 1), (THANG_10(5), 2)])

    def test_cay_duoc_de_xuat_xep_theo_hang_1_roi_so_lan_xuat_hien(self):
        cay = services.thong_ke_tu_van()["cay_duoc_de_xuat"]
        self.assertEqual(
            [(c["ma_cay"], c["so_lan_hang_1"], c["so_lan_xuat_hien"]) for c in cay],
            [("SAU_RIENG", 2, 2), ("BO", 1, 1), ("HO_TIEU", 0, 2), ("CA_PHE", 0, 1)],
        )
        self.assertEqual(cay[0]["ten_cay"], "Sầu riêng")

    def test_lan_tu_van_ngoai_pham_vi_khong_bao_gio_dong_gop_vao_cay_de_xuat(self):
        from tuvan.models import LichSuTuVan

        # dữ liệu «lệch» (ngoài phạm vi nhưng còn sót danh sách đề xuất): vẫn không được tính
        ls = LichSuTuVan.objects.get(ma_lstv="LS-T4")
        ls.ket_qua_json["de_xuat"] = [{"thu_hang": 1, "ma_cay": "CHANH_DAY", "ten_cay": "Chanh dây", "diem": 1.0}]
        ls.save()
        self.assertNotIn("CHANH_DAY", [c["ma_cay"] for c in services.thong_ke_tu_van()["cay_duoc_de_xuat"]])

    def test_loc_tu_ngay(self):
        tv = services.thong_ke_tu_van(tu_ngay=THANG_10(2))
        self.assertEqual((tv["tong"], tv["trong_pham_vi"], tv["ngoai_pham_vi"]), (3, 1, 2))
        self.assertEqual(tv["ty_le_trong_pham_vi"], D("0.3333"))

    def test_loc_den_ngay(self):
        tv = services.thong_ke_tu_van(den_ngay=THANG_10(1))
        self.assertEqual((tv["tong"], tv["ty_le_trong_pham_vi"]), (2, D("1.0")))

    def test_loc_hai_dau_deu_gom_ca_ngay_bien(self):
        self.assertEqual(services.thong_ke_tu_van(THANG_10(1), THANG_10(1))["tong"], 2)
        tv = services.thong_ke_tu_van(THANG_10(2), THANG_10(2))
        self.assertEqual((tv["tong"], [c["ma_cay"] for c in tv["cay_duoc_de_xuat"]]), (1, ["BO", "HO_TIEU"]))

    def test_khong_co_du_lieu_thi_ty_le_la_none_khong_phai_0(self):
        tv = services.thong_ke_tu_van(date(2027, 1, 1), date(2027, 1, 31))
        self.assertEqual((tv["tong"], tv["ty_le_trong_pham_vi"], tv["theo_tinh"], tv["theo_ngay"], tv["cay_duoc_de_xuat"]), (0, None, [], [], []))


class TestThongKeHoiDap(TestCaseDuLieuChung):
    def setUp(self):
        tao_du_lieu_thong_ke(self.dl)

    def test_tong_hop(self):
        hd = services.thong_ke_hoi_dap()
        self.assertEqual((hd["tong"], hd["da_tra_loi"], hd["cho_tra_loi"], hd["ngoai_pham_vi"]), (6, 2, 1, 3))
        self.assertEqual(hd["ty_le_da_tra_loi"], D("0.6667"))  # 2 / (2 + 1): chuyên gia đã trả lời trên câu hỏi trong phạm vi
        self.assertEqual(hd["ty_le_co_tra_loi"], D("0.8333"))  # (2 + 3) / 6: có câu trả lời kể cả tự động
        self.assertEqual(hd["ty_le_ngoai_pham_vi"], D("0.5"))

    def test_loc_ngay(self):
        hd = services.thong_ke_hoi_dap(tu_ngay=THANG_10(2))
        self.assertEqual((hd["tong"], hd["da_tra_loi"], hd["cho_tra_loi"], hd["ngoai_pham_vi"]), (4, 1, 1, 2))
        self.assertEqual((hd["ty_le_da_tra_loi"], hd["ty_le_co_tra_loi"]), (D("0.5"), D("0.75")))
        hd = services.thong_ke_hoi_dap(den_ngay=THANG_10(1))
        self.assertEqual((hd["ty_le_da_tra_loi"], hd["ty_le_co_tra_loi"]), (D("1.0"), D("1.0")))

    def test_chi_co_cau_ngoai_pham_vi_thi_ty_le_chuyen_gia_la_none(self):
        hd = services.thong_ke_hoi_dap(THANG_10(5), THANG_10(5))  # CH-T5 chờ, CH-T6 ngoài -> da = 0, cho = 1
        self.assertEqual((hd["da_tra_loi"], hd["ty_le_da_tra_loi"]), (0, D("0.0")))
        from hoidap.models import CauHoi

        CauHoi.objects.filter(trang_thai=CauHoi.CHO_TRA_LOI).delete()
        hd = services.thong_ke_hoi_dap(THANG_10(5), THANG_10(5))
        self.assertEqual((hd["tong"], hd["ty_le_da_tra_loi"], hd["ty_le_co_tra_loi"]), (1, None, D("1.0")))

    def test_khong_co_cau_hoi(self):
        hd = services.thong_ke_hoi_dap(date(2027, 1, 1))
        self.assertEqual((hd["tong"], hd["ty_le_da_tra_loi"], hd["ty_le_co_tra_loi"], hd["ty_le_ngoai_pham_vi"]), (0, None, None, None))


class TestThongKeTimKiem(TestCaseDuLieuChung):
    def setUp(self):
        tao_du_lieu_thong_ke(self.dl)

    def test_top_gop_cac_cach_viet_va_bo_tu_khoa_chi_ky_hieu(self):
        tk = services.thong_ke_tim_kiem()
        self.assertEqual((tk["tong"], tk["so_tu_khoa_khac_nhau"]), (9, 4))  # «!!!» không tính
        self.assertEqual(
            [(t["tu_khoa"], t["so_lan"]) for t in tk["top"]],
            [("ca phe", 4), ("ho tieu", 2), ("sau rieng", 2), ("mua mua", 1)],  # «ca phe» gộp cả «Cà phê»; bằng nhau xếp theo chữ cái
        )

    def test_gioi_han_top(self):
        self.assertEqual(len(services.thong_ke_tim_kiem(top=2)["top"]), 2)
        self.assertEqual([t["tu_khoa"] for t in services.thong_ke_tim_kiem(top=1)["top"]], ["ca phe"])

    def test_loc_ngay(self):
        tk = services.thong_ke_tim_kiem(tu_ngay=THANG_10(2))
        self.assertEqual(tk["tong"], 6)
        self.assertEqual([(t["tu_khoa"], t["so_lan"]) for t in tk["top"]], [("ca phe", 2), ("ho tieu", 2), ("mua mua", 1), ("sau rieng", 1)])

    def test_khong_co_du_lieu(self):
        self.assertEqual(services.thong_ke_tim_kiem(date(2027, 1, 1)), {"tong": 0, "so_tu_khoa_khac_nhau": 0, "top": []})

    def test_hien_thi_dang_viet_pho_bien_nhat(self):
        from timkiem.models import LichSuTimKiem

        for i in range(3):
            LichSuTimKiem.objects.create(ma_ls=f"TK-X{i}", tu_khoa="Cà Phê")
        # nhóm «ca phe» nay có 3 «ca phe», 1 «Cà phê», 3 «Cà Phê»: viết thường «cà phê» xuất hiện 4 lần > «ca phe» 3 lần
        top = services.thong_ke_tim_kiem()["top"][0]
        self.assertEqual((top["tu_khoa"], top["so_lan"]), ("cà phê", 7))


def doc_xlsx(phan_hoi):
    return openpyxl.load_workbook(BytesIO(phan_hoi.content))



class TestViewThongKe(TestCaseDuLieuChung):
    def setUp(self):
        tao_du_lieu_thong_ke(self.dl)
        self.dang_nhap_vai_tro("ADMIN")

    def test_chi_admin(self):
        self.kiem_tra_phan_quyen(URL, {"ADMIN"})
        self.kiem_tra_phan_quyen(URL + "?xuat=xlsx", {"ADMIN"}, ma_thanh_cong=200)

    def test_hien_cac_con_so_chinh(self):
        r = self.client.get(URL)
        html = r.content.decode()
        for cum in ("Lượt tư vấn", "60,0%", "66,7%", "Đăk Lăk", "Sầu riêng", "Từ khóa tìm kiếm nhiều nhất", "ca phe", "Tư vấn có đề xuất"):
            self.assertIn(cum, html, cum)
        self.assertEqual(r.context["tk"]["tu_van"]["tong"], 5)

    def test_thanh_tien_do_dung_dau_cham(self):
        html = self.client.get(URL).content.decode()
        self.assertIn("width: 60.00%", html)  # dấu chấm, không phải «60,00%» (sai CSS)
        self.assertIn("width: 66.67%", html)

    def test_loc_ngay_va_giu_bo_loc_trong_link_xuat(self):
        r = self.client.get(URL, {"tu_ngay": "2026-10-02", "den_ngay": "2026-10-05"})
        self.assertEqual(r.context["tk"]["tu_van"]["tong"], 3)
        self.assertIn("tu_ngay=2026-10-02", r.context["query_xuat"])
        self.assertIn("xuat=xlsx", r.context["query_xuat"])
        self.assertContains(r, 'value="2026-10-02"')  # form giữ lại ngày đã chọn

    def test_chap_nhan_ngay_kieu_viet_nam(self):
        r = self.client.get(URL, {"tu_ngay": "02/10/2026"})
        self.assertEqual(r.context["tk"]["tu_van"]["tong"], 3)

    def test_khoang_ngay_nguoc_hien_loi_khong_tinh_khong_xuat_file(self):
        for them in ({}, {"xuat": "xlsx"}):
            r = self.client.get(URL, {"tu_ngay": "2026-10-05", "den_ngay": "2026-10-01", **them})
            self.assertEqual(r.status_code, 200)
            self.assertContains(r, "phải trước hoặc bằng")
            self.assertNotIn("tk", r.context)
            self.assertEqual(r["Content-Type"].split(";")[0], "text/html")

    def test_ngay_rac_bi_tu_choi(self):
        r = self.client.get(URL, {"tu_ngay": "khong-phai-ngay", "xuat": "xlsx"})
        self.assertEqual(r["Content-Type"].split(";")[0], "text/html")
        self.assertTrue(r.context["form"].errors["tu_ngay"])

    def test_khong_co_du_lieu_hien_gach_thay_vi_0_phan_tram(self):
        r = self.client.get(URL, {"tu_ngay": "2027-01-01"})
        self.assertContains(r, "—")
        self.assertNotContains(r, "0,0%")


class TestXuatThongKeExcel(TestCaseDuLieuChung):
    def setUp(self):
        tao_du_lieu_thong_ke(self.dl)
        self.dang_nhap_vai_tro("ADMIN")

    def test_tep_excel_dung_loai_ten_va_cac_sheet(self):
        r = self.client.get(URL, {"xuat": "xlsx"})
        self.assertEqual(r["Content-Type"], MIME_XLSX)
        self.assertRegex(r["Content-Disposition"], r'^attachment; filename="thong-ke_\d{8}\.xlsx"$')
        self.assertEqual(
            doc_xlsx(r).sheetnames,
            ["Tổng quan", "Tư vấn theo tỉnh", "Tư vấn theo mùa", "Tư vấn theo ngày", "Cây được đề xuất", "Từ khóa tìm nhiều nhất"],
        )

    def test_sheet_tong_quan_co_so_va_ty_le_dung_dinh_dang(self):
        ws = doc_xlsx(self.client.get(URL, {"xuat": "xlsx"}))["Tổng quan"]
        o = {r[0].value: r[1] for r in ws.iter_rows() if r[0].value}
        self.assertEqual(o["Số lượt tư vấn"].value, 5)
        self.assertEqual(o["Số câu hỏi"].value, 6)
        ty_le = o["Tỷ lệ tư vấn có đề xuất"]
        self.assertAlmostEqual(float(ty_le.value), 0.6)
        self.assertEqual(ty_le.number_format, "0.0%")  # Excel hiển thị 60.0%, giá trị gốc vẫn là số 0.6
        self.assertAlmostEqual(float(o["Tỷ lệ chuyên gia đã trả lời (trên câu hỏi trong phạm vi)"].value), 0.6667)
        self.assertEqual(o["Số lượt tư vấn"].number_format, "General")  # số đếm không bị định dạng %

    def test_ghi_chu_khoang_thoi_gian_va_loc_theo_ngay(self):
        r = self.client.get(URL, {"xuat": "xlsx", "tu_ngay": "2026-10-02", "den_ngay": "2026-10-05"})
        wb = doc_xlsx(r)
        self.assertEqual(wb["Tổng quan"]["A1"].value, "Khoảng thời gian: từ 02/10/2026 đến 05/10/2026")
        o = {row[0].value: row[1].value for row in wb["Tổng quan"].iter_rows() if row[0].value}
        self.assertEqual(o["Số lượt tư vấn"], 3)

    def test_cac_sheet_con_lai(self):
        wb = doc_xlsx(self.client.get(URL, {"xuat": "xlsx"}))
        tinh = [[c.value for c in r] for r in wb["Tư vấn theo tỉnh"].iter_rows(min_row=3)]
        self.assertEqual(tinh, [["Đăk Lăk", 3], ["Gia Lai", 1], ["Lâm Đồng", 1]])
        cay = [[c.value for c in r] for r in wb["Cây được đề xuất"].iter_rows(min_row=3)]
        self.assertEqual(cay[0], ["SAU_RIENG", "Sầu riêng", 2, 2])
        tu_khoa = [[c.value for c in r] for r in wb["Từ khóa tìm nhiều nhất"].iter_rows(min_row=3)]
        self.assertEqual(tu_khoa[0], [1, "ca phe", 4])
        ngay = [[c.value for c in r] for r in wb["Tư vấn theo ngày"].iter_rows(min_row=3)]
        self.assertEqual([n[1] for n in ngay], [2, 1, 2])
        self.assertEqual(wb["Tư vấn theo ngày"]["A3"].number_format, "dd/mm/yyyy")

    def test_xuat_ghi_nhat_ky(self):
        NhatKy.objects.all().delete()
        self.client.get(URL, {"xuat": "xlsx"})
        nk = NhatKy.objects.get(hanh_dong="Xuất báo cáo")
        self.assertEqual((nk.doi_tuong, nk.nguoi_dung), ("BaoCao: thong-ke", self.dl.nguoi_dung["ADMIN"]))

    def test_chi_xem_trang_khong_ghi_nhat_ky_xuat(self):
        NhatKy.objects.all().delete()
        self.client.get(URL)
        self.assertFalse(NhatKy.objects.filter(hanh_dong="Xuất báo cáo").exists())

    def test_xuat_khi_khong_co_du_lieu_van_ra_tep_hop_le(self):
        r = self.client.get(URL, {"xuat": "xlsx", "tu_ngay": "2027-01-01"})
        wb = doc_xlsx(r)
        o = {row[0].value: row[1] for row in wb["Tổng quan"].iter_rows() if row[0].value}
        self.assertEqual(o["Số lượt tư vấn"].value, 0)
        self.assertIsNone(o["Tỷ lệ tư vấn có đề xuất"].value)  # ô trống, không phải 0%
