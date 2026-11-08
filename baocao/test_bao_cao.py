"""Báo cáo Excel: phân quyền, nội dung, lọc ngày, an toàn dữ liệu người dùng, không N+1, nhật ký."""
from datetime import datetime
from io import BytesIO

import openpyxl
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from baocao import excel
from baocao.excel import MIME_XLSX
from taikhoan.kiem_thu_chung import TestCaseDuLieuChung, gio, tao_du_lieu_thong_ke
from taikhoan.models import NhatKy
from tuvan.models import LichSuTuVan, LuatTuVan
from tuvan.services import THONG_BAO_NGOAI_PHAM_VI

URL_CAY, URL_LUAT, URL_LICH_SU = "/bao-cao/cay-trong/", "/bao-cao/luat-tu-van/", "/bao-cao/lich-su-tu-van/"


def mo(phan_hoi):
    return openpyxl.load_workbook(BytesIO(phan_hoi.content))


def bang(ws, o_dau):
    """(tiêu đề, các dòng dữ liệu) của sheet; tìm dòng tiêu đề theo ô đầu (bỏ qua dòng ghi chú phía trên)."""
    dong = [[c.value for c in r] for r in ws.iter_rows()]
    i = next(k for k, r in enumerate(dong) if r[0] == o_dau)
    return dong[i], dong[i + 1 :]


class TestPhanQuyenBaoCao(TestCaseDuLieuChung):
    def test_trang_bao_cao_va_cac_tep_chi_admin(self):
        for url in ("/bao-cao/", URL_CAY, URL_LUAT, URL_LICH_SU, "/bao-cao/thong-ke/"):
            with self.subTest(url=url):
                self.kiem_tra_phan_quyen(url, {"ADMIN"})

    def test_bien_tap_cung_khong_duoc_xuat(self):
        self.dang_nhap_vai_tro("BIEN_TAP")
        for url in (URL_CAY, URL_LUAT, URL_LICH_SU):
            self.assertEqual(self.client.get(url).status_code, 403)

    def test_chua_dang_nhap_khong_tai_duoc_tep(self):
        r = self.client.get(URL_LICH_SU)
        self.assertEqual(r.status_code, 302)
        self.assertNotEqual(r.get("Content-Type"), MIME_XLSX)


class TestTrangBaoCao(TestCaseDuLieuChung):
    def test_hien_so_luong_va_cac_nut_tai(self):
        tao_du_lieu_thong_ke(self.dl)
        self.dang_nhap_vai_tro("ADMIN")
        r = self.client.get("/bao-cao/")
        self.assertEqual((r.context["so_cay"], r.context["so_luat"], r.context["so_lich_su"]), (12, 4, 5))  # LT-OFF đang tắt nên không tính
        for url in (URL_CAY, URL_LUAT, URL_LICH_SU, "/bao-cao/thong-ke/"):
            self.assertContains(r, f'href="{url}"' if url != URL_LICH_SU else f'action="{url}"')


class TestXuatCayTrong(TestCaseDuLieuChung):
    def setUp(self):
        self.dang_nhap_vai_tro("ADMIN")
        self.r = self.client.get(URL_CAY)

    def test_dau_ra_la_excel_voi_ten_tep_co_ngay(self):
        self.assertEqual(self.r["Content-Type"], MIME_XLSX)
        self.assertRegex(self.r["Content-Disposition"], r'^attachment; filename="cay-trong_\d{8}\.xlsx"$')

    def test_du_12_cay_va_so_luat_dang_ap_dung(self):
        tieu_de, dong = bang(mo(self.r)["Cây trồng"], "Mã cây")
        self.assertEqual(tieu_de, ["Mã cây", "Tên cây", "Nhóm cây", "Đặc điểm", "Số luật đang áp dụng"])
        self.assertEqual(len(dong), 12)
        theo_ma = {d[0]: d for d in dong}
        self.assertEqual(theo_ma["SAU_RIENG"][1:3], ["Sầu riêng", "Cây ăn quả"])  # nhãn tiếng Việt, không phải mã
        self.assertEqual([theo_ma[m][4] for m in ("SAU_RIENG", "CA_PHE", "HO_TIEU", "BO")], [1, 1, 1, 1])
        self.assertEqual(theo_ma["CHANH_DAY"][4], 0)  # luật duy nhất đang tắt nên không tính
        self.assertEqual(theo_ma["CAO_SU"][4], 0)
        self.assertEqual([d[0] for d in dong], sorted(d[0] for d in dong))


