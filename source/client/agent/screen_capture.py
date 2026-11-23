import io
import time
import logging
from PIL import Image, ImageDraw

logger = logging.getLogger("agent.capture")

class ScreenCapturer:
    """Lớp chịu trách nhiệm chụp khung hình desktop và nén thành mảng byte JPEG"""

    def __init__(self, max_width: int = 1920, max_height: int = 1080, quality: int = 75):
        self.max_width = max_width
        self.max_height = max_height
        self.quality = quality
        self.sct = None
        self.monitor = None
        self.is_mock = False
        self.real_width = 1920
        self.real_height = 1080
        # Tái sử dụng buffer thay vì tạo mới mỗi frame → giảm GC overhead
        self._buffer = io.BytesIO()
        self.last_raw = None
        self.last_jpeg = None
        self._init_capturer()

    def _init_capturer(self):
        try:
            import mss
            self.sct = mss.mss()
            # Lấy màn hình chính (monitors[1])
            self.monitor = self.sct.monitors[1] if len(self.sct.monitors) > 1 else self.sct.monitors[0]
            self.real_width = self.monitor["width"]
            self.real_height = self.monitor["height"]
            logger.info(f"Screen capturer initialized. Resolution: {self.real_width}x{self.real_height}")
        except Exception as e:
            logger.warning(f"Could not initialize native screen capturer ({e}). Falling back to mock screen mode.")
            self.is_mock = True
            self.real_width = 1280
            self.real_height = 720

    def capture_jpeg_bytes(self) -> bytes:
        """Chụp màn hình và trả về chuỗi byte nhị phân định dạng JPEG"""
        if self.is_mock or not self.sct:
            return self._generate_mock_frame()

        try:
            # 1. Chụp màn hình bằng mss (siêu nhanh)
            sct_img = self.sct.grab(self.monitor)

            # Kiểm tra nếu màn hình đứng yên (không thay đổi pixel)
            # Tái sử dụng frame JPEG trước đó ngay lập tức (chỉ tốn ~0.5ms so với ~25ms nén lại)
            if self.last_raw == sct_img.raw and self.last_jpeg is not None:
                return self.last_jpeg

            self.last_raw = sct_img.raw

            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            # 2. Resize nếu vượt quá kích thước cho phép để tối ưu băng thông (giữ đúng tỉ lệ gốc)
            if img.width > self.max_width or img.height > self.max_height:
                img.thumbnail((self.max_width, self.max_height), Image.Resampling.BILINEAR)

            # 3. Nén JPEG: dùng chuẩn 4:2:0 mặc định giúp giảm 80% dung lượng frame
            self._buffer.seek(0)
            self._buffer.truncate()
            img.save(self._buffer, format="JPEG", quality=self.quality, optimize=False)
            self.last_jpeg = self._buffer.getvalue()
            return self.last_jpeg

        except Exception as e:
            logger.error(f"Error capturing real screen: {e}. Switching to mock.")
            self.is_mock = True
            return self._generate_mock_frame()

    def _generate_mock_frame(self) -> bytes:
        """Vẽ khung hình mô phỏng sinh động khi test trên máy không có GUI"""
        img = Image.new("RGB", (self.max_width, self.max_height), color=(24, 24, 27))
        draw = ImageDraw.Draw(img)

        # Vẽ lưới grid
        for x in range(0, self.max_width, 80):
            draw.line([(x, 0), (x, self.max_height)], fill=(39, 39, 42), width=1)
        for y in range(0, self.max_height, 80):
            draw.line([(0, y), (self.max_width, y)], fill=(39, 39, 42), width=1)

        # Vẽ hộp thông tin ở giữa
        cur_time = time.strftime("%H:%M:%S")
        text = f"MOCK DESKTOP STREAM [PTIT LTM]\nTime: {cur_time}\nResolution: {self.real_width}x{self.real_height}"
        draw.text((100, 100), text, fill=(59, 130, 246))

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=self.quality)
        return buffer.getvalue()

    def update_quality_config(self, quality: int | None = None, scale: float | None = None):
        """Cập nhật độ phân giải hoặc chất lượng nén theo yêu cầu động từ Web"""
        if quality is not None:
            self.quality = max(10, min(quality, 95))
            logger.info(f"Updated JPEG quality to {self.quality}")
        if scale is not None:
            self.max_width = int(self.real_width * scale)
            self.max_height = int(self.real_height * scale)
            logger.info(f"Updated stream max resolution to {self.max_width}x{self.max_height}")
        # Reset buffer khi thay đổi cấu hình
        self._buffer = io.BytesIO()
        self.last_raw = None
        self.last_jpeg = None
