# Viet Font Studio

Ứng dụng local một người dùng để Việt hóa font từ file TTF/OTF tới bản export. Frontend React + TypeScript, backend FastAPI, SQLite và file đầu ra lưu cục bộ. Mỗi lần tạo hoặc tinh chỉnh VER đều cần provider AI đã kết nối; AI đề xuất hồ sơ phong cách/tham số, còn VFK rule engine luôn áp dụng quy tắc tạo font, giới hạn tham số và kiểm định tại local.

## Chạy ở chế độ phát triển

Cần có Python 3.12, uv, Node.js và npm.

Terminal 1 — backend:

~~~powershell
Set-Location -LiteralPath 'E:\viethoa-font-tool\backend'
uv sync
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
uv run --env-file .env uvicorn app.main:app --host 127.0.0.1 --port 8000
~~~

Terminal 2 — frontend:

~~~powershell
Set-Location -LiteralPath 'E:\viethoa-font-tool\frontend'
npm install
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
npm run dev
~~~

Mở địa chỉ Vite hiển thị trong terminal (mặc định http://127.0.0.1:5173). Vite chuyển tiếp /api tới backend 127.0.0.1:8000.

## Chạy bản build

~~~powershell
Set-Location -LiteralPath 'E:\viethoa-font-tool\frontend'
npm run build
Set-Location -LiteralPath 'E:\viethoa-font-tool\backend'
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
uv run --env-file .env uvicorn app.main:app --host 127.0.0.1 --port 8000
~~~

FastAPI tự phục vụ frontend/dist nếu thư mục build tồn tại.

## Chạy bằng Docker

Docker Compose build frontend và backend thành một container. Mặc định ứng dụng chỉ mở trên `127.0.0.1:8000`; callback `127.0.0.1:8765` được map để đăng nhập ChatGPT OAuth hoạt động từ trình duyệt trên máy host.

~~~powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Mở .env và thay VFK_KEYRING_PASSWORD bằng một secret ngẫu nhiên dài.
docker compose up --build -d
docker compose logs -f vietfont-studio
~~~

Database, font tải lên, file export và GNOME Keyring được giữ trong named volumes của Docker. Giữ nguyên `VFK_KEYRING_PASSWORD` để mở khóa credential store sau khi restart. `docker compose down` giữ dữ liệu; `docker compose down -v` xóa cả dữ liệu dự án và provider credentials.

Volume dữ liệu Docker tách biệt với thư mục `.data` của lần chạy local; chuyển từ backend local sang Docker không tự nhập các dự án cũ.

## Sao lưu Google Drive

Để bật backup lên Drive, tạo Google Cloud project, bật Google Drive API và Google Picker API, rồi tạo API key cùng OAuth Client ID cho ứng dụng web. Cấu hình OAuth scope `https://www.googleapis.com/auth/drive.file`; Google Picker sẽ yêu cầu người dùng chọn thư mục đích cụ thể. App chỉ giữ access token trong bộ nhớ trang hiện tại và không lưu refresh token.

- Chạy development: điền `VITE_GOOGLE_CLIENT_ID`, `VITE_GOOGLE_API_KEY` và `VITE_GOOGLE_APP_ID` trong `frontend/.env`, sau đó khởi động lại Vite.
- Chạy Docker: điền cùng ba giá trị trong file `.env` ở thư mục gốc rồi chạy lại `docker compose up --build -d` để đóng gói lại frontend.
- Thêm authorized JavaScript origins cho `http://127.0.0.1:5173`, `http://localhost:5173` và `http://localhost:8000` theo cách bạn chạy app. Giới hạn API key theo các origin này và `https://docs.google.com/*`; chỉ bật Google Picker API cùng Google Drive API. `VITE_GOOGLE_APP_ID` là project number trong Google Cloud.
- Sao lưu chỉ gửi các file TTF/OTF export tới thư mục được chọn. App đọc family/style từ metadata font; AI chỉ nhận metadata tên/kiểu và tên file hiện tại để chuẩn hóa tên thư mục, tên file.

## CI

- `.github/workflows/ci.yml` chạy trên mọi push, pull request và khi chạy thủ công. Workflow build/typecheck frontend, đồng bộ dependency backend từ `uv.lock`, biên dịch module Python và kiểm tra import/OpenAPI.

## Cấu hình môi trường

- Backend: sao chép `backend/.env.example` thành `backend/.env`. `VFK_DATA_DIR` chọn thư mục lưu database và font; đường dẫn tương đối được tính từ `backend/`.
- Frontend: sao chép `frontend/.env.example` thành `frontend/.env`. `VITE_API_BASE_URL` đặt đường dẫn API và `VFK_API_ORIGIN` đặt đích proxy trong Vite khi chạy development.
- File `.env` và `.env.local` không được Git theo dõi. Chỉ chia sẻ các file `.env.example`, không đưa token hoặc API key vào đó.

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