class TestXuatLuat(TestCaseDuLieuChung):
    def setUp(self):
        self.dang_nhap_vai_tro("ADMIN")
        self.r = self.client.get(URL_LUAT)

    def test_chi_gom_luat_dang_bat(self):
        tieu_de, dong = bang(mo(self.r)["Luật tư vấn hiện hành"], "Mã luật")
        self.assertEqual([d[0] for d in dong], ["LT-BO", "LT-CF", "LT-HT", "LT-SR"])  # không có LT-OFF
        self.assertEqual(len(tieu_de), 9)

    def test_noi_dung_mot_luat(self):
        _, dong = bang(mo(self.r)["Luật tư vấn hiện hành"], "Mã luật")
        sr = next(d for d in dong if d[0] == "LT-SR")
        self.assertEqual(sr, ["LT-SR", "SAU_RIENG", "Sầu riêng", "Đăk Lăk", "Mùa mưa", "gia tri cao; kinh te cao", 1, "Tài liệu kiểm thử", "WASI"])

    def test_luat_chung_ghi_moi_tinh_moi_mua_he_so_la_so(self):
        ws = mo(self.r)["Luật tư vấn hiện hành"]
        _, dong = bang(ws, "Mã luật")
        ht = next(d for d in dong if d[0] == "LT-HT")
        self.assertEqual(ht[3:5], ["Mọi tỉnh", "Mọi mùa"])
        self.assertIsInstance(ht[6], (int, float))  # là số để Excel tính toán được, không phải chuỗi
        self.assertEqual(ws["G2"].number_format, "0.00")

    def test_luat_khong_co_tai_lieu_de_trong(self):
        LuatTuVan.objects.filter(rule_id="LT-HT").update(tai_lieu=None)
        _, dong = bang(mo(self.client.get(URL_LUAT))["Luật tư vấn hiện hành"], "Mã luật")
        ht = next(d for d in dong if d[0] == "LT-HT")
        self.assertEqual(ht[7:9], [None, None])

    def test_bat_luat_tat_thi_xuat_hien_trong_bao_cao(self):
        LuatTuVan.objects.filter(rule_id="LT-OFF").update(is_active=True)
        _, dong = bang(mo(self.client.get(URL_LUAT))["Luật tư vấn hiện hành"], "Mã luật")
        self.assertIn("LT-OFF", [d[0] for d in dong])


class TestXuatLichSu(TestCaseDuLieuChung):
    def setUp(self):
        tao_du_lieu_thong_ke(self.dl)
        self.dang_nhap_vai_tro("ADMIN")

    def lay(self, **loc):
        r = self.client.get(URL_LICH_SU, loc)
        self.assertEqual(r["Content-Type"], MIME_XLSX)
        return bang(mo(r)["Lịch sử tư vấn"], "Mã")

    def test_du_cot_va_sap_xep_theo_thoi_gian(self):
        tieu_de, dong = self.lay()
        self.assertEqual(tieu_de[:4], ["Mã", "Thời gian", "Người dùng", "Nhu cầu"])
        self.assertEqual(len(tieu_de), 10)
        self.assertEqual([d[0] for d in dong], ["LS-T1", "LS-T2", "LS-T3", "LS-T4", "LS-T5"])

    def test_dong_co_de_xuat(self):
        _, dong = self.lay()
        t1 = dong[0]
        self.assertEqual(t1[1], datetime(2026, 10, 1, 12, 0))  # ngày giờ thật (không múi giờ), không phải chuỗi
        self.assertEqual(t1[2:7], ["nongdan", "Cây giá trị kinh tế cao", "Đăk Lăk", "Mùa mưa", "Có đề xuất"])
        self.assertEqual(t1[7], "Sầu riêng (1.000); Cà phê (0.875)")
        self.assertEqual((t1[8], t1[9]), (1.0, "0.5 / 0.3 / 0.2"))

    def test_dong_ngoai_pham_vi(self):
        _, dong = self.lay()
        t4 = dong[3]
        self.assertEqual((t4[6], t4[7], t4[8]), ("Ngoài phạm vi", THONG_BAO_NGOAI_PHAM_VI, None))
        self.assertIsNone(t4[5])  # không chọn mùa: ô để trống (Excel không phân biệt ô trống và chuỗi rỗng)

    def test_dinh_dang_o_thoi_gian_va_diem(self):
        ws = mo(self.client.get(URL_LICH_SU))["Lịch sử tư vấn"]
        self.assertEqual(ws["B3"].number_format, "dd/mm/yyyy hh:mm")  # dòng 1 là ghi chú, 2 là tiêu đề, 3 là dữ liệu đầu
        self.assertEqual(ws["I3"].number_format, "0.000")

    def test_loc_theo_khoang_ngay(self):
        self.assertEqual([d[0] for d in self.lay(tu_ngay="2026-10-02", den_ngay="2026-10-02")[1]], ["LS-T3"])
        self.assertEqual([d[0] for d in self.lay(tu_ngay="2026-10-05")[1]], ["LS-T4", "LS-T5"])
        self.assertEqual([d[0] for d in self.lay(den_ngay="2026-10-01")[1]], ["LS-T1", "LS-T2"])
        self.assertEqual(self.lay(tu_ngay="2027-01-01")[1], [])  # rỗng: vẫn có tiêu đề

    def test_ghi_chu_khoang_thoi_gian(self):
        ws = mo(self.client.get(URL_LICH_SU, {"tu_ngay": "2026-10-02"}))["Lịch sử tư vấn"]
        self.assertEqual(ws["A1"].value, "Khoảng thời gian: từ 02/10/2026 đến nay")

    def test_khoang_ngay_sai_khong_xuat_file_va_chuyen_ve_trang_bao_cao(self):
        NhatKy.objects.all().delete()
        for loc in ({"tu_ngay": "2026-10-05", "den_ngay": "2026-10-01"}, {"tu_ngay": "abc"}):
            r = self.client.get(URL_LICH_SU, loc, follow=True)
            self.assertRedirects(r, "/bao-cao/")
            self.assertContains(r, "Khoảng ngày không hợp lệ")
        self.assertFalse(NhatKy.objects.filter(hanh_dong="Xuất báo cáo").exists())

    def test_nguoi_dung_da_xoa_van_xuat_duoc(self):
        LichSuTuVan.objects.filter(ma_lstv="LS-T1").update(nguoi_dung=None)
        _, dong = self.lay()
        self.assertIsNone(dong[0][2])  # ô trống


