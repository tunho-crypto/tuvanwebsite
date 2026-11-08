"""Nạp dữ liệu mẫu. Chạy lại nhiều lần không lỗi, không trùng (dùng get_or_create, không ghi đè dữ liệu đã sửa)."""
from django.core.management.base import BaseCommand
from django.db import transaction

from cauhinh.models import CauHinhHeThong
from danhmuc.models import CayTrong, KyThuat, MuaVu, TaiLieu, TinhThanh
from taikhoan import du_lieu_mau as dl
from taikhoan.models import NguoiDung, VaiTro
from tuvan.models import LuatTuVan


class Command(BaseCommand):
    help = "Nạp dữ liệu mẫu: vai trò, 4 tài khoản, 12 cây, 5 tỉnh, 2 mùa, tài liệu, trọng số, luật tư vấn."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dat-lai-mat-khau",
            action="store_true",
            help="Đặt lại mật khẩu 4 tài khoản mẫu về 123456 (mặc định chỉ đặt khi tạo mới).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        moi = {}

        def lay_hoac_tao(ten, model, tra_cuu, mac_dinh):
            doi_tuong, da_tao = model.objects.get_or_create(**tra_cuu, defaults=mac_dinh)
            moi[ten] = moi.get(ten, 0) + int(da_tao)
            return doi_tuong

        vai_tro = {}
        for ma, ten, mo_ta in dl.VAI_TRO:
            vai_tro[ma] = lay_hoac_tao("vai trò", VaiTro, {"ma_vai_tro": ma}, {"ten_vai_tro": ten, "mo_ta": mo_ta})

        for username, ho, ten, ma_vt in dl.TAI_KHOAN:
            nd, da_tao = NguoiDung.objects.get_or_create(
                username=username,
                defaults={"last_name": ho, "first_name": ten, "vai_tro": vai_tro[ma_vt], "is_active": True},
            )
            if da_tao or options["dat_lai_mat_khau"]:
                nd.set_password(dl.MAT_KHAU_MAC_DINH)
                nd.save(update_fields=["password"])
            moi["tài khoản"] = moi.get("tài khoản", 0) + int(da_tao)

        cay = {}
        for ma, ten, nhom, dac_diem in dl.CAY_TRONG:
            cay[ma] = lay_hoac_tao("cây trồng", CayTrong, {"ma_cay": ma},
                                   {"ten_cay": ten, "nhom_cay": nhom, "dac_diem": dac_diem})
        tinh = {}
        for ma, ten in dl.TINH_THANH:
            tinh[ma] = lay_hoac_tao("tỉnh thành", TinhThanh, {"ma_tinh": ma},
                                    {"ten_tinh": ten, "vung_mien": "Tây Nguyên"})
        mua = {}
        for ma, ten, tu, den in dl.MUA_VU:
            mua[ma] = lay_hoac_tao("mùa vụ", MuaVu, {"ma_mua": ma},
                                   {"ten_mua": ten, "thoi_gian_tu": tu, "thoi_gian_den": den})
        tai_lieu = {}
        for ma, ten, nguon in dl.TAI_LIEU:
            tai_lieu[ma] = lay_hoac_tao("tài liệu", TaiLieu, {"ma_tl": ma},
                                        {"ten_tl": ten, "nguon_tham_chieu": nguon})
        for ma, ten, loai, noi_dung in dl.KY_THUAT:
            lay_hoac_tao("kỹ thuật", KyThuat, {"ma_kt": ma},
                         {"ten_kt": ten, "loai_kt": loai, "noi_dung": noi_dung})
        for ten, gia_tri in dl.CAU_HINH:
            lay_hoac_tao("cấu hình", CauHinhHeThong, {"ten_cau_hinh": ten}, {"gia_tri": gia_tri})

        for rule_id, ma_cay, ma_tinh, ma_mua, tu_khoa, trong_so, ma_tl, kich_hoat in dl.LUAT_TU_VAN:
            lay_hoac_tao(
                "luật tư vấn",
                LuatTuVan,
                {"rule_id": rule_id},
                {
                    "cay_tro": cay[ma_cay],
                    "tinh_thanh": tinh[ma_tinh] if ma_tinh else None,
                    "mua_vu": mua[ma_mua] if ma_mua else None,
                    "condition_json": {"tu_khoa": tu_khoa},
                    "score_weight": trong_so,
                    "tai_lieu": tai_lieu[ma_tl],
                    "is_active": kich_hoat,
                },
            )

        tom_tat = ", ".join(f"{so} {ten}" for ten, so in moi.items())
        self.stdout.write(self.style.SUCCESS(f"Nạp dữ liệu mẫu xong. Tạo mới: {tom_tat}."))
