import platform
import logging

logger = logging.getLogger("agent.config")

OS_NAME = platform.system()  # 'Darwin' (macOS), 'Windows', hoặc 'Linux'

# Cấu hình máy chủ Relay Server (Mạng LAN / cùng Wi-Fi)
DEFAULT_SERVER_HTTP = "http://172.20.10.2:8000"
DEFAULT_SERVER_WS = "ws://172.20.10.2:8000"


# Cấu hình video streaming
DEFAULT_FPS = 30
DEFAULT_JPEG_QUALITY = 60
DEFAULT_MAX_WIDTH = 1280
DEFAULT_MAX_HEIGHT = 720

def generate_random_pin() -> str:
    """Sinh ngẫu nhiên mã PIN gồm 6 chữ số"""
    import random
    return f"{random.randint(100000, 999999)}"

def setup_os_environment(quiet: bool = False):
    """
    Thiết lập môi trường chuyên biệt cho từng hệ điều hành:
    - Windows: Bật High-DPI Awareness chống lệch tọa độ khi scale 125%/150%.
    - macOS: Kiểm tra và in cảnh báo phân quyền Screen Recording & Accessibility.
    """
    if OS_NAME == "Windows":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
            logger.info("Đã kích hoạt Windows Per-Monitor DPI Awareness v2.")
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
                logger.info("Đã kích hoạt Windows DPI Awareness (Fallback).")
            except Exception as e:
                logger.warning(f"Không thể thiết lập Windows DPI Awareness: {e}")

    elif OS_NAME == "Darwin" and not quiet:
        print("\n" + "="*60)
        print("[LƯU Ý DÀNH CHO MACOS]")
        print("  macOS yêu cầu cấp 2 quyền bảo mật bắt buộc để điều khiển:")
        print("  1. Chụp màn hình: System Settings > Privacy & Security > Screen Recording")
        print("  2. Chuột & Bàn phím: System Settings > Privacy & Security > Accessibility")
        print("  (Hãy đảm bảo cấp quyền cho Terminal / VS Code / Python)")
        print("="*60 + "\n")

def get_macos_retina_factor(physical_width: int) -> float:
    """
    Xác định hệ số tỉ lệ màn hình (Retina Scale Factor) trên macOS:
    Trên MacBook Retina, mss chụp độ phân giải vật lý (2560 hoặc 3024),
    nhưng pynput lại nhận tọa độ điểm ảnh logic (1280 hoặc 1512).
    """
    if OS_NAME != "Darwin":
        return 1.0

    try:
        if physical_width > 2000:
            logger.info(f"Phát hiện màn hình Retina (Physical: {physical_width}px). Áp dụng Retina Scale Factor = 2.0")
            return 2.0
    except Exception:
        pass

    return 1.0
