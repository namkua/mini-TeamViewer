# BÀI TẬP LỚN: LẬP TRÌNH MẠNG (PTIT)

## ĐỀ TÀI: HỆ THỐNG ĐIỀU KHIỂN MÁY TÍNH TỪ XA QUA GIAO DIỆN WEB (WEB-BASED REMOTE DESKTOP / MINI ANYDESK)

> **Học viện Công nghệ Bưu chính Viễn thông — Khoa Công nghệ Thông tin 1**  
> **Giảng viên phụ trách:** TS. Đặng Ngọc Hùng  

---

## THÔNG TIN NHÓM

| STT | Họ và Tên | MSSV | Nhiệm vụ phụ trách |
| :---: | :--- | :---: | :--- |
| 1 | Nguyễn Công Hải Nam | B23DCCN583 | Phụ trách phần Server (Relay Server, WebSocket Router, REST API, Database) |
| 2 | Nguyễn Hoàng Tùng | B23DCCN901 | Phụ trách phần Client (Host Agent Python & Web Viewer React) |

**Tên nhóm:** Nhóm 22 — Lập trình mạng  
**Chủ đề đã đăng ký:** Hệ thống điều khiển máy tính từ xa qua Web Socket (Web-based Remote Desktop)

---

## MÔ TẢ HỆ THỐNG

Dự án hiện thực hóa giải pháp **Remote Desktop gọn nhẹ** kết hợp giữa ứng dụng Web và Desktop Native:
- **Người điều khiển (Viewer):** Không cần cài đặt bất kỳ phần mềm nào, chỉ cần mở trình duyệt Web (Chrome, Edge, Safari...) trên laptop, máy tính bảng hoặc điện thoại là có thể theo dõi màn hình và điều khiển chuột, bàn phím máy tính từ xa theo thời gian thực.
- **Máy bị điều khiển (Host):** Chạy ứng dụng **Desktop Agent** siêu nhẹ bằng Python. Ứng dụng tự động đăng ký với máy chủ, tạo mã kết nối **Device ID (6 chữ số)** và **mã PIN** ngẫu nhiên.
- **Máy chủ chuyển tiếp (Relay Server):** Xây dựng trên nền tảng **FastAPI**, quản lý các phòng phiên làm việc (Session Rooms) và chuyển tiếp luồng dữ liệu hai chiều:
  - **Luồng Downlink (Hình ảnh):** Dãy byte nhị phân thô (`Binary Frame`) của ảnh JPEG được chuyển tiếp trực tiếp (Zero-Copy forwarding) từ Host đến Viewer.
  - **Luồng Uplink (Điều khiển):** Gói tin JSON (`Text Frame`) chứa sự kiện chuột/phím từ Viewer gửi về Host.

### Cấu trúc logic tổng quát:
```
[Máy bị điều khiển: Python Agent]
          ▲
          │ 1. Upload Binary JPEG Frames (25-30 FPS)
          │ 2. Nhận JSON Event (Mouse/Key)
          ▼
[Máy chủ trung chuyển: FastAPI Relay Server] (Port 8000)
          ▲
          │ 3. Forward Binary Frames sang Canvas
          │ 4. Nhận JSON Event từ Web
          ▼
[Người điều khiển: React Web App] (Port 3000)
```

---

## CÔNG NGHỆ SỬ DỤNG

| Thành phần | Công nghệ / Thư viện | Vai trò kỹ thuật |
| :--- | :--- | :--- |
| **Relay Server** | Python 3.11 + **FastAPI** | Server WebSocket bất đồng bộ (`asyncio`), xử lý chuyển tiếp gói tin |
| | Uvicorn (ASGI) | Máy chủ Web Server hiệu năng cao |
| | SQLAlchemy + SQLite | Quản lý thiết bị, kiểm tra PIN bảo mật, nhật ký phiên kết nối |
| **Host Agent** | Python 3.10+ | Chạy ngầm trên máy bị điều khiển |
| | `mss` | Thư viện chụp màn hình tốc độ cao (~60 FPS) |
| | `Pillow` (PIL) | Nén ảnh màn hình thành chuỗi byte JPEG trong bộ nhớ RAM |
| | `pynput` | Mô phỏng sự kiện chuột và bàn phím ở tầng hệ điều hành |
| | `websockets` | Socket client bất đồng bộ kết nối liên tục với Server |
| **Web Viewer** | **React 18 + Vite** | Giao diện điều khiển SPA (Single Page Application) |
| | HTML5 Canvas API | Render trực tiếp luồng byte ảnh nhị phân |
| | Lucide React | Hệ thống icon giao diện người dùng |
| **Triển khai** | **Docker & Docker Compose** | Đóng gói toàn bộ Server và Web chạy độc lập chỉ với 1 câu lệnh |

---

## HƯỚNG DẪN CHẠY DỰ ÁN

### Cách 1: Khởi chạy nhanh bằng Docker (Khuyên dùng)
Yêu cầu: Đã cài đặt Docker và Docker Compose.

