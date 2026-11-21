import random
import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Device
from app.schemas.schemas import DeviceRegisterRequest

async def generate_unique_device_id(db: AsyncSession) -> str:
    """Sinh mã thiết bị 6 số ngẫu nhiên (ví dụ: '839201') không bị trùng"""
    for _ in range(20):
        code = str(random.randint(100000, 999999))
        result = await db.execute(select(Device).where(Device.id == code))
        if not result.scalar_one_or_none():
            return code
    # Fallback nếu ngẫu nhiên bị đầy
    return str(int(datetime.datetime.utcnow().timestamp()))[-6:]

async def register_or_update_device(db: AsyncSession, req: DeviceRegisterRequest) -> Device:
    """Đăng ký thiết bị mới hoặc cập nhật thông tin thiết bị đã tồn tại"""
    device_id = req.device_id.strip() if req.device_id else None
    
    device = None
    if device_id:
        result = await db.execute(select(Device).where(Device.id == device_id))
        device = result.scalar_one_or_none()

    if not device:
        if not device_id:
            device_id = await generate_unique_device_id(db)
        device = Device(
            id=device_id,
            name=req.name,
            pin=req.pin,
            os_info=req.os_info,
            screen_resolution=req.screen_resolution,
            is_online=False,
            last_seen=datetime.datetime.utcnow()
        )
        db.add(device)
    else:
        device.name = req.name
        device.pin = req.pin
        device.os_info = req.os_info
        device.screen_resolution = req.screen_resolution
        device.last_seen = datetime.datetime.utcnow()

    await db.commit()
    await db.refresh(device)
    return device

async def verify_device_credentials(db: AsyncSession, device_id: str, pin: str) -> tuple[bool, Device | None]:
    """Kiểm tra mã Device ID và PIN"""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        return False, None
    if device.pin != pin:
        return False, device
    return True, device

async def set_device_online_status(db: AsyncSession, device_id: str, is_online: bool):
    """Cập nhật trạng thái trực tuyến của thiết bị"""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if device:
        device.is_online = is_online
        device.last_seen = datetime.datetime.utcnow()
        await db.commit()
