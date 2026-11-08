"""Sinh tài liệu từ MÃ NGUỒN (không gõ tay nên không thể lệch hệ thống):
    python tai_lieu/tao_tai_lieu.py   ->  TU_DIEN_DU_LIEU.md (kèm ERD Mermaid)  và  MA_TRAN_PHAN_QUYEN.md
Không chứa ngày giờ để file sinh ra ổn định (có test so sánh với bản đã lưu)."""
import os
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tuvannongnghiep.settings")

import django  # noqa: E402

django.setup()

from django.apps import apps  # noqa: E402
from django.db import connection, models  # noqa: E402
from django.urls import URLResolver, get_resolver  # noqa: E402

THU_MUC = Path(__file__).resolve().parent
TEP_TU_DIEN, TEP_MA_TRAN = THU_MUC / "TU_DIEN_DU_LIEU.md", THU_MUC / "MA_TRAN_PHAN_QUYEN.md"
CAC_APP = ["taikhoan", "danhmuc", "tuvan", "timkiem", "hoidap", "cauhinh"]  # 6 app có model
VAI_TRO = [("ADMIN", "Quản trị"), ("BIEN_TAP", "Biên tập"), ("CHUYEN_GIA", "Chuyên gia"), ("NONG_DAN", "Nông dân")]
CONG_KHAI = {
    "trang_chu", "gioi_thieu", "dang_nhap", "dang_ky", "dang_xuat", "quen_mat_khau",
    "quen_mat_khau_done", "quen_mat_khau_ma", "quen_mat_khau_complete",
}
MA_DEFAULT = {"dict": "{}", "now": "thời điểm hiện tại"}


def _o(x):
    return " ".join(str(x).split()).replace("|", "/")


# ====================================================================================== Từ điển dữ liệu
def cac_model():
    return [m for ten in CAC_APP for m in apps.get_app_config(ten).get_models()]


def rang_buoc(f):
    cac = []
    if f.primary_key:
        cac.append("khóa chính")
    elif f.is_relation:
        cac.append(f"khóa ngoại → {f.related_model.__name__} ({f.remote_field.on_delete.__name__})")
    if f.unique and not f.primary_key:
        cac.append("duy nhất")
    cac.append("cho phép NULL" if f.null else "NOT NULL")
    if f.has_default():
        mac_dinh = f.default
        cac.append("mặc định " + MA_DEFAULT.get(getattr(mac_dinh, "__name__", ""), repr(mac_dinh)) if callable(mac_dinh) else f"mặc định {mac_dinh!r}")
    if getattr(f, "auto_now_add", False):
        cac.append("tự ghi thời điểm tạo")
    if f.choices:
        cac.append("giá trị: " + ", ".join(f"{ma} ({ten})" for ma, ten in f.choices))
    if f.db_index and not f.unique and not f.primary_key and not f.is_relation:
        cac.append("có chỉ mục")
    return "; ".join(cac)


def mo_ta_model(m):
    """Dòng đầu của docstring; model không có docstring thì Django tự gán «Ten(id, ...)», khi đó dùng tên hiển thị."""
    doc = (m.__doc__ or "").strip().splitlines()[0] if m.__doc__ else ""
    return _o(m._meta.verbose_name if (not doc or doc.startswith(m.__name__ + "(")) else doc)


def cac_cot(model):
    return [f for f in model._meta.concrete_fields]


def tao_tu_dien():
    models_ = cac_model()
    dong = [
        "# Từ điển dữ liệu",
        "",
        f"Sinh tự động từ mã nguồn: **{len(models_)} bảng** trong {len(CAC_APP)} app (chưa tính các bảng của Django như phiên đăng nhập, loại nội dung, quyền).",
        "Kiểu dữ liệu là kiểu thật trong PostgreSQL.",
        "",
        "| Bảng (class) | App | Ý nghĩa |",
        "|---|---|---|",
    ]
    for m in models_:
        dong.append(f"| {m._meta.db_table} ({m.__name__}) | {m._meta.app_label} | {mo_ta_model(m)} |")
    dong += ["", "## Sơ đồ quan hệ (ERD)", "", "```mermaid", tao_erd(models_), "```", ""]
    dong.append("Ký hiệu: `||--o{` một-nhiều bắt buộc; `|o--o{` một-nhiều tùy chọn (khóa ngoại cho phép NULL); `||--o|` một-một.")
    for m in models_:
        dong += ["", f"## {m.__name__} (`{m._meta.db_table}`)", "", mo_ta_model(m), "",
                 "| Cột | Kiểu (PostgreSQL) | Ràng buộc | Ý nghĩa |", "|---|---|---|---|"]
        for f in cac_cot(m):
            dong.append(f"| {f.column} | {_o(f.db_type(connection))} | {_o(rang_buoc(f))} | {_o(f.verbose_name)} |")
        if m.__name__ == "NguoiDung":
            dong += ["", "Kế thừa `AbstractUser` của Django nên có thêm các cột chuẩn (mật khẩu đã băm, lần đăng nhập cuối, ngày tạo...). "
                         "Các quan hệ nhiều-nhiều `groups`, `user_permissions` của Django không được dùng (phân quyền theo `vai_tro`)."]
    return "\n".join(dong) + "\n"


