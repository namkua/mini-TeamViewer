/**
 * Application Protocol Helpers
 * Đóng gói các loại gói tin điều khiển theo chuẩn đặc tả giao thức
 */

export const createMouseMovePacket = (x_ratio, y_ratio) => JSON.stringify({
  type: "MOUSE_MOVE",
  x_ratio: Math.max(0, Math.min(1, x_ratio)),
  y_ratio: Math.max(0, Math.min(1, y_ratio))
});

export const createMouseClickPacket = (button = "left", action = "click") => JSON.stringify({
  type: "MOUSE_CLICK",
  button, // "left" | "right" | "middle"
  action  // "click" | "down" | "up" | "double_click"
});

export const createMouseScrollPacket = (dx, dy) => JSON.stringify({
  type: "MOUSE_SCROLL",
  dx,
  dy
});

export const createKeyEventPacket = (key, action = "down") => JSON.stringify({
  type: "KEY_EVENT",
  key,
  action // "down" | "up"
});

export const createConfigPacket = (fps, quality, scale) => JSON.stringify({
  type: "CONFIG_UPDATE",
  fps,
  quality,
  scale
});

export const createPingPacket = () => JSON.stringify({
  type: "PING",
  timestamp: Date.now()
});
