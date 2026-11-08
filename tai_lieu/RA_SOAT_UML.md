# Rà soát lệch giữa Phần A (đề cương), sơ đồ UML và hệ thống thật

## 0. Giới hạn của bản rà soát này (đọc trước)

- **Tôi chưa được xem sơ đồ UML nào của bạn** (use case, lớp, tuần tự, hoạt động). Vì vậy bản này **không** khẳng định «sơ đồ của bạn đúng/sai chỗ nào».
- Bản này làm hai việc chắc chắn được: **(A)** liệt kê các chỗ hệ thống thật khác với chữ trong Phần A (đề cương), kèm đề xuất sửa sơ đồ hay sửa code; **(B)** lập sẵn danh sách «sự thật của hệ thống» theo từng loại sơ đồ để bạn tự đối chiếu, hoặc gửi sơ đồ cho tôi để đối chiếu từng nét.
- Mọi số liệu dưới đây lấy từ mã nguồn hiện tại. Từ điển dữ liệu và ma trận phân quyền là **file sinh tự động**, luôn khớp mã nguồn: `TU_DIEN_DU_LIEU.md`, `MA_TRAN_PHAN_QUYEN.md`.
- Câu hỏi duy nhất cần bạn trả lời để làm tiếp: **bạn gửi các sơ đồ UML nào (ảnh hoặc PlantUML/draw.io)?** Tôi sẽ đối chiếu từng sơ đồ với hệ thống và nêu từng nét cần sửa.

## A. Những chỗ hệ thống khác với Phần A

Cột «Đề xuất»: **Sửa tài liệu** = Phần A/sơ đồ ghi sai hoặc thiếu so với hệ thống, nên sửa tài liệu. **Quyết định** = có hai hướng hợp lý, bạn chọn. **Bổ sung** = Phần A chưa quy định, hệ thống đã chọn một cách làm, sơ đồ nên thể hiện.

### A1. Dữ liệu

| # | Chỗ lệch | Phần A nói | Hệ thống thật | Đề xuất |
|---|---|---|---|---|
| 1 | Số bảng | Mục 3 liệt kê `TraLoi` trong app `hoidap`, nhưng mục 4 chỉ nêu **13 bảng** và không có `TraLoi` (mâu thuẫn nội bộ) | **14 bảng**; `TraLoi` quan hệ 1-1 với `CauHoi` (mỗi câu hỏi tối đa một câu trả lời; có cột `la_tu_dong`) | **Sửa tài liệu**: mục 4 thành 14 bảng, thêm lớp `TraLoi` vào sơ đồ lớp và ERD |
| 2 | Luật → Tài liệu | Mục 4 không có khóa ngoại từ `LuatTuVan` sang `TaiLieu`, nhưng quy tắc 10 yêu cầu truy xuất «luật → tài liệu» | Cột `LuatTuVan.tai_lieu_id` (khóa ngoại, cho phép NULL, `PROTECT`) | **Sửa tài liệu**: thêm quan hệ `LuatTuVan` → `TaiLieu` (0..1) |
| 3 | Thời điểm hỏi | `CauHoi` không có cột thời gian | Thêm `CauHoi.thoi_gian` (để hiển thị ngày hỏi và thống kê theo khoảng ngày) | **Sửa tài liệu**: thêm thuộc tính |
| 4 | App của `TaiLieu` | Mục 3 không liệt kê `TaiLieu` trong app `danhmuc` | `TaiLieu` nằm trong `danhmuc`, có CRUD như 4 bảng danh mục khác (tổng 5 bảng danh mục) | **Sửa tài liệu**: mục 3, `danhmuc` gồm 5 bảng |
| 5 | Nội dung `thongke` | Mục 3 (dòng `thongke`): «Thống kê lượt tra cứu, tỷ lệ đạt của các bộ test case tư vấn». Tuần 5 lại ghi: «Đếm số lượt tư vấn, tỷ lệ câu hỏi được trả lời, các từ khóa tìm kiếm nhiều nhất» (hai chỗ trong đề cương tự khác nhau) | Hệ thống thống kê: số lượt tư vấn, tỷ lệ tư vấn có đề xuất, tỷ lệ câu hỏi được trả lời, từ khóa tìm nhiều nhất, cây được đề xuất nhiều nhất. **Không có** bảng/chức năng quản lý test case trong hệ thống | **Sửa tài liệu**: mục 3 theo nội dung tuần 5. Bảng test case là tài liệu của đồ án, không phải chức năng |
| 6 | Xóa danh mục | Không nêu | Bản ghi đang được luật dùng thì **không xóa được** (thông báo nêu số luật đang dùng); áp dụng cho cây trồng, tỉnh thành, mùa vụ, tài liệu | **Bổ sung** vào sơ đồ lớp (quan hệ `PROTECT`) và activity «Xóa danh mục» |