def tao_erd(models_):
    kieu = lambda f: f.db_type(connection).split("(")[0].replace(" ", "_")
    dong = ["erDiagram"]
    for m in models_:
        dong.append(f"    {m.__name__} {{")
        for f in cac_cot(m):
            ghi_chu = " PK" if f.primary_key else (" FK" if f.is_relation else "")
            dong.append(f"        {kieu(f)} {f.column}{ghi_chu}")
        dong.append("    }")
    for m in models_:
        for f in cac_cot(m):
            if not f.is_relation:
                continue
            dich = f.related_model.__name__
            if isinstance(f, models.OneToOneField):
                dong.append(f'    {dich} ||--o| {m.__name__} : "{f.name}"')
            else:
                dong.append(f'    {dich} {"|o" if f.null else "||"}--o{{ {m.__name__} : "{f.name}"')
    return "\n".join(dong)


# ====================================================================================== Ma trận phân quyền
MO_TA = {
    "trang_chu": "Trang chủ (công khai trước đăng nhập)", "gioi_thieu": "Giới thiệu hệ thống (menu thành viên)",
    "doi_mat_khau": "Đổi mật khẩu của chính mình", "dang_nhap": "Đăng nhập",
    "dang_ky": "Đăng ký tài khoản nông dân", "dang_xuat": "Đăng xuất (chỉ POST)",
    "quen_mat_khau": "Yêu cầu mã khôi phục mật khẩu qua email",
    "quen_mat_khau_done": "Thông báo đã gửi mã khôi phục",
    "quen_mat_khau_ma": "Xác minh mã email và đặt mật khẩu mới",
    "quen_mat_khau_complete": "Thông báo đặt lại mật khẩu thành công",
    "nguoi_dung_ds": "Danh sách người dùng", "nguoi_dung_them": "Thêm người dùng", "nguoi_dung_sua": "Sửa người dùng",
    "nguoi_dung_khoa": "Khóa / mở khóa tài khoản (POST)", "nhat_ky": "Nhật ký hệ thống",
    "danhmuc:ds": "Xem danh mục (5 bảng)", "danhmuc:them": "Thêm bản ghi danh mục", "danhmuc:sua": "Sửa bản ghi danh mục", "danhmuc:xoa": "Xóa bản ghi danh mục",
    "tuvan:tu_van": "Form tư vấn, «Xem kết quả» (ghi lịch sử)", "tuvan:api_tinh_diem": "API tính nhanh, không ghi CSDL (POST)",
    "tuvan:lich_su": "Danh sách lịch sử tư vấn", "tuvan:lich_su_chi_tiet": "Kết quả đã lưu của một lần tư vấn",
    "tuvan:luat_ds": "Danh sách luật tư vấn", "tuvan:luat_them": "Thêm luật", "tuvan:luat_sua": "Sửa luật", "tuvan:luat_xoa": "Xóa luật",
    "tuvan:luat_bat_tat": "Bật / tắt luật (POST)", "timkiem:tim_kiem": "Tìm kiếm cây trồng, kỹ thuật, mùa vụ", "truyxuat:truy_xuat": "Truy xuất nguồn: luật → tài liệu",
    "hoidap:ds": "Danh sách câu hỏi", "hoidap:them": "Đặt câu hỏi", "hoidap:chi_tiet": "Xem câu hỏi và câu trả lời", "hoidap:tra_loi": "Chuyên gia trả lời",
    "cauhinh:trong_so": "Cấu hình trọng số w1, w2, w3", "thongke:thong_ke": "Thống kê (có xuất Excel với ?xuat=xlsx)",
    "baocao:bao_cao": "Trang báo cáo", "baocao:cay_trong": "Tải Excel cây trồng", "baocao:luat": "Tải Excel luật hiện hành", "baocao:lich_su": "Tải Excel lịch sử tư vấn",
}
PHAM_VI_DU_LIEU = {
    "tuvan:lich_su": "Nông dân chỉ thấy lịch sử của mình", "tuvan:lich_su_chi_tiet": "Nông dân chỉ mở được của mình (của người khác: 404)",
    "hoidap:ds": "Nông dân chỉ thấy câu hỏi của mình", "hoidap:chi_tiet": "Nông dân chỉ mở được câu hỏi của mình (của người khác: 404)",
    "hoidap:tra_loi": "Chỉ khi câu hỏi đang «Chờ trả lời»", "tuvan:api_tinh_diem": "Không ghi CSDL",
}


