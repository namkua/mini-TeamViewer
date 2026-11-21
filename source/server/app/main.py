import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.api.router import router as api_router
from app.ws.router import router as ws_router

# Thiết lập logging định dạng chuẩn
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
)
logger = logging.getLogger("relay.server")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời khởi tạo và đóng ứng dụng"""
    logger.info("Starting Remote Desktop Relay Server...")
    await init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down Remote Desktop Relay Server...")

app = FastAPI(
    title="Remote Desktop Relay Server",
    description="Backend máy chủ trung chuyển gói tin mạng (Binary Frames & Control Packets) môn LTM - PTIT",
    version="1.0.0",
    lifespan=lifespan
)

# Cấu hình CORS để Web React có thể gọi API mà không bị chặn
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gắn router REST API và WebSocket
app.include_router(api_router)
app.include_router(ws_router)

@app.get("/")
async def root():
    return {
        "message": "Remote Desktop Relay Server is running.",
        "docs_url": "/docs",
        "api_health": "/api/v1/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
