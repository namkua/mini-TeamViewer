# MODULE: RELAY SERVER (FastAPI)

## Vai trò
Máy chủ trung chuyển (Relay Server) đóng vai trò trung tâm điều phối kết nối:
1. **REST API (`/api/v1`):** Cấp phát mã thiết bị (Device ID 6 số), xác thực PIN, kiểm tra trạng thái thiết bị trực tuyến và lưu vào SQLite.
2. **WebSocket Relay (`/ws`):**
   - Nhận luồng byte ảnh JPEG từ Host Agent (`/ws/host/{device_id}`) và chuyển tiếp trực tiếp (Zero-Copy forwarding) sang các Web Viewer.
   - Nhận các gói tin điều khiển JSON (chuột, phím, ping) từ Web Viewer (`/ws/viewer/{device_id}`) và chuyển tiếp về Host Agent.

## Hướng dẫn chạy

### Cách 1: Chạy trực tiếp với Python
```bash
# Tạo môi trường ảo
python3 -m venv venv
source venv/bin/activate # Hoặc venv\Scripts\activate trên Windows

# Cài đặt thư viện
pip install -r requirements.txt

# Khởi chạy server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation tự động tại: `http://localhost:8000/docs`

### Cách 2: Chạy bằng Docker
```bash
docker build -t remote-desktop-server .
docker run -p 8000:8000 remote-desktop-server
```
