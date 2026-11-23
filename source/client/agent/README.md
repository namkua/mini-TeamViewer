# MODULE: HOST AGENT (DESKTOP CLIENT)

## Vai trò
Host Agent là chương trình chạy trên máy tính cần chia sẻ màn hình và cho phép điều khiển từ xa:
1. **Chụp màn hình:** Sử dụng thư viện `mss` chụp desktop với tốc độ khung hình cao (25 - 60 FPS).
2. **Nén hình ảnh:** Sử dụng `Pillow` nén trực tiếp trong bộ nhớ RAM thành luồng byte JPEG.
3. **Truyền Socket:** Kết nối WebSocket đến Relay Server để gửi mảng byte nhị phân liên tục.
4. **Nhận lệnh & Điều khiển:** Lắng nghe các gói tin JSON điều khiển chuột (`MOUSE_MOVE`, `MOUSE_CLICK`, `MOUSE_SCROLL`) và bàn phím (`KEY_EVENT`) từ Web để kích hoạt sự kiện phần cứng bằng `pynput`.

## Hướng dẫn chạy

### 1. Cài đặt môi trường
```bash
python3 -m venv venv
source venv/bin/activate # Hoặc venv\Scripts\activate trên Windows
pip install -r requirements.txt
```

### 2. Khởi chạy
```bash
# Chạy với cấu hình mặc định (kết nối tới localhost:8000, PIN: 123456)
python agent.py

# Hoặc chỉ định rõ Server và mã PIN riêng
python agent.py --server http://192.168.1.15:8000 --ws ws://192.168.1.15:8000 --pin 654321

# Chạy chế độ Mock Screen (cho máy không có màn hình thật hoặc CI/CD)
python agent.py --mock
```

### 3. Đóng gói thành file chạy duy nhất (.exe trên Windows)
```bash
pip install pyinstaller
pyinstaller --onefile --noconsole agent.py
# File chạy sau khi đóng gói sẽ nằm tại: dist/agent.exe
```
