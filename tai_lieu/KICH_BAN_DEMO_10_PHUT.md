# Kịch bản demo 10 phút

Trình tự đúng theo đề cương: Nông dân tư vấn → hỏi ngoài phạm vi → ADMIN đổi trọng số → tư vấn lại thấy kết quả đổi → truy xuất nguồn tài liệu.

> **Lưu ý trung thực.** Mọi con số trên màn hình dưới đây đã được kiểm chứng tự động bằng chính các thao tác này (xem test case TV-01, TV-02, HD-03, CH-02, CH-05, TX-01). **Thời lượng mỗi bước là ước tính**, tôi không thể diễn tập thay bạn: hãy bấm giờ một lần và chỉnh lại. Tôi cũng chưa xem giao diện trên trình duyệt thật.

## 1. Chuẩn bị trước demo

**Trước giờ G khoảng 30 phút** (làm sạch dữ liệu, tránh «dữ liệu bẩn» từ lúc test):

```bash
python manage.py flush --noinput          # xóa sạch dữ liệu cũ (xóa cả tài khoản)
python manage.py nap_du_lieu_mau           # nạp lại: 4 tài khoản (mật khẩu 123456), 12 cây, 5 tỉnh, 7 luật, trọng số 0,5 / 0,3 / 0,2
```

Trong `.env` đặt `BOOTSTRAP_CUC_BO=1` nếu không chắc có mạng (giao diện dùng bản Bootstrap có sẵn trong máy). Rồi chạy `python manage.py runserver`.

**Chuẩn bị màn hình:**
- Hai cửa sổ trình duyệt: **cửa sổ thường** cho Nông dân, **cửa sổ ẩn danh** cho ADMIN (đăng nhập hai tài khoản cùng lúc mà không phải đăng xuất).
- Phóng to chữ (Ctrl và dấu +) lên khoảng 125% để hội đồng đọc được. Tắt thông báo, tắt gợi ý lưu mật khẩu của trình duyệt.
- Mở sẵn tab `/dang-nhap/` ở cả hai cửa sổ.
- Có sẵn: file Excel đã tải (phòng khi mở file chậm), ảnh chụp màn hình từng bước, một đoạn video quay lại toàn bộ demo.

**Kiểm tra 5 phút trước:** đăng nhập `admin`, vào Quản trị → Trọng số tư vấn, phải thấy **0,5 / 0,3 / 0,2**. Nếu khác, đặt lại.

## 2. Kịch bản từng bước