### A2. Phân quyền (so với mục 6)

| # | Chỗ lệch | Phần A nói | Hệ thống thật | Đề xuất |
|---|---|---|---|---|
| 7 | Phạm vi sửa danh mục của Biên tập | Mục 6, dòng BIEN_TAP: «CRUD danh mục (cây trồng, kỹ thuật, tài liệu)». Cũng ở mục 6: «Danh mục: mọi người dùng đăng nhập đều xem, chỉ ADMIN và BIEN_TAP được thêm, sửa, xóa» | Biên tập sửa được **cả 5 bảng** (kể cả Tỉnh thành, Mùa vụ), theo quy tắc chung | **Quyết định**. (a) Giữ code, sửa mô tả vai trò. (b) Siết lại: Biên tập không sửa tỉnh/mùa (khoảng 5 dòng + 2 test). Khuyến nghị (a) nếu giảng viên không nhấn mạnh |
| 8 | Ai quản lý luật | Mục 6: chỉ dòng BIEN_TAP có «quản lý luật tư vấn (LuatTuVan)»; dòng ADMIN chỉ ghi «CRUD danh mục» | **ADMIN và BIEN_TAP** cùng quản lý luật (CHUYEN_GIA, NONG_DAN: 403) | **Quyết định**: sửa use case thêm ADMIN, hoặc siết code (1 dòng `vai_tro_cho_phep`) |
| 9 | Ai được tư vấn | Mục 6, dòng NONG_DAN: «thực hiện tư vấn (Rule-based)»; các vai trò khác không có dòng này | **Cả 4 vai trò** đều dùng được form tư vấn. Lý do: kịch bản demo cho ADMIN đổi trọng số rồi tư vấn lại ngay | **Quyết định**: (a) sửa use case «Tư vấn» thành mọi người dùng đã đăng nhập (khuyến nghị); (b) siết code về Nông dân, khi đó demo phải đăng xuất rồi đăng nhập Nông dân để tư vấn lại |
| 10 | Quyền xem hỏi đáp | Mục 6: CHUYEN_GIA «xem danh sách câu hỏi, trả lời câu hỏi»; NONG_DAN «đặt câu hỏi»; ADMIN và BIEN_TAP không có quyền về hỏi đáp | ADMIN **xem** danh sách và chi tiết câu hỏi (chỉ đọc); BIEN_TAP **không** vào được Hỏi đáp (403) | **Sửa tài liệu** (thêm ADMIN xem hỏi đáp) hoặc siết code |
| 11 | Quyền xuất báo cáo | «ADMIN: báo cáo và mọi Excel» | Đúng như vậy, và có thêm 3 địa chỉ tải Excel (`/bao-cao/cay-trong/`, `/luat-tu-van/`, `/lich-su-tu-van/`); các vai trò khác 403 | **Sửa tài liệu**: bảng URL mục 7 thêm 3 dòng |

### A3. Nghiệp vụ mà Phần A chưa quy định, hệ thống đã chọn

Sơ đồ tuần tự và hoạt động **nên thể hiện** các điểm sau, vì đây là chỗ giảng viên dễ hỏi.