def tat_ca_duong_dan():
    """{tên url: URLPattern} cho cả url có namespace."""
    def duyet(mau, ns=""):
        for p in mau:
            if isinstance(p, URLResolver):
                yield from duyet(p.url_patterns, f"{ns}{p.namespace}:" if p.namespace else ns)
            elif p.name is not None:
                yield f"{ns}{p.name}", p
    return dict(duyet(get_resolver().url_patterns))


def _duong_dan_day_du(ten, mau):
    """Đường dẫn đầy đủ dạng /danh-muc/<muc>/<id>/sua/, dựng bằng reverse với giá trị mẫu rồi thay lại bằng tên tham số."""
    from django.urls import reverse

    tham_so = {k: ("cay-trong" if k == "muc" else 987654321) for k in mau.pattern.converters}
    url = reverse(ten, kwargs=tham_so)
    if "muc" in tham_so:
        url = url.replace("/cay-trong/", "/<muc>/", 1)
    if "pk" in tham_so:
        url = url.replace("987654321", "<id>")
    return url


def _phuong_thuc(view_class):
    """GET / POST thật sự được view hỗ trợ (có khai báo và không bị loại khỏi http_method_names)."""
    return ", ".join(m.upper() for m in ("get", "post") if m in view_class.http_method_names and hasattr(view_class, m))


def tao_ma_tran():
    cac = tat_ca_duong_dan()
    thieu = sorted(set(cac) - set(MO_TA))
    if thieu:
        raise KeyError(f"Thiếu mô tả cho đường dẫn: {thieu}")
    dong = [
        "# Ma trận phân quyền",
        "",
        f"Sinh tự động từ mã nguồn: **{len(cac)} đường dẫn** (khai báo `vai_tro_cho_phep` của từng view). ✔ = được phép.",
        "",
        "Các đường dẫn ghi «Công khai» dùng được khi chưa đăng nhập; những đường dẫn còn lại chuyển về `/dang-nhap/?next=...` (302). Đã đăng nhập nhưng sai vai trò → trang 403; tài khoản bị khóa → bị đăng xuất ở yêu cầu kế tiếp.",
        "",
        "| Đường dẫn | Chức năng | Phương thức | " + " | ".join(t for _, t in VAI_TRO) + " | Phạm vi dữ liệu |",
        "|---|---|---|" + "|".join(["---"] * len(VAI_TRO)) + "|---|",
    ]
    for ten, mau in sorted(cac.items(), key=lambda kv: _duong_dan_day_du(*kv)):
        vc = mau.callback.view_class
        if ten in CONG_KHAI:  # không cần đăng nhập
            vai, pham_vi = ["✔"] * len(VAI_TRO), "Công khai"
        else:
            khai_bao = vc.vai_tro_cho_phep  # None nghĩa là mọi người dùng đã đăng nhập
            vai = ["✔" if (not khai_bao or ma in khai_bao) else "" for ma, _ in VAI_TRO]
            pham_vi = PHAM_VI_DU_LIEU.get(ten, "")
        dong.append(f"| `{_duong_dan_day_du(ten, mau)}` | {_o(MO_TA[ten])} | {_phuong_thuc(vc)} | " + " | ".join(vai) + f" | {_o(pham_vi)} |")
    return "\n".join(dong) + "\n"


def main():
    TEP_TU_DIEN.write_text(tao_tu_dien(), encoding="utf-8")
    TEP_MA_TRAN.write_text(tao_ma_tran(), encoding="utf-8")
    print(f"Đã ghi {TEP_TU_DIEN.name} và {TEP_MA_TRAN.name} vào {THU_MUC}")


if __name__ == "__main__":
    main()
