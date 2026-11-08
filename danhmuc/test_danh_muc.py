"""CRUD danh mục: chuẩn hóa mã, trùng mã, chặn xóa khi đang dùng, tìm kiếm, phân trang, nhật ký, hoàn tác."""
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from danhmuc.models import CayTrong, KyThuat, MuaVu, TaiLieu, TinhThanh
from danhmuc.services import luu_danh_muc, xoa_danh_muc
from taikhoan.kiem_thu_chung import TestCaseDuLieuChung
from taikhoan.models import NhatKy
from taikhoan.services import NghiepVuError


def url(ten, muc, pk=None):
    kwargs = {"muc": muc} if pk is None else {"muc": muc, "pk": pk}
    return reverse(f"danhmuc:{ten}", kwargs=kwargs)


def anh_png(ten="minh-hoa.png"):
    noi_dung = BytesIO()
    Image.new("RGB", (2, 2), "green").save(noi_dung, format="PNG")
    return SimpleUploadedFile(ten, noi_dung.getvalue(), content_type="image/png")


class DanhMucTestCase(TestCaseDuLieuChung):
    def setUp(self):
        self.nguoi = self.dang_nhap_vai_tro("BIEN_TAP")
        NhatKy.objects.all().delete()  # bỏ dòng «Đăng nhập»


