import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from app.database import Base

class Device(Base):
    __tablename__ = "devices"

    id = Column(String(32), primary_key=True, index=True) # 6-digit Device ID (ví dụ: 839201)
    name = Column(String(128), nullable=False, default="Remote PC")
    pin = Column(String(64), nullable=False) # Mã PIN để xác thực kết nối
    os_info = Column(String(64), nullable=True, default="Unknown OS")
    screen_resolution = Column(String(32), nullable=True, default="1920x1080")
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
