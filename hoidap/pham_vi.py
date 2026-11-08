"""Phân loại một câu hỏi là TRONG hay NGOÀI phạm vi hỗ trợ (quy tắc 9). Thứ tự kiểm tra:

1. Nhắc tới tỉnh/thành NGOÀI 5 tỉnh Tây Nguyên  -> ngoài phạm vi.
2. Hỏi chủ đề hệ thống chưa hỗ trợ (giá cả thị trường, dự đoán) -> ngoài phạm vi.
3. Không nhắc tới cây trồng hay kỹ thuật nào trong danh mục -> ngoài phạm vi.
4. Còn lại -> trong phạm vi, chờ chuyên gia trả lời.

Giới hạn (nên nói rõ khi bảo vệ): so khớp theo cụm từ nguyên văn của tên trong danh mục (bỏ dấu, không phân biệt hoa/thường),
nên Biên tập viên cần đặt tên cây/kỹ thuật thông dụng. Tỉnh ngoài vùng nhận ra được qua danh sách bên dưới
và qua các tỉnh ngoài 5 tỉnh mà Biên tập đã thêm vào danh mục.
"""
import re
import unicodedata

from danhmuc.models import CayTrong, KyThuat, TinhThanh
from tuvan.services import MA_TINH_TAY_NGUYEN, chuan_hoa_van_ban

TINH_NGOAI_TAY_NGUYEN = [
    "An Giang", "Bà Rịa", "Vũng Tàu", "Bạc Liêu", "Bắc Giang", "Bắc Kạn", "Bắc Ninh", "Bến Tre", "Bình Dương", "Bình Định",
    "Bình Phước", "Bình Thuận", "Cà Mau", "Cao Bằng", "Cần Thơ", "Đà Nẵng", "Điện Biên", "Đồng Nai", "Đồng Tháp", "Hà Giang",
    "Hà Nam", "Hà Nội", "Hà Tĩnh", "Hải Dương", "Hải Phòng", "Hậu Giang", "Hòa Bình", "Hưng Yên", "Khánh Hòa", "Kiên Giang",
    "Lai Châu", "Lạng Sơn", "Lào Cai", "Long An", "Nam Định", "Nghệ An", "Ninh Bình", "Ninh Thuận", "Phú Thọ", "Phú Yên",
    "Quảng Bình", "Quảng Nam", "Quảng Ngãi", "Quảng Ninh", "Quảng Trị", "Sóc Trăng", "Sơn La", "Tây Ninh", "Thái Bình",
    "Thái Nguyên", "Thanh Hóa", "Thừa Thiên Huế", "Huế", "Tiền Giang", "Hồ Chí Minh", "Sài Gòn", "Trà Vinh", "Tuyên Quang",
    "Vĩnh Long", "Vĩnh Phúc", "Yên Bái",
]

# Chủ đề chưa hỗ trợ (mục 10 của đề cương: không dự đoán giá nông sản).
CUM_CHU_DE_KHONG_HO_TRO = [("thi", "truong"), ("du", "doan"), ("du", "bao"), ("bao", "nhieu", "tien")]
# «giá trị», «giá thể» là từ nông nghiệp bình thường, không phải hỏi giá.
TU_SAU_GIA_KHONG_PHAI_GIA_CA = {"tri", "the"}
# Người dùng gõ KHÔNG dấu thì «gia» có thể là «Gia Lai», «gia cầm»... nên chỉ coi là hỏi giá khi đi kèm các từ sau.
TU_SAU_GIA_KHONG_DAU_LA_GIA_CA = {"ca", "ban", "hom", "ngay", "bao", "thi"}

LY_DO_TINH = "tinh_ngoai_vung"
LY_DO_CHU_DE = "chu_de_khong_ho_tro"
LY_DO_KHONG_CO_DANH_MUC = "khong_co_trong_danh_muc"


def _co_cum(tu_cau_hoi, cum):
    """True nếu dãy từ `cum` xuất hiện LIÊN TIẾP trong danh sách từ của câu hỏi."""
    n = len(cum)
    return n > 0 and any(tu_cau_hoi[i : i + n] == list(cum) for i in range(len(tu_cau_hoi) - n + 1))


def _tach_tu_goc(noi_dung):
    """Tách từ, GIỮ NGUYÊN dấu (chữ thường, NFC) để phân biệt «giá» (price) với «Gia» trong «Gia Lai»."""
    return re.findall(r"[^\W_]+", unicodedata.normalize("NFC", noi_dung or "").lower())


def _hoi_gia_ca(tu_goc):
    tu = [chuan_hoa_van_ban(t) for t in tu_goc]
    for i, t in enumerate(tu_goc):
        sau = tu[i + 1] if i + 1 < len(tu) else ""
        if t == "giá" and sau not in TU_SAU_GIA_KHONG_PHAI_GIA_CA:
            return True
        if t == "gia" and sau in TU_SAU_GIA_KHONG_DAU_LA_GIA_CA:
            return True
    return any(_co_cum(tu, cum) for cum in CUM_CHU_DE_KHONG_HO_TRO)


def phan_loai_cau_hoi(noi_dung):
    """Trả về (trong_pham_vi: bool, ly_do: str). ly_do rỗng nếu trong phạm vi."""
    tu_goc = _tach_tu_goc(noi_dung)
    tu = chuan_hoa_van_ban(noi_dung).split()

    ten_tinh_ngoai = [t for t in TINH_NGOAI_TAY_NGUYEN]
    ten_tinh_ngoai += [t.ten_tinh for t in TinhThanh.objects.exclude(ma_tinh__in=MA_TINH_TAY_NGUYEN)]
    if any(_co_cum(tu, chuan_hoa_van_ban(t).split()) for t in ten_tinh_ngoai):
        return False, LY_DO_TINH

    if _hoi_gia_ca(tu_goc):
        return False, LY_DO_CHU_DE

    cum_danh_muc = [c.ten_cay for c in CayTrong.objects.all()]
    for kt in KyThuat.objects.all():
        cum_danh_muc += [kt.ten_kt, kt.loai_kt]
    if any(_co_cum(tu, chuan_hoa_van_ban(c).split()) for c in cum_danh_muc):
        return True, ""
    return False, LY_DO_KHONG_CO_DANH_MUC
