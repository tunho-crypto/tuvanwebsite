"""Sinh bảng test case thủ công từ danh_sach.py:
    python kiem_thu_thu_cong/xuat.py     ->  tai_lieu/TEST_CASE_THU_CONG.md  và  tai_lieu/TEST_CASE_THU_CONG.xlsx
Không chứa ngày giờ để file sinh ra ổn định (test so sánh với bản đã lưu)."""
import os
import sys
from collections import Counter
from io import BytesIO
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tuvannongnghiep.settings")

import django  # noqa: E402

django.setup()

from kiem_thu_thu_cong.danh_sach import TC_LIST  # noqa: E402

CAC_COT = ["Mã TC", "Use case", "Điều kiện ban đầu", "Các bước", "Dữ liệu vào", "Kết quả mong đợi", "Kết quả thực tế", "Đạt / Không đạt", "Ghi chú"]
THU_MUC = GOC / "tai_lieu"
TEP_MD, TEP_XLSX = THU_MUC / "TEST_CASE_THU_CONG.md", THU_MUC / "TEST_CASE_THU_CONG.xlsx"


def _o(van_ban):
    """Một ô Markdown: không xuống dòng, không chứa dấu | (làm vỡ bảng)."""
    return " ".join(str(van_ban).split()).replace("|", "/")


def cac_buoc(buoc):
    return "; ".join(f"{i}) {b}" for i, b in enumerate(buoc, start=1))


def dong_tc(t):
    ghi_chu = f"[{t['loai']}] {t['ghi_chu']}".strip()
    return [t["ma"], t["use_case"], t["dieu_kien"], cac_buoc(t["buoc"]), t["du_lieu"], t["mong_doi"], "", "", ghi_chu]


def tao_markdown():
    thong_ke_uc, thong_ke_loai = Counter(t["use_case"] for t in TC_LIST), Counter(t["loai"] for t in TC_LIST)
    dong = [
        "# Bảng test case thủ công: Hệ thống tư vấn thông tin nông nghiệp Tây Nguyên",
        "",
        f"Tổng cộng **{len(TC_LIST)} test case**. Cột «Kết quả thực tế» và «Đạt / Không đạt» để trống cho bạn điền khi làm theo.",
        "",
        "## 1. Chuẩn bị",
        "",
        "```bash",
        "python manage.py migrate",
        "python manage.py flush --noinput         # xóa sạch dữ liệu cũ (nếu đã chạy thử trước đó)",
        "python manage.py nap_du_lieu_mau          # 4 vai trò, 4 tài khoản, 12 cây, 5 tỉnh, 2 mùa, 7 luật, trọng số 0,5 / 0,3 / 0,2",
        "python manage.py runserver                # mở http://127.0.0.1:8000/",
        "```",
        "",
        "| Tài khoản | Mật khẩu | Vai trò |",
        "|---|---|---|",
        "| admin | 123456 | Quản trị viên |",
        "| bientap | 123456 | Biên tập viên |",
        "| chuyengia | 123456 | Chuyên gia |",
        "| nongdan | 123456 | Nông dân |",
        "",
        "Nên mở **hai cửa sổ trình duyệt** (một cửa sổ thường, một cửa sổ ẩn danh) để đăng nhập hai tài khoản cùng lúc ở các test case ND-04, PQ-xx.",
        "",
        "## 2. Cách làm và quy ước",
        "",
        "- Làm theo thứ tự các dòng trong bảng. Mỗi dòng ghi rõ điều kiện ban đầu; nhiều dòng dùng kết quả của dòng trước (ví dụ TX-01, CH-02, CH-05 cần TV-01; LU-05 cần LU-02; HD-02 và HD-08 cần HD-01).",
        "- Các số liệu lấy từ dữ liệu mẫu nên làm đúng sẽ ra đúng số. Điểm hiển thị làm tròn 2 chữ số (0,875 hiện là 0,88).",
        "- Một số test case làm thay đổi dữ liệu (ND-07 đổi vai trò bientap, DN-04 đổi mật khẩu, CH-02 đổi trọng số...). Dọn dẹp theo cột «Ghi chú» hoặc chạy lại `flush` + `nap_du_lieu_mau` trước khi sang nhóm test case khác.",
        "- Loại test case ghi ở đầu cột «Ghi chú»: [Bình thường], [Biên], [Lỗi], [Phân quyền].",
        "- Mọi thông báo trong cột «Kết quả mong đợi» là nguyên văn hiển thị trên màn hình.",
        "",
        "## 3. Bảng test case",
        "",
        "| " + " | ".join(CAC_COT) + " |",
        "|" + "|".join(["---"] * len(CAC_COT)) + "|",
    ]
    dong += ["| " + " | ".join(_o(c) for c in dong_tc(t)) + " |" for t in TC_LIST]
    dong += ["", "## 4. Thống kê", "", "| Use case | Số test case |", "|---|---|"]
    dong += [f"| {uc} | {n} |" for uc, n in thong_ke_uc.items()]
    dong += ["", "| Loại | Số test case |", "|---|---|"]
    dong += [f"| {loai} | {n} |" for loai, n in thong_ke_loai.items()]
    dong += [
        "",
        "## 5. Mức độ đã được kiểm chứng",
        "",
        f"Mỗi test case ở trên có một hàm kiểm chứng tự động tương ứng (`kiem_thu_thu_cong/test_kich_ban_thu_cong.py`, chạy bằng `python manage.py test kiem_thu_thu_cong`), "
        "thực hiện đúng các bước và so sánh với «Kết quả mong đợi» trên dữ liệu thật của `nap_du_lieu_mau`.",
        "",
        "Chưa kiểm chứng được bằng máy (cần bạn nhìn bằng mắt trên trình duyệt thật): màu sắc, bố cục, hộp thoại, tải file Excel mở bằng phần mềm Excel/LibreOffice, "
        "và test case **UI-01** (chạy khi không có mạng).",
        "",
    ]
    return "\n".join(dong)


def tao_xlsx():
    from openpyxl import load_workbook
    from openpyxl.worksheet.datavalidation import DataValidation

    from baocao.excel import tao_xlsx as dung_xlsx

    noi_dung, _ = dung_xlsx([{"ten": "Test case", "cot": CAC_COT, "dong": [dong_tc(t) for t in TC_LIST]}])
    wb = load_workbook(BytesIO(noi_dung))
    ws = wb["Test case"]
    kiem = DataValidation(type="list", formula1='"Đạt,Không đạt"', allow_blank=True)  # ô «Đạt / Không đạt» chọn từ danh sách
    kiem.add(f"H2:H{len(TC_LIST) + 1}")
    ws.add_data_validation(kiem)
    bo_nho = BytesIO()
    wb.save(bo_nho)
    return bo_nho.getvalue()


def main():
    THU_MUC.mkdir(exist_ok=True)
    TEP_MD.write_text(tao_markdown(), encoding="utf-8")
    TEP_XLSX.write_bytes(tao_xlsx())
    print(f"Đã ghi {TEP_MD.name} và {TEP_XLSX.name} ({len(TC_LIST)} test case) vào {THU_MUC}")


if __name__ == "__main__":
    main()
