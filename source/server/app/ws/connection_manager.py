import asyncio
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger("relay.manager")

class RemoteSessionRoom:
    """Đại diện cho 1 phòng kết nối giữa 1 Host Agent và các Web Viewers"""
    def __init__(self, device_id: str):
        self.device_id: str = device_id
        self.host_ws: WebSocket | None = None
        self.viewers: Set[WebSocket] = set()

class ConnectionManager:
    """Quản lý các kết nối WebSocket và điều phối gói tin theo mô hình Relay"""
    def __init__(self):
        self.rooms: Dict[str, RemoteSessionRoom] = {}

    def _get_or_create_room(self, device_id: str) -> RemoteSessionRoom:
        if device_id not in self.rooms:
            self.rooms[device_id] = RemoteSessionRoom(device_id)
        return self.rooms[device_id]

    async def connect_host(self, device_id: str, websocket: WebSocket) -> bool:
        """Chấp nhận kết nối từ Host Agent"""
        await websocket.accept()
        room = self._get_or_create_room(device_id)
        
        # Nếu đã có host cũ đang nối, ngắt host cũ
        if room.host_ws and room.host_ws != websocket:
            try:
                await room.host_ws.close(code=1000, reason="New host instance connected")
            except Exception:
                pass

        room.host_ws = websocket
        logger.info(f"[HOST_CONNECTED] Device {device_id} connected as host.")

        # Thông báo cho các viewers đang chờ biết Host đã online
        await self.broadcast_to_viewers(device_id, '{"type": "HOST_STATUS", "status": "online"}')
        return True

    async def disconnect_host(self, device_id: str, websocket: WebSocket):
        """Xử lý khi Host Agent ngắt kết nối"""
        room = self.rooms.get(device_id)
        if room and room.host_ws == websocket:
            room.host_ws = None
            logger.info(f"[HOST_DISCONNECTED] Device {device_id} host disconnected.")
            await self.broadcast_to_viewers(
                device_id,
                '{"type": "HOST_STATUS", "status": "offline", "message": "Mất tín hiệu từ máy Host."}'
            )
            self._cleanup_room_if_empty(device_id)

    async def connect_viewer(self, device_id: str, websocket: WebSocket) -> bool:
        """Chấp nhận kết nối từ Web Viewer"""
        await websocket.accept()
        room = self._get_or_create_room(device_id)
        room.viewers.add(websocket)
        logger.info(f"[VIEWER_CONNECTED] Viewer joined device {device_id}. Total viewers: {len(room.viewers)}")

        # Gửi trạng thái hiện tại của host cho viewer mới vào
        host_status = "online" if room.host_ws else "offline"
        try:
            await websocket.send_text(f'{{"type": "HOST_STATUS", "status": "{host_status}"}}')
        except Exception:
            pass

        # Thông báo có người kết nối cho Host Agent
        if room.host_ws:
            try:
                await room.host_ws.send_text('{"type": "VIEWER_STATUS", "connected": true}')
            except Exception:
                pass

        return True

    async def disconnect_viewer(self, device_id: str, websocket: WebSocket):
        """Xử lý khi Web Viewer ngắt kết nối"""
        room = self.rooms.get(device_id)
        if room and websocket in room.viewers:
            room.viewers.remove(websocket)
            logger.info(f"[VIEWER_DISCONNECTED] Viewer left device {device_id}. Remaining: {len(room.viewers)}")

            # Cập nhật trạng thái người xem cho Host Agent
            if room.host_ws:
                try:
                    has_viewers = len(room.viewers) > 0
                    await room.host_ws.send_text(f'{{"type": "VIEWER_STATUS", "connected": {str(has_viewers).lower()}}}')
                except Exception:
                    pass

            self._cleanup_room_if_empty(device_id)

    async def forward_binary_to_viewers(self, device_id: str, frame_bytes: bytes):
        """Chuyển tiếp luồng byte ảnh JPEG từ Host sang toàn bộ Viewers đang xem song song"""
        room = self.rooms.get(device_id)
        if not room or not room.viewers:
            return

        async def _send_one(viewer):
            try:
                await viewer.send_bytes(frame_bytes)
                return None
            except Exception as e:
                logger.warning(f"Failed to forward binary to viewer of {device_id}: {e}")
                return viewer

        dead_viewers = await asyncio.gather(*[_send_one(v) for v in list(room.viewers)])
        for v in dead_viewers:
            if v:
                room.viewers.discard(v)

    async def forward_control_to_host(self, device_id: str, event_json_str: str):
        """Chuyển tiếp lệnh điều khiển từ Web Viewer về cho Host Agent"""
        room = self.rooms.get(device_id)
        if not room or not room.host_ws:
            return

        try:
            await room.host_ws.send_text(event_json_str)
        except Exception as e:
            logger.warning(f"Failed to forward control to host {device_id}: {e}")

    async def broadcast_to_viewers(self, device_id: str, message: str):
        """Gửi thông điệp dạng JSON/Text đến toàn bộ Viewer của phòng"""
        room = self.rooms.get(device_id)
        if not room:
            return

        for viewer in list(room.viewers):
            try:
                await viewer.send_text(message)
            except Exception:
                room.viewers.discard(viewer)

    def is_host_online(self, device_id: str) -> bool:
        room = self.rooms.get(device_id)
        return room is not None and room.host_ws is not None

    def _cleanup_room_if_empty(self, device_id: str):
        room = self.rooms.get(device_id)
        if room and not room.host_ws and not room.viewers:
            del self.rooms[device_id]
            logger.debug(f"Room {device_id} deleted as it became empty.")

manager = ConnectionManager()
