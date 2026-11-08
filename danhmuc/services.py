"""Ghi danh mục + nhật ký trong một transaction."""
from collections import Counter

from django.db import transaction
from django.db.models import ProtectedError

from taikhoan.models import NhatKy
from taikhoan.services import NghiepVuError


def luu_danh_muc(nguoi_thuc_hien, form, truong_ma):
    """Lưu form danh mục (thêm hoặc sửa) và ghi nhật ký."""
    la_tao = form.instance.pk is None
    with transaction.atomic():
        anh_cu = None
        if not la_tao and "hinh_anh" in form.fields:
            anh_cu = form._meta.model.objects.filter(pk=form.instance.pk).values_list("hinh_anh", flat=True).first()
        doi_tuong = form.save()
        anh_moi = getattr(doi_tuong, "hinh_anh", None)
        if anh_cu and (not anh_moi or anh_cu != anh_moi.name):
            storage = doi_tuong._meta.get_field("hinh_anh").storage
            transaction.on_commit(lambda: storage.delete(anh_cu))
        ten_bang = doi_tuong._meta.verbose_name
        NhatKy.ghi(
            nguoi_thuc_hien,
            "Thêm danh mục" if la_tao else "Sửa danh mục",
            f"{ten_bang}: {getattr(doi_tuong, truong_ma)}",
            str(doi_tuong),
        )
    return doi_tuong


def xoa_danh_muc(nguoi_thuc_hien, doi_tuong, truong_ma):
    """Xóa bản ghi. Đang được tham chiếu (ProtectedError) thì từ chối bằng NghiepVuError có thông báo rõ ràng."""
    ten_bang = doi_tuong._meta.verbose_name
    ma, ten = getattr(doi_tuong, truong_ma), str(doi_tuong)
    anh_cu = getattr(doi_tuong, "hinh_anh", None)
    try:
        with transaction.atomic():
            doi_tuong.delete()
            if anh_cu:
                transaction.on_commit(lambda: anh_cu.storage.delete(anh_cu.name))
            NhatKy.ghi(nguoi_thuc_hien, "Xóa danh mục", f"{ten_bang}: {ma}", ten)
    except ProtectedError as loi:
        dem = Counter(o._meta.verbose_name.lower() for o in loi.protected_objects)
        chi_tiet = ", ".join(f"{so} {ten_model}" for ten_model, so in dem.items())
        raise NghiepVuError(f"Không thể xóa «{ten}» vì đang được sử dụng bởi {chi_tiet}.") from loi
