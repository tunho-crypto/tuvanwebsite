"""Sinh mã tự động theo ngày: XXyyyymmdd-nnn (quy tắc 6). Ví dụ LT20261030-001, LS20261030-012.

Khi hai người cùng lấy một mã, ràng buộc UNIQUE của CSDL làm một bên thất bại; bên đó thử lại với mã kế tiếp (tối đa 10 lần).
"""
import zlib

from django.db import IntegrityError, connection, transaction
from django.utils import timezone

from taikhoan.services import NghiepVuError

SO_LAN_THU_TOI_DA = 10


def sinh_ma_ke_tiep(model, truong, tien_to, ngay=None):
    """Mã kế tiếp trong ngày = số lớn nhất đã dùng + 1 (không phụ thuộc thứ tự chuỗi nên vẫn đúng khi vượt 999)."""
    ngay = ngay or timezone.localdate()
    mau = f"{tien_to}{ngay:%Y%m%d}-"
    so_lon_nhat = 0
    for ma in model.objects.filter(**{f"{truong}__startswith": mau}).values_list(truong, flat=True):
        phan_so = ma[len(mau):]
        if phan_so.isdigit():
            so_lon_nhat = max(so_lon_nhat, int(phan_so))
    return f"{mau}{so_lon_nhat + 1:03d}"


def _khoa_sinh_ma(model, tien_to, ngay):
    """Khóa tư vấn của PostgreSQL (tự nhả khi kết thúc transaction ngoài cùng).

    Các lần sinh mã cùng tiền tố, cùng ngày xếp hàng với nhau nên gần như không còn tranh nhau một mã;
    ràng buộc UNIQUE và cơ chế thử lại bên dưới vẫn là lớp bảo vệ cuối cùng.
    """
    ngay = ngay or timezone.localdate()
    khoa = zlib.crc32(f"{model._meta.label}:{tien_to}{ngay:%Y%m%d}".encode())
    with connection.cursor() as con_tro:
        con_tro.execute("SELECT pg_advisory_xact_lock(%s)", [khoa])


def tao_voi_ma_tu_sinh(model, truong, tien_to, tao, ngay=None):
    """Gọi tao(ma) để tạo bản ghi với mã tự sinh; trùng mã thì thử lại, tối đa SO_LAN_THU_TOI_DA lần.

    Mỗi lần thử nằm trong một savepoint để lỗi trùng không làm hỏng transaction bên ngoài.
    Lỗi ràng buộc KHÁC (không phải trùng mã) được ném lại ngay, không thử lại.
    """
    for _ in range(SO_LAN_THU_TOI_DA):
        ma = None
        try:
            with transaction.atomic():
                _khoa_sinh_ma(model, tien_to, ngay)
                ma = sinh_ma_ke_tiep(model, truong, tien_to, ngay)
                return tao(ma)
        except IntegrityError:
            if ma is None or not model.objects.filter(**{truong: ma}).exists():
                raise
    raise NghiepVuError(f"Không sinh được mã {tien_to}… sau {SO_LAN_THU_TOI_DA} lần thử, vui lòng thử lại.")
