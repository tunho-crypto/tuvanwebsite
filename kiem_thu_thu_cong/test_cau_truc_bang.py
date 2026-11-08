"""Bảo đảm bảng test case thủ công luôn đầy đủ, đúng cấu trúc, có kiểm chứng tương ứng và khớp file đã xuất."""
import inspect
from io import BytesIO
from pathlib import Path

import openpyxl
from django.test import SimpleTestCase

from kiem_thu_thu_cong import danh_sach, test_kich_ban_thu_cong, xuat
from kiem_thu_thu_cong.danh_sach import TC_LIST

BAT_BUOC = ("ma", "use_case", "loai", "dieu_kien", "buoc", "du_lieu", "mong_doi")
USE_CASE_YEU_CAU = {"Đăng nhập", "Quản lý người dùng", "Danh mục", "Tư vấn", "Tìm kiếm", "Hỏi đáp", "Cấu hình trọng số", "Báo cáo"}


def ten_ham_kiem_chung(ma):
    return "test_tc_" + ma.lower().replace("-", "_")


class TestBangTestCase(SimpleTestCase):
    def test_so_luong_tu_50_den_70(self):
        self.assertTrue(50 <= len(TC_LIST) <= 70, len(TC_LIST))

    def test_ma_duy_nhat_va_dung_dinh_dang(self):
        ma = [t["ma"] for t in TC_LIST]
        self.assertEqual(len(ma), len(set(ma)))
        for m in ma:
            self.assertRegex(m, r"^[A-Z]{2}-\d{2}$")

    def test_khong_o_nao_bi_bo_trong(self):
        for t in TC_LIST:
            for truong in BAT_BUOC:
                self.assertTrue(t[truong], f"{t['ma']}.{truong}")
            self.assertGreaterEqual(len(t["buoc"]), 1, t["ma"])

    def test_phu_du_cac_use_case_theo_de_cuong(self):
        self.assertTrue(USE_CASE_YEU_CAU <= {t["use_case"] for t in TC_LIST})

    def test_co_du_bon_loai_va_loai_hop_le(self):
        loai = {t["loai"] for t in TC_LIST}
        self.assertEqual(loai, {danh_sach.BINH_THUONG, danh_sach.BIEN, danh_sach.LOI, danh_sach.PHAN_QUYEN})

    def test_moi_use_case_chinh_co_ca_truong_hop_binh_thuong_va_loi_hoac_bien(self):
        for uc in USE_CASE_YEU_CAU:
            cac = {t["loai"] for t in TC_LIST if t["use_case"] == uc}
            self.assertIn(danh_sach.BINH_THUONG, cac, uc)
            self.assertTrue(cac & {danh_sach.LOI, danh_sach.BIEN}, uc)

    def test_su_dung_tinh_huong_trong_de_cuong(self):
        van_ban = " ".join(str(t.values()) for t in TC_LIST)
        for cum in ("Cây giá trị kinh tế cao", "Sầu riêng", "Cà phê", "giá cà phê ngày mai", "0,8"):
            self.assertIn(cum, van_ban, cum)

    def test_chi_dung_tai_khoan_cua_du_lieu_mau(self):
        import re

        van_ban = " ".join(" ".join(t["buoc"]) + " " + t["du_lieu"] + " " + t["dieu_kien"] for t in TC_LIST)
        # Tên tài khoản là từ viết thường ASCII đứng ngay sau «đăng nhập»; «lần», «bằng», «lại»... có dấu nên không bị bắt nhầm
        cac_ten = set(re.findall(r"\b[Đđ]ăng nhập\s+([a-z]+)\b", van_ban))
        self.assertTrue(cac_ten, "không tìm thấy tên tài khoản nào")
        self.assertLessEqual(cac_ten, {"admin", "bientap", "chuyengia", "nongdan", "nvmoi"}, cac_ten)
        self.assertTrue({"admin", "bientap", "chuyengia", "nongdan"} <= cac_ten)  # cả 4 vai trò đều được dùng


