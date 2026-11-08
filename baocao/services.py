"""Dữ liệu cho các báo cáo Excel. Mỗi hàm trả về một «sheet» {ten, cot, dong, ...} cho baocao.excel.tao_xlsx.
Truy vấn dùng annotate/select_related nên số truy vấn không tăng theo số dòng (không bị N+1)."""
from django.db.models import Count, Q
from django.db.models.functions import Collate

from baocao.excel import DINH_DANG_NGAY_GIO
from danhmuc.models import CayTrong
from tuvan.models import LichSuTuVan, LuatTuVan
from tuvan.services import THONG_BAO_NGOAI_PHAM_VI


def sheet_cay_trong():
    # Collation C sorts these ASCII identifiers consistently, regardless of
    # the PostgreSQL server's locale (where '_' may otherwise sort before letters).
    cay = CayTrong.objects.annotate(so_luat=Count("luat_tu_van", filter=Q(luat_tu_van__is_active=True))).order_by(Collate("ma_cay", "C"))
    return {
        "ten": "Cây trồng",
        "cot": ["Mã cây", "Tên cây", "Nhóm cây", "Đặc điểm", "Số luật đang áp dụng"],
        "dong": ([c.ma_cay, c.ten_cay, c.get_nhom_cay_display(), c.dac_diem, c.so_luat] for c in cay),
    }


def sheet_luat_hien_hanh():
    """Chỉ các luật đang bật (is_active=True), tức là các luật hiện đang được dùng để tư vấn."""
    luat = LuatTuVan.objects.filter(is_active=True).select_related("cay_tro", "tinh_thanh", "mua_vu", "tai_lieu").order_by("rule_id")
    return {
        "ten": "Luật tư vấn hiện hành",
        "cot": ["Mã luật", "Mã cây", "Cây trồng", "Tỉnh thành", "Mùa vụ", "Từ khóa nhu cầu", "Hệ số ưu tiên", "Tài liệu", "Nguồn tham chiếu"],
        "dong": (
            [
                l.rule_id,
                l.cay_tro.ma_cay,
                l.cay_tro.ten_cay,
                l.tinh_thanh.ten_tinh if l.tinh_thanh else "Mọi tỉnh",
                l.mua_vu.ten_mua if l.mua_vu else "Mọi mùa",
                "; ".join((l.condition_json or {}).get("tu_khoa", [])),
                l.score_weight,
                l.tai_lieu.ten_tl if l.tai_lieu else "",
                l.tai_lieu.nguon_tham_chieu if l.tai_lieu else "",
            ]
            for l in luat
        ),
        "dinh_dang_cot": {6: "0.00"},
    }


def _tom_tat_lich_su(ls):
    kq = ls.ket_qua_json or {}
    de_xuat = kq.get("de_xuat", [])
    w = kq.get("trong_so", {})
    return [
        ls.ma_lstv,
        ls.thoi_gian,
        ls.nguoi_dung.username if ls.nguoi_dung else "",
        ls.nhu_cau,
        ls.tinh_thanh,
        ls.mua_vu,
        "Có đề xuất" if kq.get("trong_pham_vi") else "Ngoài phạm vi",
        "; ".join(f"{dx['ten_cay']} ({dx['diem']:.3f})" for dx in de_xuat) if kq.get("trong_pham_vi") else THONG_BAO_NGOAI_PHAM_VI,
        de_xuat[0]["diem"] if de_xuat else None,
        f"{w.get('w1')} / {w.get('w2')} / {w.get('w3')}" if w else "",
    ]


def sheet_lich_su_tu_van(tu_ngay=None, den_ngay=None):
    qs = LichSuTuVan.objects.select_related("nguoi_dung").order_by("thoi_gian", "id")
    if tu_ngay:
        qs = qs.filter(thoi_gian__date__gte=tu_ngay)
    if den_ngay:
        qs = qs.filter(thoi_gian__date__lte=den_ngay)
    return {
        "ten": "Lịch sử tư vấn",
        "cot": ["Mã", "Thời gian", "Người dùng", "Nhu cầu", "Tỉnh thành", "Mùa vụ", "Kết quả", "Đề xuất (điểm)", "Điểm cao nhất", "Trọng số w1 / w2 / w3"],
        "dong": (_tom_tat_lich_su(ls) for ls in qs),
        "dinh_dang_cot": {1: DINH_DANG_NGAY_GIO, 8: "0.000"},
        "ghi_chu": [mo_ta_khoang(tu_ngay, den_ngay)],
    }


def mo_ta_khoang(tu_ngay, den_ngay):
    tu = f"{tu_ngay:%d/%m/%Y}" if tu_ngay else "đầu"
    den = f"{den_ngay:%d/%m/%Y}" if den_ngay else "nay"
    return f"Khoảng thời gian: từ {tu} đến {den}"
