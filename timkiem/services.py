"""Tra cứu cây trồng, kỹ thuật, mùa vụ. Không phân biệt hoa/thường và dấu tiếng Việt ('ca phe' tìm ra 'Cà phê')."""
import re
import unicodedata

from django.db import transaction

from danhmuc.models import CayTrong, KyThuat, MuaVu
from taikhoan.ma_tu_sinh import tao_voi_ma_tu_sinh
from timkiem.models import LichSuTimKiem
from tuvan.services import chuan_hoa_van_ban

TOI_DA_MOI_NHOM = 50
TOI_DA_DO_DAI_TU_KHOA = 255


def lam_sach_tu_khoa(tu_khoa):
    """Gộp khoảng trắng thừa và cắt theo độ dài cột lưu trữ."""
    return " ".join((tu_khoa or "").split())[:TOI_DA_DO_DAI_TU_KHOA]


def _viet_thuong(van_ban):
    return unicodedata.normalize("NFC", van_ban or "").lower()


def _khop(cac_tu_goc, chuoi_co_dau, chuoi_khong_dau):
    """Từ gõ CÓ dấu phải khớp đúng dấu («mưa» không khớp «mùa»); từ gõ KHÔNG dấu khớp rộng («mua» khớp cả hai)."""
    for tu in cac_tu_goc:
        if chuan_hoa_van_ban(tu) != tu:
            if tu not in chuoi_co_dau:
                return False
        elif tu not in chuoi_khong_dau:
            return False
    return True


def _tim_trong(doi_tuong_ds, cac_tu_goc, truong_ten, truong_khac):
    """Mọi từ của từ khóa phải xuất hiện (dạng chuỗi con) trong tên hoặc các trường khác. Khớp trong TÊN thì xếp trước."""
    ket_qua = []
    for dt in doi_tuong_ds:
        ten_goc = getattr(dt, truong_ten)
        phan_khac = [getattr(dt, t) for t in truong_khac]
        ten_co_dau, ten_khong_dau = _viet_thuong(ten_goc), chuan_hoa_van_ban(ten_goc)
        co_dau = " ".join([ten_co_dau] + [_viet_thuong(x) for x in phan_khac])
        khong_dau = " ".join([ten_khong_dau] + [chuan_hoa_van_ban(x) for x in phan_khac])
        if _khop(cac_tu_goc, co_dau, khong_dau):
            ket_qua.append((0 if _khop(cac_tu_goc, ten_co_dau, ten_khong_dau) else 1, ten_khong_dau, dt))
    ket_qua.sort(key=lambda x: (x[0], x[1]))
    return [dt for _, _, dt in ket_qua][:TOI_DA_MOI_NHOM]


def tim_kiem(tu_khoa):
    """Trả về {'cay_trong': [...], 'ky_thuat': [...], 'mua_vu': [...]}; từ khóa rỗng -> cả ba nhóm rỗng."""
    cac_tu = list(dict.fromkeys(re.findall(r"[^\W_]+", _viet_thuong(tu_khoa))))  # bỏ từ lặp, giữ thứ tự
    if not cac_tu:
        return {"cay_trong": [], "ky_thuat": [], "mua_vu": []}
    return {
        "cay_trong": _tim_trong(CayTrong.objects.all(), cac_tu, "ten_cay", ["ma_cay", "dac_diem", "nhom_cay"]),
        "ky_thuat": _tim_trong(KyThuat.objects.all(), cac_tu, "ten_kt", ["ma_kt", "loai_kt", "noi_dung"]),
        "mua_vu": _tim_trong(MuaVu.objects.all(), cac_tu, "ten_mua", ["ma_mua"]),
    }


def tra_cuu_va_luu(tu_khoa):
    """Tra cứu và lưu LichSuTimKiem (mã TKyyyymmdd-nnn). Từ khóa không có chữ/số nào thì không tra cứu, không lưu.
    Trả về (kết quả, lịch sử hoặc None)."""
    tu_khoa = lam_sach_tu_khoa(tu_khoa)
    ket_qua = tim_kiem(tu_khoa)
    if not chuan_hoa_van_ban(tu_khoa):
        return ket_qua, None
    with transaction.atomic():
        lich_su = tao_voi_ma_tu_sinh(
            LichSuTimKiem, "ma_ls", "TK", lambda ma: LichSuTimKiem.objects.create(ma_ls=ma, tu_khoa=tu_khoa)
        )
    return ket_qua, lich_su