| # | Điểm | Hệ thống làm gì |
|---|---|---|
| 12 | Mức khớp trong công thức điểm | Điểm = w1×khớp(nhu cầu) + w2×khớp(tỉnh) + w3×khớp(mùa). **Khớp nhu cầu** = tỷ lệ cụm từ khóa của luật có mặt trong nhu cầu (bỏ dấu, không phân biệt hoa thường; một cụm khớp khi đủ mọi từ của cụm). **Khớp tỉnh/mùa**: đúng = 1; luật chung (để trống) = 0,5; luật chỉ định giá trị khác với đầu vào **bị loại**; đầu vào mùa để trống mà luật có chỉ định mùa = 0. Luật không khớp từ khóa nào cũng bị loại. Mỗi cây chỉ giữ luật điểm cao nhất. `score_weight` **không** nằm trong công thức, chỉ dùng xếp hạng khi bằng điểm |
| 13 | «Ngoài phạm vi» xảy ra ở hai nơi, hai cơ chế | **Tư vấn**: nhu cầu rỗng, tỉnh ngoài 5 tỉnh Tây Nguyên, mùa không nhận ra, hoặc không luật nào khớp. **Hỏi đáp**: kiểm tra theo thứ tự (1) nhắc tỉnh ngoài vùng, (2) hỏi giá/dự đoán, (3) không nhắc cây trồng/kỹ thuật trong danh mục. Cả hai trả đúng một câu: «Hệ thống chưa đủ thông tin dữ liệu về nội dung này trong phạm vi hỗ trợ» |
| 14 | Tư vấn có hai luồng | «Xem kết quả»: tính điểm, **ghi lịch sử**, ghi nhật ký, rồi **chuyển hướng** sang trang kết quả đã lưu. «Tính nhanh»: gọi API, **không ghi gì**. Trang kết quả/lịch sử **không tính lại**, chỉ hiển thị bản chụp JSON đã lưu |
| 15 | Hỏi đáp | Gửi câu hỏi: phân loại; ngoài phạm vi thì lưu `NGOAI_PHAM_VI` và tạo ngay `TraLoi` tự động. Chuyên gia trả lời: khóa dòng câu hỏi, chỉ khi đang `CHO_TRA_LOI`; hai chuyên gia cùng lúc thì một người thành công, người kia nhận thông báo «đã được xử lý» |
| 16 | Mã phiếu tự sinh | 4 loại: `LT` (luật), `LS` (lịch sử tư vấn), `CH` (câu hỏi), `TK` (lịch sử tìm kiếm), dạng `XXyyyymmdd-nnn`. Có khóa tư vấn PostgreSQL theo (tiền tố, ngày) và thử lại tối đa 10 lần khi trùng |
| 17 | Truy xuất nguồn | `?ma=<mã luật>` và tùy chọn `&ls=<mã lịch sử>`. Luật đã bị xóa thì vẫn truy xuất được từ bản chụp trong lịch sử (nếu người dùng được xem lịch sử đó); cảnh báo nếu tài liệu của luật đã đổi sau lần tư vấn |
| 18 | Trọng số | Chỉ ADMIN. Ba giá trị không âm, tổng bằng 1, chấp nhận dấu phẩy. Cập nhật trong một transaction có khóa dòng; ghi nhật ký giá trị cũ → mới. Lịch sử cũ không bị ảnh hưởng |
| 19 | Tài khoản | Khóa tài khoản: người đang đăng nhập bị đưa ra ở yêu cầu kế tiếp. Không tự khóa mình, không tự hạ quyền ADMIN của mình |
| 20 | Nhật ký | 21 hành động được ghi: Đăng nhập, Đăng nhập thất bại, Đăng xuất, Đổi mật khẩu, Tạo/Sửa người dùng, Khóa/Mở khóa tài khoản, Thêm/Sửa/Xóa danh mục, Tư vấn, Gửi câu hỏi, Trả lời câu hỏi, Sửa trọng số, Thêm/Sửa/Bật/Tắt/Xóa luật tư vấn, Xuất báo cáo. **Không** ghi: tìm kiếm (đã có bảng lịch sử tìm kiếm), xem trang |
| 21 | Tìm kiếm | Dùng GET (chia sẻ được liên kết); mỗi lần tìm hợp lệ ghi một dòng `LichSuTimKiem` (không có cột người dùng). Gõ có dấu thì khớp đúng dấu, không dấu thì khớp rộng |
| 22 | Giao diện | Bootstrap tải từ CDN (đúng mục 2) và có bản dự phòng cục bộ trong `static/vendor/bootstrap` (tự dùng khi CDN lỗi, hoặc bật `BOOTSTRAP_CUC_BO=1`) |

### A4. Đề nghị cập nhật Phần A (dán thẳng vào đề cương)

1. **Mục 3:** `hoidap` gồm `CauHoi`, `TraLoi`; `danhmuc` gồm `CayTrong`, `TinhThanh`, `MuaVu`, `KyThuat`, `TaiLieu`; `thongke` thống kê lượt tư vấn, tỷ lệ câu hỏi được trả lời, từ khóa tìm kiếm nhiều nhất (bỏ «tỷ lệ đạt của các bộ test case»).
2. **Mục 4:** «14 bảng» (thêm `TraLoi`); thêm `LuatTuVan.tai_lieu` (khóa ngoại tới `TaiLieu`, cho phép NULL); thêm `CauHoi.thoi_gian`.
3. **Mục 6:** ghi rõ các quyết định ở A2 (dòng 7 đến 10).
4. **Mục 7:** thêm `/bao-cao/cay-trong/`, `/bao-cao/luat-tu-van/`, `/bao-cao/lich-su-tu-van/`, `/tu-van/api-tinh-diem/`, `/tu-van/lich-su/<id>/`, `/tu-van/luat/...`, `/hoi-dap/<id>/tra-loi/`, `/truy-xuat/`.
5. **Mục 5:** thêm định nghĩa «mức khớp» (dòng 12) để công thức tính tay lại được.