```bash
# 1. Khởi động Relay Server và Web Viewer bằng Docker
docker-compose up --build
```
- Máy chủ Relay Server sẽ chạy tại: `http://localhost:8000` (Tài liệu API: `http://localhost:8000/docs`)
- Giao diện Web Viewer sẽ chạy tại: `http://localhost:3000`

```bash
# 2. Khởi chạy Host Agent trên máy cần điều khiển:
cd source/client/agent
pip install -r requirements.txt
python agent.py
```
*Lưu ý: Màn hình console của Agent sẽ in ra mã **Device ID** (ví dụ: `839201`) và **mã PIN** (mặc định: `123456`). Truy cập `http://localhost:3000` để bắt đầu điều khiển.*

---

### Cách 2: Chạy trực tiếp (Local không dùng Docker)

#### Bước 1: Chạy Relay Server (FastAPI)
```bash
cd source/server
python3 -m venv venv
source venv/bin/activate # Hoặc venv\Scripts\activate trên Windows
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Bước 2: Chạy Web Viewer (React)
```bash
cd source/client/web
npm install
npm run dev
# Mở trình duyệt tại: http://localhost:3000
```

#### Bước 3: Chạy Host Agent (Python)
```bash
cd source/client/agent
python3 -m venv venv
source venv/bin/activate # Hoặc venv\Scripts\activate trên Windows
pip install -r requirements.txt
python agent.py
```

---

## GIAO TIẾP (GIAO THỨC SỬ DỤNG)

### 1. Bảng API REST (Khởi tạo & Xác thực phiên)

| Endpoint | Protocol | Method | Input (JSON) | Output (JSON) | Mục đích |
| :--- | :---: | :---: | :--- | :--- | :--- |
| `/api/v1/health` | HTTP/1.1 | `GET` | — | `{"status": "online", "active_rooms": 1}` | Kiểm tra tình trạng server |
| `/api/v1/devices/register` | HTTP/1.1 | `POST` | `{"name":"PC-Nam", "pin":"123456"}` | `{"device_id":"839201", "pin":"123456"}` | Agent đăng ký lấy mã 6 số |
| `/api/v1/session/verify` | HTTP/1.1 | `POST` | `{"device_id":"839201", "pin":"123456"}` | `{"valid":true, "is_online":true}` | Web kiểm tra mã trước khi nối |
| `/api/v1/devices/{id}` | HTTP/1.1 | `GET` | — | `{"device_id":"839201", "is_online":true}` | Kiểm tra trạng thái máy |

---

### 2. Giao thức WebSocket Channels

| Endpoint WebSocket | Chiều dữ liệu | Định dạng gói tin | Nội dung chi tiết |
| :--- | :---: | :---: | :--- |
| `ws://<server>/ws/host/{id}?pin=...` | Host ➔ Server | **Binary Frame** | Dãy byte thô nén JPEG của màn hình máy tính |
| | Server ➔ Host | **Text (JSON)** | Các gói tin điều khiển chuột, bàn phím |
| `ws://<server>/ws/viewer/{id}?pin=...` | Server ➔ Web | **Binary Frame** | Chuyển tiếp mảng byte JPEG để render lên Canvas |
| | Web ➔ Server | **Text (JSON)** | Gửi gói tin di chuyển chuột, click, phím bấm, Ping |

#### Các định dạng gói tin JSON điều khiển:
- **Chuột di chuyển (Normalized coordinates):**
  `{"type": "MOUSE_MOVE", "x_ratio": 0.542, "y_ratio": 0.312}`
- **Nhấn chuột:**
  `{"type": "MOUSE_CLICK", "button": "left", "action": "down"}`
- **Bàn phím:**
  `{"type": "KEY_EVENT", "key": "Enter", "action": "down"}`
- **Đo Ping RTT (Heartbeat):**
  - Web gửi: `{"type": "PING", "timestamp": 1718000000000}`
  - Agent phản hồi: `{"type": "PONG", "timestamp": 1718000000000}`
  - Web tính: $\text{Ping} = \text{Date.now()} - \text{timestamp}$.

---

## CẤU TRÚC DỰ ÁN

