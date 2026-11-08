"""Thống kê (tuần 5): đọc từ dữ liệu sẵn có, không ghi gì.

- Tư vấn: số lượt, trong/ngoài phạm vi, theo tỉnh, theo mùa, theo ngày, cây được đề xuất (từ ket_qua_json của LichSuTuVan).
- Hỏi đáp: tỷ lệ câu hỏi được trả lời.
- Tìm kiếm: các từ khóa tìm nhiều nhất (gộp «Cà phê» và «ca phe» thành một).

Mọi hàm nhận khoảng ngày [tu_ngay, den_ngay] (gồm cả hai đầu, theo múi giờ của hệ thống); None là không giới hạn.
Tỷ lệ là Decimal trong [0, 1] làm tròn 4 chữ số; chia cho 0 thì trả None (không phải 0) để không nhầm «không có dữ liệu» với «0%».
"""
from collections import Counter
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Count
from django.db.models.functions import TruncDate

from hoidap.models import CauHoi
from timkiem.models import LichSuTimKiem
from tuvan.models import LichSuTuVan
from tuvan.services import chuan_hoa_van_ban

TOP_MAC_DINH = 10
LAM_TRON = Decimal("0.0001")
NHAN_KHONG_XAC_DINH_TINH = "(Không xác định)"
NHAN_KHONG_CHON_MUA = "Không chọn mùa"


def ty_le(tu, mau):
    """tu / mau làm tròn 4 chữ số; mau = 0 thì None."""
    if not mau:
        return None
    return (Decimal(tu) / Decimal(mau)).quantize(LAM_TRON, rounding=ROUND_HALF_UP)


def _loc_ngay(qs, truong, tu_ngay, den_ngay):
    if tu_ngay:
        qs = qs.filter(**{f"{truong}__date__gte": tu_ngay})
    if den_ngay:
        qs = qs.filter(**{f"{truong}__date__lte": den_ngay})
    return qs


def _dem_nhom(qs, truong, nhan_rong):
    """[(nhãn, số lượt)] giảm dần theo số lượt, bằng nhau thì theo nhãn.
    Sắp xếp bằng Python (không dựa vào collation của CSDL) để thứ tự giống nhau trên mọi máy."""
    dong = qs.values(truong).annotate(n=Count("id")).order_by()  # order_by() rỗng để GROUP BY không dính Meta.ordering
    return sorted(((d[truong] or nhan_rong, d["n"]) for d in dong), key=lambda x: (-x[1], x[0]))


def thong_ke_tu_van(tu_ngay=None, den_ngay=None):
    qs = _loc_ngay(LichSuTuVan.objects.all(), "thoi_gian", tu_ngay, den_ngay)
    tong = qs.count()
    trong = qs.filter(ket_qua_json__trong_pham_vi=True).count()

    so_hang_1, so_xuat_hien, ten_cay = Counter(), Counter(), {}
    for ket_qua in qs.values_list("ket_qua_json", flat=True).iterator(chunk_size=1000):
        if not ket_qua.get("trong_pham_vi"):
            continue
        for dx in ket_qua.get("de_xuat", []):
            ma = dx["ma_cay"]
            ten_cay.setdefault(ma, dx.get("ten_cay", ma))
            so_xuat_hien[ma] += 1
            if dx.get("thu_hang") == 1:
                so_hang_1[ma] += 1
    cay = [
        {"ma_cay": ma, "ten_cay": ten_cay[ma], "so_lan_hang_1": so_hang_1[ma], "so_lan_xuat_hien": so_xuat_hien[ma]}
        for ma in ten_cay
    ]
    cay.sort(key=lambda c: (-c["so_lan_hang_1"], -c["so_lan_xuat_hien"], c["ten_cay"]))

    theo_ngay = qs.annotate(ngay=TruncDate("thoi_gian")).values("ngay").annotate(n=Count("id")).order_by("ngay")
    return {
        "tong": tong,
        "trong_pham_vi": trong,
        "ngoai_pham_vi": tong - trong,
        "ty_le_trong_pham_vi": ty_le(trong, tong),
        "theo_tinh": _dem_nhom(qs, "tinh_thanh", NHAN_KHONG_XAC_DINH_TINH),
        "theo_mua": _dem_nhom(qs, "mua_vu", NHAN_KHONG_CHON_MUA),
        "theo_ngay": [(d["ngay"], d["n"]) for d in theo_ngay],
        "cay_duoc_de_xuat": cay,
    }


def thong_ke_hoi_dap(tu_ngay=None, den_ngay=None):
    """Hai cách hiểu «tỷ lệ câu hỏi được trả lời» (cả hai đều được báo cáo):
    - ty_le_da_tra_loi: trong các câu hỏi thuộc phạm vi hỗ trợ, bao nhiêu câu đã được CHUYÊN GIA trả lời = da / (da + cho).
    - ty_le_co_tra_loi: bao nhiêu câu có câu trả lời, kể cả trả lời tự động = (da + ngoài phạm vi) / tổng.
    """
    qs = _loc_ngay(CauHoi.objects.all(), "thoi_gian", tu_ngay, den_ngay)
    dem = dict(qs.values_list("trang_thai").annotate(n=Count("id")).order_by())
    cho, da, ngoai = dem.get(CauHoi.CHO_TRA_LOI, 0), dem.get(CauHoi.DA_TRA_LOI, 0), dem.get(CauHoi.NGOAI_PHAM_VI, 0)
    tong = cho + da + ngoai
    return {
        "tong": tong,
        "cho_tra_loi": cho,
        "da_tra_loi": da,
        "ngoai_pham_vi": ngoai,
        "ty_le_da_tra_loi": ty_le(da, da + cho),
        "ty_le_co_tra_loi": ty_le(da + ngoai, tong),
        "ty_le_ngoai_pham_vi": ty_le(ngoai, tong),
    }


def thong_ke_tim_kiem(tu_ngay=None, den_ngay=None, top=TOP_MAC_DINH):
    qs = _loc_ngay(LichSuTimKiem.objects.all(), "thoi_gian", tu_ngay, den_ngay)
    so_lan, dang_viet = Counter(), {}
    tong = 0
    for tu_khoa in qs.values_list("tu_khoa", flat=True).iterator(chunk_size=1000):
        khoa = chuan_hoa_van_ban(tu_khoa)
        if not khoa:
            continue
        tong += 1
        so_lan[khoa] += 1
        dang_viet.setdefault(khoa, Counter())[tu_khoa.lower()] += 1
    xep_hang = sorted(so_lan.items(), key=lambda kv: (-kv[1], kv[0]))  # bằng nhau thì theo từ khóa chuẩn hóa, kết quả ổn định
    return {
        "tong": tong,
        "so_tu_khoa_khac_nhau": len(so_lan),
        "top": [
            {"tu_khoa": sorted(dang_viet[k].items(), key=lambda kv: (-kv[1], kv[0]))[0][0], "so_lan": n} for k, n in xep_hang[:top]
        ],
    }


def thong_ke(tu_ngay=None, den_ngay=None, top=TOP_MAC_DINH):
    return {
        "khoang": {"tu_ngay": tu_ngay, "den_ngay": den_ngay},
        "tu_van": thong_ke_tu_van(tu_ngay, den_ngay),
        "hoi_dap": thong_ke_hoi_dap(tu_ngay, den_ngay),
        "tim_kiem": thong_ke_tim_kiem(tu_ngay, den_ngay, top),
    }
