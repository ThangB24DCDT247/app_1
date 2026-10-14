#!/usr/bin/env python3
"""
PTIT MQTT Monitor — Python Desktop App
Học viện Công nghệ Bưu chính Viễn thông (PTIT)
Theo tài liệu: doc.md | paho-mqtt v2
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import datetime
import os
import sys

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

# ─── Màu sắc PTIT ─────────────────────────────────────────────────────────────
C_RED       = "#C8102E"
C_RED_DARK  = "#9B0B22"
C_WHITE     = "#FFFFFF"
C_BG        = "#F8F8F8"
C_PANEL     = "#FFFFFF"
C_BORDER    = "#E0E0E0"
C_TEXT      = "#1A1A1A"
C_GRAY      = "#6B7280"
C_GREEN     = "#16A34A"
C_ORANGE    = "#D97706"
C_TELE_BG   = "#FFF5F5"
C_HB_BG     = "#F0FFF4"

# ─── Cấu hình mặc định ────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "host":        "mqtt.mysignage.vn",
    "port":        1883,
    "transport":   "tcp",
    "keepalive":   60,
    "client_id":   "KIT-001-python-monitor",
    "max_messages": 500,
    "json_indent":  2,
}

TOPIC_TELEMETRY = "lab/kit/KIT-001/telemetry"
TOPIC_HEARTBEAT = "lab/kit/KIT-001/heartbeat"


# ═══════════════════════════════════════════════════════════════════════════════
#  MQTT Engine — paho-mqtt v2 (CallbackAPIVersion.VERSION2)
# ═══════════════════════════════════════════════════════════════════════════════
import random, threading

class MQTTEngine:
    def __init__(self, on_message_cb, on_status_cb):
        self.on_message  = on_message_cb
        self.on_status   = on_status_cb
        self.client      = None
        self.connected   = False
        self._user_disconnect = False   # phân biệt ngắt chủ động vs bị động

    def _cleanup(self):
        if self.client:
            try:
                self.client.loop_stop()
            except Exception:
                pass
            try:
                self.client.disconnect()
            except Exception:
                pass
            self.client = None

    def connect(self, cfg):
        if not MQTT_AVAILABLE:
            self.on_status("error", "Thư viện paho-mqtt chưa cài.\nChạy: pip install paho-mqtt")
            return
        self._user_disconnect = False
        self._cleanup()
        self.on_status("connecting", f"Đang kết nối tới {cfg['host']}:{cfg['port']} …")
        try:
            # Thêm suffix ngẫu nhiên để tránh xung đột client_id với các app khác (MQTTX, ...)
            unique_id = f"{cfg['client_id']}-{random.randint(1000, 9999)}"
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=unique_id,
                clean_session=True,
                protocol=mqtt.MQTTv311,
                transport=cfg["transport"],
            )
            # TẮT auto-reconnect: đặt delay = 86400s (24h) → thực tế không bao giờ tự reconnect
            self.client.reconnect_delay_set(min_delay=86400, max_delay=86400)
            self.client.on_connect    = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message    = self._on_message
            self.client.connect_async(cfg["host"], cfg["port"], cfg["keepalive"])
            self.client.loop_start()
        except Exception as e:
            self.on_status("error", f"Lỗi khởi tạo: {e}")

    def disconnect(self):
        self._user_disconnect = True   # đánh dấu: chính chúng ta ngắt
        self._cleanup()
        self.connected = False
        self.on_status("disconnected", "Đã ngắt kết nối.")

    # on_connect(client, userdata, connect_flags, reason_code, properties)
    def _on_connect(self, client, userdata, connect_flags, reason_code, properties):
        if reason_code.is_failure:
            self.connected = False
            if reason_code.value in (4, 5):
                msg = "Broker từ chối kết nối — cần xác thực hoặc không có quyền anonymous. Liên hệ quản trị viên."
            else:
                msg = f"Kết nối thất bại: {reason_code!s}"
            self.on_status("error", msg)
        else:
            self.connected = True
            client.subscribe([(TOPIC_TELEMETRY, 0), (TOPIC_HEARTBEAT, 0)])
            self.on_status("connected", "Kết nối thành công ✔  |  Đang lắng nghe topics KIT-001…")

    # on_disconnect(client, userdata, disconnect_flags, reason_code, properties)
    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        self.connected = False
        if self._user_disconnect:
            # Chính người dùng bấm Disconnect — bình thường, không báo lỗi
            self.on_status("disconnected", "Đã ngắt kết nối.")
        elif disconnect_flags.is_disconnect_packet_from_server:
            self.on_status("error", f"Broker ngắt kết nối ({reason_code!s}). Nhấn Reconnect để thử lại.")
        else:
            # Mất kết nối mạng hoặc lý do khác
            self.on_status("error", "Mất kết nối. Nhấn Reconnect để thử lại.")

    # on_message(client, userdata, message)
    def _on_message(self, client, userdata, msg):
        self.on_message(msg.topic, msg.payload)


# ═══════════════════════════════════════════════════════════════════════════════
#  GUI Application
# ═══════════════════════════════════════════════════════════════════════════════
class PTITMQTTApp:
    def __init__(self, root: tk.Tk):
        self.root    = root
        self.config  = dict(DEFAULT_CONFIG)
        self.counts  = {"total": 0, "telemetry": 0, "heartbeat": 0}
        self.buf     = []
        self.auto_scroll = tk.BooleanVar(value=True)

        self._build_window()
        self._build_header()
        self._build_status_bar()
        self._build_main_area()
        self._build_bottom_bar()

        self.mqtt = MQTTEngine(
            on_message_cb=lambda t, p: self.root.after(0, self._display_message, t, p),
            on_status_cb =lambda s, m: self.root.after(0, self._set_status, s, m),
        )

        if MQTT_AVAILABLE:
            self.root.after(300, lambda: self.mqtt.connect(self.config))
        else:
            self._set_status("error", "⚠ Cài paho-mqtt trước:  pip install paho-mqtt")

    # ── Window ────────────────────────────────────────────────────────────────
    def _build_window(self):
        self.root.title("PTIT MQTT Monitor — KIT-001")
        self.root.geometry("1100x720")
        self.root.minsize(900, 580)
        self.root.configure(bg=C_BG)

        logo_path = os.path.join(os.path.dirname(__file__), "ptit_logo.png")
        if os.path.exists(logo_path):
            try:
                icon = tk.PhotoImage(file=logo_path)
                self.root.iconphoto(True, icon)
                self._win_icon = icon
            except Exception:
                pass

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self.root, bg=C_RED, height=72)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        # Logo
        logo_path = os.path.join(os.path.dirname(__file__), "ptit_logo.png")
        self._header_logo = None
        if os.path.exists(logo_path):
            try:
                from PIL import Image, ImageTk
                img = Image.open(logo_path).resize((52, 52), Image.LANCZOS)
                self._header_logo = ImageTk.PhotoImage(img)
                tk.Label(hdr, image=self._header_logo, bg=C_RED).pack(side=tk.LEFT, padx=(14, 8), pady=10)
            except Exception:
                pass
        if not self._header_logo:
            tk.Label(hdr, text="PTIT", font=("Arial", 22, "bold"), fg=C_WHITE, bg=C_RED
                     ).pack(side=tk.LEFT, padx=(14, 8), pady=10)

        # Tiêu đề
        tf = tk.Frame(hdr, bg=C_RED)
        tf.pack(side=tk.LEFT, pady=8)
        tk.Label(tf, text="MQTT Monitor",
                 font=("Segoe UI", 20, "bold"), fg=C_WHITE, bg=C_RED).pack(anchor="w")
        tk.Label(tf, text="Học viện Công nghệ Bưu chính Viễn thông — PTIT",
                 font=("Segoe UI", 9), fg="#FFCCCC", bg=C_RED).pack(anchor="w")

        # Badge
        badge = tk.Frame(hdr, bg=C_RED_DARK, padx=12, pady=6)
        badge.pack(side=tk.RIGHT, padx=16)
        tk.Label(badge, text="KIT-001", font=("Consolas", 13, "bold"),
                 fg=C_WHITE, bg=C_RED_DARK).pack()
        tk.Label(badge, text="mqtt.mysignage.vn", font=("Consolas", 9),
                 fg="#FFB3B3", bg=C_RED_DARK).pack()

    # ── Status bar ────────────────────────────────────────────────────────────
    def _build_status_bar(self):
        sb = tk.Frame(self.root, bg=C_WHITE,
                      highlightthickness=1, highlightbackground=C_BORDER)
        sb.pack(fill=tk.X)

        self._dot = tk.Label(sb, text="●", font=("Arial", 16), fg=C_GRAY, bg=C_WHITE)
        self._dot.pack(side=tk.LEFT, padx=(14, 4), pady=8)

        self._status_var = tk.StringVar(value="Đang khởi động…")
        self._status_lbl = tk.Label(sb, textvariable=self._status_var,
                                    font=("Segoe UI", 10), fg=C_GRAY, bg=C_WHITE, anchor="w")
        self._status_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=8)

        bf = tk.Frame(sb, bg=C_WHITE)
        bf.pack(side=tk.RIGHT, padx=10, pady=6)

        self._btn_connect    = self._btn(bf, "⚡ Connect",    self._do_connect,    C_RED, C_WHITE)
        self._btn_reconnect  = self._btn(bf, "🔄 Reconnect",  self._do_reconnect,  C_WHITE, C_RED, relief="solid")
        self._btn_disconnect = self._btn(bf, "✖ Disconnect",  self._do_disconnect, C_WHITE, C_GRAY, relief="solid")
        for b in (self._btn_connect, self._btn_reconnect, self._btn_disconnect):
            b.pack(side=tk.LEFT, padx=3)

    # ── Main area ─────────────────────────────────────────────────────────────
    def _build_main_area(self):
        main = tk.Frame(self.root, bg=C_BG)
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=(8, 4))

        # Left — feed
        left = tk.Frame(main, bg=C_PANEL, highlightthickness=1, highlightbackground=C_BORDER)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        lh = tk.Frame(left, bg=C_RED, padx=10, pady=6)
        lh.pack(fill=tk.X)
        tk.Label(lh, text="📨  Tin nhắn nhận được",
                 font=("Segoe UI", 11, "bold"), fg=C_WHITE, bg=C_RED).pack(side=tk.LEFT)

        cf = tk.Frame(lh, bg=C_RED)
        cf.pack(side=tk.RIGHT)
        self._lbl_total = tk.Label(cf, text="Tổng: 0",        font=("Segoe UI", 9), fg="#FFD0D0", bg=C_RED)
        self._lbl_tele  = tk.Label(cf, text="Telemetry: 0",   font=("Segoe UI", 9), fg="#FFD0D0", bg=C_RED)
        self._lbl_hb    = tk.Label(cf, text="Heartbeat: 0",   font=("Segoe UI", 9), fg="#FFD0D0", bg=C_RED)
        for l in (self._lbl_total, self._lbl_tele, self._lbl_hb):
            l.pack(side=tk.LEFT, padx=6)

        tb = tk.Frame(left, bg=C_BG, padx=8, pady=4)
        tb.pack(fill=tk.X)
        tk.Checkbutton(tb, text="Tự cuộn", variable=self.auto_scroll,
                       font=("Segoe UI", 9), bg=C_BG, fg=C_TEXT).pack(side=tk.LEFT)
        self._btn(tb, "🗑 Xóa", self._clear, C_WHITE, C_RED, relief="solid", w=8).pack(side=tk.RIGHT, padx=2)
        self._btn(tb, "💾 Lưu log", self._save_log, C_WHITE, C_GRAY, relief="solid", w=10).pack(side=tk.RIGHT, padx=2)

        self._feed = scrolledtext.ScrolledText(
            left, wrap=tk.WORD, state=tk.DISABLED,
            font=("Consolas", 10), bg=C_WHITE, fg=C_TEXT,
            relief=tk.FLAT, padx=8, pady=6,
        )
        self._feed.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        self._feed.tag_configure("time",    foreground=C_GRAY,  font=("Consolas", 9))
        self._feed.tag_configure("topic_t", foreground=C_RED,   font=("Consolas", 10, "bold"))
        self._feed.tag_configure("topic_h", foreground=C_GREEN, font=("Consolas", 10, "bold"))
        self._feed.tag_configure("sep",     foreground=C_BORDER)

        # Right panel
        right = tk.Frame(main, bg=C_BG, width=300)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        right.pack_propagate(False)

        self._latest_tele = self._latest_panel(right, "📡  Telemetry gần nhất", C_TELE_BG)
        self._latest_hb   = self._latest_panel(right, "💓  Heartbeat gần nhất", C_HB_BG)
        self._build_config_panel(right)

    def _latest_panel(self, parent, title, bg):
        f = tk.LabelFrame(parent, text=title,
                          font=("Segoe UI", 9, "bold"), fg=C_RED, bg=C_BG,
                          relief="solid", bd=1, labelanchor="n")
        f.pack(fill=tk.X, pady=(0, 8))
        t = scrolledtext.ScrolledText(f, wrap=tk.WORD, state=tk.DISABLED,
                                      font=("Consolas", 9), bg=bg, fg=C_TEXT,
                                      height=8, relief=tk.FLAT, padx=6, pady=4)
        t.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        return t

    def _build_config_panel(self, parent):
        f = tk.LabelFrame(parent, text="⚙  Cấu hình kết nối",
                          font=("Segoe UI", 9, "bold"), fg=C_RED, bg=C_BG,
                          relief="solid", bd=1, labelanchor="n")
        f.pack(fill=tk.BOTH, expand=True)
        self._cfg_vars = {}
        for label, key in [("Host", "host"), ("Port", "port"),
                            ("Client ID", "client_id"), ("Keepalive", "keepalive")]:
            row = tk.Frame(f, bg=C_BG)
            row.pack(fill=tk.X, padx=8, pady=3)
            tk.Label(row, text=label + ":", font=("Segoe UI", 9),
                     fg=C_GRAY, bg=C_BG, width=10, anchor="w").pack(side=tk.LEFT)
            var = tk.StringVar(value=str(self.config[key]))
            self._cfg_vars[key] = var
            tk.Entry(row, textvariable=var, font=("Consolas", 9),
                     fg=C_TEXT, bg=C_WHITE, relief="solid", bd=1
                     ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._btn(f, "💾 Áp dụng & Reconnect", self._apply_config,
                  C_RED, C_WHITE).pack(fill=tk.X, padx=8, pady=(6, 8))

    # ── Bottom bar ────────────────────────────────────────────────────────────
    def _build_bottom_bar(self):
        bb = tk.Frame(self.root, bg=C_WHITE,
                      highlightthickness=1, highlightbackground=C_BORDER)
        bb.pack(fill=tk.X, side=tk.BOTTOM)
        self._time_var = tk.StringVar()
        tk.Label(bb, textvariable=self._time_var,
                 font=("Consolas", 9), fg=C_GRAY, bg=C_WHITE).pack(side=tk.LEFT, padx=12, pady=4)
        tk.Label(bb, text="© PTIT — Học viện Công nghệ Bưu chính Viễn thông",
                 font=("Segoe UI", 9), fg=C_GRAY, bg=C_WHITE).pack(side=tk.RIGHT, padx=12, pady=4)
        self._tick()

    def _tick(self):
        self._time_var.set("🕐  " + datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
        self.root.after(1000, self._tick)

    # ── Helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _btn(parent, text, cmd, bg=C_WHITE, fg=C_TEXT, relief="flat", w=None):
        kw = {"width": w} if w else {}
        return tk.Button(parent, text=text, command=cmd,
                         font=("Segoe UI", 9, "bold"),
                         bg=bg, fg=fg, activebackground=C_RED_DARK,
                         activeforeground=C_WHITE, relief=relief,
                         cursor="hand2", bd=1, padx=8, pady=4, **kw)

    def _set_status(self, state, msg):
        colors = {"connected": C_GREEN, "connecting": C_ORANGE,
                  "disconnected": C_GRAY, "error": C_RED}
        c = colors.get(state, C_GRAY)
        self._dot.config(fg=c)
        self._status_var.set(msg)
        self._status_lbl.config(fg=c)

    # ── Messages ──────────────────────────────────────────────────────────────
    def _display_message(self, topic, payload_bytes):
        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        try:
            data   = json.loads(payload_bytes.decode("utf-8"))
            pretty = json.dumps(data, indent=self.config["json_indent"], ensure_ascii=False)
        except Exception:
            pretty = payload_bytes.decode("utf-8", errors="replace")

        self.buf.append((ts, topic, pretty))
        if len(self.buf) > self.config["max_messages"]:
            self.buf.pop(0)

        self.counts["total"] += 1
        if topic == TOPIC_TELEMETRY:
            self.counts["telemetry"] += 1
            self._update_latest(self._latest_tele, ts, pretty)
        else:
            self.counts["heartbeat"] += 1
            self._update_latest(self._latest_hb, ts, pretty)

        self._lbl_total.config(text=f"Tổng: {self.counts['total']}")
        self._lbl_tele.config(text=f"Telemetry: {self.counts['telemetry']}")
        self._lbl_hb.config(text=f"Heartbeat: {self.counts['heartbeat']}")

        self._feed.config(state=tk.NORMAL)
        self._feed.insert(tk.END, f"[{ts}]  ", "time")
        tag = "topic_t" if topic == TOPIC_TELEMETRY else "topic_h"
        self._feed.insert(tk.END, topic + "\n", tag)
        self._feed.insert(tk.END, pretty + "\n")
        self._feed.insert(tk.END, "─" * 60 + "\n", "sep")
        self._feed.config(state=tk.DISABLED)
        if self.auto_scroll.get():
            self._feed.see(tk.END)

    def _update_latest(self, widget, ts, pretty):
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, f"[{ts}]\n{pretty}")
        widget.config(state=tk.DISABLED)

    # ── Button actions ────────────────────────────────────────────────────────
    def _do_connect(self):
        self.mqtt.connect(self.config)

    def _do_reconnect(self):
        self.mqtt.disconnect()
        self.root.after(500, lambda: self.mqtt.connect(self.config))

    def _do_disconnect(self):
        self.mqtt.disconnect()

    def _apply_config(self):
        try:
            self.config["host"]      = self._cfg_vars["host"].get().strip()
            self.config["port"]      = int(self._cfg_vars["port"].get())
            self.config["client_id"] = self._cfg_vars["client_id"].get().strip()
            self.config["keepalive"] = int(self._cfg_vars["keepalive"].get())
        except ValueError as e:
            messagebox.showerror("Lỗi cấu hình", str(e))
            return
        self._do_reconnect()

    def _clear(self):
        self._feed.config(state=tk.NORMAL)
        self._feed.delete("1.0", tk.END)
        self._feed.config(state=tk.DISABLED)
        self.buf.clear()
        self.counts = {"total": 0, "telemetry": 0, "heartbeat": 0}
        self._lbl_total.config(text="Tổng: 0")
        self._lbl_tele.config(text="Telemetry: 0")
        self._lbl_hb.config(text="Heartbeat: 0")

    def _save_log(self):
        if not self.buf:
            messagebox.showinfo("Lưu log", "Chưa có tin nhắn nào.")
            return
        ts_file = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(os.path.dirname(__file__), f"mqtt_log_{ts_file}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump([{"time": t, "topic": top, "payload": p}
                       for t, top, p in self.buf], f, ensure_ascii=False, indent=2)
        messagebox.showinfo("Đã lưu", f"File: {path}")


# ═══════════════════════════════════════════════════════════════════════════════
def main():
    root = tk.Tk()
    try:
        style = ttk.Style(root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass

    app = PTITMQTTApp(root)

    def on_closing():
        try:
            app.mqtt.disconnect()
        except Exception:
            pass
        root.destroy()
        sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
