import platform
import time
import logging
from typing import Dict, Any, Callable
from config import get_macos_retina_factor

logger = logging.getLogger("agent.input")

IS_WINDOWS = platform.system() == "Windows"
LLKHF_INJECTED = 0x10
LLMHF_INJECTED = 0x01
LLMHF_LOWER_IL_INJECTED = 0x02

class InputHandler:
    """Xử lý và chuyển đổi các gói tin JSON điều khiển từ Web thành sự kiện OS thật,
    tích hợp cơ chế Local Input Priority (ưu tiên người ngồi máy thật)."""

    def __init__(self, physical_width: int = 1920, on_local_active: Callable[[], None] = None):
        self.mouse = None
        self.keyboard = None
        # Xác định hệ số Retina trên macOS hoặc DPI trên Windows
        self.scale_factor = get_macos_retina_factor(physical_width)
        self.on_local_active = on_local_active

        # Cấu hình Local Input Priority
        self.last_local_input_time = 0.0
        self.local_priority_timeout = 2.0  # Khóa remote 2.0s sau thao tác vật lý
        self._is_injecting = False
        self._last_synthetic_pos = (0, 0)
        self._synthetic_move_ts = 0.0
        self._synthetic_click_ts = 0.0
        self._synthetic_scroll_ts = 0.0
        self._synthetic_key_ts = 0.0

        # Cờ nhận diện gói tin giả lập do chính OS gắn (chính xác tuyệt đối trên Windows)
        self._has_win32_mouse_filter = False
        self._has_win32_kb_filter = False
        self._win32_mouse_injected = False
        self._win32_kb_injected = False

        self._mouse_listener = None
        self._keyboard_listener = None

        self._init_controllers()
        self._init_listeners()

    def _init_controllers(self):
        try:
            from pynput.mouse import Controller as MouseController
            from pynput.keyboard import Controller as KeyboardController
            self.mouse = MouseController()
            self.keyboard = KeyboardController()
            logger.info("Input controllers initialized successfully.")
        except Exception as e:
            logger.warning(
                f"Could not initialize native input controllers ({e}). "
                f"Nếu trên macOS: Hãy kiểm tra quyền Accessibility trong System Settings."
            )

    def _init_listeners(self):
        """Lắng nghe sự kiện chuột và phím vật lý trực tiếp trên máy thật"""
        try:
            from pynput import mouse, keyboard

            def win32_mouse_filter(msg, data):
                self._has_win32_mouse_filter = True
                flags = getattr(data, "flags", 0)
                self._win32_mouse_injected = bool(flags & (LLMHF_INJECTED | LLMHF_LOWER_IL_INJECTED))
                return True

            def win32_kb_filter(msg, data):
                self._has_win32_kb_filter = True
                flags = getattr(data, "flags", 0)
                self._win32_kb_injected = bool(flags & LLKHF_INJECTED)
                return True

            def _is_synthetic_mouse(ts: float) -> bool:
                if self._is_injecting:
                    return True
                if self._has_win32_mouse_filter:
                    return self._win32_mouse_injected
                return (time.time() - ts) < 0.12

            def on_local_move(x, y):
                if self._is_injecting:
                    return
                if self._has_win32_mouse_filter:
                    if self._win32_mouse_injected:
                        return
                elif time.time() - self._synthetic_move_ts < 0.10:
                    dx = abs(x - self._last_synthetic_pos[0])
                    dy = abs(y - self._last_synthetic_pos[1])
                    if dx < 15 and dy < 15:
                        return
                self._record_local_input()

            def on_local_click(x, y, button, pressed):
                if not _is_synthetic_mouse(self._synthetic_click_ts):
                    self._record_local_input()

            def on_local_scroll(x, y, dx, dy):
                if not _is_synthetic_mouse(self._synthetic_scroll_ts):
                    self._record_local_input()

            def on_local_key(key):
                if self._is_injecting:
                    return
                if self._has_win32_kb_filter:
                    if self._win32_kb_injected:
                        return
                elif (time.time() - self._synthetic_key_ts) < 0.12:
                    return
                self._record_local_input()

            mouse_kwargs = {
                "on_move": on_local_move,
                "on_click": on_local_click,
                "on_scroll": on_local_scroll,
            }
            kb_kwargs = {
                "on_press": on_local_key,
            }
            if IS_WINDOWS:
                mouse_kwargs["win32_event_filter"] = win32_mouse_filter
                kb_kwargs["win32_event_filter"] = win32_kb_filter

            self._mouse_listener = mouse.Listener(**mouse_kwargs)
            self._mouse_listener.daemon = True
            self._mouse_listener.start()

            self._keyboard_listener = keyboard.Listener(**kb_kwargs)
            self._keyboard_listener.daemon = True
            self._keyboard_listener.start()

            logger.info(f"Local Input Priority active (Lockout window: {self.local_priority_timeout}s).")
        except Exception as e:
            logger.warning(f"Could not initialize local input listener: {e}")

    def _record_local_input(self):
        """Ghi nhận người ngồi máy thật vừa thao tác chuột hoặc bàn phím"""
        self.last_local_input_time = time.time()
        if self.on_local_active:
            try:
                self.on_local_active()
            except Exception:
                pass

    def is_local_active(self) -> bool:
        """Kiểm tra người ngồi máy thật có đang thao tác trong vòng timeout không"""
        return (time.time() - self.last_local_input_time) < self.local_priority_timeout

    def handle_packet(self, data: Dict[str, Any], screen_width: int, screen_height: int) -> bool:
        """Phân loại và thực thi gói tin điều khiển.
        Trả về False nếu bị chặn bởi Local Input Priority, True nếu thành công."""
        if self.is_local_active():
            return False

        packet_type = data.get("type")
        self._is_injecting = True
        try:
            if packet_type == "MOUSE_MOVE":
                self._handle_mouse_move(data, screen_width, screen_height)
            elif packet_type == "MOUSE_CLICK":
                self._handle_mouse_click(data)
            elif packet_type == "MOUSE_SCROLL":
                self._handle_mouse_scroll(data)
            elif packet_type == "KEY_EVENT":
                self._handle_keyboard(data)
            return True
        finally:
            self._is_injecting = False

    def _handle_mouse_move(self, data: Dict[str, Any], screen_width: int, screen_height: int):
        if not self.mouse:
            return
        x_ratio = data.get("x_ratio", 0.0)
        y_ratio = data.get("y_ratio", 0.0)

        # Tính toán tọa độ logic (Logical coordinate)
        # Trên macOS Retina: chia cho scale_factor (thường là 2.0) để khớp với hệ tọa độ pynput
        logical_width = screen_width / self.scale_factor
        logical_height = screen_height / self.scale_factor

        real_x = int(x_ratio * logical_width)
        real_y = int(y_ratio * logical_height)

        self._last_synthetic_pos = (real_x, real_y)
        self._synthetic_move_ts = time.time()

        try:
            self.mouse.position = (real_x, real_y)
        except Exception as e:
            logger.debug(f"Failed to move mouse: {e}")

    def _handle_mouse_click(self, data: Dict[str, Any]):
        if not self.mouse:
            return
        from pynput.mouse import Button

        button_str = data.get("button", "left")
        action = data.get("action", "click")

        btn = Button.left
        if button_str == "right":
            btn = Button.right
        elif button_str == "middle":
            btn = Button.middle

        try:
            self._synthetic_click_ts = time.time()
            if action == "down":
                self.mouse.press(btn)
            elif action == "up":
                self.mouse.release(btn)
            elif action == "double_click":
                self.mouse.click(btn, 2)
            else: # click
                self.mouse.click(btn, 1)
        except Exception as e:
            logger.debug(f"Failed mouse click action: {e}")

    def _handle_mouse_scroll(self, data: Dict[str, Any]):
        if not self.mouse:
            return
        dx = data.get("dx", 0)
        dy = data.get("dy", 0)
        try:
            self._synthetic_scroll_ts = time.time()
            # Cuộn chuột (chuẩn hóa bước cuộn)
            steps = 2 if dy < 0 else -2
            self.mouse.scroll(dx, steps)
        except Exception as e:
            logger.debug(f"Failed mouse scroll: {e}")

    def _handle_keyboard(self, data: Dict[str, Any]):
        if not self.keyboard:
            return
        from pynput.keyboard import Key

        key_name = data.get("key", "")
        action = data.get("action", "down")

        # Ánh xạ đầy đủ các phím đặc biệt, xử lý tương thích macOS (Command) vs Windows (Control)
        key_map = {
            "Enter": Key.enter,
            "Backspace": Key.backspace,
            "Tab": Key.tab,
            "Escape": Key.esc,
            "ArrowUp": Key.up,
            "ArrowDown": Key.down,
            "ArrowLeft": Key.left,
            "ArrowRight": Key.right,
            "Space": Key.space,
            " ": Key.space,
            "Shift": Key.shift,
            "Delete": Key.delete,
            # Phím Control
            "Control": Key.ctrl,
            # Phím Command trên macOS / Windows Key trên PC (W3C gọi là 'Meta')
            "Meta": Key.cmd,
            "Command": Key.cmd,
            # Phím Alt / Option
            "Alt": Key.alt,
            "Option": Key.alt,
        }

        target_key = key_map.get(key_name, key_name if len(key_name) == 1 else None)
        if not target_key:
            return

        try:
            self._synthetic_key_ts = time.time()
            if action == "down":
                self.keyboard.press(target_key)
            else:
                self.keyboard.release(target_key)
        except Exception as e:
            logger.debug(f"Failed keyboard action for {key_name}: {e}")
