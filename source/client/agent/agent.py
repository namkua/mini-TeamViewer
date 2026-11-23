import argparse
import asyncio
import json
import logging
import platform
import socket
import sys
import time
import requests
import websockets
from config import (
    DEFAULT_SERVER_HTTP,
    DEFAULT_SERVER_WS,
    DEFAULT_FPS,
    DEFAULT_JPEG_QUALITY,
    DEFAULT_MAX_WIDTH,
    DEFAULT_MAX_HEIGHT,
    setup_os_environment,
    generate_random_pin
)
from screen_capture import ScreenCapturer
from input_handler import InputHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Agent]: %(message)s"
)
logger = logging.getLogger("agent.main")

class DesktopAgent:
    """Ứng dụng Host Agent chạy ngầm trên máy tính bị điều khiển"""

    def __init__(self, server_http: str, server_ws: str, device_id: str | None, pin: str, gui=None):
        self.server_http = server_http.rstrip("/")
        self.server_ws = server_ws.rstrip("/")
        self.device_id = device_id
        self.pin = pin
        self.target_fps = DEFAULT_FPS
        self.gui = gui
        
        self.capturer = ScreenCapturer(
            max_width=DEFAULT_MAX_WIDTH,
            max_height=DEFAULT_MAX_HEIGHT,
            quality=DEFAULT_JPEG_QUALITY
        )
        self.input_handler = InputHandler(physical_width=self.capturer.real_width)
        self.running = True
        self.loop = None
        self.current_ws = None
        self._last_notice_sent = 0.0
        self._last_gui_status = None

    def _update_gui_status(self, text: str, color: str = "#4ade80"):
        """Chỉ cập nhật GUI khi trạng thái thay đổi để tránh nghẽn hàng đợi Tkinter."""
        if self.gui and self._last_gui_status != (text, color):
            self._last_gui_status = (text, color)
            self.gui.set_status(text, color)

    def stop(self):
        """Dừng Agent và đóng WebSocket nếu còn mở"""
        self.running = False
        if self.loop and self.current_ws:
            try:
                async def _close():
                    try:
                        await self.current_ws.close()
                    except Exception:
                        pass
                fut = asyncio.run_coroutine_threadsafe(_close(), self.loop)
                fut.result(timeout=0.5)
            except Exception:
                pass

    def register_device(self) -> bool:
        """Đăng ký thông tin máy tính lên Relay Server qua REST API"""
        url = f"{self.server_http}/api/v1/devices/register"
        hostname = socket.gethostname()
        os_info = f"{platform.system()} {platform.release()}"
        res_str = f"{self.capturer.real_width}x{self.capturer.real_height}"

        payload = {
            "device_id": self.device_id,
            "name": hostname,
            "pin": self.pin,
            "os_info": os_info,
            "screen_resolution": res_str
        }

        try:
            res = requests.post(url, json=payload, timeout=5)
            if res.status_code == 200:
                data = res.json()
                self.device_id = data["device_id"]
                self.pin = data["pin"]
                if self.gui:
                    self.gui.update_info(self.device_id, self.pin)
                return True
            else:
                logger.error(f"Failed to register device: {res.text}")
                return False
        except Exception as e:
            logger.error(f"Could not connect to server HTTP at {url}: {e}")
            return False

    def refresh_pin(self):
        """Đổi mã PIN ngẫu nhiên mới và đăng ký lại lên Server"""
        new_pin = generate_random_pin()
        self.pin = new_pin
        logger.info(f"Đã tạo mã PIN ngẫu nhiên mới: {self.pin}")
        if self.register_device():
            if self.gui:
                self.gui.update_info(self.device_id, self.pin)
                self.gui.set_status("Đã đổi PIN mới. Sẵn sàng kết nối")

    async def run(self):
        """Vòng lặp kết nối và duy trì WebSocket với cơ chế tự động kết nối lại"""
        self.loop = asyncio.get_running_loop()
        setup_os_environment(quiet=bool(self.gui))

        # Đăng ký lấy thông tin thiết bị trước
        while not self.register_device():
            if self.gui:
                self.gui.set_status("Lỗi kết nối Server. Thử lại sau 3s...", "#ef4444")
            logger.info("Retrying server registration in 3 seconds...")
            await asyncio.sleep(3)

        ws_url = f"{self.server_ws}/ws/host/{self.device_id}?pin={self.pin}"

        while self.running:
            try:
                if self.gui:
                    self.gui.set_status("Đang kết nối tới máy chủ...", "#f59e0b")
                logger.info(f"Connecting to Relay WebSocket: {ws_url}")
                async with websockets.connect(
                    ws_url,
                    ping_interval=20,
                    ping_timeout=30,
                    max_size=10 * 1024 * 1024, # 10MB frame buffer
                    compression=None
                ) as ws:
                    self.current_ws = ws
                    logger.info("Connected to Relay Server! Ready to stream screen.")
                    if self.gui:
                        self.gui.set_status("Sẵn sàng nhận kết nối", "#4ade80")

                    # Chạy đồng thời 2 luồng: Gửi ảnh màn hình và Nhận lệnh điều khiển
                    stream_task = asyncio.create_task(self._send_screen_loop(ws))
                    receive_task = asyncio.create_task(self._receive_control_loop(ws))

                    done, pending = await asyncio.wait(
                        [stream_task, receive_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    for task in pending:
                        task.cancel()
                    self.current_ws = None

            except (websockets.ConnectionClosed, websockets.WebSocketException) as e:
                logger.warning(f"WebSocket disconnected ({e}). Reconnecting in 3 seconds...")
                if self.gui:
                    self.gui.set_status("Mất kết nối mạng. Đang thử lại...", "#ef4444")
            except Exception as e:
                logger.error(f"Unexpected error: {e}. Reconnecting in 3 seconds...")
                if self.gui:
                    self.gui.set_status("Mất kết nối máy chủ. Đang thử lại...", "#ef4444")

            await asyncio.sleep(3)

    async def _send_screen_loop(self, ws):
        """Vòng lặp pipeline song song: Chụp frame tiếp theo trong background thread cùng lúc gửi mạng"""
        loop = asyncio.get_running_loop()
        next_frame_fut = loop.run_in_executor(None, self.capturer.capture_jpeg_bytes)

        while True:
            start_time = time.time()

            # 1. Chờ frame đang chụp hoàn tất (không block asyncio event loop)
            jpeg_bytes = await next_frame_fut

            # 2. Bắt đầu chụp frame tiếp theo ngay trên thread khác song song với lúc gửi socket
            next_frame_fut = loop.run_in_executor(None, self.capturer.capture_jpeg_bytes)

            # 3. Gửi binary frame trực tiếp qua WebSocket
            try:
                await ws.send(jpeg_bytes)
            except Exception as e:
                logger.debug(f"Failed to send frame: {e}")
                break

            # 4. Điều tiết FPS ổn định
            elapsed = time.time() - start_time
            sleep_duration = max(0.001, (1.0 / self.target_fps) - elapsed)
            await asyncio.sleep(sleep_duration)

    async def _receive_control_loop(self, ws):
        """Vòng lặp nhận các gói tin điều khiển JSON từ Web Viewer"""
        while True:
            try:
                message = await ws.recv()
                if isinstance(message, str):
                    data = json.loads(message)
                    pkt_type = data.get("type")

                    # Khi có bất kỳ tín hiệu nào từ Web Viewer -> Đảm bảo GUI hiển thị "Đang chia sẻ màn hình"
                    if pkt_type in ("CONFIG_UPDATE", "PING", "VIEWER_JOINED", "MOUSE_MOVE", "MOUSE_CLICK", "MOUSE_SCROLL", "KEY_EVENT"):
                        self._update_gui_status("Đang chia sẻ màn hình", "#38bdf8")

                    if pkt_type == "PING":
                        # Phản hồi PONG tức thì để Web tính toán RTT Ping
                        pong_payload = json.dumps({"type": "PONG", "timestamp": data.get("timestamp")})
                        await ws.send(pong_payload)

                    elif pkt_type == "CONFIG_UPDATE":
                        # Thay đổi chất lượng streaming theo yêu cầu của Web
                        new_fps = data.get("fps")
                        new_quality = data.get("quality")
                        new_scale = data.get("scale")
                        if new_fps:
                            self.target_fps = max(5, min(new_fps, 60))
                        self.capturer.update_quality_config(quality=new_quality, scale=new_scale)

                    elif pkt_type == "VIEWER_STATUS":
                        connected = data.get("connected", False)
                        if connected:
                            self._update_gui_status("Đang chia sẻ màn hình", "#38bdf8")
                        else:
                            self._update_gui_status("Sẵn sàng nhận kết nối", "#4ade80")

                    else:
                        # Sự kiện chuột hoặc bàn phím
                        handled = self.input_handler.handle_packet(
                            data,
                            self.capturer.real_width,
                            self.capturer.real_height
                        )
                        # Nếu bị chặn bởi Local Input Priority, gửi thông báo cảnh báo về Web Viewer
                        if not handled and (time.time() - self._last_notice_sent > 1.0):
                            self._last_notice_sent = time.time()
                            notice = json.dumps({
                                "type": "LOCAL_INPUT_ACTIVE",
                                "message": "Người ngồi máy thật đang thao tác. Tạm khóa điều khiển từ xa.",
                                "timeout": 2.0
                            })
                            await ws.send(notice)

            except Exception as e:
                logger.debug(f"Receive loop error: {e}")
                break

def main():
    parser = argparse.ArgumentParser(description="Remote Desktop Host Agent (PTIT LTM)")
    parser.add_argument("--server", default=DEFAULT_SERVER_HTTP, help="Địa chỉ HTTP của Server (VD: http://localhost:8000)")
    parser.add_argument("--ws", default=DEFAULT_SERVER_WS, help="Địa chỉ WebSocket của Server (VD: ws://localhost:8000)")
    parser.add_argument("--id", default=None, help="Mã thiết bị mong muốn (6 số). Mặc định để trống để server tự sinh")
    parser.add_argument("--pin", default=None, help="Mã PIN kết nối bảo mật (mặc định: sinh ngẫu nhiên)")
    parser.add_argument("--mock", action="store_true", help="Chạy ở chế độ mô phỏng màn hình (cho headless/Docker)")
    parser.add_argument("--no-gui", "--headless", action="store_true", dest="headless", help="Chạy chế độ terminal không bật giao diện đồ họa")

    args = parser.parse_args()

    # 1. Device ID: Mặc định None để Server tự sinh mã ngẫu nhiên cho mỗi phiên
    device_id = args.id

    # 2. PIN: Tự động sinh ngẫu nhiên 6 số nếu không truyền --pin
    pin = args.pin or generate_random_pin()

    # 3. Khởi tạo GUI Tkinter nếu môi trường hỗ trợ
    gui = None
    if not args.headless:
        try:
            from gui import AgentGUI
            gui = AgentGUI()
        except Exception as e:
            logger.info(f"Khởi động chế độ Terminal (Giao diện Tkinter không khả dụng: {e})")

    agent = DesktopAgent(
        server_http=args.server,
        server_ws=args.ws,
        device_id=device_id,
        pin=pin,
        gui=gui
    )
    if args.mock:
        agent.capturer.is_mock = True

    if gui:
        # Tắt in log ra terminal khi đã bật giao diện GUI
        logging.getLogger().setLevel(logging.WARNING)

        gui.on_change_pin = agent.refresh_pin
        gui.on_close = agent.stop

        import threading
        # Chạy luồng streaming WebSocket của Agent trong background
        agent_thread = threading.Thread(target=lambda: asyncio.run(agent.run()), daemon=True)
        agent_thread.start()

        # Chạy giao diện Tkinter trên Main Thread
        try:
            gui.start()
        except KeyboardInterrupt:
            agent.stop()
            sys.exit(0)
    else:
        try:
            asyncio.run(agent.run())
        except KeyboardInterrupt:
            print("\n[INFO] Đang dừng Host Agent...")
            agent.stop()
            sys.exit(0)

if __name__ == "__main__":
    main()