| Thời gian | Tài khoản | Thao tác | Câu nói chính | Màn hình mong đợi | Điểm kỹ thuật nên nhấn mạnh |
|---|---|---|---|---|---|
| 0:00 đến 0:50 | Chưa đăng nhập | Mở trang đăng nhập | «Hệ thống tư vấn cây trồng cho 5 tỉnh Tây Nguyên. Nông dân nhập nhu cầu, hệ thống đề xuất cây phù hợp **kèm lý do và nguồn**.» | Trang đăng nhập | Django theo mô hình MTV, PostgreSQL. Tư vấn theo **luật lưu trong CSDL** (Rule-based), không phải hộp đen: giải thích được, truy xuất được nguồn |
| 0:50 đến 1:30 | `nongdan` / `123456` | Đăng nhập | «Em đăng nhập bằng tài khoản Nông dân.» | Trang chủ «Xin chào, Phạm Nông Dân», menu: Trang chủ, Giới thiệu, Danh mục, Tra cứu, Tư vấn, Hỏi đáp | **4 vai trò**, menu hiển thị theo vai trò; nông dân không thấy Báo cáo hay Quản trị |
| 1:30 đến 3:45 | `nongdan` | Menu Tư vấn → Tư vấn cây trồng. Nhập nhu cầu **Cây giá trị kinh tế cao**, tỉnh **Đăk Lăk**, mùa **Mùa mưa**. Bấm **Xem kết quả** | «Nhu cầu là cây giá trị kinh tế cao, ở Đăk Lăk, trồng vào mùa mưa.» | Chuyển sang trang kết quả: **#1 Sầu riêng, Điểm 1,00 · #2 Cà phê, Điểm 0,88 · #3 Hồ tiêu, Điểm 0,75**. Có lý do từng cây, bảng điểm thành phần, nguồn tài liệu | Chỉ vào thẻ **Cà phê**, tính tay trên bảng: 0,5 × 0,75 + 0,3 × 1 + 0,2 × 1 = **0,875**. «Điểm phù hợp = w1 × khớp nhu cầu + w2 × khớp tỉnh + w3 × khớp mùa.» Hồ tiêu là luật **chung** cho mọi tỉnh nên chỉ còn 0,75: nói thẳng để hội đồng không hỏi vặn. Kết quả được **lưu lịch sử** (mã `LS...`) trong một transaction cùng nhật ký |
| 3:45 đến 5:00 | `nongdan` | Menu Hỏi đáp → «+ Đặt câu hỏi». Nhập **giá cà phê ngày mai** → Gửi câu hỏi | «Giờ em thử hỏi một câu hệ thống không hỗ trợ: giá cà phê ngày mai.» | Báo vàng «Câu hỏi nằm ngoài phạm vi hỗ trợ nên đã được trả lời tự động.»; trạng thái **Ngoài phạm vi**; khối **Trả lời tự động** có đúng câu: «Hệ thống chưa đủ thông tin dữ liệu về nội dung này trong phạm vi hỗ trợ» | Hệ thống **không bịa**: câu hỏi hỏi giá hoặc dự đoán, hoặc ngoài 5 tỉnh, hoặc không nhắc cây/kỹ thuật trong danh mục thì trả câu tiêu chuẩn. Không cần chuyên gia xử lý. (Nếu còn thời gian: «Trồng cà phê ở Bình Phước được không?» cũng ra kết quả tương tự) |
| 5:00 đến 6:30 | `admin` / `123456` (cửa sổ ẩn danh) | Đăng nhập. Menu Quản trị → **Trọng số tư vấn**. Đặt **w1 = 0,8; w2 = 0,1; w3 = 0,1** → Lưu | «Quản trị viên chỉnh độ quan trọng của nhu cầu lên 0,8. Hai trọng số còn lại cộng 0,2 vì hệ thống bắt tổng bằng 1.» | Báo «Đã cập nhật trọng số.» Menu của admin có thêm Báo cáo, Quản trị | Chỉ **ADMIN** đổi được; kiểm tra **tổng = 1** (thử nhập 0,8 / 0,3 / 0,1 để cho thấy bị từ chối: «Tổng w1 + w2 + w3 phải bằng 1»); lưu trong **transaction có khóa dòng**, ghi nhật ký giá trị cũ → mới |
| 6:30 đến 7:45 | `admin` | Menu Tư vấn → Tư vấn cây trồng. Nhập **đúng dữ liệu cũ** → Xem kết quả | «Em tư vấn lại cùng dữ liệu để xem trọng số tác động thế nào.» | **#1 Sầu riêng 1,00 · #2 Hồ tiêu 0,90 · #3 Cà phê 0,80**: Hồ tiêu **vượt** Cà phê | Cùng dữ liệu, đổi trọng số thì thứ hạng đổi, **không sửa code**, không cần khởi động lại. Cho xem Lịch sử tư vấn: lần cũ của nongdan **vẫn là Cà phê 0,88 trước Hồ tiêu 0,75** (lịch sử là **bản chụp JSON**, không tính lại) |
| 7:45 đến 8:45 | `admin` | Ở trang kết quả bấm **Xem nguồn** của Sầu riêng | «Mỗi đề xuất đều truy xuất được nguồn.» | Trang truy xuất: luật `LT20260101-001` «Đang áp dụng», Sầu riêng, Đăk Lăk, Mùa mưa; **Tài liệu: Quy trình kỹ thuật trồng trọt cây công nghiệp và cây ăn quả Tây Nguyên, nguồn WASI** | Chuỗi truy xuất: **kết quả → luật → tài liệu**. Luật có thể đã bị xóa mà lịch sử vẫn truy xuất được nguồn nhờ bản chụp. Admin còn thấy «Hệ số ưu tiên», nông dân thì không |
| 8:45 đến 9:30 | `admin` | Menu Báo cáo → Thống kê → bấm **Xuất Excel** | «Quản trị viên xem thống kê và xuất báo cáo.» | Số lượt tư vấn, tỷ lệ tư vấn có đề xuất, tỷ lệ câu hỏi được trả lời, từ khóa tìm nhiều nhất; tải `thong-ke_yyyymmdd.xlsx` | Ô tỷ lệ là **số thật** định dạng %, không phải chữ. Dữ liệu người dùng nhập được chống chèn công thức Excel |
| 9:30 đến 10:00 | Không | Quay về slide kết | «Hệ thống có hơn 450 bài kiểm thử tự động, 69 test case thủ công, ma trận phân quyền 40 đường dẫn × 4 vai trò. Hạn chế: chưa dự đoán giá, nhận dạng cây theo tên đúng trong danh mục.» | Slide kết luận | Tự nhận hạn chế trước khi bị hỏi |

**Tổng 10 phút.** Nếu bị rút xuống 7 phút: bỏ bước thống kê (8:45) và phần «thử nhập sai tổng trọng số» ở bước 5:00. Nếu còn dư thời gian: cho xem «Tính nhanh (không lưu)» và quy trình chuyên gia trả lời câu hỏi.

