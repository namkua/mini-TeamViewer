import React, { useState, useEffect, useRef, useCallback } from "react";
import ConnectModal from "./components/ConnectModal";
import ControlHeader from "./components/ControlHeader";
import RemoteCanvas from "./components/RemoteCanvas";
import NetworkHUD from "./components/NetworkHUD";
import { createPingPacket, createConfigPacket } from "./utils/protocol";

export default function App() {
  const [session, setSession] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const [lastFrameBlob, setLastFrameBlob] = useState(null);
  const [isHostOnline, setIsHostOnline] = useState(false);
  const [resolution, setResolution] = useState(null);
  const [isLocalActive, setIsLocalActive] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);

  // Network stats
  const [ping, setPing] = useState(null);
  const [fps, setFps] = useState(0);
  const [bandwidthKbps, setBandwidthKbps] = useState(0);
  const [showHUD, setShowHUD] = useState(true);

  const wsRef = useRef(null);
  const pingIntervalRef = useRef(null);
  const localActiveTimerRef = useRef(null);
  const lastPongTimeRef = useRef(Date.now());
  const isManualDisconnectRef = useRef(false);
  const reconnectTimerRef = useRef(null);
  const sessionRef = useRef(null);
  const statsCounterRef = useRef({ frames: 0, bytes: 0, lastCheckTime: Date.now() });

  // 1. Xác thực và Mở kết nối WebSocket
  const handleConnect = async ({ serverUrl, deviceId, pin }, isRetry = false) => {
    if (!isRetry) {
      setIsLoading(true);
      setErrorMsg("");
    }
    isManualDisconnectRef.current = false;
    sessionRef.current = { serverUrl, deviceId, pin };

    try {
      // 1.1 Gọi REST API xác thực mã PIN và trạng thái thiết bị
      const verifyRes = await fetch(`${serverUrl}/api/v1/session/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device_id: deviceId, pin: pin })
      });

      if (!verifyRes.ok) {
        throw new Error("Không thể liên lạc với máy chủ Relay.");
      }

      const verifyData = await verifyRes.json();
      if (!verifyData.valid) {
        setErrorMsg(verifyData.message || "Mã thiết bị hoặc mã PIN không hợp lệ.");
        setIsLoading(false);
        setReconnecting(false);
        if (isRetry) handleManualDisconnect();
        return;
      }

      // 1.2 Mở kết nối WebSocket
      const wsProtocol = serverUrl.startsWith("https") ? "wss" : "ws";
      const hostPart = serverUrl.replace(/^https?:\/\//, "");
      const wsUrl = `${wsProtocol}://${hostPart}/ws/viewer/${deviceId}?pin=${encodeURIComponent(pin)}`;

      const ws = new WebSocket(wsUrl);
      ws.binaryType = "blob"; // Bắt buộc để nhận mảng byte nhị phân JPEG

      ws.onopen = () => {
        setIsConnected(true);
        setIsLoading(false);
        setReconnecting(false);
        setSession({ serverUrl, deviceId, pin });
        setIsHostOnline(verifyData.is_online);
        wsRef.current = ws;
        lastPongTimeRef.current = Date.now();

        // Gửi gói tin báo Viewer đã vào và đồng bộ cấu hình (30 FPS, 60% quality)
        ws.send(JSON.stringify({ type: "VIEWER_JOINED" }));
        ws.send(createConfigPacket(30, 60, null));

        // Bắt đầu vòng lặp Heartbeat & Ping RTT (mỗi 2.5s)
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            // Phát hiện Ping Timeout: nếu quá 5.5 giây không nhận được PONG
            if (Date.now() - lastPongTimeRef.current > 5500) {
              setPing(null);
            }
            ws.send(createPingPacket());
          }
        }, 2500);
      };

      ws.onmessage = (event) => {
        if (event.data instanceof Blob) {
          // Nhận Frame ảnh nhị phân JPEG
          setLastFrameBlob(event.data);
          statsCounterRef.current.bytes += event.data.size;
        } else if (typeof event.data === "string") {
          // Nhận gói tin điều khiển JSON
          try {
            const data = JSON.parse(event.data);
            if (data.type === "PONG") {
              lastPongTimeRef.current = Date.now();
              const rtt = Date.now() - data.timestamp;
              setPing(rtt);
            } else if (data.type === "HOST_STATUS") {
              setIsHostOnline(data.status === "online");
            } else if (data.type === "LOCAL_INPUT_ACTIVE") {
              // Người ngồi máy thật đang thao tác -> kích hoạt trạng thái ưu tiên
              setIsLocalActive(true);
              if (localActiveTimerRef.current) {
                clearTimeout(localActiveTimerRef.current);
              }
              localActiveTimerRef.current = setTimeout(() => {
                setIsLocalActive(false);
              }, 2000);
            }
          } catch (e) {
            console.warn("Lỗi phân tích JSON từ server:", e);
          }
        }
      };

      ws.onerror = () => {
        console.warn("Lỗi kết nối Socket tới Relay Server.");
      };

      ws.onclose = (event) => {
        if (event.code === 4003) {
          setErrorMsg("Xác thực thất bại (Sai mã PIN).");
          handleManualDisconnect();
          return;
        }

        // Tự động kết nối lại liên tục nếu bị rớt mạng bất thường hoặc server restart
        if (!isManualDisconnectRef.current && sessionRef.current) {
          setReconnecting(true);
          setPing(null);
          if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
          reconnectTimerRef.current = setTimeout(() => {
            if (sessionRef.current && !isManualDisconnectRef.current) {
              handleConnect(sessionRef.current, true);
            }
          }, 3000);
          return;
        }

        handleDisconnect();
      };

    } catch (err) {
      // Khi server tạm ngắt hoặc rớt mạng trong phiên: tiếp tục giữ màn hình và thử lại sau 3s
      if (isRetry || (!isManualDisconnectRef.current && isConnected)) {
        setReconnecting(true);
        setPing(null);
        if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = setTimeout(() => {
          if (sessionRef.current && !isManualDisconnectRef.current) {
            handleConnect(sessionRef.current, true);
          }
        }, 3000);
      } else {
        setErrorMsg(err.message || "Không thể kết nối tới server.");
        setReconnecting(false);
        setIsLoading(false);
        handleDisconnect();
      }
    }
  };

  // Ngắt kết nối do người dùng bấm chủ động
  const handleManualDisconnect = useCallback(() => {
    isManualDisconnectRef.current = true;
    sessionRef.current = null;
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    setReconnecting(false);
    handleDisconnect();
  }, []);

  // 2. Ngắt kết nối và dọn dẹp
  const handleDisconnect = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
    if (localActiveTimerRef.current) {
      clearTimeout(localActiveTimerRef.current);
      localActiveTimerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setIsLoading(false);
    setIsLocalActive(false);
    setLastFrameBlob(null);
    setPing(null);
    setFps(0);
    setBandwidthKbps(0);
  }, []);

  // 3. Tính toán FPS và Băng thông mạng mỗi giây
  const handleFrameRendered = useCallback(() => {
    statsCounterRef.current.frames += 1;
  }, []);

  useEffect(() => {
    if (!isConnected) return;

    const interval = setInterval(() => {
      const now = Date.now();
      const elapsedSec = (now - statsCounterRef.current.lastCheckTime) / 1000;

      if (elapsedSec > 0) {
        const calculatedFps = Math.round(statsCounterRef.current.frames / elapsedSec);
        const calculatedKbps = (statsCounterRef.current.bytes / 1024) / elapsedSec;

        setFps(calculatedFps);
        setBandwidthKbps(calculatedKbps);

        statsCounterRef.current.frames = 0;
        statsCounterRef.current.bytes = 0;
        statsCounterRef.current.lastCheckTime = now;
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [isConnected]);

  // 4. Gửi lệnh điều khiển qua WebSocket
  const handleSendControl = useCallback((jsonString) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(jsonString);
    }
  }, []);

  // 5. Cập nhật cấu hình chất lượng hình ảnh & FPS
  const handleUpdateConfig = useCallback((targetFps, quality) => {
    handleSendControl(createConfigPacket(targetFps, quality, null));
  }, [handleSendControl]);

  return (
    <div style={{ width: "100vw", height: "100vh", display: "flex", flexDirection: "column", background: "#0f172a" }}>
      {!isConnected ? (
        <ConnectModal
          onConnect={handleConnect}
          isLoading={isLoading}
          errorMsg={errorMsg}
        />
      ) : (
        <>
          <ControlHeader
            deviceId={session?.deviceId}
            isHostOnline={isHostOnline}
            onDisconnect={handleManualDisconnect}
            onUpdateConfig={handleUpdateConfig}
            showHUD={showHUD}
            setShowHUD={setShowHUD}
          />

          {reconnecting && (
            <div style={{
              background: "#dc2626",
              color: "#ffffff",
              padding: "7px 16px",
              fontSize: 12,
              fontWeight: 600,
              textAlign: "center",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 45
            }}>
              <span>Mất kết nối mạng. Đang tự động kết nối lại...</span>
            </div>
          )}

          <RemoteCanvas
            lastFrameBlob={lastFrameBlob}
            onSendControl={handleSendControl}
            onFrameRendered={handleFrameRendered}
            onResolutionDetected={setResolution}
            isHostOnline={isHostOnline}
            isLocalActive={isLocalActive}
          />

          <NetworkHUD
            ping={ping}
            fps={fps}
            bandwidthKbps={bandwidthKbps}
            resolution={resolution}
            visible={showHUD}
          />
        </>
      )}
    </div>
  );
}
