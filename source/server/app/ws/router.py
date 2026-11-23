import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.ws.connection_manager import manager
from app.services.device_service import verify_device_credentials, set_device_online_status

logger = logging.getLogger("relay.ws")
router = APIRouter()

@router.websocket("/ws/host/{device_id}")
async def websocket_host_endpoint(
    websocket: WebSocket,
    device_id: str,
    pin: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint dành cho Host Agent (máy bị điều khiển):
    - Xác thực device_id & pin
    - Nhận luồng nhị phân (Binary Frames) của ảnh chụp màn hình JPEG và chuyển tiếp sang Viewers
    """
    # 1. Xác thực thiết bị
    is_valid, device = await verify_device_credentials(db, device_id, pin)
    if not is_valid:
        await websocket.close(code=4003, reason="Invalid Device ID or PIN")
        logger.warning(f"[REJECT_HOST] Device {device_id} auth failed.")
        return

    # 2. Chấp nhận kết nối vào phòng Relay
    await manager.connect_host(device_id, websocket)
    await set_device_online_status(db, device_id, True)

    try:
        while True:
            # Nhận gói tin từ Agent (có thể là bytes hoặc text)
            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                logger.info(f"Host {device_id} disconnected (code={message.get('code')}).")
                break
            if "bytes" in message and message["bytes"]:
                # Gói tin nhị phân JPEG frame
                await manager.forward_binary_to_viewers(device_id, message["bytes"])
            elif "text" in message and message["text"]:
                # Gói tin text (PONG hoặc thông báo trạng thái từ Agent)
                await manager.broadcast_to_viewers(device_id, message["text"])

    except WebSocketDisconnect as e:
        logger.info(f"Host {device_id} disconnected (code={e.code}).")
    except Exception as e:
        logger.error(f"Error on host websocket {device_id}: {e}")
    finally:
        await manager.disconnect_host(device_id, websocket)
        await set_device_online_status(db, device_id, False)


@router.websocket("/ws/viewer/{device_id}")
async def websocket_viewer_endpoint(
    websocket: WebSocket,
    device_id: str,
    pin: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint dành cho Web Viewer (máy điều khiển):
    - Xác thực device_id & pin
    - Nhận sự kiện chuột, bàn phím và ping/pong (dạng JSON text) để gửi về Host Agent
    """
    # 1. Xác thực quyền điều khiển
    is_valid, device = await verify_device_credentials(db, device_id, pin)
    if not is_valid:
        await websocket.close(code=4003, reason="Invalid Device ID or PIN")
        logger.warning(f"[REJECT_VIEWER] Viewer attempt on {device_id} failed auth.")
        return

    # 2. Chấp nhận kết nối vào phòng Relay
    await manager.connect_viewer(device_id, websocket)

    try:
        while True:
            # Nhận sự kiện điều khiển từ Web Client (JSON Text)
            event_text = await websocket.receive_text()
            
            # Chuyển tiếp ngay lập tức về cho Host Agent thực thi
            await manager.forward_control_to_host(device_id, event_text)

    except WebSocketDisconnect:
        logger.info(f"Viewer of {device_id} disconnected normally.")
    except Exception as e:
        logger.error(f"Error on viewer websocket {device_id}: {e}")
    finally:
        await manager.disconnect_viewer(device_id, websocket)
