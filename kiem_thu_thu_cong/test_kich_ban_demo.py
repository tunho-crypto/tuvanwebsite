"""Chạy tự động ĐÚNG trình tự của tai_lieu/KICH_BAN_DEMO_10_PHUT.md với các con số hiển thị trên màn hình.
Nếu test này đỏ thì kịch bản demo không còn đúng: sửa code hoặc sửa kịch bản trước khi lên demo."""
import html as html_lib
import re
from io import BytesIO, StringIO

import openpyxl
from django.core.management import call_command
from django.test import Client, TestCase

from kiem_thu_thu_cong.test_kich_ban_thu_cong import de_xuat, loi_form, van_ban, vao
from tuvan.models import LichSuTuVan

HAM = "Hệ thống chưa đủ thông tin dữ liệu về nội dung này trong phạm vi hỗ trợ"
DU_LIEU = {"nhu_cau": "Cây giá trị kinh tế cao", "tinh_thanh": "DAK_LAK", "mua_vu": "MUA_MUA"}


class TestKichBanDemo(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("nap_du_lieu_mau", stdout=StringIO())

    def test_demo_10_phut(self):
        nong_dan, admin = Client(), Client()  # hai cửa sổ trình duyệt (thường và ẩn danh)

        # 0:50 Đăng nhập Nông dân
        r = nong_dan.post("/dang-nhap/", {"username": "nongdan", "password": "123456"}, follow=True)
        self.assertIn("Xin chào, Phạm Nông Dân", van_ban(r))
        self.assertEqual([m["ten"] for m in r.context["menu"]], ["Trang chủ", "Giới thiệu", "Danh mục", "Tra cứu", "Tư vấn", "Hỏi đáp"])

        # 1:30 Tư vấn: Cây giá trị kinh tế cao, Đăk Lăk, Mùa mưa
        r = nong_dan.post("/tu-van/", DU_LIEU, follow=True)
        t = van_ban(r)
        for cum in ("#1 · Sầu riêng Điểm 1,00", "#2 · Cà phê Điểm 0,88", "#3 · Hồ tiêu Điểm 0,75"):
            self.assertIn(cum, t)
        cf = t[t.index("#2 · Cà phê") : t.index("#3 · Hồ tiêu")]
        for dong in ("Nhu cầu 0,5 0,75 0,375", "Tỉnh thành 0,3 1,00 0,300", "Mùa vụ 0,2 1,00 0,200", "Điểm phù hợp 0,875"):
            self.assertIn(dong, cf)  # phép tính tay: 0,5 × 0,75 + 0,3 × 1 + 0,2 × 1 = 0,875
        self.assertIn("luật chung cho mọi tỉnh trong vùng", t)  # lý do của Hồ tiêu (điểm thấp hơn vì luật chung)
        ls_cu = LichSuTuVan.objects.get()
        self.assertTrue(ls_cu.ma_lstv.startswith("LS"))

        # 3:45 Hỏi ngoài phạm vi
        r = nong_dan.post("/hoi-dap/them/", {"noi_dung": "giá cà phê ngày mai"}, follow=True)
        t = van_ban(r)
        self.assertIn("Câu hỏi nằm ngoài phạm vi hỗ trợ nên đã được trả lời tự động.", t)
        self.assertIn("Ngoài phạm vi", t)
        self.assertIn("Trả lời tự động", t)
        self.assertIn(HAM, t)

        # 5:00 ADMIN đổi trọng số (thử tổng sai trước, rồi w1 = 0,8)
        r = admin.post("/dang-nhap/", {"username": "admin", "password": "123456"}, follow=True)
        self.assertEqual([m["ten"] for m in r.context["menu"]][-2:], ["Báo cáo", "Quản trị"])
        self.assertEqual(r.context["menu"][0]["ten"], "Trang chủ")
        self.assertEqual(admin.get("/cau-hinh/").context["form"].initial, {"w1": "0,5", "w2": "0,3", "w3": "0,2"})  # đúng giá trị mặc định lúc bắt đầu
        self.assertEqual(loi_form(admin.post("/cau-hinh/", {"w1": "0,8", "w2": "0,3", "w3": "0,1"})), ["Tổng w1 + w2 + w3 phải bằng 1"])
        r = admin.post("/cau-hinh/", {"w1": "0,8", "w2": "0,1", "w3": "0,1"}, follow=True)
        self.assertIn("Đã cập nhật trọng số.", van_ban(r))

        # 6:30 Tư vấn lại cùng dữ liệu: thứ hạng đổi
        r = admin.post("/tu-van/", DU_LIEU, follow=True)
        self.assertEqual(de_xuat(r), [("Sầu riêng", 1.0), ("Hồ tiêu", 0.9), ("Cà phê", 0.8)])
        self.assertIn("#2 · Hồ tiêu Điểm 0,90", van_ban(r))
        # lần tư vấn cũ vẫn như cũ (bản chụp)
        cu = admin.get(f"/tu-van/lich-su/{ls_cu.pk}/")
        self.assertEqual(de_xuat(cu), [("Sầu riêng", 1.0), ("Cà phê", 0.875), ("Hồ tiêu", 0.75)])

        # 7:45 Truy xuất nguồn từ nút «Xem nguồn» của Sầu riêng
        link = re.search(r'href="(/truy-xuat/\?ma=LT20260101-001[^"]*)"', r.content.decode())
        self.assertIsNotNone(link)
        r = admin.get(html_lib.unescape(link.group(1)))
        t = van_ban(r)
        for cum in ("Luật LT20260101-001", "Đang áp dụng", "Sầu riêng", "Đăk Lăk", "Mùa mưa", "WASI", "Quy trình kỹ thuật trồng trọt cây công nghiệp và cây ăn quả Tây Nguyên", "Hệ số ưu tiên"):
            self.assertIn(cum, t)

        # 8:45 Thống kê và xuất Excel
        r = admin.get("/bao-cao/thong-ke/")
        self.assertEqual(r.context["tk"]["tu_van"]["tong"], 2)
        self.assertEqual(r.context["tk"]["hoi_dap"]["ngoai_pham_vi"], 1)
        x = admin.get("/bao-cao/thong-ke/", {"xuat": "xlsx"})
        self.assertEqual(len(openpyxl.load_workbook(BytesIO(x.content)).sheetnames), 6)

    def test_nong_dan_khong_thay_cau_hinh_va_bao_cao_trong_luc_demo(self):
        nd = vao("nongdan")
        for url in ("/cau-hinh/", "/bao-cao/", "/bao-cao/thong-ke/"):
            self.assertEqual(nd.get(url).status_code, 403)
