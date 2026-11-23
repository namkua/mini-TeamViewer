# MODULE: WEB VIEWER (REACT CLIENT)

## Vai trò
Web Viewer là giao diện điều khiển trực tiếp trên trình duyệt, không yêu cầu người dùng phải cài đặt bất kỳ phần mềm nào:
1. **HTML5 Canvas Rendering:** Nhận chuỗi byte nhị phân JPEG (`Blob`) từ WebSocket và render đè liên tục lên Canvas với tốc độ mượt mà.
2. **Normalized Coordinates Input:** Bắt các sự kiện chuột (`mousemove`, `mousedown`, `mouseup`, `wheel`) và tính toán tọa độ theo tỉ lệ tương đối $0.0 \to 1.0$ so với kích thước Canvas để tương thích mọi độ phân giải máy tính.
3. **Keyboard Mapping:** Bắt sự kiện bàn phím của trình duyệt và gửi gói tin JSON điều khiển về máy Host.
4. **Network HUD Monitor:** Đo lường và hiển thị trực quan các chỉ số mạng thời gian thực:
   - **Ping / RTT (ms):** Tính toán độ trễ vòng lặp qua cơ chế PING/PONG.
   - **FPS:** Tốc độ khung hình render thực tế mỗi giây.
   - **Băng thông (KB/s - MB/s):** Lưu lượng dữ liệu mạng thực tế nhận được.

## Hướng dẫn chạy

### 1. Cài đặt thư viện
```bash
npm install
```

### 2. Khởi chạy ở môi trường phát triển (Dev)
```bash
npm run dev
# Truy cập tại: http://localhost:3000
```

### 3. Build chạy bằng Docker
```bash
docker build -t remote-desktop-web .
docker run -p 3000:80 remote-desktop-web
```
