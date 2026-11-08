"""Tự ghi nhật ký đăng nhập, đăng nhập thất bại, đăng xuất. KHÔNG ghi mật khẩu."""
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from taikhoan.models import NhatKy


@receiver(user_logged_in)
def ghi_dang_nhap(sender, request, user, **kwargs):
    NhatKy.ghi(user, "Đăng nhập", f"NguoiDung: {user.get_username()}")


@receiver(user_login_failed)
def ghi_dang_nhap_that_bai(sender, credentials, request=None, **kwargs):
    username = (credentials or {}).get("username", "")
    NhatKy.ghi(None, "Đăng nhập thất bại", f"NguoiDung: {username}")


@receiver(user_logged_out)
def ghi_dang_xuat(sender, request, user, **kwargs):
    if user is not None:  # phiên đã hết hạn thì không có người dùng
        NhatKy.ghi(user, "Đăng xuất", f"NguoiDung: {user.get_username()}")
