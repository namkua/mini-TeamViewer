import React, { useState } from "react";

export default function ConnectModal({ onConnect, isLoading, errorMsg }) {
  const [serverUrl, setServerUrl] = useState(
    window.location.hostname === "localhost"
      ? "http://localhost:8000"
      : `http://${window.location.hostname}:8000`
  );
  const [deviceId, setDeviceId] = useState("");
  const [pin, setPin] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!deviceId.trim() || !pin.trim()) return;
    onConnect({
      serverUrl: serverUrl.trim(),
      deviceId: deviceId.trim().replace(/\D/g, ""), // Chỉ lấy số
      pin: pin.trim()
    });
  };

  return (
    <div style={{
      position: "fixed",
      inset: 0,
      background: "radial-gradient(circle at 50% 30%, #1e293b, #090d16)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: 20,
      zIndex: 100
    }}>
      <div style={{
        background: "#0f172a",
        border: "1px solid #334155",
        borderRadius: 16,
        width: "100%",
        maxWidth: 440,
        padding: 32,
        boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.7)"
      }}>
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: "#f8fafc" }}>Web Remote Desktop</h2>
        </div>

        {errorMsg && (
          <div style={{
            background: "rgba(239, 68, 68, 0.15)",
            border: "1px solid #ef4444",
            color: "#fca5a5",
            borderRadius: 8,
            padding: "10px 14px",
            fontSize: 13,
            marginBottom: 20
          }}>
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <div>
            <label style={{ display: "block", fontSize: 13, color: "#cbd5e1", marginBottom: 6 }}>
              Máy chủ Relay Server:
            </label>
            <input
              type="text"
              value={serverUrl}
              onChange={(e) => setServerUrl(e.target.value)}
              placeholder="http://localhost:8000"
              required
              style={{
                width: "100%",
                background: "#1e293b",
                border: "1px solid #334155",
                borderRadius: 8,
                padding: "10px 12px",
                color: "#fff",
                fontSize: 14,
                fontFamily: "inherit",
                outline: "none"
              }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: 13, color: "#cbd5e1", marginBottom: 6 }}>
              Mã thiết bị (Device ID - 6 số):
            </label>
            <input
              type="text"
              value={deviceId}
              onChange={(e) => setDeviceId(e.target.value)}
              placeholder="Ví dụ: 839201"
              maxLength={10}
              required
              style={{
                width: "100%",
                background: "#1e293b",
                border: "1px solid #334155",
                borderRadius: 8,
                padding: "10px 12px",
                color: "#fff",
                fontSize: 14,
                fontFamily: "inherit",
                outline: "none"
              }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: 13, color: "#cbd5e1", marginBottom: 6 }}>
              Mã PIN bảo mật:
            </label>
            <input
              type="password"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              placeholder="Nhập mã PIN máy tính"
              required
              style={{
                width: "100%",
                background: "#1e293b",
                border: "1px solid #334155",
                borderRadius: 8,
                padding: "10px 12px",
                color: "#fff",
                fontSize: 14,
                fontFamily: "inherit",
                outline: "none"
              }}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            style={{
              marginTop: 10,
              width: "100%",
              background: isLoading ? "#475569" : "#2563eb",
              color: "#fff",
              padding: "12px",
              borderRadius: 8,
              fontSize: 15,
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
              cursor: isLoading ? "not-allowed" : "pointer"
            }}
          >
            {isLoading ? "Đang xác thực kết nối..." : "Kết nối tới máy tính"}
          </button>
        </form>
      </div>
    </div>
  );
}