## 3. Phương án dự phòng

| Sự cố | Cách xử lý |
|---|---|
| **Mất mạng** | Hệ thống chạy hoàn toàn trên máy bạn, chỉ giao diện Bootstrap mặc định tải từ CDN. Đặt `BOOTSTRAP_CUC_BO=1` trong `.env` rồi chạy lại `runserver`: dùng bản có sẵn trong `static/vendor/bootstrap`, **không cần mạng**. Nên bật sẵn từ trước demo. Nếu quên và CDN lỗi, trang tự chuyển sang bản cục bộ nhưng có thể chờ vài giây. **Chưa kiểm chứng trên trình duyệt thật**, hãy thử một lần (test case UI-01) |
| PostgreSQL không chạy | Khởi động lại dịch vụ PostgreSQL của máy (Windows: Services; Linux: `service postgresql start`). Nếu không kịp: chuyển sang video quay sẵn |
| Dữ liệu bị lệch (đã test trước đó) | `python manage.py flush --noinput` rồi `python manage.py nap_du_lieu_mau` (khoảng 30 giây), sau đó kiểm tra trọng số 0,5 / 0,3 / 0,2 |
| Quên mật khẩu hoặc tài khoản bị khóa nhầm | `python manage.py nap_du_lieu_mau --dat-lai-mat-khau` đặt lại mật khẩu 4 tài khoản về 123456. Tài khoản bị khóa: đăng nhập admin, mở khóa ở Quản trị → Người dùng |
| Một bước lỗi bất ngờ | Mở ảnh chụp màn hình bước đó, nói «đây là kết quả đã kiểm thử», làm tiếp bước sau. Không sửa code trước hội đồng |
| Máy trường không có PostgreSQL | Dùng laptop cá nhân; hoặc chiếu video |

## 4. Câu hỏi hội đồng thường hỏi (trả lời bám đúng hệ thống)

1. **Vì sao Rule-based mà không học máy?** Dữ liệu ít và cần giải thích được: mỗi đề xuất có lý do, điểm thành phần, nguồn tài liệu. Hạn chế: không tự học, luật do Biên tập viên nhập.
2. **Điểm tính thế nào?** Điểm = w1 × khớp nhu cầu + w2 × khớp tỉnh + w3 × khớp mùa, tổng w bằng 1. Khớp nhu cầu là tỷ lệ cụm từ khóa của luật có trong nhu cầu; luật chung cho mọi tỉnh/mùa được 0,5; luật chỉ định tỉnh hoặc mùa khác với đầu vào thì bị loại. Ví dụ Cà phê: 0,5 × 0,75 + 0,3 + 0,2 = 0,875.
3. **Đổi trọng số thì lịch sử cũ ra sao?** Giữ nguyên: lịch sử lưu bản chụp JSON gồm cả trọng số lúc tư vấn, trang lịch sử không tính lại.
4. **Hai người cùng sửa trọng số, hoặc hai chuyên gia cùng trả lời một câu?** Cập nhật trọng số khóa dòng nên xếp hàng, kết quả luôn là một bộ ba nguyên vẹn. Hai chuyên gia cùng trả lời: chỉ một người thành công. Cả hai đều có test đa luồng.
5. **Câu hỏi ngoài phạm vi xử lý thế nào?** Kiểm tra theo thứ tự: nhắc tỉnh ngoài Tây Nguyên, hỏi giá hoặc dự đoán, không nhắc cây/kỹ thuật trong danh mục. Ngoài phạm vi thì trả đúng một câu chuẩn và lưu trạng thái để thống kê.
6. **Bảo mật?** Phân quyền theo vai trò (chưa đăng nhập 302, sai vai trò 403), CSRF, mật khẩu băm và có kiểm tra độ mạnh bằng tiếng Việt, khóa tài khoản, thoát ký tự HTML, chống chèn công thức khi xuất Excel, nhật ký 22 loại hành động.
7. **Kiểm thử ra sao?** Hơn 450 bài kiểm thử tự động (trong đó có kiểm thử đa luồng và «phá thử» quy tắc để xem test có bắt được không), 69 test case thủ công đã được kiểm chứng tự động, ma trận 40 đường dẫn × 4 vai trò + chưa đăng nhập.
8. **Hạn chế?** Không dự đoán giá; nhận dạng cây theo đúng cụm tên trong danh mục (hỏi «trồng lúa» khi danh mục ghi «Lúa nước» thì chưa khớp); thống kê tính trong Python nên hợp quy mô đồ án, không cho hàng triệu dòng; chưa có biểu đồ đồ họa.
9. **Hướng phát triển?** Thêm tên gọi khác cho cây trồng, đề xuất dựa trên lịch sử, biểu đồ thống kê, xuất báo cáo theo luồng cho dữ liệu lớn.
