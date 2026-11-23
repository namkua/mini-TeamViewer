import React, { useState } from "react";
import { Maximize, Minimize, Power } from "lucide-react";

export default function ControlHeader({
  deviceId,
  isHostOnline,
  onDisconnect,
  onUpdateConfig,
  showHUD,
  setShowHUD
}) {
  const [showSettings, setShowSettings] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [fps, setFps] = useState(30);
  const [quality, setQuality] = useState(60);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => { });
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => { });
      setIsFullscreen(false);
    }
  };

  const handleApplyConfig = (newFps, newQuality) => {
    setFps(newFps);
    setQuality(newQuality);
    onUpdateConfig(newFps, newQuality);
  };

  return (
    <header style={{
      height: 48,
      background: "#0f172a",
      borderBottom: "1px solid #1e293b",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "0 16px",
      zIndex: 40,
      position: "relative"
    }}>
      {/* Cụm thông tin máy */}
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontWeight: 600, fontSize: 14 }}>
          <span>Device: {deviceId}</span>
        </div>

        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          fontSize: 12,
          padding: "3px 8px",
          borderRadius: 12,
          background: isHostOnline ? "rgba(34, 197, 94, 0.15)" : "rgba(239, 68, 68, 0.15)",
          color: isHostOnline ? "#4ade80" : "#f87171"
        }}>
          <span style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: isHostOnline ? "#22c55e" : "#ef4444"
          }} />
          {isHostOnline ? "Host Online" : "Mất tín hiệu Host"}
        </div>
      </div>

      {/* Cụm công cụ */}
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        {/* Toggle HUD Button */}
        <button
          onClick={() => setShowHUD(!showHUD)}
          title="Bật/Tắt HUD thông số mạng"
          style={{
            background: showHUD ? "#1e293b" : "transparent",
            color: showHUD ? "#38bdf8" : "#94a3b8",
            border: "1px solid #334155",
            borderRadius: 6,
            padding: "5px 10px",
            fontSize: 12,
            display: "flex",
            alignItems: "center",
            gap: 6
          }}
        >
          HUD Stats
        </button>

        {/* Settings Button */}
        <div style={{ position: "relative" }}>
          <button
            onClick={() => setShowSettings(!showSettings)}
            title="Cài đặt chất lượng truyền tải"
            style={{
              background: showSettings ? "#1e293b" : "transparent",
              color: "#94a3b8",
              border: "1px solid #334155",
              borderRadius: 6,
              padding: "5px 10px",
              fontSize: 12,
              display: "flex",
              alignItems: "center",
              gap: 6
            }}
          >
            Chất lượng
          </button>

          {/* Settings Dropdown */}
          {showSettings && (
            <div style={{
              position: "absolute",
              right: 0,
              top: 38,
              background: "#0f172a",
              border: "1px solid #334155",
              borderRadius: 10,
              padding: 16,
              width: 260,
              boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
              zIndex: 60
            }}>
              <h4 style={{ fontSize: 13, marginBottom: 12, color: "#f8fafc" }}>Tùy chỉnh mạng & hình ảnh</h4>

              <div style={{ marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "#94a3b8", marginBottom: 4 }}>
                  <span>Tốc độ khung hình (FPS):</span>
                  <span style={{ color: "#38bdf8", fontWeight: 600 }}>{fps} fps</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="60"
                  step="5"
                  value={fps}
                  onChange={(e) => handleApplyConfig(Number(e.target.value), quality)}
                  style={{ width: "100%", accentColor: "#38bdf8" }}
                />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "#94a3b8", marginBottom: 4 }}>
                  <span>Chất lượng JPEG:</span>
                  <span style={{ color: "#38bdf8", fontWeight: 600 }}>{quality}%</span>
                </div>
                <input
                  type="range"
                  min="20"
                  max="90"
                  step="10"
                  value={quality}
                  onChange={(e) => handleApplyConfig(fps, Number(e.target.value))}
                  style={{ width: "100%", accentColor: "#38bdf8" }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Fullscreen Button */}
        <button
          onClick={toggleFullscreen}
          title="Toàn màn hình"
          style={{
            background: "transparent",
            color: "#94a3b8",
            border: "1px solid #334155",
            borderRadius: 6,
            padding: "5px 10px",
            fontSize: 12,
            display: "flex",
            alignItems: "center",
            cursor: "pointer"
          }}
        >
          {isFullscreen ? <Minimize size={14} /> : <Maximize size={14} />}
        </button>

        {/* Disconnect Button */}
        <button
          onClick={onDisconnect}
          title="Ngắt kết nối"
          style={{
            background: "rgba(239, 68, 68, 0.2)",
            color: "#ef4444",
            border: "1px solid rgba(239, 68, 68, 0.4)",
            borderRadius: 6,
            padding: "5px 12px",
            fontSize: 12,
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            gap: 6,
            cursor: "pointer"
          }}
        >
          <Power size={14} /> Ngắt kết nối
        </button>
      </div>
    </header>
  );
}
