"""Dựng file Excel (.xlsx) bằng openpyxl. Dữ liệu do người dùng nhập (nhu cầu, từ khóa, câu hỏi...) được xử lý để:
- không bị Excel hiểu thành CÔNG THỨC (ô bắt đầu bằng «=» luôn lưu dạng chuỗi);
- không làm hỏng file vì ký tự điều khiển.
"""
import re
from datetime import date, datetime
from io import BytesIO

from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
KY_TU_DIEU_KHIEN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
KY_TU_CAM_TEN_SHEET = re.compile(r"[\[\]:*?/\\]")
DO_RONG_TOI_DA = 60
DINH_DANG_NGAY_GIO = "dd/mm/yyyy hh:mm"
DINH_DANG_NGAY = "dd/mm/yyyy"
DINH_DANG_PHAN_TRAM = "0.0%"


def ten_sheet_hop_le(ten):
    return KY_TU_CAM_TEN_SHEET.sub(" ", ten).strip()[:31] or "Sheet"


def chuan_hoa_gia_tri(gia_tri):
    """Đổi về kiểu Excel hiểu được. Ngày giờ có múi giờ -> giờ địa phương không múi giờ (Excel không hỗ trợ múi giờ)."""
    if isinstance(gia_tri, bool):
        return "Có" if gia_tri else "Không"
    if isinstance(gia_tri, datetime):
        if timezone.is_aware(gia_tri):
            gia_tri = timezone.localtime(gia_tri).replace(tzinfo=None)
        return gia_tri
    if isinstance(gia_tri, str):
        return KY_TU_DIEU_KHIEN.sub("", gia_tri)
    return gia_tri


def _ghi_o(ws, hang, cot, gia_tri, dinh_dang=None):
    gia_tri = chuan_hoa_gia_tri(gia_tri)
    o = ws.cell(row=hang, column=cot)
    o.value = gia_tri
    if isinstance(gia_tri, str):
        o.data_type = "s"  # luôn là chuỗi, kể cả khi bắt đầu bằng «=», «+», «-», «@»: không bao giờ thành công thức
    if dinh_dang:
        o.number_format = dinh_dang
    elif isinstance(gia_tri, datetime):
        o.number_format = DINH_DANG_NGAY_GIO
    elif isinstance(gia_tri, date):
        o.number_format = DINH_DANG_NGAY
    o.alignment = Alignment(vertical="top", wrap_text=isinstance(gia_tri, str))
    return o


def ghi_sheet(ws, cot, dong, dinh_dang_cot=None, ghi_chu=None):
    """cot: danh sách tiêu đề. dong: iterable các list giá trị. dinh_dang_cot: {chỉ số cột bắt đầu từ 0: number_format}.
    ghi_chu: danh sách chuỗi ghi phía trên bảng (ví dụ khoảng thời gian)."""
    dinh_dang_cot = dinh_dang_cot or {}
    hang = 1
    for dong_ghi_chu in ghi_chu or []:
        _ghi_o(ws, hang, 1, dong_ghi_chu).font = Font(italic=True, color="555555")
        hang += 1
    hang_tieu_de = hang
    for i, ten in enumerate(cot, start=1):
        o = _ghi_o(ws, hang_tieu_de, i, ten)
        o.font = Font(bold=True, color="FFFFFF")
        o.fill = PatternFill("solid", start_color="198754")
        o.alignment = Alignment(vertical="center", wrap_text=True)
    do_rong = [len(str(t)) for t in cot]
    hang = hang_tieu_de
    for gia_tri_dong in dong:
        hang += 1
        for i, gia_tri in enumerate(gia_tri_dong, start=1):
            dinh_dang = dinh_dang_cot.get(i - 1)
            if isinstance(gia_tri, tuple) and len(gia_tri) == 2:  # (giá trị, number_format) để định dạng riêng từng ô
                gia_tri, dinh_dang = gia_tri
            o = _ghi_o(ws, hang, i, gia_tri, dinh_dang)
            do_dai = len(str(o.value)) if o.value is not None else 0
            if i - 1 < len(do_rong):
                do_rong[i - 1] = max(do_rong[i - 1], min(do_dai, DO_RONG_TOI_DA))
    for i, rong in enumerate(do_rong, start=1):
        ws.column_dimensions[get_column_letter(i)].width = min(rong, DO_RONG_TOI_DA) + 2
    ws.freeze_panes = ws.cell(row=hang_tieu_de + 1, column=1)
    if cot:
        ws.auto_filter.ref = f"A{hang_tieu_de}:{get_column_letter(len(cot))}{max(hang, hang_tieu_de)}"
    return hang - hang_tieu_de  # số dòng dữ liệu


def tao_xlsx(cac_sheet):
    """cac_sheet: list dict {ten, cot, dong, dinh_dang_cot?, ghi_chu?}. Trả về (bytes, tổng số dòng dữ liệu)."""
    wb = Workbook()
    wb.remove(wb.active)
    tong_dong = 0
    for sheet in cac_sheet:
        ws = wb.create_sheet(ten_sheet_hop_le(sheet["ten"]))
        tong_dong += ghi_sheet(ws, sheet["cot"], sheet["dong"], sheet.get("dinh_dang_cot"), sheet.get("ghi_chu"))
    bo_nho = BytesIO()
    wb.save(bo_nho)
    return bo_nho.getvalue(), tong_dong


def phan_hoi_xlsx(noi_dung, ten_tep):
    phan_hoi = HttpResponse(noi_dung, content_type=MIME_XLSX)
    phan_hoi["Content-Disposition"] = f'attachment; filename="{ten_tep}"'
    return phan_hoi


def ten_tep(tien_to):
    return f"{tien_to}_{timezone.localdate():%Y%m%d}.xlsx"
