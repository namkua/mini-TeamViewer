# MODULE: CLIENT

Mục này chứa 2 thành phần Client của dự án:

1. **`agent/` (Desktop Host Agent):** 
   - Ứng dụng Python chạy trên máy tính bị điều khiển.
   - Chụp màn hình, nén ảnh JPEG và gửi binary bytes qua WebSocket; đồng thời nhận lệnh chuột/bàn phím để kích hoạt trên hệ điều hành.
2. **`web/` (Web Viewer Controller):**
   - Ứng dụng React chạy trên trình duyệt web của người điều khiển.
   - Nhận mảng byte nhị phân JPEG vẽ lên HTML5 Canvas, bắt sự kiện chuột/phím và gửi gói tin điều khiển về server.
