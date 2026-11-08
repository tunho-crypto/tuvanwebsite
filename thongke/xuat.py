"""Xuất thống kê ra Excel: mỗi nhóm số liệu một sheet."""
from baocao.excel import DINH_DANG_NGAY, DINH_DANG_PHAN_TRAM
from baocao.services import mo_ta_khoang


def cac_sheet_thong_ke(tk):
    k = tk["khoang"]
    ghi_chu = [mo_ta_khoang(k["tu_ngay"], k["den_ngay"])]
    tv, hd, tkiem = tk["tu_van"], tk["hoi_dap"], tk["tim_kiem"]
    return [
        {
            "ten": "Tổng quan",
            "ghi_chu": ghi_chu,
            "cot": ["Chỉ số", "Giá trị"],
            "dong": [
                ["Số lượt tư vấn", tv["tong"]],
                ["Lượt tư vấn có đề xuất", tv["trong_pham_vi"]],
                ["Lượt tư vấn ngoài phạm vi", tv["ngoai_pham_vi"]],
                ["Tỷ lệ tư vấn có đề xuất", (tv["ty_le_trong_pham_vi"], DINH_DANG_PHAN_TRAM)],
                ["Số câu hỏi", hd["tong"]],
                ["Câu hỏi chờ chuyên gia trả lời", hd["cho_tra_loi"]],
                ["Câu hỏi chuyên gia đã trả lời", hd["da_tra_loi"]],
                ["Câu hỏi ngoài phạm vi (trả lời tự động)", hd["ngoai_pham_vi"]],
                ["Tỷ lệ chuyên gia đã trả lời (trên câu hỏi trong phạm vi)", (hd["ty_le_da_tra_loi"], DINH_DANG_PHAN_TRAM)],
                ["Tỷ lệ có câu trả lời (kể cả tự động)", (hd["ty_le_co_tra_loi"], DINH_DANG_PHAN_TRAM)],
                ["Số lượt tìm kiếm", tkiem["tong"]],
                ["Số từ khóa tìm kiếm khác nhau", tkiem["so_tu_khoa_khac_nhau"]],
            ],
        },
        {"ten": "Tư vấn theo tỉnh", "ghi_chu": ghi_chu, "cot": ["Tỉnh thành", "Số lượt"], "dong": [list(d) for d in tv["theo_tinh"]]},
        {"ten": "Tư vấn theo mùa", "ghi_chu": ghi_chu, "cot": ["Mùa vụ", "Số lượt"], "dong": [list(d) for d in tv["theo_mua"]]},
        {"ten": "Tư vấn theo ngày", "ghi_chu": ghi_chu, "cot": ["Ngày", "Số lượt"], "dong": [list(d) for d in tv["theo_ngay"]], "dinh_dang_cot": {0: DINH_DANG_NGAY}},
        {
            "ten": "Cây được đề xuất",
            "ghi_chu": ghi_chu,
            "cot": ["Mã cây", "Tên cây", "Số lần đứng hạng 1", "Số lần xuất hiện"],
            "dong": [[c["ma_cay"], c["ten_cay"], c["so_lan_hang_1"], c["so_lan_xuat_hien"]] for c in tv["cay_duoc_de_xuat"]],
        },
        {
            "ten": "Từ khóa tìm nhiều nhất",
            "ghi_chu": ghi_chu,
            "cot": ["Hạng", "Từ khóa", "Số lần tìm"],
            "dong": [[i, t["tu_khoa"], t["so_lan"]] for i, t in enumerate(tkiem["top"], start=1)],
        },
    ]

