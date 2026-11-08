"""Menu theo vai trò. Thêm mục mới ở các tuần sau chỉ cần thêm vào MENU.

Mỗi mục: {"ten", "url": (tên_url, kwargs) , "vai_tro": tuple|None} hoặc nhóm xổ xuống {"ten", "nhom": [mục...], "vai_tro"}.
"""
from django.conf import settings
from django.urls import reverse

MENU = [
    {"ten": "Trang chủ", "url": ("trang_chu", {})},
    {"ten": "Giới thiệu", "url": ("gioi_thieu", {})},
    {
        "ten": "Danh mục",
        "nhom": [
            {"ten": "Cây trồng", "url": ("danhmuc:ds", {"muc": "cay-trong"})},
            {"ten": "Tỉnh thành", "url": ("danhmuc:ds", {"muc": "tinh-thanh"})},
            {"ten": "Mùa vụ", "url": ("danhmuc:ds", {"muc": "mua-vu"})},
            {"ten": "Kỹ thuật", "url": ("danhmuc:ds", {"muc": "ky-thuat"})},
            {"ten": "Tài liệu", "url": ("danhmuc:ds", {"muc": "tai-lieu"})},
        ],
    },
    {
        "ten": "Tra cứu",
        "nhom": [
            {"ten": "Tìm kiếm", "url": ("timkiem:tim_kiem", {})},
            {"ten": "Truy xuất nguồn", "url": ("truyxuat:truy_xuat", {})},
        ],
    },
    {
        "ten": "Tư vấn",
        "nhom": [
            {"ten": "Tư vấn cây trồng", "url": ("tuvan:tu_van", {})},
            {"ten": "Lịch sử tư vấn", "url": ("tuvan:lich_su", {})},
            {"ten": "Luật tư vấn", "url": ("tuvan:luat_ds", {}), "vai_tro": ("ADMIN", "BIEN_TAP")},
        ],
    },
    {"ten": "Hỏi đáp", "url": ("hoidap:ds", {}), "vai_tro": ("ADMIN", "CHUYEN_GIA", "NONG_DAN")},
    {
        "ten": "Báo cáo",
        "vai_tro": ("ADMIN",),
        "nhom": [
            {"ten": "Xuất Excel", "url": ("baocao:bao_cao", {})},
            {"ten": "Thống kê", "url": ("thongke:thong_ke", {})},
        ],
    },
    {
        "ten": "Quản trị",
        "vai_tro": ("ADMIN",),
        "nhom": [
            {"ten": "Người dùng", "url": ("nguoi_dung_ds", {})},
            {"ten": "Nhật ký", "url": ("nhat_ky", {})},
            {"ten": "Trọng số tư vấn", "url": ("cauhinh:trong_so", {})},
        ],
    },
]


def _duoc_phep(muc, nguoi_dung):
    vai_tro = muc.get("vai_tro")
    return not vai_tro or nguoi_dung.co_vai_tro(*vai_tro)


def _tinh_url(muc):
    ten_url, kwargs = muc["url"]
    return reverse(ten_url, kwargs=kwargs)


def _dung_muc(url, duong_dan):
    return duong_dan == url if url == "/" else duong_dan.startswith(url)


def menu(request):
    nguoi_dung = getattr(request, "user", None)
    if nguoi_dung is None or not nguoi_dung.is_authenticated:
        return {"menu": []}
    ket_qua = []
    for goc in MENU:
        if not _duoc_phep(goc, nguoi_dung):
            continue
        muc = {"ten": goc["ten"]}
        if "nhom" in goc:
            muc["nhom"] = [
                {"ten": con["ten"], "url": _tinh_url(con), "active": False} for con in goc["nhom"] if _duoc_phep(con, nguoi_dung)
            ]
            # Chỉ đánh dấu mục con có đường dẫn khớp DÀI NHẤT (/tu-van/lich-su/ thắng /tu-van/)
            khop = [c for c in muc["nhom"] if _dung_muc(c["url"], request.path)]
            if khop:
                max(khop, key=lambda c: len(c["url"]))["active"] = True
            muc["active"] = any(c["active"] for c in muc["nhom"])
        else:
            muc["url"] = _tinh_url(goc)
            muc["active"] = _dung_muc(muc["url"], request.path)
        ket_qua.append(muc)
    return {"menu": ket_qua}


def giao_dien(request):
    """Cờ cho base.html: True thì dùng Bootstrap cục bộ, không gọi CDN."""
    return {"bootstrap_cuc_bo": settings.BOOTSTRAP_CUC_BO}