## B. Danh sách đối chiếu theo từng loại sơ đồ

### B1. Sơ đồ use case

- **Tác nhân (5):** Khách chưa đăng nhập (chỉ đăng nhập); Nông dân; Chuyên gia; Biên tập viên; Quản trị viên. Quản trị viên có mọi quyền của Biên tập viên về danh mục và luật.
- **Use case theo tác nhân** (đầy đủ ở `MA_TRAN_PHAN_QUYEN.md`):
  - Mọi người dùng đã đăng nhập: đăng xuất, đổi mật khẩu, xem danh mục, tìm kiếm, tư vấn (xem kết quả / tính nhanh), xem lịch sử tư vấn, truy xuất nguồn.
  - Nông dân: đặt câu hỏi, xem câu hỏi của mình. Chuyên gia: xem câu hỏi, trả lời.
  - Biên tập viên và Quản trị viên: thêm/sửa/xóa danh mục, quản lý luật tư vấn (thêm, sửa, xóa, bật/tắt).
  - Quản trị viên: quản lý người dùng (thêm, sửa, khóa/mở khóa), xem nhật ký, cấu hình trọng số, xem hỏi đáp, xuất báo cáo (cây trồng, luật hiện hành, lịch sử tư vấn), xem và xuất thống kê.
- **Quan hệ nên có:** «Xem kết quả tư vấn» **include** «Tính điểm» và «Lưu lịch sử»; «Xem nguồn» **extend** «Xem kết quả tư vấn»; «Trả lời tự động» **extend** «Đặt câu hỏi» (khi ngoài phạm vi); «Xuất Excel» **extend** «Xem thống kê».
- **Hỏi để kiểm tra sơ đồ của bạn:** Có tác nhân «Khách» không? Use case «Tư vấn» gắn với mấy tác nhân (dòng 9)? ADMIN có use case «Quản lý luật» không (dòng 8)?

### B2. Sơ đồ lớp / ERD

- **14 lớp**, 6 app có model (xem `TU_DIEN_DU_LIEU.md`, có sẵn ERD Mermaid sinh từ mã nguồn): `VaiTro`, `NguoiDung`, `NhatKy`, `CayTrong`, `TinhThanh`, `MuaVu`, `KyThuat`, `TaiLieu`, `LuatTuVan`, `LichSuTuVan`, `LichSuTimKiem`, `CauHoi`, `TraLoi`, `CauHinhHeThong`.
- **10 quan hệ:** `VaiTro 1—* NguoiDung`; `NguoiDung 0..1—* NhatKy`; `CayTrong 1—* LuatTuVan`; `TinhThanh 0..1—* LuatTuVan`; `MuaVu 0..1—* LuatTuVan`; `TaiLieu 0..1—* LuatTuVan`; `NguoiDung 0..1—* LichSuTuVan`; `NguoiDung 1—* CauHoi`; `CauHoi 1—0..1 TraLoi`; `NguoiDung 0..1—* TraLoi`.
- **Không có khóa ngoại** từ `LichSuTuVan` tới luật hay cây (lưu bản chụp JSON), từ `LichSuTimKiem` tới người dùng, từ `CauHinhHeThong` tới bảng nào.
- **Phương thức đáng vẽ:** `NguoiDung.co_vai_tro(*ma)`, `NguoiDung.ho_ten`, `NhatKy.ghi(...)` (phương thức lớp).
- **Lưu ý:** nghiệp vụ nằm ở các **hàm dịch vụ** (`tuvan/services.py`, `hoidap/services.py`, `taikhoan/services.py`, `cauhinh/services.py`...), không phải lớp. Nếu sơ đồ lớp có lớp «RuleEngine» hay «TuVanService», đó là sơ đồ khái niệm, ánh xạ sang module `tuvan/services.py`; nên ghi chú để khỏi bị hỏi «lớp này nằm ở đâu trong code».
- **Kiểu dữ liệu hay vẽ sai:** `MuaVu.thoi_gian_tu/den` là **tháng (1 đến 12)** chứ không phải ngày; `LuatTuVan.condition_json` là JSONB dạng `{"tu_khoa": [...]}`; `LuatTuVan.score_weight` là số thập phân (6,2); trọng số w1,w2,w3 lưu **chuỗi** trong `CauHinhHeThong.gia_tri`.

