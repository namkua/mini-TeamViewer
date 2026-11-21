from typing import Optional
from pydantic import BaseModel, Field

# --- REST Schemas ---

class DeviceRegisterRequest(BaseModel):
    device_id: Optional[str] = Field(None, description="Mã 6 số nếu muốn chỉ định, hoặc để trống để server sinh ngẫu nhiên")
    name: str = Field(default="My Desktop", description="Tên thiết bị hiển thị")
    pin: str = Field(..., min_length=4, max_length=12, description="Mã PIN bảo mật kết nối")
    os_info: Optional[str] = "Unknown OS"
    screen_resolution: Optional[str] = "1920x1080"

class DeviceRegisterResponse(BaseModel):
    status: str = "ok"
    device_id: str
    pin: str
    message: str

class VerifySessionRequest(BaseModel):
    device_id: str
    pin: str

class VerifySessionResponse(BaseModel):
    valid: bool
    is_online: bool
    screen_resolution: Optional[str] = "1920x1080"
    message: str

class DeviceStatusResponse(BaseModel):
    device_id: str
    name: str
    is_online: bool
    os_info: Optional[str]
    screen_resolution: Optional[str]
