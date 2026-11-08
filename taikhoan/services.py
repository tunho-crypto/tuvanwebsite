"""Nghiệp vụ tài khoản. Mọi thao tác ghi nhiều bảng (người dùng + nhật ký) nằm trong transaction.atomic."""
import secrets
import smtplib
import socket
import logging
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from taikhoan.models import MaKhoiPhucMatKhau, NguoiDung, NhatKy, VaiTro

logger = logging.getLogger(__name__)


class NghiepVuError(Exception):
    """Vi phạm quy tắc nghiệp vụ; thông điệp hiển thị trực tiếp cho người dùng."""


class LoiGuiEmailKhoiPhuc(NghiepVuError):
    """Không gửi được email khôi phục qua nhà cung cấp SMTP."""


THOI_HAN_MA_KHOI_PHUC = timedelta(minutes=10)
THOI_GIAN_CHO_GUI_LAI_MA = timedelta(seconds=60)
SO_LAN_NHAP_MA_TOI_DA = 5


def gui_ma_khoi_phuc_mat_khau(email):
    """Gửi mã OTP email; trả về cùng kết quả dù email không tồn tại hay đang trong thời gian chờ."""
    email = email.strip()
    luc_nay = timezone.now()
    with transaction.atomic():
        nguoi_dung = (
            NguoiDung.objects.select_for_update()
            .filter(email__iexact=email, is_active=True)
            .first()
        )
        if not nguoi_dung or not nguoi_dung.has_usable_password():
            return
        ma_moi_nhat = (
            MaKhoiPhucMatKhau.objects.select_for_update()
            .filter(nguoi_dung=nguoi_dung)
            .order_by("-tao_luc", "-id")
            .first()
        )
        if ma_moi_nhat and ma_moi_nhat.tao_luc > luc_nay - THOI_GIAN_CHO_GUI_LAI_MA:
            return
        MaKhoiPhucMatKhau.objects.filter(nguoi_dung=nguoi_dung).delete()
        ma = f"{secrets.randbelow(1_000_000):06d}"
        ma_khoi_phuc = MaKhoiPhucMatKhau.objects.create(
            nguoi_dung=nguoi_dung,
            ma_bam=make_password(ma),
            het_han_luc=luc_nay + THOI_HAN_MA_KHOI_PHUC,
        )

    try:
        send_mail(
            subject="Mã xác minh đặt lại mật khẩu",
            message=(
                f"Mã xác minh đặt lại mật khẩu của bạn là: {ma}\n\n"
                "Mã có hiệu lực trong 10 phút và chỉ sử dụng được một lần. "
                "Nếu bạn không yêu cầu đặt lại mật khẩu, hãy bỏ qua email này."
            ),
            from_email=None,
            recipient_list=[nguoi_dung.email],
            fail_silently=False,
        )
    except (smtplib.SMTPException, OSError, socket.timeout, ValueError) as loi:
        MaKhoiPhucMatKhau.objects.filter(pk=ma_khoi_phuc.pk).delete()
        logger.exception("Không gửi được email khôi phục mật khẩu.")
        raise LoiGuiEmailKhoiPhuc(
            "Không gửi được email khôi phục. Vui lòng kiểm tra cấu hình SMTP hoặc thử lại sau."
        ) from loi


def xac_nhan_ma_khoi_phuc_mat_khau(email, ma, mat_khau_moi):
    """Xác minh OTP, giới hạn số lần thử và đổi mật khẩu trong cùng một transaction."""
    luc_nay = timezone.now()
    with transaction.atomic():
        nguoi_dung = (
            NguoiDung.objects.select_for_update()
            .filter(email__iexact=email.strip(), is_active=True)
            .first()
        )
        if not nguoi_dung:
            return False
        ma_khoi_phuc = (
            MaKhoiPhucMatKhau.objects.select_for_update()
            .filter(nguoi_dung=nguoi_dung, da_su_dung_luc__isnull=True)
            .order_by("-tao_luc", "-id")
            .first()
        )
        if not ma_khoi_phuc:
            return False
        if ma_khoi_phuc.het_han_luc <= luc_nay or ma_khoi_phuc.so_lan_thu >= SO_LAN_NHAP_MA_TOI_DA:
            ma_khoi_phuc.da_su_dung_luc = luc_nay
            ma_khoi_phuc.save(update_fields=["da_su_dung_luc"])
            return False

        ma_khoi_phuc.so_lan_thu += 1
        if not check_password(ma, ma_khoi_phuc.ma_bam):
            if ma_khoi_phuc.so_lan_thu >= SO_LAN_NHAP_MA_TOI_DA:
                ma_khoi_phuc.da_su_dung_luc = luc_nay
            ma_khoi_phuc.save(update_fields=["so_lan_thu", "da_su_dung_luc"])
            return False

        nguoi_dung.set_password(mat_khau_moi)
        nguoi_dung.save(update_fields=["password"])
        ma_khoi_phuc.da_su_dung_luc = luc_nay
        ma_khoi_phuc.save(update_fields=["so_lan_thu", "da_su_dung_luc"])
        return True


