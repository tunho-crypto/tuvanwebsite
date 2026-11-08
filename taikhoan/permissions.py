"""Phân quyền theo vai trò.

- Chưa đăng nhập -> chuyển về trang đăng nhập (302).
- Đã đăng nhập nhưng sai vai trò -> 403.
"""
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied

from taikhoan.models import VaiTro


class VaiTroRequiredMixin(AccessMixin):
    """Đặt `vai_tro_cho_phep = ("ADMIN", "BIEN_TAP")`; để None nghĩa là mọi người dùng đã đăng nhập."""

    vai_tro_cho_phep = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()  # redirect tới LOGIN_URL?next=...
        if self.vai_tro_cho_phep and not request.user.co_vai_tro(*self.vai_tro_cho_phep):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class QuanTriMixin(VaiTroRequiredMixin):
    """Chỉ ADMIN."""

    vai_tro_cho_phep = (VaiTro.ADMIN,)