class TestThemSua(DanhMucTestCase):
    def test_them_cay_cat_khoang_trang_va_viet_hoa_ma(self):
        r = self.client.post(
            url("them", "cay-trong"), {"ma_cay": "  mac_ca  ", "ten_cay": "Mắc ca", "nhom_cay": "CONG_NGHIEP", "dac_diem": ""}
        )
        self.assertRedirects(r, url("ds", "cay-trong"))
        self.assertTrue(CayTrong.objects.filter(ma_cay="MAC_CA", ten_cay="Mắc ca").exists())

    def test_ma_trung_sau_khi_chuan_hoa_bi_tu_choi(self):
        r = self.client.post(url("them", "cay-trong"), {"ma_cay": " ca_phe", "ten_cay": "Trùng", "nhom_cay": "AN_QUA"})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["form"].errors["ma_cay"])
        self.assertEqual(CayTrong.objects.filter(ma_cay="CA_PHE").count(), 1)
        self.assertEqual(NhatKy.objects.count(), 0)

    def test_thieu_truong_bat_buoc_bao_loi_va_gan_is_invalid(self):
        r = self.client.post(url("them", "tinh-thanh"), {"ma_tinh": "", "ten_tinh": ""})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "is-invalid")
        self.assertEqual(TinhThanh.objects.count(), 5)

    def test_mua_vu_thang_ngoai_khoang_1_12_bi_tu_choi(self):
        r = self.client.post(url("them", "mua-vu"), {"ma_mua": "X", "ten_mua": "X", "thoi_gian_tu": 0, "thoi_gian_den": 13})
        self.assertTrue(r.context["form"].errors["thoi_gian_tu"])
        self.assertTrue(r.context["form"].errors["thoi_gian_den"])

    def test_them_ghi_nhat_ky(self):
        self.client.post(url("them", "tai-lieu"), {"ma_tl": "tl_moi", "ten_tl": "Tài liệu mới", "nguon_tham_chieu": "WASI"})
        nk = NhatKy.objects.get()
        self.assertEqual((nk.hanh_dong, nk.doi_tuong, nk.nguoi_dung), ("Thêm danh mục", "Tài liệu: TL_MOI", self.nguoi))

    def test_tai_len_anh_cay_va_hien_thi_trong_danh_sach(self):
        with TemporaryDirectory() as media_root, self.settings(MEDIA_ROOT=media_root):
            r = self.client.post(
                url("sua", "cay-trong", self.dl.cay["CAO_SU"].pk),
                {
                    "ma_cay": "CAO_SU",
                    "ten_cay": "Cao su",
                    "nhom_cay": "CONG_NGHIEP",
                    "dac_diem": "",
                    "hinh_anh": anh_png(),
                },
            )
            self.assertRedirects(r, url("ds", "cay-trong"))
            cay = CayTrong.objects.get(ma_cay="CAO_SU")
            anh_cu = Path(media_root, cay.hinh_anh.name)
            self.assertTrue(anh_cu.is_file())
            with self.captureOnCommitCallbacks(execute=True):
                r = self.client.post(
                    url("sua", "cay-trong", cay.pk),
                    {
                        "ma_cay": "CAO_SU",
                        "ten_cay": "Cao su",
                        "nhom_cay": "CONG_NGHIEP",
                        "dac_diem": "",
                        "hinh_anh": anh_png(),
                    },
                )
            self.assertRedirects(r, url("ds", "cay-trong"))
            cay.refresh_from_db()
            self.assertFalse(anh_cu.exists())
            self.assertTrue(Path(media_root, cay.hinh_anh.name).is_file())
            self.assertContains(self.client.get(url("ds", "cay-trong")), cay.hinh_anh.url)

    def test_tai_len_anh_ky_thuat(self):
        with TemporaryDirectory() as media_root, self.settings(MEDIA_ROOT=media_root):
            r = self.client.post(
                url("them", "ky-thuat"),
                {
                    "ma_kt": "KT_MINH_HOA",
                    "ten_kt": "Kỹ thuật minh họa",
                    "loai_kt": "Tưới nước",
                    "noi_dung": "",
                    "hinh_anh": anh_png("ky-thuat.png"),
                },
            )
            self.assertRedirects(r, url("ds", "ky-thuat"))
            ky_thuat = KyThuat.objects.get(ma_kt="KT_MINH_HOA")
            self.assertTrue(Path(media_root, ky_thuat.hinh_anh.name).is_file())
            self.assertContains(self.client.get(url("ds", "ky-thuat")), ky_thuat.hinh_anh.url)

    def test_tai_lieu_luu_va_hien_thi_lien_ket_an_toan(self):
        r = self.client.post(
            url("them", "tai-lieu"),
            {
                "ma_tl": "TL_LINK",
                "ten_tl": "Tài liệu trực tuyến",
                "nguon_tham_chieu": "WASI",
                "duong_dan": "https://example.org/tai-lieu",
            },
        )
        self.assertRedirects(r, url("ds", "tai-lieu"))
        tai_lieu = TaiLieu.objects.get(ma_tl="TL_LINK")
        self.assertContains(self.client.get(url("ds", "tai-lieu")), 'href="https://example.org/tai-lieu"')
        self.assertEqual(tai_lieu.duong_dan, "https://example.org/tai-lieu")

    def test_tu_choi_lien_ket_tai_lieu_khong_an_toan(self):
        r = self.client.post(
            url("them", "tai-lieu"),
            {
                "ma_tl": "TL_BAD",
                "ten_tl": "Tài liệu",
                "nguon_tham_chieu": "WASI",
                "duong_dan": "javascript:alert(1)",
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("duong_dan", r.context["form"].errors)
        self.assertFalse(TaiLieu.objects.filter(ma_tl="TL_BAD").exists())

    def test_khong_tao_link_click_duoc_tu_duong_dan_cu_khong_an_toan(self):
        TaiLieu.objects.create(
            ma_tl="TL_OLD",
            ten_tl="Tài liệu cũ",
            nguon_tham_chieu="Nguồn cũ",
            duong_dan="javascript:alert(1)",
        )
        r = self.client.get(url("ds", "tai-lieu"))
        self.assertContains(r, "javascript:alert(1)")
        self.assertNotContains(r, 'href="javascript:alert(1)"')

    def test_sua_doi_ten_giu_nguyen_ma_va_ghi_nhat_ky(self):
        cay = self.dl.cay["CAO_SU"]
        r = self.client.post(
            url("sua", "cay-trong", cay.pk), {"ma_cay": "CAO_SU", "ten_cay": "Cao su (đã sửa)", "nhom_cay": "CONG_NGHIEP"}
        )
        self.assertRedirects(r, url("ds", "cay-trong"))
        cay.refresh_from_db()
        self.assertEqual(cay.ten_cay, "Cao su (đã sửa)")
        self.assertEqual(NhatKy.objects.get().hanh_dong, "Sửa danh mục")

    def test_sua_giu_nguyen_ma_cua_chinh_no_khong_bi_bao_trung(self):
        cay = self.dl.cay["CAO_SU"]
        r = self.client.post(url("sua", "cay-trong", cay.pk), {"ma_cay": "cao_su", "ten_cay": "Cao su", "nhom_cay": "CONG_NGHIEP"})
        self.assertRedirects(r, url("ds", "cay-trong"))

    def test_sua_sang_ma_cua_ban_ghi_khac_bi_tu_choi(self):
        cay = self.dl.cay["CAO_SU"]
        r = self.client.post(url("sua", "cay-trong", cay.pk), {"ma_cay": "Ca_Phe", "ten_cay": "X", "nhom_cay": "AN_QUA"})
        self.assertTrue(r.context["form"].errors["ma_cay"])

    def test_sua_ban_ghi_khong_ton_tai_404(self):
        self.assertEqual(self.client.get(url("sua", "cay-trong", 999999)).status_code, 404)

    def test_form_sua_dien_san_gia_tri(self):
        cay = self.dl.cay["CAO_SU"]
        html = self.client.get(url("sua", "cay-trong", cay.pk)).content.decode()
        self.assertIn('value="CAO_SU"', html)

    def test_cac_form_them_cua_5_danh_muc_render_duoc(self):
        for muc in ("cay-trong", "tinh-thanh", "mua-vu", "ky-thuat", "tai-lieu"):
            r = self.client.get(url("them", muc))
            self.assertEqual(r.status_code, 200, muc)
            self.assertContains(r, "form-control")


class TestXoa(DanhMucTestCase):
    def test_trang_xac_nhan_khong_xoa(self):
        cay = self.dl.cay["CAO_SU"]
        r = self.client.get(url("xoa", "cay-trong", cay.pk))
        self.assertContains(r, "Cao su")
        self.assertTrue(CayTrong.objects.filter(pk=cay.pk).exists())

    def test_xoa_ban_ghi_chua_dung_thanh_cong_va_ghi_nhat_ky(self):
        cay = self.dl.cay["CAO_SU"]
        r = self.client.post(url("xoa", "cay-trong", cay.pk), follow=True)
        self.assertContains(r, "Đã xóa cây trồng")
        self.assertFalse(CayTrong.objects.filter(pk=cay.pk).exists())
        nk = NhatKy.objects.get()
        self.assertEqual((nk.hanh_dong, nk.doi_tuong), ("Xóa danh mục", "Cây trồng: CAO_SU"))

    def test_xoa_ky_thuat_khong_bi_chan(self):
        self.client.post(url("xoa", "ky-thuat", self.dl.ky_thuat.pk))
        self.assertFalse(KyThuat.objects.exists())

    def kiem_tra_bi_chan(self, muc, doi_tuong, model, cum_thong_bao):
        r = self.client.post(url("xoa", muc, doi_tuong.pk), follow=True)
        self.assertContains(r, "Không thể xóa")
        self.assertContains(r, cum_thong_bao)
        self.assertTrue(model.objects.filter(pk=doi_tuong.pk).exists())
        self.assertEqual(NhatKy.objects.count(), 0)  # xóa thất bại thì không ghi nhật ký

    def test_cay_dang_co_luat_bi_chan_va_noi_ro_ly_do(self):
        self.kiem_tra_bi_chan("cay-trong", self.dl.cay["CA_PHE"], CayTrong, "1 luật tư vấn")

    def test_tinh_dang_co_luat_bi_chan(self):
        self.kiem_tra_bi_chan("tinh-thanh", self.dl.tinh["DAK_LAK"], TinhThanh, "luật tư vấn")  # LT-SR, LT-CF

    def test_mua_vu_dang_co_luat_bi_chan(self):
        self.kiem_tra_bi_chan("mua-vu", self.dl.mua["MUA_MUA"], MuaVu, "luật tư vấn")

    def test_tai_lieu_dang_duoc_luat_dung_bi_chan(self):
        self.kiem_tra_bi_chan("tai-lieu", self.dl.tai_lieu, TaiLieu, "luật tư vấn")

    def test_gỡ_luat_roi_xoa_duoc(self):
        from tuvan.models import LuatTuVan

        LuatTuVan.objects.all().delete()
        self.client.post(url("xoa", "tai-lieu", self.dl.tai_lieu.pk))
        self.assertFalse(TaiLieu.objects.exists())


class TestDanhSach(DanhMucTestCase):
    def test_hien_thi_gia_tri_nhom_cay_bang_nhan_tieng_viet(self):
        r = self.client.get(url("ds", "cay-trong"))
        self.assertContains(r, "Cây công nghiệp")
        self.assertNotContains(r, ">CONG_NGHIEP<")

    def test_tim_kiem_theo_ma_va_ten_khong_phan_biet_hoa_thuong(self):
        ds = lambda q: [o.ma_cay for o in self.client.get(url("ds", "cay-trong"), {"q": q}).context["page_obj"]]
        self.assertEqual(ds("sầu"), ["SAU_RIENG"])
        self.assertEqual(ds("hO_tieu"), ["HO_TIEU"])
        self.assertEqual(ds("không-có-gì"), [])

    def test_phan_trang_10_dong_giu_tu_khoa_tim_kiem(self):
        r = self.client.get(url("ds", "cay-trong"))
        self.assertEqual(len(r.context["page_obj"]), 10)
        self.assertEqual(r.context["page_obj"].paginator.num_pages, 2)
        self.assertEqual(len(self.client.get(url("ds", "cay-trong"), {"page": 2}).context["page_obj"]), 2)
        for i in range(12):
            CayTrong.objects.create(ma_cay=f"DEMO{i:02d}", ten_cay=f"Cây demo {i}", nhom_cay="NGAN_NGAY")
        r = self.client.get(url("ds", "cay-trong"), {"q": "demo"})
        self.assertEqual(r.context["page_obj"].paginator.count, 12)
        self.assertContains(r, "q=demo&amp;page=2")
        self.assertEqual(len(self.client.get(url("ds", "cay-trong"), {"q": "demo", "page": 2}).context["page_obj"]), 2)

    def test_nut_them_sua_xoa_hien_theo_vai_tro(self):
        self.assertContains(self.client.get(url("ds", "cay-trong")), "Thêm mới")
        for ma in ("CHUYEN_GIA", "NONG_DAN"):
            self.dang_nhap_vai_tro(ma)
            html = self.client.get(url("ds", "cay-trong")).content.decode()
            self.assertNotIn("Thêm mới", html, ma)
            self.assertNotIn("/xoa/", html, ma)

    def test_moi_danh_muc_co_du_cot(self):
        for muc, so_cot, co_anh in (
            ("cay-trong", 3, True),
            ("tinh-thanh", 3, False),
            ("mua-vu", 4, False),
            ("ky-thuat", 3, True),
            ("tai-lieu", 4, False),
        ):
            r = self.client.get(url("ds", muc))
            self.assertEqual(len(r.context["tieu_de_cot"]), so_cot + co_anh, muc)
            self.assertEqual(len(r.context["dong"][0]["o"]), so_cot, muc)


class TestHoanTac(DanhMucTestCase):
    def test_luu_loi_o_buoc_cuoi_thi_khong_con_ban_ghi(self):
        from danhmuc.forms import tao_form_danh_muc
        from danhmuc.views import CAU_HINH_DANH_MUC

        form = tao_form_danh_muc(CAU_HINH_DANH_MUC["tai-lieu"])(
            {"ma_tl": "tl_x", "ten_tl": "X", "nguon_tham_chieu": "WASI"}
        )
        self.assertTrue(form.is_valid())
        with mock.patch("danhmuc.services.NhatKy.ghi", side_effect=RuntimeError("lỗi giả lập")):
            with self.assertRaises(RuntimeError):
                luu_danh_muc(self.nguoi, form, "ma_tl")
        self.assertFalse(TaiLieu.objects.filter(ma_tl="TL_X").exists())

    def test_xoa_loi_o_buoc_cuoi_thi_ban_ghi_van_con(self):
        cay = self.dl.cay["CAO_SU"]
        pk = cay.pk  # delete() đặt pk = None trên đối tượng trong bộ nhớ dù CSDL đã hoàn tác
        with mock.patch("danhmuc.services.NhatKy.ghi", side_effect=RuntimeError("lỗi giả lập")):
            with self.assertRaises(RuntimeError):
                xoa_danh_muc(self.nguoi, cay, "ma_cay")
        self.assertTrue(CayTrong.objects.filter(pk=pk).exists())

    def test_xoa_bi_chan_nem_nghiep_vu_error_co_thong_bao(self):
        with self.assertRaisesMessage(NghiepVuError, "Không thể xóa «Cà phê»"):
            xoa_danh_muc(self.nguoi, self.dl.cay["CA_PHE"], "ma_cay")