def tao_nguoi_dung(nguoi_thuc_hien, *, username, mat_khau, vai_tro, ho="", ten="", email="", is_active=True):
    with transaction.atomic():
        nguoi_dung = NguoiDung.objects.create_user(
            username=username,
            password=mat_khau,
            email=email,
            last_name=ho,
            first_name=ten,
            vai_tro=vai_tro,
            is_active=is_active,
        )
        NhatKy.ghi(nguoi_thuc_hien, "Tạo người dùng", f"NguoiDung: {username}", f"Vai trò {vai_tro.ma_vai_tro}")
    return nguoi_dung


def dang_ky_nguoi_dung(*, username, mat_khau, ho, ten, email):
    with transaction.atomic():
        vai_tro, _ = VaiTro.objects.get_or_create(
            ma_vai_tro=VaiTro.NONG_DAN,
            defaults={"ten_vai_tro": "Nông dân", "mo_ta": "Tra cứu, tư vấn, đặt câu hỏi"},
        )
        nguoi_dung = NguoiDung.objects.create_user(
            username=username,
            password=mat_khau,
            email=email,
            last_name=ho,
            first_name=ten,
            vai_tro=vai_tro,
            is_active=True,
        )
        NhatKy.ghi(None, "Đăng ký tài khoản", f"NguoiDung: {username}", "Vai trò NONG_DAN")
    return nguoi_dung


def cap_nhat_nguoi_dung(nguoi_thuc_hien, nguoi_dung, *, vai_tro, is_active, ho="", ten="", email="", mat_khau_moi=None):
    """Quy tắc 12: không tự khóa mình, không tự bỏ quyền ADMIN của mình."""
    tu_sua_minh = nguoi_thuc_hien.pk == nguoi_dung.pk
    # Đọc lại từ CSDL để chắc chắn so với giá trị cũ
    cu = NguoiDung.objects.select_related("vai_tro").get(pk=nguoi_dung.pk)
    if tu_sua_minh and cu.vai_tro.ma_vai_tro == VaiTro.ADMIN and vai_tro.ma_vai_tro != VaiTro.ADMIN:
        raise NghiepVuError("Không thể tự bỏ quyền ADMIN của chính mình.")
    if tu_sua_minh and not is_active:
        raise NghiepVuError("Không thể tự khóa tài khoản của chính mình.")

    with transaction.atomic():
        cu.last_name, cu.first_name, cu.email = ho, ten, email
        cu.vai_tro, cu.is_active = vai_tro, is_active
        if mat_khau_moi:
            cu.set_password(mat_khau_moi)
        cu.save()
        chi_tiet = f"Vai trò {vai_tro.ma_vai_tro}, {'hoạt động' if is_active else 'khóa'}"
        if mat_khau_moi:
            chi_tiet += ", đặt lại mật khẩu"
        NhatKy.ghi(nguoi_thuc_hien, "Sửa người dùng", f"NguoiDung: {cu.username}", chi_tiet)
    return cu


def doi_trang_thai_khoa(nguoi_thuc_hien, nguoi_dung):
    """Khóa nếu đang hoạt động, mở khóa nếu đang khóa. Trả về True nếu sau đó tài khoản đang hoạt động."""
    if nguoi_thuc_hien.pk == nguoi_dung.pk:
        raise NghiepVuError("Không thể tự khóa tài khoản của chính mình.")
    with transaction.atomic():
        cu = NguoiDung.objects.select_for_update().get(pk=nguoi_dung.pk)
        cu.is_active = not cu.is_active
        cu.save(update_fields=["is_active"])
        NhatKy.ghi(
            nguoi_thuc_hien,
            "Mở khóa tài khoản" if cu.is_active else "Khóa tài khoản",
            f"NguoiDung: {cu.username}",
        )
    return cu.is_active