class TestAnToanDuLieuNguoiDung(TestCaseDuLieuChung):
    """Nhu cầu, từ khóa... do người dùng nhập; không được để Excel hiểu thành công thức hay làm hỏng file."""

    NHAN_PHAM = ["=HYPERLINK(\"http://x.test\",\"bấm\")", "+1+1", "-2+3", "@SUM(A1:A2)", "=1+1"]

    def setUp(self):
        self.dang_nhap_vai_tro("ADMIN")
        for i, nhu_cau in enumerate(self.NHAN_PHAM, start=1):
            LichSuTuVan.objects.create(ma_lstv=f"LS-X{i}", nhu_cau=nhu_cau, ket_qua_json={"trong_pham_vi": False, "de_xuat": []})

    def test_o_bat_dau_bang_dau_cong_thuc_van_la_chuoi(self):
        ws = mo(self.client.get(URL_LICH_SU))["Lịch sử tư vấn"]
        o_nhu_cau = [r[3] for r in ws.iter_rows(min_row=3)]
        self.assertEqual([o.value for o in o_nhu_cau], self.NHAN_PHAM)
        for o in o_nhu_cau:
            self.assertEqual(o.data_type, "s", o.value)  # «f» mới là công thức

    def test_dau_cong_thuc_trong_tep_khong_co_the_f(self):
        import zipfile

        with zipfile.ZipFile(BytesIO(self.client.get(URL_LICH_SU).content)) as z:
            sheet = z.read("xl/worksheets/sheet1.xml").decode()
        self.assertNotIn("<f>", sheet)  # không có thẻ công thức nào

    def test_ky_tu_dieu_khien_bi_loai_bo_khong_lam_hong_tep(self):
        LichSuTuVan.objects.filter(ma_lstv="LS-X1").update(nhu_cau="giá\x07 trị\x0b cao\x1f")
        ws = mo(self.client.get(URL_LICH_SU))["Lịch sử tư vấn"]
        self.assertEqual(ws["D3"].value, "giá trị cao")

    def test_ten_nguoi_dung_cung_duoc_lam_sach(self):
        nd = self.dl.nguoi_dung["NONG_DAN"]
        nd.username = "=cmd"
        nd.save()
        LichSuTuVan.objects.filter(ma_lstv="LS-X1").update(nguoi_dung=nd)
        ws = mo(self.client.get(URL_LICH_SU))["Lịch sử tư vấn"]
        self.assertEqual((ws["C3"].value, ws["C3"].data_type), ("=cmd", "s"))