class TestBangKhopMaKiemChung(SimpleTestCase):
    """Mỗi câu thông báo (từ 3 từ trở lên, trong dấu « ») ở cột «Kết quả mong đợi» phải xuất hiện NGUYÊN VĂN trong mã kiểm chứng,
    để bảng test case không thể nói một đằng còn hệ thống (đã được kiểm chứng) làm một nẻo."""

    # Ngoại lệ có lý do:
    NGOAI_LE = {
        "Bản xem trước, chưa lưu vào lịch sử": "kiểm chứng tách làm hai phần «Bản xem trước» và «chưa lưu»",
        "Số luật đang áp dụng": "tên cột Excel, kiểm chứng qua giá trị của cột",
    }
    GIU_CHO = ("yyyy", "…", "dd/mm", "<id")  # phần giữ chỗ (mã sinh theo ngày...) không thể khớp nguyên văn

    def test_moi_cau_thong_bao_trong_bang_deu_duoc_kiem_chung(self):
        import re

        nguon = Path(test_kich_ban_thu_cong.__file__).read_text(encoding="utf-8")
        thieu = []
        for t in TC_LIST:
            for cau in re.findall(r"«([^«»]+)»", t["mong_doi"]):
                if len(cau.split()) < 3 or cau in self.NGOAI_LE or any(g in cau for g in self.GIU_CHO):
                    continue
                if cau == danh_sach.HAM_NGOAI_PHAM_VI:  # kiểm chứng qua hằng số dùng chung
                    self.assertIn("HAM_NGOAI_PHAM_VI", nguon)
                    continue
                if cau.rstrip(".") not in nguon:
                    thieu.append((t["ma"], cau))
        self.assertEqual(thieu, [], "Câu trong bảng test case không có trong mã kiểm chứng (sửa bảng hoặc sửa hàm kiểm chứng cho khớp)")

    def test_ngoai_le_van_con_xuat_hien_trong_bang(self):
        van_ban = " ".join(t["mong_doi"] for t in TC_LIST)
        for cau in self.NGOAI_LE:
            self.assertIn(cau, van_ban, f"Ngoại lệ thừa, hãy xóa: {cau}")


class TestMoiTestCaseCoKiemChung(SimpleTestCase):
    def test_dung_mot_ham_kiem_chung_cho_moi_test_case(self):
        ham = set()
        for _, lop in inspect.getmembers(test_kich_ban_thu_cong, inspect.isclass):
            if lop.__module__ == test_kich_ban_thu_cong.__name__:
                ham |= {ten for ten in dir(lop) if ten.startswith("test_tc_")}
        mong_doi = {ten_ham_kiem_chung(t["ma"]) for t in TC_LIST}
        self.assertEqual(sorted(mong_doi - ham), [], "Test case chưa có hàm kiểm chứng")
        self.assertEqual(sorted(ham - mong_doi), [], "Hàm kiểm chứng không có test case tương ứng")


class TestFileXuat(SimpleTestCase):
    def test_markdown_moi_dong_du_9_cot_va_khong_vo_bang(self):
        md = xuat.tao_markdown().split("\n")
        i = next(k for k, d in enumerate(md) if d.startswith("| Mã TC"))
        bang = md[i : i + 2 + len(TC_LIST)]
        self.assertEqual({d.count("|") for d in bang}, {len(xuat.CAC_COT) + 1})
        self.assertTrue(all(d.startswith("| ") or d.startswith("|---") for d in bang))
        self.assertTrue(md[i + 2 + len(TC_LIST)] == "")

    def test_markdown_da_luu_khop_voi_nguon(self):
        tep = Path(xuat.TEP_MD)
        self.assertTrue(tep.exists(), "Chưa sinh file: chạy python kiem_thu_thu_cong/xuat.py")
        self.assertEqual(tep.read_text(encoding="utf-8"), xuat.tao_markdown(), "Bảng đã lưu cũ hơn danh_sach.py: chạy lại python kiem_thu_thu_cong/xuat.py")

    def test_cot_ket_qua_thuc_te_va_dat_de_trong(self):
        for t in TC_LIST:
            dong = xuat.dong_tc(t)
            self.assertEqual((dong[6], dong[7]), ("", ""), t["ma"])

    def test_excel_co_du_dong_va_o_chon_dat_khong_dat(self):
        ws = openpyxl.load_workbook(BytesIO(xuat.tao_xlsx()))["Test case"]
        self.assertEqual(ws.max_row, len(TC_LIST) + 1)
        self.assertEqual([c.value for c in ws[1]], xuat.CAC_COT)
        kiem = ws.data_validations.dataValidation
        self.assertEqual(len(kiem), 1)
        self.assertIn("Đạt,Không đạt", kiem[0].formula1)
        self.assertEqual(str(kiem[0].sqref), f"H2:H{len(TC_LIST) + 1}")

    def test_excel_da_luu_khop_so_dong(self):
        ws = openpyxl.load_workbook(xuat.TEP_XLSX)["Test case"]
        self.assertEqual(ws.max_row, len(TC_LIST) + 1)
