"""Tài liệu sinh từ mã nguồn (tai_lieu/) phải luôn khớp mã nguồn hiện tại."""
from django.test import SimpleTestCase

from tai_lieu import tao_tai_lieu as tl


class TestTaiLieuSinhTuMaNguon(SimpleTestCase):
    def test_tu_dien_da_luu_khop_ma_nguon(self):
        self.assertTrue(tl.TEP_TU_DIEN.exists(), "Chạy: python tai_lieu/tao_tai_lieu.py")
        self.assertEqual(tl.TEP_TU_DIEN.read_text(encoding="utf-8"), tl.tao_tu_dien(), "Model đã đổi: chạy lại python tai_lieu/tao_tai_lieu.py")

    def test_ma_tran_da_luu_khop_ma_nguon(self):
        self.assertTrue(tl.TEP_MA_TRAN.exists(), "Chạy: python tai_lieu/tao_tai_lieu.py")
        self.assertEqual(tl.TEP_MA_TRAN.read_text(encoding="utf-8"), tl.tao_ma_tran(), "View/quyền đã đổi: chạy lại python tai_lieu/tao_tai_lieu.py")

    def test_dung_15_bang_va_14_quan_he(self):
        self.assertEqual(len(tl.cac_model()), 15)
        self.assertEqual({m.__name__ for m in tl.cac_model()}, {
            "VaiTro", "NguoiDung", "NhatKy", "CayTrong", "TinhThanh", "MuaVu", "KyThuat", "TaiLieu", "LuatTuVan", "LichSuTuVan",
            "LichSuTimKiem", "CauHoi", "TraLoi", "CauHinhHeThong", "MaKhoiPhucMatKhau",
        })
        erd = tl.tao_erd(tl.cac_model())
        self.assertEqual(sum(1 for d in erd.split("\n") if "--o" in d), 14)
        self.assertIn("CauHoi ||--o| TraLoi", erd)  # mỗi câu hỏi tối đa một câu trả lời

    def test_tu_dien_khong_con_chuoi_do_django_tu_sinh(self):
        import re

        self.assertIsNone(re.search(r"\| \w+\(id,", tl.tao_tu_dien()))

    def test_mo_ta_url_khong_thua_khong_thieu(self):
        cac = set(tl.tat_ca_duong_dan())
        self.assertEqual(sorted(cac - set(tl.MO_TA)), [])
        self.assertEqual(sorted(set(tl.MO_TA) - cac), [], "MO_TA còn đường dẫn đã bị xóa")
        self.assertEqual(sorted(set(tl.PHAM_VI_DU_LIEU) - cac), [])

    def test_ma_tran_dung_so_dong_va_quyen_chinh(self):
        dong = [d for d in tl.tao_ma_tran().split("\n") if d.startswith("| `/")]
        self.assertEqual(len(dong), 40)
        quyen = {d.split("`")[1]: [c.strip() for c in d.split("|")[4:8]] for d in dong}  # Quản trị, Biên tập, Chuyên gia, Nông dân
        self.assertEqual(quyen["/bao-cao/thong-ke/"], ["✔", "", "", ""])
        self.assertEqual(quyen["/hoi-dap/them/"], ["", "", "", "✔"])
        self.assertEqual(quyen["/hoi-dap/<id>/tra-loi/"], ["", "", "✔", ""])
        self.assertEqual(quyen["/danh-muc/<muc>/them/"], ["✔", "✔", "", ""])
        self.assertEqual(quyen["/tu-van/"], ["✔"] * 4)
