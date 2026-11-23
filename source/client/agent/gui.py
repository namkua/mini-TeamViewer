import queue
import sys
import tkinter as tk
import logging

logger = logging.getLogger("agent.gui")

class ModernButton(tk.Label):
    """Nút bấm phẳng hiện đại, tương thích tốt cả macOS và Windows"""
    def __init__(
        self,
        master,
        text="",
        command=None,
        bg="#2563eb",
        fg="#ffffff",
        hover_bg="#1d4ed8",
        active_bg="#1e40af",
        font=("Segoe UI", 11, "bold"),
        padx=12,
        pady=6,
        **kwargs
    ):
        super().__init__(
            master,
            text=text,
            bg=bg,
            fg=fg,
            font=font,
            padx=padx,
            pady=pady,
            cursor="hand2",
            relief="flat",
            **kwargs
        )
        self.command = command
        self.normal_bg = bg
        self.hover_bg = hover_bg
        self.active_bg = active_bg

        self.bind("<Enter>", lambda e: self.config(bg=self.hover_bg))
        self.bind("<Leave>", lambda e: self.config(bg=self.normal_bg))
        self.bind("<ButtonPress-1>", lambda e: self.config(bg=self.active_bg))
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_release(self, event):
        self.config(bg=self.hover_bg)
        if self.command:
            self.command()


