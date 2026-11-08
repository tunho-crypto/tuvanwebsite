"""Cấu hình trọng số w1, w2, w3 (quy tắc 5): chỉ ADMIN sửa, trong một transaction."""
from django.db import transaction

from cauhinh.models import CauHinhHeThong
from taikhoan.models import NhatKy
from tuvan.services import TEN_TRONG_SO, kiem_tra_trong_so


def chuoi_trong_so(so):
    """Decimal('0.80') -> '0.8' (lưu gọn, không dùng ký hiệu khoa học)."""
    return format(so.normalize(), "f")


def cap_nhat_trong_so(nguoi_thuc_hien, w1, w2, w3):
    """Cập nhật đồng thời 3 trọng số. Ném TrongSoKhongHopLe nếu không hợp lệ (khi đó không đổi gì).

    Các dòng cấu hình được khóa (SELECT ... FOR UPDATE) theo thứ tự cố định nên hai ADMIN sửa cùng lúc sẽ xếp hàng,
    kết quả cuối luôn là MỘT bộ ba hoàn chỉnh (không bao giờ trộn nửa này nửa kia).
    """
    moi = kiem_tra_trong_so({"w1": w1, "w2": w2, "w3": w3})
    with transaction.atomic():
        cu = {
            c.ten_cau_hinh: c.gia_tri
            for c in CauHinhHeThong.objects.select_for_update().filter(ten_cau_hinh__in=TEN_TRONG_SO).order_by("ten_cau_hinh")
        }
        for ten in TEN_TRONG_SO:
            CauHinhHeThong.objects.update_or_create(ten_cau_hinh=ten, defaults={"gia_tri": chuoi_trong_so(moi[ten])})
        chi_tiet = "; ".join(f"{ten}: {cu.get(ten, '—')} → {chuoi_trong_so(moi[ten])}" for ten in TEN_TRONG_SO)
        NhatKy.ghi(nguoi_thuc_hien, "Sửa trọng số", "CauHinhHeThong", chi_tiet)
    return moi
