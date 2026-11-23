import React, { useRef, useEffect, useCallback } from "react";
import {
  createMouseMovePacket,
  createMouseClickPacket,
  createMouseScrollPacket,
  createKeyEventPacket
} from "../utils/protocol";

export default function RemoteCanvas({
  lastFrameBlob,
  onSendControl,
  onFrameRendered,
  onResolutionDetected,
  isHostOnline,
  isLocalActive
}) {
  const canvasRef = useRef(null);
  const throttleTimerRef = useRef(null);

  // 1. Render khung hình nhận được từ luồng nhị phân JPEG
  useEffect(() => {
    if (!lastFrameBlob) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    // Dùng createImageBitmap thay Image() → decode trên thread riêng, nhanh hơn ~30%
    createImageBitmap(lastFrameBlob).then((bitmap) => {
      // Cập nhật kích thước canvas theo frame ảnh
      if (canvas.width !== bitmap.width || canvas.height !== bitmap.height) {
        canvas.width = bitmap.width;
        canvas.height = bitmap.height;
        if (onResolutionDetected) {
          onResolutionDetected(`${bitmap.width}x${bitmap.height}`);
        }
      }

      // Vẽ frame mới lên canvas rồi giải phóng ngay
      ctx.drawImage(bitmap, 0, 0);
      bitmap.close(); // Giải phóng GPU memory ngay lập tức

      // Thông báo frame đã render để tính FPS
      if (onFrameRendered) {
        onFrameRendered(lastFrameBlob.size);
      }
    }).catch(() => {
      // Fallback về Image() nếu browser không hỗ trợ createImageBitmap
      const img = new Image();
      const objectUrl = URL.createObjectURL(lastFrameBlob);
      img.src = objectUrl;
      img.onload = () => {
        if (canvas.width !== img.width || canvas.height !== img.height) {
          canvas.width = img.width;
          canvas.height = img.height;
          if (onResolutionDetected) onResolutionDetected(`${img.width}x${img.height}`);
        }
        ctx.drawImage(img, 0, 0);
        URL.revokeObjectURL(objectUrl);
        if (onFrameRendered) onFrameRendered(lastFrameBlob.size);
      };
      img.onerror = () => URL.revokeObjectURL(objectUrl);
    });
  }, [lastFrameBlob, onFrameRendered, onResolutionDetected]);

  // 2. Tính toán tọa độ tương đối (0.0 -> 1.0) theo tỷ lệ Canvas
  const getNormalizedCoordinates = useCallback((e) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };

    const rect = canvas.getBoundingClientRect();
    const clientX = e.clientX;
    const clientY = e.clientY;

    const x_ratio = (clientX - rect.left) / rect.width;
    const y_ratio = (clientY - rect.top) / rect.height;

    return {
      x: Math.max(0, Math.min(1, x_ratio)),
      y: Math.max(0, Math.min(1, y_ratio))
    };
  }, []);

  // 3. Xử lý di chuyển chuột (Throttle ~16ms ≈ 60fps để tránh flood socket)
  const handleMouseMove = (e) => {
    if (!isHostOnline || isLocalActive) return;
    if (throttleTimerRef.current) return;

    const { x, y } = getNormalizedCoordinates(e);
    onSendControl(createMouseMovePacket(x, y));

    throttleTimerRef.current = setTimeout(() => {
      throttleTimerRef.current = null;
    }, 16);
  };

  // 4. Xử lý nhấn / thả chuột
  const handleMouseDown = (e) => {
    if (!isHostOnline || isLocalActive) return;
    canvasRef.current?.focus();
    const buttonMap = { 0: "left", 1: "middle", 2: "right" };
    const btn = buttonMap[e.button] || "left";
    onSendControl(createMouseClickPacket(btn, "down"));
  };

  const handleMouseUp = (e) => {
    if (!isHostOnline || isLocalActive) return;
    const buttonMap = { 0: "left", 1: "middle", 2: "right" };
    const btn = buttonMap[e.button] || "left";
    onSendControl(createMouseClickPacket(btn, "up"));
  };

  // 5. Xử lý cuộn chuột
  const handleWheel = (e) => {
    if (!isHostOnline || isLocalActive) return;
    e.preventDefault();
    onSendControl(createMouseScrollPacket(e.deltaX, e.deltaY));
  };

  // 6. Xử lý bàn phím
  const handleKeyDown = (e) => {
    if (!isHostOnline || isLocalActive) return;
    // Bỏ qua một số phím chức năng của trình duyệt nếu cần
    if (["F5", "F12"].includes(e.key)) return;
    e.preventDefault();
    onSendControl(createKeyEventPacket(e.key, "down"));
  };

  const handleKeyUp = (e) => {
    if (!isHostOnline || isLocalActive) return;
    if (["F5", "F12"].includes(e.key)) return;
    e.preventDefault();
    onSendControl(createKeyEventPacket(e.key, "up"));
  };

  return (
    <div
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onKeyUp={handleKeyUp}
      style={{
        flex: 1,
        width: "100%",
        height: "calc(100vh - 48px)",
        background: "#090d16",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        overflow: "hidden",
        position: "relative",
        outline: "none"
      }}
    >
      <canvas
        ref={canvasRef}
        onMouseMove={handleMouseMove}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
        onContextMenu={(e) => e.preventDefault()}
        style={{
          maxWidth: "100%",
          maxHeight: "100%",
          objectFit: "contain",
          boxShadow: "0 10px 30px rgba(0, 0, 0, 0.8)",
          cursor: (!isHostOnline || isLocalActive) ? "not-allowed" : "crosshair"
        }}
      />

      {isLocalActive && (
        <div style={{
          position: "absolute",
          top: 16,
          background: "rgba(245, 158, 11, 0.95)",
          color: "#0f172a",
          padding: "8px 18px",
          borderRadius: 24,
          fontWeight: 600,
          fontSize: 13,
          boxShadow: "0 8px 24px rgba(0, 0, 0, 0.5)",
          display: "flex",
          alignItems: "center",
          gap: 8,
          zIndex: 50,
          pointerEvents: "none",
          animation: "pulse-subtle 1.5s infinite"
        }}>
          <span>Người ngồi máy thật đang thao tác — Đang ưu tiên máy tính</span>
        </div>
      )}

      {!isHostOnline && (
        <div style={{
          position: "absolute",
          background: "rgba(15, 23, 42, 0.85)",
          padding: "16px 24px",
          borderRadius: 12,
          border: "1px solid #ef4444",
          color: "#fca5a5",
          textAlign: "center"
        }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>Host Agent Chưa Sẵn Sàng</h3>
          <p style={{ fontSize: 13, color: "#94a3b8" }}>
            Đang chờ máy bị điều khiển khởi động phần mềm kết nối...
          </p>
        </div>
      )}
    </div>
  );
}