class AgentGUI:
    """Giao diện thu nhỏ vừa khít nội dung, không có khoảng trống thừa, không có icon"""

    def __init__(self, on_change_pin=None, on_close=None):
        self.on_change_pin = on_change_pin
        self.on_close_cb = on_close

        self.root = tk.Tk()
        self.root.title("Remote Desktop Agent")
        self.root.configure(bg="#0f172a")

        # Variables
        self.device_id_var = tk.StringVar(value="Đang lấy mã...")
        self.pin_var = tk.StringVar(value="------")
        self.status_var = tk.StringVar(value="Đang kết nối máy chủ...")
        self.status_color = "#f59e0b"

        self._build_ui()

        # Tự động tính toán kích thước chuẩn theo DPI và font trên Windows/macOS
        self.root.update_idletasks()
        req_w = max(400, self.root.winfo_reqwidth())
        req_h = self.root.winfo_reqheight()

        # Căn giữa màn hình
        scr_w = self.root.winfo_screenwidth()
        scr_h = self.root.winfo_screenheight()
        x = max(0, (scr_w - req_w) // 2)
        y = max(0, (scr_h - req_h) // 2)

        self.root.geometry(f"{req_w}x{req_h}+{x}+{y}")
        self.root.minsize(req_w, req_h)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self._ui_queue = queue.Queue()
        self.root.after(100, self._process_ui_queue)

    def _build_ui(self):
        # 1. Header thoáng đãng, dễ đọc
        header_frame = tk.Frame(self.root, bg="#0f172a", pady=14)
        header_frame.pack(fill="x")

        title_lbl = tk.Label(
            header_frame,
            text="Remote Desktop",
            font=("Segoe UI", 18, "bold"),
            fg="#f8fafc",
            bg="#0f172a"
        )
        title_lbl.pack()


        content_frame = tk.Frame(self.root, bg="#0f172a", padx=18)
        content_frame.pack(fill="x")

        # 2. Card: Device ID
        id_card = tk.Frame(
            content_frame,
            bg="#1e293b",
            padx=14,
            pady=10,
            highlightbackground="#334155",
            highlightthickness=1
        )
        id_card.pack(fill="x", pady=(0, 10))

        id_title = tk.Label(
            id_card,
            text="DEVICE ID",
            font=("Segoe UI", 9, "bold"),
            fg="#94a3b8",
            bg="#1e293b"
        )
        id_title.pack(anchor="w")

        id_row = tk.Frame(id_card, bg="#1e293b")
        id_row.pack(fill="x", pady=(4, 0))

        self.id_label = tk.Label(
            id_row,
            textvariable=self.device_id_var,
            font=("Segoe UI", 19, "bold"),
            fg="#38bdf8",
            bg="#1e293b"
        )
        self.id_label.pack(side="left")

        copy_id_btn = ModernButton(
            id_row,
            text="Sao chép",
            bg="#2563eb",
            hover_bg="#3b82f6",
            command=self._copy_id
        )
        copy_id_btn.pack(side="right")

        # 3. Card: PIN
        pin_card = tk.Frame(
            content_frame,
            bg="#1e293b",
            padx=14,
            pady=10,
            highlightbackground="#334155",
            highlightthickness=1
        )
        pin_card.pack(fill="x", pady=(0, 10))

        pin_title = tk.Label(
            pin_card,
            text="MÃ PIN KẾT NỐI",
            font=("Segoe UI", 9, "bold"),
            fg="#94a3b8",
            bg="#1e293b"
        )
        pin_title.pack(anchor="w")

        pin_row = tk.Frame(pin_card, bg="#1e293b")
        pin_row.pack(fill="x", pady=(4, 0))

        self.pin_label = tk.Label(
            pin_row,
            textvariable=self.pin_var,
            font=("Segoe UI", 19, "bold"),
            fg="#4ade80",
            bg="#1e293b"
        )
        self.pin_label.pack(side="left")

        btn_box = tk.Frame(pin_row, bg="#1e293b")
        btn_box.pack(side="right")

        copy_pin_btn = ModernButton(
            btn_box,
            text="Sao chép",
            bg="#2563eb",
            hover_bg="#3b82f6",
            command=self._copy_pin
        )
        copy_pin_btn.pack(side="left", padx=(0, 6))

        refresh_pin_btn = ModernButton(
            btn_box,
            text="Đổi PIN",
            bg="#334155",
            hover_bg="#475569",
            command=self._trigger_change_pin
        )
        refresh_pin_btn.pack(side="left")

        # 4. Footer Trạng thái nằm ngay sát dưới card
        footer_frame = tk.Frame(self.root, bg="#1e293b", pady=10, padx=16)
        footer_frame.pack(fill="x")

        self.status_lbl = tk.Label(
            footer_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 11, "bold"),
            fg=self.status_color,
            bg="#1e293b"
        )
        self.status_lbl.pack(anchor="w")

    def _copy_id(self):
        val = self.device_id_var.get().replace(" ", "")
        if val and "..." not in val:
            self.root.clipboard_clear()
            self.root.clipboard_append(val)
            self._flash_status("Đã sao chép Device ID")

    def _copy_pin(self):
        val = self.pin_var.get().replace(" ", "")
        if val and "-" not in val:
            self.root.clipboard_clear()
            self.root.clipboard_append(val)
            self._flash_status("Đã sao chép mã PIN")

    def _trigger_change_pin(self):
        if self.on_change_pin:
            self.on_change_pin()

    def _flash_status(self, msg: str):
        prev_msg = self.status_var.get()
        self.status_var.set(msg)
        self.root.after(1600, lambda: self.status_var.set(prev_msg))

    def _process_ui_queue(self):
        """Xử lý an toàn các cập nhật giao diện từ background thread trên Main Thread."""
        try:
            while True:
                fn = self._ui_queue.get_nowait()
                fn()
        except queue.Empty:
            pass
        self.root.after(100, self._process_ui_queue)

    def update_info(self, device_id: str, pin: str):
        def _apply():
            fmt_id = f"{device_id[:3]} {device_id[3:]}" if len(device_id) == 6 else device_id
            fmt_pin = f"{pin[:3]} {pin[3:]}" if len(pin) == 6 else pin
            self.device_id_var.set(fmt_id)
            self.pin_var.set(fmt_pin)
            self.status_var.set("Sẵn sàng nhận kết nối")
            self.status_lbl.config(fg="#4ade80")
        self._ui_queue.put(_apply)

    def set_status(self, text: str, color: str = "#4ade80"):
        def _apply():
            self.status_var.set(text)
            self.status_lbl.config(fg=color)
        self._ui_queue.put(_apply)

    def _on_closing(self):
        if self.on_close_cb:
            self.on_close_cb()
        self.root.destroy()
        sys.exit(0)

    def start(self):
        self.root.mainloop()