### B3. Sơ đồ tuần tự (các luồng nên vẽ)

1. **Đăng nhập:** Trình duyệt → `DangNhapView` → `DangNhapForm` (xác thực, báo riêng khi tài khoản bị khóa) → tín hiệu `user_logged_in` → `NhatKy.ghi`. Sai mật khẩu: `user_login_failed` → `NhatKy.ghi` (không ghi mật khẩu).
2. **Xem kết quả tư vấn:** `TuVanView` (POST) → `TuVanForm` → `tu_van_va_luu` → `tinh_diem_tu_van` (đọc `CauHinhHeThong` qua `lay_trong_so`; đọc các `LuatTuVan` đang bật; tính điểm) → `luu_lich_su_tu_van` (**một transaction**: `tao_voi_ma_tu_sinh` → tạo `LichSuTuVan`; `NhatKy.ghi`) → chuyển hướng (302) → `LichSuChiTietView` (đọc JSON, **không gọi lại** bộ máy tính điểm).
3. **Tính nhanh:** JS → `ApiTinhDiemView` → `tinh_diem_tu_van` → trả JSON + HTML; **không có** bước ghi.
4. **Gửi câu hỏi:** `CauHoiThemView` → `gui_cau_hoi` → `phan_loai_cau_hoi` → (một transaction) tạo `CauHoi` [+ tạo `TraLoi` tự động nếu ngoài phạm vi] + `NhatKy.ghi`.
5. **Chuyên gia trả lời:** `TraLoiView` → `tra_loi_cau_hoi` → (transaction) khóa dòng `CauHoi` → kiểm tra trạng thái → tạo `TraLoi` → đổi trạng thái → `NhatKy.ghi`.
6. **Đổi trọng số:** `TrongSoView` → `TrongSoForm` → `cap_nhat_trong_so` → (transaction) khóa 3 dòng cấu hình → cập nhật → `NhatKy.ghi`.
7. **Xuất Excel:** `XuatExcelView` → `baocao.services` (truy vấn) → `tao_xlsx` → `NhatKy.ghi` → file.
8. **Truy xuất nguồn:** `TruyXuatView` → tìm `LuatTuVan` (→ `TaiLieu`); nếu không có luật và có `ls` hợp lệ thì dùng bản chụp trong `LichSuTuVan`.

### B4. Sơ đồ hoạt động

- **Tư vấn:** [form hợp lệ?] không → hiện lỗi, giữ dữ liệu, không ghi. Có → [trọng số hợp lệ?] không → báo lỗi cấu hình, không ghi. Có → [tỉnh thuộc 5 tỉnh Tây Nguyên và nhu cầu không rỗng?] không → ngoài phạm vi. Có → lọc luật đang bật, loại luật khác tỉnh/mùa, tính điểm, mỗi cây giữ luật điểm cao nhất, sắp xếp → [còn đề xuất nào?] không → ngoài phạm vi. Có → hiển thị. **Cả hai nhánh (có đề xuất/ngoài phạm vi) đều được lưu lịch sử** khi bấm «Xem kết quả».
- **Hỏi đáp:** [nhắc tỉnh ngoài vùng?] → [hỏi giá/dự đoán?] → [nhắc cây/kỹ thuật trong danh mục?] → «Chờ trả lời» hoặc «Ngoài phạm vi + trả lời tự động»; nhánh chuyên gia: [còn «Chờ trả lời»?] → trả lời hoặc báo «đã được xử lý».
- **Xóa danh mục:** [đang được luật dùng?] có → từ chối, nêu số luật; không → xóa, ghi nhật ký.

## C. Việc nên làm tiếp (theo thứ tự)

1. Gửi các sơ đồ UML để tôi đối chiếu từng nét với mục B.
2. Quyết định 4 điểm ở A2 (dòng 7 đến 10): giữ code và sửa tài liệu, hay siết code.
3. Cập nhật Phần A theo A4, rồi mới viết các chương báo cáo (báo cáo lấy từ Phần A đã cập nhật để khỏi mâu thuẫn).
