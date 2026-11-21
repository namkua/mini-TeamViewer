from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Device
from app.schemas.schemas import (
    DeviceRegisterRequest,
    DeviceRegisterResponse,
    VerifySessionRequest,
    VerifySessionResponse,
    DeviceStatusResponse
)
from app.services.device_service import (
    register_or_update_device,
    verify_device_credentials
)
from app.ws.connection_manager import manager

router = APIRouter(prefix="/api/v1")

@router.get("/health", tags=["Health"])
async def health_check():
    """Kiểm tra tình trạng hoạt động của Relay Server"""
    return {
        "status": "online",
        "service": "FastAPI Remote Desktop Relay",
        "active_rooms": len(manager.rooms)
    }

@router.post("/devices/register", response_model=DeviceRegisterResponse, tags=["Devices"])
async def register_device(
    payload: DeviceRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Đăng ký Host Agent với hệ thống.
    Nếu không truyền device_id, server sẽ tự tạo mã 6 số ngẫu nhiên.
    """
    device = await register_or_update_device(db, payload)
    return DeviceRegisterResponse(
        status="ok",
        device_id=device.id,
        pin=device.pin,
        message=f"Device {device.id} registered successfully."
    )

@router.post("/session/verify", response_model=VerifySessionResponse, tags=["Session"])
async def verify_session(
    payload: VerifySessionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Kiểm tra tính hợp lệ của Device ID và PIN trước khi mở kênh WebSocket.
    """
    is_valid, device = await verify_device_credentials(db, payload.device_id, payload.pin)
    if not is_valid:
        return VerifySessionResponse(
            valid=False,
            is_online=False,
            screen_resolution=None,
            message="Mã thiết bị hoặc mã PIN không chính xác."
        )

    # Kiểm tra xem Host Agent có đang online trên WebSocket không
    is_online = manager.is_host_online(payload.device_id)

    return VerifySessionResponse(
        valid=True,
        is_online=is_online,
        screen_resolution=device.screen_resolution if device else "1920x1080",
        message="Xác thực thành công, sẵn sàng kết nối."
    )

@router.get("/devices/{device_id}", response_model=DeviceStatusResponse, tags=["Devices"])
async def get_device_status(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Lấy trạng thái trực tuyến của thiết bị"""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    return DeviceStatusResponse(
        device_id=device.id,
        name=device.name,
        is_online=manager.is_host_online(device_id),
        os_info=device.os_info,
        screen_resolution=device.screen_resolution
    )
