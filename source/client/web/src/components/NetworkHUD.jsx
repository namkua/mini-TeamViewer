import React from "react";

export default function NetworkHUD({ ping, fps, bandwidthKbps, resolution, visible = true }) {
  if (!visible) return null;

  const getPingColor = (ms) => {
    if (ms === null || ms === undefined) return "#ef4444"; // Red / mất tín hiệu
    if (ms < 50) return "#22c55e"; // Green
    if (ms < 150) return "#eab308"; // Yellow
    return "#ef4444"; // Red
  };

  return (
    <div style={{
      position: "absolute",
      top: 60,
      right: 16,
      background: "rgba(15, 23, 42, 0.85)",
      backdropFilter: "blur(8px)",
      border: "1px solid rgba(51, 65, 85, 0.6)",
      borderRadius: 10,
      padding: "10px 14px",
      fontSize: 12,
      color: "#e2e8f0",
      display: "flex",
      flexDirection: "column",
      gap: 6,
      zIndex: 50,
      boxShadow: "0 4px 12px rgba(0, 0, 0, 0.4)",
      pointerEvents: "none"
    }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
        <span style={{ color: "#94a3b8" }}>
          Ping (RTT):
        </span>
        <strong style={{ color: getPingColor(ping) }}>
          {ping !== null ? `${ping} ms` : "--"}
        </strong>
      </div>

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
        <span style={{ color: "#94a3b8" }}>
          FPS:
        </span>
        <strong style={{ color: fps >= 20 ? "#38bdf8" : "#fbbf24" }}>
          {fps} fps
        </strong>
      </div>

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
        <span style={{ color: "#94a3b8" }}>
          Băng thông:
        </span>
        <strong style={{ color: "#a855f7" }}>
          {bandwidthKbps > 1024 
            ? `${(bandwidthKbps / 1024).toFixed(2)} MB/s` 
            : `${bandwidthKbps.toFixed(0)} KB/s`}
        </strong>
      </div>

      {resolution && (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
          <span style={{ color: "#94a3b8" }}>
            Resolution:
          </span>
          <span style={{ color: "#cbd5e1" }}>{resolution}</span>
        </div>
      )}
    </div>
  );
}
