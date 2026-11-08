"""Nghiệp vụ hỏi đáp: gửi câu hỏi (tự trả lời nếu ngoài phạm vi) và chuyên gia trả lời."""
from django.db import transaction

from hoidap.models import CauHoi, TraLoi
from hoidap.pham_vi import phan_loai_cau_hoi
from taikhoan.ma_tu_sinh import tao_voi_ma_tu_sinh
from taikhoan.models import NhatKy
from taikhoan.services import NghiepVuError
from tuvan.services import THONG_BAO_NGOAI_PHAM_VI


def gui_cau_hoi(nguoi_dung, noi_dung):
    """Tạo câu hỏi với mã CHyyyymmdd-nnn. Ngoài phạm vi thì lưu trạng thái NGOAI_PHAM_VI và trả lời ngay bằng câu tiêu chuẩn."""
    trong_pham_vi, _ = phan_loai_cau_hoi(noi_dung)
    with transaction.atomic():
        cau_hoi = tao_voi_ma_tu_sinh(
            CauHoi,
            "ma_ch",
            "CH",
            lambda ma: CauHoi.objects.create(
                ma_ch=ma,
                nguoi_dung=nguoi_dung,
                noi_dung=noi_dung,
                trang_thai=CauHoi.CHO_TRA_LOI if trong_pham_vi else CauHoi.NGOAI_PHAM_VI,
            ),
        )
        if not trong_pham_vi:
            TraLoi.objects.create(cau_hoi=cau_hoi, nguoi_tra_loi=None, noi_dung=THONG_BAO_NGOAI_PHAM_VI, la_tu_dong=True)
        NhatKy.ghi(
            nguoi_dung,
            "Gửi câu hỏi",
            f"CauHoi: {cau_hoi.ma_ch}",
            "Chờ chuyên gia trả lời" if trong_pham_vi else "Ngoài phạm vi, đã trả lời tự động",
        )
    return cau_hoi


def tra_loi_cau_hoi(nguoi_thuc_hien, cau_hoi, noi_dung):
    """Chuyên gia trả lời. Khóa dòng câu hỏi nên hai chuyên gia cùng trả lời thì chỉ một người thành công,
    người còn lại nhận NghiepVuError."""
    with transaction.atomic():
        hien_tai = CauHoi.objects.select_for_update().get(pk=cau_hoi.pk)
        if hien_tai.trang_thai != CauHoi.CHO_TRA_LOI:
            raise NghiepVuError("Câu hỏi này đã được xử lý, không thể trả lời nữa.")
        tra_loi = TraLoi.objects.create(cau_hoi=hien_tai, nguoi_tra_loi=nguoi_thuc_hien, noi_dung=noi_dung)
        hien_tai.trang_thai = CauHoi.DA_TRA_LOI
        hien_tai.save(update_fields=["trang_thai"])
        NhatKy.ghi(nguoi_thuc_hien, "Trả lời câu hỏi", f"CauHoi: {hien_tai.ma_ch}")
    return tra_loi
