# Viet Font Studio

Ứng dụng local một người dùng để Việt hóa font từ file TTF/OTF tới bản export. Frontend React + TypeScript, backend FastAPI, SQLite và file đầu ra lưu cục bộ. Mỗi lần tạo hoặc tinh chỉnh VER đều cần provider AI đã kết nối; AI đề xuất hồ sơ phong cách/tham số, còn VFK rule engine luôn áp dụng quy tắc tạo font, giới hạn tham số và kiểm định tại local.

## Chạy ở chế độ phát triển

Cần có Python 3.12, uv, Node.js và npm.

Terminal 1 — backend:

~~~powershell
Set-Location -LiteralPath 'E:\viethoa-font-tool\backend'
uv sync
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
~~~

Terminal 2 — frontend:

~~~powershell
Set-Location -LiteralPath 'E:\viethoa-font-tool\frontend'
npm install
npm run dev
~~~

Mở địa chỉ Vite hiển thị trong terminal (mặc định http://127.0.0.1:5173). Vite chuyển tiếp /api tới backend 127.0.0.1:8000.

## Chạy bản build

~~~powershell
Set-Location -LiteralPath 'E:\viethoa-font-tool\frontend'
npm run build
Set-Location -LiteralPath 'E:\viethoa-font-tool\backend'
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
~~~

FastAPI tự phục vụ frontend/dist nếu thư mục build tồn tại.

## Luồng MVP

1. Tạo project và tải lên font.
2. Phân tích cấu trúc font ở local; người dùng phải kết nối provider và chọn model trước khi tạo VER. AI nhận metadata cùng phép đo glyph đã chuẩn hóa để đề xuất hồ sơ phong cách và ba lựa chọn VER 1A / 1B / 1C, sau đó VFK rule engine ánh xạ tham số hợp lệ vào pipeline dựng font.
3. Chỉnh contour vector trong editor; bản nháp là revision mới.
4. Gửi feedback để AI tinh chỉnh một lựa chọn VER thành revision mới, hoặc chỉnh vector thủ công.
5. Build và kiểm định revision bằng engine local, duyệt đúng revision rồi export đúng định dạng.

Các job chạy lần lượt trong một worker local. Bản export và database nằm dưới .data/ tại thư mục dự án.

## Phạm vi engine

- Hỗ trợ font tĩnh regular: TTF TrueType và OTF CFF. Font nghiêng và variable font được báo là chưa hỗ trợ.
- VER 1B đặt các dấu thanh trên đỉnh dấu mũ/trăng. VER 1C dựng dấu hỏi từ phần trên của dấu ?.
- Editor dùng contour và thao tác node để sửa nét xuất ra. Nét cọ là guide để ghi chú và xem trước, không được tự động gộp vào outline.
- Kiểm định dùng kiemword.py và OpenType Sanitizer (`opentype-sanitizer`); chạy `uv sync` để cài đầy đủ dependency backend trước khi dùng QA hoặc export.
- Kit nguồn được giữ trong backend/vendor/viet-font-kit. README của kit nêu điều khoản sử dụng phi thương mại; hãy giữ thông báo nguồn và tuân theo điều khoản đó.

## Dữ liệu local

VFK_DATA_DIR có thể đặt để chuyển database và font files sang thư mục khác. Mặc định mọi dữ liệu nằm trong .data/.

## Kết nối provider AI

- ChatGPT dùng Sign in with ChatGPT để người dùng cấp quyền sử dụng hạn mức theo gói ChatGPT. Ollama Cloud dùng API key.
- Token và API key được lưu trong credential store của hệ điều hành (Windows Credential Manager trên Windows), không lưu trong SQLite hoặc trình duyệt.
- Khi người dùng mở bộ chọn model, backend mới yêu cầu danh sách model của provider. Dashboard chỉ đọc trạng thái đã lưu.
- Khi gọi AI, hệ thống gửi metadata font đã chuẩn hóa, một số tỷ lệ hình học đo cục bộ và feedback người dùng. File font, đường dẫn file và contour glyph không được gửi. Provider xử lý prompt và câu trả lời trên dịch vụ đám mây.
- AI chỉ được phép đề xuất các tham số thiết kế trong khoảng giới hạn. Engine Việt hóa, chỉnh sửa vector, validation và export font vẫn chạy local.
- Không có chế độ tạo hoặc tinh chỉnh VER chỉ bằng rule engine; kết nối AI là điều kiện bắt buộc, còn rule engine là lớp xử lý và validation luôn chạy cùng.
