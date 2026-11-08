"""Import data from the legacy hand-written SQL schema into Django ORM tables."""
import json

from django.contrib.auth.hashers import identify_hasher, make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from cauhinh.models import CauHinhHeThong
from danhmuc.models import CayTrong, KyThuat, MuaVu, TaiLieu, TinhThanh
from hoidap.models import CauHoi, TraLoi
from taikhoan.models import MaKhoiPhucMatKhau, NguoiDung, NhatKy, VaiTro
from timkiem.models import LichSuTimKiem
from tuvan.models import LichSuTuVan, LuatTuVan


TABLES = (
    "vai_tro",
    "cau_hinh_he_thong",
    "cay_trong",
    "tinh_thanh",
    "mua_vu",
    "ky_thuat",
    "tai_lieu",
    "nguoi_dung",
    "nhat_ky",
    "luat_tu_van",
    "lich_su_tu_van",
    "cau_hoi",
    "lich_su_tim_kiem",
)

ROLE_CODES = {
    "ADMIN": VaiTro.ADMIN,
    "BIENTAP": VaiTro.BIEN_TAP,
    "BIEN_TAP": VaiTro.BIEN_TAP,
    "CHUYENGIA": VaiTro.CHUYEN_GIA,
    "CHUYEN_GIA": VaiTro.CHUYEN_GIA,
    "NONGDAN": VaiTro.NONG_DAN,
    "NONG_DAN": VaiTro.NONG_DAN,
}
CROP_CODES = {
    "CAFE": "CA_PHE",
    "HOTIEU": "HO_TIEU",
    "SAURIENG": "SAU_RIENG",
    "CAOSU": "CAO_SU",
}
PROVINCE_CODES = {
    "KONTUM": "KON_TUM",
    "GIALAI": "GIA_LAI",
    "DAKLAK": "DAK_LAK",
    "DAKNONG": "DAK_NONG",
    "LAMDONG": "LAM_DONG",
}
SEASON_CODES = {
    "MUAMUA": ("MUA_MUA", 5, 10),
    "MUAKHO": ("MUA_KHO", 11, 4),
    "QUANHNAM": ("QUANH_NAM", 1, 12),
}


def _rows(table):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {connection.ops.quote_name(table)} ORDER BY id")
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _password_hash(value):
    try:
        identify_hasher(value)
    except (ValueError, TypeError):
        return make_password(value)
    return value


def _category(value):
    normalized = (value or "").casefold()
    if "công nghiệp" in normalized:
        return CayTrong.CONG_NGHIEP
    if "ăn quả" in normalized or "ăn trái" in normalized:
        return CayTrong.AN_QUA
    if "ngắn ngày" in normalized or "lương thực" in normalized:
        return CayTrong.NGAN_NGAY
    return value if value in dict(CayTrong.NHOM_CAY_CHOICES) else CayTrong.NGAN_NGAY


def _technical_type(name):
    normalized = (name or "").casefold()
    if "tưới" in normalized:
        return "Tưới nước"
    if "bón" in normalized:
        return "Bón phân"
    if "sâu" in normalized or "bệnh" in normalized:
        return "Phòng bệnh"
    return "Khác"


def _import_log(row, user):
    details = row.get("chi_tiet")
    if not isinstance(details, str):
        details = json.dumps(details, ensure_ascii=False) if details is not None else ""
    defaults = {
        "nguoi_dung": user,
        "thoi_gian": row["thoi_gian"],
        "hanh_dong": row["hanh_dong"][:100],
        "doi_tuong": row.get("doi_tuong") or "",
        "chi_tiet": details or "",
    }
    return NhatKy.objects.get_or_create(**defaults)[0]