class TestKhongNPlusMot(TestCaseDuLieuChung):
    def dem(self, url):
        self.client.get("/")  # làm nóng phiên
        with CaptureQueriesContext(connection) as ctx:
            self.assertEqual(self.client.get(url)["Content-Type"], MIME_XLSX)
        return len(ctx)

    def test_so_truy_van_khong_tang_theo_so_dong(self):
        self.dang_nhap_vai_tro("ADMIN")
        tao_du_lieu_thong_ke(self.dl)
        truoc = {u: self.dem(u) for u in (URL_CAY, URL_LUAT, URL_LICH_SU)}
        for i in range(60):
            LichSuTuVan.objects.create(
                ma_lstv=f"LS-N{i}", nguoi_dung=self.dl.nguoi_dung["NONG_DAN"], nhu_cau="x",
                ket_qua_json={"trong_pham_vi": True, "de_xuat": [{"ten_cay": "A", "diem": 1.0}], "trong_so": {}},
            )
            LuatTuVan.objects.create(
                rule_id=f"LT-N{i}", cay_tro=self.dl.cay["BO"], tinh_thanh=self.dl.tinh["GIA_LAI"], mua_vu=self.dl.mua["MUA_MUA"],
                condition_json={"tu_khoa": ["a"]}, tai_lieu=self.dl.tai_lieu,
            )
        sau = {u: self.dem(u) for u in (URL_CAY, URL_LUAT, URL_LICH_SU)}
        self.assertEqual(truoc, sau)


class TestNhatKyXuat(TestCaseDuLieuChung):
    def test_moi_lan_xuat_ghi_nhat_ky_voi_so_dong(self):
        tao_du_lieu_thong_ke(self.dl)
        self.dang_nhap_vai_tro("ADMIN")
        NhatKy.objects.all().delete()
        self.client.get(URL_CAY)
        self.client.get(URL_LUAT)
        self.client.get(URL_LICH_SU)
        nhat_ky = {nk.doi_tuong: nk.chi_tiet for nk in NhatKy.objects.filter(hanh_dong="Xuất báo cáo")}
        self.assertEqual(nhat_ky, {"BaoCao: cay-trong": "12 dòng", "BaoCao: luat-tu-van": "4 dòng", "BaoCao: lich-su-tu-van": "5 dòng"})


class TestBoDungExcel(TestCaseDuLieuChung):
    def test_ten_sheet(self):
        self.assertEqual(excel.ten_sheet_hop_le("Luật: tư vấn/hiện hành?"), "Luật  tư vấn hiện hành")
        self.assertEqual(len(excel.ten_sheet_hop_le("a" * 50)), 31)
        self.assertEqual(excel.ten_sheet_hop_le("[]"), "Sheet")

    def test_chuan_hoa_gia_tri(self):
        from django.utils import timezone

        self.assertEqual(excel.chuan_hoa_gia_tri(True), "Có")
        self.assertEqual(excel.chuan_hoa_gia_tri(False), "Không")
        self.assertEqual(excel.chuan_hoa_gia_tri(gio(10, 1)), datetime(2026, 10, 1, 12, 0))  # giờ địa phương, bỏ múi giờ
        self.assertIsNone(excel.chuan_hoa_gia_tri(timezone.make_aware(datetime(2026, 10, 1, 12)).replace(tzinfo=None)).tzinfo)
        self.assertEqual(excel.chuan_hoa_gia_tri("a\x00b"), "ab")
        self.assertEqual(excel.chuan_hoa_gia_tri(5), 5)

    def test_tao_xlsx_sheet_rong_va_dinh_dang_rieng_tung_o(self):
        noi_dung, so_dong = excel.tao_xlsx([
            {"ten": "Rỗng", "cot": ["A", "B"], "dong": []},
            {"ten": "Có dữ liệu", "cot": ["Chỉ số", "Giá trị"], "dong": [["x", (0.5, "0.0%")], ["y", 7]], "ghi_chu": ["Ghi chú"]},
        ])
        self.assertEqual(so_dong, 2)
        wb = openpyxl.load_workbook(BytesIO(noi_dung))
        self.assertEqual(wb.sheetnames, ["Rỗng", "Có dữ liệu"])
        ws = wb["Có dữ liệu"]
        self.assertEqual((ws["B3"].value, ws["B3"].number_format), (0.5, "0.0%"))
        self.assertEqual(ws["B4"].number_format, "General")
        self.assertEqual(ws.freeze_panes, "A3")  # cố định dòng ghi chú + tiêu đề
        self.assertEqual(ws.auto_filter.ref, "A2:B4")

    def test_do_rong_cot_bi_chan_tren(self):
        noi_dung, _ = excel.tao_xlsx([{"ten": "S", "cot": ["Cột"], "dong": [["x" * 500]]}])
        ws = openpyxl.load_workbook(BytesIO(noi_dung))["S"]
        self.assertEqual(ws.column_dimensions["A"].width, excel.DO_RONG_TOI_DA + 2)
        self.assertEqual(len(ws["A2"].value), 500)  # dữ liệu không bị cắt, chỉ giới hạn độ rộng cột