```
assignment-network-project/
├── INSTRUCTION.md               # Hướng dẫn của Giảng viên (Không chỉnh sửa)
├── README.md                    # Tài liệu mô tả dự án và hướng dẫn chạy
├── PROJECT_SPECIFICATION.md     # Tài liệu đặc tả kỹ thuật chi tiết
├── BTL_LapTrinhMang_DacTaDuAn.docx # File Word nộp bài tập lớn
├── docker-compose.yml           # Khởi chạy toàn bộ hệ thống bằng 1 lệnh
├── statics/                     # Thư mục chứa hình ảnh diagram và demo
└── source/
    ├── server/                  # Module máy chủ trung chuyển (FastAPI)
    │   ├── app/
    │   │   ├── main.py          # Entrypoint FastAPI app, CORS, lifespan
    │   │   ├── config.py        # Cấu hình biến môi trường, port, database URL
    │   │   ├── database.py      # Kết nối SQLite bất đồng bộ (SQLAlchemy)
    │   │   ├── models.py        # Model ORM bảng Device lưu trạng thái thiết bị
    │   │   ├── schemas/         # Pydantic schemas kiểm thực dữ liệu
    │   │   ├── services/        # Logic đăng ký thiết bị và xác thực PIN
    │   │   ├── ws/              # Logic ConnectionManager & WebSocket Router
    │   │   └── api/             # REST API Router
    │   ├── requirements.txt
    │   ├── Dockerfile
    │   └── README.md
    └── client/
        ├── agent/               # Module Desktop Agent (Python)
        │   ├── agent.py         # Ứng dụng chạy ngầm, gửi byte ảnh & nhận lệnh
        │   ├── screen_capture.py# Chụp màn hình (mss) và nén JPEG (Pillow)
        │   ├── input_handler.py # Điều khiển chuột & phím OS (pynput)
        │   ├── config.py        # Thiết lập cấu hình và DPI Awareness
        │   ├── requirements.txt
        │   └── README.md
        └── web/                 # Module Web Viewer (React + Vite)
            ├── src/
            │   ├── components/  # RemoteCanvas, ControlHeader, NetworkHUD, ConnectModal
            │   ├── utils/       # Định nghĩa protocol đóng gói JSON packets
            │   ├── App.jsx      # Quản lý WebSocket và trạng thái ứng dụng
            │   └── main.jsx
            ├── package.json
            ├── vite.config.js
            ├── Dockerfile
            └── README.md
```

---

## HƯỚNG PHÁT TRIỂN TIẾP THEO

Nhằm nâng cấp hệ thống từ một phiên bản đồ án cơ sở lên giải pháp điều khiển máy tính từ xa tiệm cận chất lượng thương mại (như TeamViewer, AnyDesk), dự án có thể mở rộng theo các hướng sau:

1. **Chuyển đổi giao thức sang Video Streaming chuẩn (WebRTC / H.264 / VP9 / AV1):**
   - Hiện tại hệ thống truyền chuỗi khung hình JPEG độc lập (Motion JPEG). 
   - Hướng nâng cấp: Tích hợp thư viện WebRTC hoặc mã hóa video sử dụng phần cứng GPU (Nvidia NVENC, Intel QuickSync, Apple VideoToolbox) để chỉ truyền các vùng pixel thay đổi (delta frames), giúp giảm 70% – 80% băng thông và đạt chuẩn mượt 60 FPS.

2. **Truyền âm thanh 2 chiều (Bi-directional Audio Streaming):**
   - Thu âm thanh hệ thống (Desktop Loopback Audio qua WASAPI trên Windows hoặc CoreAudio trên macOS).
   - Truyền tải âm thanh bằng codec Opus thời gian thực để người xem nghe được âm thanh phát ra từ máy Host.

3. **Tính năng truyền tệp tin (File Transfer):**
   - Xây dựng kênh truyền dữ liệu nhị phân chuyên dụng (Data Channel) cho phép người dùng kéo thả (Drag & Drop) tệp tin qua lại giữa trình duyệt Web và máy tính Host.

4. **Đồng bộ hóa Clipboard hai chiều (Clipboard Synchronization):**
   - Tự động đồng bộ nội dung sao chép (văn bản, link URL) giữa khay nhớ tạm của máy tính Host và Web Viewer theo thời gian thực.

5. **Mã hóa đầu cuối (End-to-End Encryption - E2EE):**
   - Ứng dụng thuật toán mã hóa AES-256-GCM kết hợp trao đổi khóa Diffie-Hellman để mã hóa toàn bộ hình ảnh và sự kiện bàn phím/chuột. Khi đó, máy chủ trung chuyển (Relay Server) chỉ đóng vai trò chuyển tiếp gói tin mà hoàn toàn không thể giải mã hay đọc trộm dữ liệu.

6. **Hỗ trợ đa màn hình (Multi-monitor Support):**
   - Bổ sung tùy chọn cho phép Viewer chuyển đổi qua lại giữa các màn hình (Monitor 1, Monitor 2) hoặc hiển thị đồng thời toàn bộ màn hình khi máy Host cắm nhiều màn hình ngoài.

---

## KẾT QUẢ THỰC NGHIỆM

1. **Hiệu năng truyền tải:**
   - Đạt tốc độ khung hình ổn định từ **25 — 30 FPS** trong mạng nội bộ (LAN / Wi-Fi).
   - Độ trễ Round-Trip Time (**Ping / RTT**) duy trì ở mức thấp: **< 35ms**.
   - Băng thông tiêu thụ trung bình: **~400 KB/s — 900 KB/s** tùy thuộc vào mức độ chuyển động của màn hình và cấu hình chất lượng JPEG (Quality 50-70%).
2. **Khả năng chịu lỗi (Fault Tolerance):**
   - Khi tắt đột ngột một bên (rút mạng hoặc tắt tab trình duyệt), Server tự động dọn dẹp kết nối trong `ConnectionManager` mà không bị rò rỉ bộ nhớ hoặc treo luồng.
   - Khi Agent mất kết nối, hệ thống tự động kích hoạt tiến trình kết nối lại (Auto-reconnect) sau mỗi 3 giây.