class Command(BaseCommand):
    help = "Copy data from legacy SQL tables into Django's application tables."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Write imported records; default is a dry run.")
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Clear Django application data covered by the legacy schema before importing it.",
        )
        parser.add_argument("--confirm-database", help="Must exactly match the configured database name.")
        parser.add_argument(
            "--allow-live-database",
            action="store_true",
            help="Allow writes to tuvannongnghiep_db; intended only after a verified backup.",
        )

    def handle(self, *args, **options):
        database_name = connection.settings_dict["NAME"]
        missing = sorted(set(TABLES) - set(connection.introspection.table_names()))
        if missing:
            raise CommandError(f"Không tìm thấy các bảng SQL nguồn: {', '.join(missing)}")
        data = {table: _rows(table) for table in TABLES}
        self.stdout.write(f"Database đích: {database_name}")
        for table in TABLES:
            self.stdout.write(f"{table}: {len(data[table])} dòng nguồn")
        if not options["apply"]:
            self.stdout.write(self.style.WARNING("Dry-run: chưa ghi dữ liệu. Dùng --apply để đồng bộ."))
            return
        if options["confirm_database"] != database_name:
            raise CommandError("--confirm-database phải khớp chính xác tên database hiện tại.")
        if database_name == "tuvannongnghiep_db" and not options["allow_live_database"]:
            raise CommandError(
                "Đã chặn ghi lên database chính. Chỉ thêm --allow-live-database sau khi đã sao lưu và kiểm tra trên bản sao."
            )
        self.import_data(data, replace=options["replace"])

    @transaction.atomic
    def import_data(self, data, *, replace=False):
        if replace:
            for model in (
                LichSuTimKiem,
                TraLoi,
                CauHoi,
                LichSuTuVan,
                NhatKy,
                MaKhoiPhucMatKhau,
                LuatTuVan,
                NguoiDung,
                TaiLieu,
                KyThuat,
                MuaVu,
                TinhThanh,
                CayTrong,
                CauHinhHeThong,
                VaiTro,
            ):
                model.objects.all().delete()

        roles = {}
        for row in data["vai_tro"]:
            code = ROLE_CODES.get(row["ma_vai_tro"], row["ma_vai_tro"])
            role, _ = VaiTro.objects.update_or_create(
                ma_vai_tro=code,
                defaults={"ten_vai_tro": row["ten_vai_tro"], "mo_ta": row.get("mo_ta") or ""},
            )
            roles[row["id"]] = role

        users = {}
        for row in data["nguoi_dung"]:
            role = roles.get(row["vai_tro_id"])
            if not role:
                raise CommandError(f"Không tìm thấy vai trò nguồn cho username={row['username']}.")
            is_admin = role.ma_vai_tro == VaiTro.ADMIN
            user, _ = NguoiDung.objects.update_or_create(
                username=row["username"],
                defaults={
                    "password": _password_hash(row["password"]),
                    "email": row.get("email") or "",
                    "is_active": row["is_active"],
                    "is_staff": is_admin,
                    "is_superuser": is_admin,
                    "vai_tro": role,
                    "date_joined": row.get("ngay_tao") or timezone.now(),
                },
            )
            users[row["id"]] = user

        crops = {}
        for row in data["cay_trong"]:
            code = CROP_CODES.get(row["ma_cay"], row["ma_cay"])
            crop, _ = CayTrong.objects.update_or_create(
                ma_cay=code,
                defaults={
                    "ten_cay": row["ten_cay"],
                    "nhom_cay": _category(row.get("nhom_cay")),
                    "dac_diem": row.get("dac_diem") or "",
                },
            )
            crops[row["id"]] = crop

        provinces = {}
        for row in data["tinh_thanh"]:
            code = PROVINCE_CODES.get(row["ma_tinh"], row["ma_tinh"])
            province, _ = TinhThanh.objects.update_or_create(
                ma_tinh=code,
                defaults={"ten_tinh": row["ten_tinh"], "vung_mien": "Tây Nguyên"},
            )
            provinces[row["id"]] = province

        seasons = {}
        for row in data["mua_vu"]:
            code, month_from, month_to = SEASON_CODES.get(
                row["ma_mua"], (row["ma_mua"], 1, 12)
            )
            season, _ = MuaVu.objects.update_or_create(
                ma_mua=code,
                defaults={
                    "ten_mua": row["ten_mua"],
                    "thoi_gian_tu": month_from,
                    "thoi_gian_den": month_to,
                },
            )
            seasons[row["id"]] = season

        techniques = {}
        for row in data["ky_thuat"]:
            technique, _ = KyThuat.objects.update_or_create(
                ma_kt=row["ma_kt"],
                defaults={
                    "ten_kt": row["ten_kt"],
                    "loai_kt": _technical_type(row["ten_kt"]),
                    "noi_dung": row.get("noi_dung") or "",
                },
            )
            techniques[row["id"]] = technique

        documents = {}
        for row in data["tai_lieu"]:
            document, _ = TaiLieu.objects.update_or_create(
                ma_tl=row["ma_tl"],
                defaults={
                    "ten_tl": (row.get("tieu_de") or row["ma_tl"])[:255],
                    "nguon_tham_chieu": row["nguon"],
                    "duong_dan": row.get("duong_dan") or "",
                },
            )
            documents[row["id"]] = document

        for row in data["cau_hinh_he_thong"]:
            value = row["gia_tri"]
            if isinstance(value, str):
                value = json.loads(value)
            if isinstance(value, dict) and {"w1", "w2", "w3"}.issubset(value):
                settings_values = [(key, value[key]) for key in ("w1", "w2", "w3")]
            else:
                settings_values = [(row["ten_cau_hinh"], value)]
            for name, setting_value in settings_values:
                CauHinhHeThong.objects.update_or_create(
                    ten_cau_hinh=name,
                    defaults={"gia_tri": str(setting_value)},
                )

        for row in data["luat_tu_van"]:
            crop = crops.get(row["cay_trong_id"])
            if not crop:
                raise CommandError(f"Không tìm thấy cây trồng cho luật {row['rule_id']}.")
            condition = row.get("condition_json") or {}
            if isinstance(condition, str):
                try:
                    condition = json.loads(condition)
                except json.JSONDecodeError as loi:
                    raise CommandError(f"condition_json không hợp lệ cho luật {row['rule_id']}.") from loi
            if not isinstance(condition, dict):
                raise CommandError(f"condition_json phải là object cho luật {row['rule_id']}.")
            if "tu_khoa" not in condition and "nhu_cau" in condition:
                condition["tu_khoa"] = condition.pop("nhu_cau")
            LuatTuVan.objects.update_or_create(
                rule_id=row["rule_id"],
                defaults={
                    "cay_tro": crop,
                    "tinh_thanh": provinces.get(row.get("tinh_thanh_id")),
                    "mua_vu": seasons.get(row.get("mua_vu_id")),
                    "ky_thuat": techniques.get(row.get("ky_thuat_id")),
                    "condition_json": condition,
                    "score_weight": row.get("score_weight") or 1,
                    "is_active": row.get("is_active", True),
                    "tai_lieu": documents.get(row.get("tai_lieu_id")),
                },
            )

        for row in data["nhat_ky"]:
            _import_log(row, users.get(row.get("nguoi_dung_id")))

        histories = {}
        for row in data["lich_su_tu_van"]:
            history, _ = LichSuTuVan.objects.update_or_create(
                ma_lstv=row["ma_lstv"],
                defaults={
                    "nguoi_dung": users.get(row.get("nguoi_dung_id")),
                    "nhu_cau": row["nhu_cau"],
                    "tinh_thanh": (
                        provinces[row["tinh_thanh_id"]].ten_tinh
                        if row.get("tinh_thanh_id") in provinces else ""
                    ),
                    "mua_vu": (
                        seasons[row["mua_vu_id"]].ten_mua
                        if row.get("mua_vu_id") in seasons else ""
                    ),
                    "ket_qua_json": row.get("ket_qua_json") or [],
                    "thoi_gian": row["thoi_gian"],
                },
            )
            histories[row["id"]] = history

        questions = {}
        for row in data["cau_hoi"]:
            owner = users.get(row["nguoi_dung_id"])
            if not owner:
                raise CommandError(f"Không tìm thấy người hỏi cho câu hỏi {row['ma_ch']}.")
            question, _ = CauHoi.objects.update_or_create(
                ma_ch=row["ma_ch"],
                defaults={
                    "nguoi_dung": owner,
                    "noi_dung": row["noi_dung"],
                    "trang_thai": row["trang_thai"],
                    "thoi_gian": row["ngay_hoi"],
                },
            )
            questions[row["id"]] = question
            answer_text = row.get("tra_loi")
            if answer_text:
                responder_id = row.get("nguoi_tra_loi_id")
                TraLoi.objects.update_or_create(
                    cau_hoi=question,
                    defaults={
                        "nguoi_tra_loi": users.get(responder_id),
                        "noi_dung": answer_text,
                        "la_tu_dong": responder_id is None,
                        "thoi_gian": row.get("ngay_tra_loi") or row["ngay_hoi"],
                    },
                )

        for row in data["lich_su_tim_kiem"]:
            LichSuTimKiem.objects.update_or_create(
                ma_ls=row["ma_ls"],
                defaults={
                    "tu_khoa": row["tu_khoa"][:255],
                    "thoi_gian": row["thoi_gian"],
                    "lich_su_tu_van": histories.get(row.get("lich_su_tu_van_id")),
                    "cau_hoi": questions.get(row.get("cau_hoi_id")),
                },
            )

        mode = "thay dữ liệu Django bằng dữ liệu nguồn" if replace else "gộp/cập nhật dữ liệu Django"
        self.stdout.write(self.style.SUCCESS(f"Đồng bộ dữ liệu SQL thủ công sang Django ORM hoàn tất ({mode})."))
