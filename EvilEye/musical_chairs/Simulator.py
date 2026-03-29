import tkinter as tk
from tkinter import ttk
import socket
import threading
import time
import json
import os
import psutil
from datetime import datetime

# --- Configuration ---
_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eye_sim_config.json")

def _load_config():
    defaults = {"send_port": 7800, "recv_port": 4626, "device_ip": "127.0.0.1"}
    if os.path.exists(_CONFIG_FILE):
        try:
            with open(_CONFIG_FILE, encoding="utf-8") as f:
                defaults.update(json.load(f))
        except: pass
    return defaults

CONFIG = _load_config()
NUM_CHANNELS = 4
LEDS_PER_CHANNEL = 11

class WallCanvas(tk.Canvas):
    LAYOUT_ROWS, LAYOUT_COLS = 3, 5

    def __init__(self, parent, channel, on_press, on_release, **kwargs):
        super().__init__(parent, bg="#111", highlightthickness=0, **kwargs)
        self._ch = channel
        self._on_press = on_press
        self._on_rel = on_release
        self._colors = [(0, 0, 0)] * LEDS_PER_CHANNEL
        self._items = {}
        self.bind("<Configure>", self._redraw)
        self.bind("<ButtonPress-1>", self._click_press)
        self.bind("<ButtonRelease-1>", self._click_release)

    def set_color(self, index, r, g, b):
        self._colors[index] = (r, g, b)
        self._apply_color(index)

    def _apply_color(self, index):
        if index not in self._items: return
        iid = self._items[index]
        r, g, b = self._colors[index]
        fill = f"#{r:02x}{g:02x}{b:02x}" if (r or g or b) else ("black" if index == 0 else "#0a0a0a")
        self.itemconfig(iid, fill=fill)
        if index == 0:
            self.itemconfig(iid, outline=(fill if (r or g or b) else "#ff0000"))

    def _cell_rect(self, idx, w, h, pad):
        cell_w, cell_h = (w - 2 * pad) / self.LAYOUT_COLS, (h - 2 * pad) / self.LAYOUT_ROWS
        if idx == 0:
            cx, cy = w / 2, pad + cell_h * 0.5
            r = min(cell_w, cell_h) * 0.38
            return (cx - r, cy - r, cx + r, cy + r)
        else:
            btn = idx - 1
            row, col = btn // 5 + 1, btn % 5
            x1, y1 = pad + col * cell_w + cell_w * 0.08, pad + row * cell_h + cell_h * 0.08
            return (x1, y1, x1 + cell_w * 0.84, y1 + cell_h * 0.84)

    def _redraw(self, event=None):
        self.delete("all"); self._items.clear()
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10: return
        pad = max(6, min(w, h) * 0.04)
        
        x1, y1, x2, y2 = self._cell_rect(0, w, h, pad)
        halo = max(4, (x2 - x1) * 0.12)
        self.create_oval(x1 - halo, y1 - halo, x2 + halo, y2 + halo, fill="#111", outline="#333", width=1)
        self._items[0] = self.create_oval(x1, y1, x2, y2, fill="black", outline="#ff0000", width=max(2, halo * 0.5))

        for i in range(1, 11):
            x1, y1, x2, y2 = self._cell_rect(i, w, h, pad)
            self._items[i] = self.create_rectangle(x1, y1, x2, y2, fill="#0a0a0a", outline="#333")
            self._apply_color(i)
        self._apply_color(0)

    def _hit_test(self, x, y):
        w, h = self.winfo_width(), self.winfo_height()
        pad = max(6, min(w, h) * 0.04)
        for idx in range(LEDS_PER_CHANNEL):
            x1, y1, x2, y2 = self._cell_rect(idx, w, h, pad)
            if x1 <= x <= x2 and y1 <= y <= y2: return idx
        return None

    def _click_press(self, event):
        idx = self._hit_test(event.x, event.y)
        if idx is not None: self._on_press(self._ch, idx)

    def _click_release(self, event):
        idx = self._hit_test(event.x, event.y)
        if idx is not None: self._on_rel(self._ch, idx)


class EvilEyeSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Evil Eye Simulator (Optimized)")
        self.root.configure(bg="#1a1a1a")

        self.pressed_leds = set()
        self._press_lock = threading.Lock()
        self._running = True
        
        # Buffer decuplat pentru randare fluidă
        self.display_colors = {c: {l: (0,0,0) for l in range(11)} for c in range(1, 5)}

        self.listen_port = CONFIG.get("recv_port", 4626)
        self.send_port = CONFIG.get("send_port", 7800)

        self._wall_canvases = {}
        self._build_ui()
        self._setup_network()

        threading.Thread(target=self._network_loop, daemon=True).start()
        self.root.after(33, self._gui_render_loop) # Loop fix la 30 FPS

    def _build_ui(self):
        pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#1a1a1a")
        pane.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(pane, bg="#1a1a1a")
        pane.add(left, stretch="always")
        for ch in range(1, 5):
            row, col = (ch - 1) // 2, (ch - 1) % 2
            left.grid_rowconfigure(row, weight=1); left.grid_columnconfigure(col, weight=1)
            wf = tk.LabelFrame(left, text=f" WALL {ch} ", bg="#1a1a1a", fg="#ff4444")
            wf.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            cv = WallCanvas(wf, ch, self._on_press, self._on_release)
            cv.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
            self._wall_canvases[ch] = cv

    def _on_press(self, channel, index):
        with self._press_lock: self.pressed_leds.add((channel, index))
        self._send_trigger_packet()

    def _on_release(self, channel, index):
        with self._press_lock: self.pressed_leds.discard((channel, index))
        self._send_trigger_packet()

    def _setup_network(self):
        self._sock_listen = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock_listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock_listen.bind(("0.0.0.0", self.listen_port))
        
        self._sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _network_loop(self):
        while self._running:
            try: 
                data, _ = self._sock_listen.recvfrom(2048)
                if data[0] == 0x75 and len(data) > 10:
                    cmd = (data[8] << 8) | data[9]
                    if cmd == 0x8877:
                        msg_loc = (data[10] << 8) | data[11]
                        if msg_loc != 0xFFF0:
                            frame = data[14:-2]
                            self._decode_frame(frame)
            except: pass

    def _decode_frame(self, frame):
        # Decodează pachetul de 132 bytes intercalat
        for led in range(11):
            for ch in range(4):
                off = led * 12 + ch
                if off + 8 < len(frame):
                    g, r, b = frame[off], frame[off+4], frame[off+8]
                    self.display_colors[ch+1][led] = (r, g, b)

    def _gui_render_loop(self):
        # Aplică culorile o singură dată pe frame (elimină sacadarea)
        for c in range(1, 5):
            for l in range(11):
                self._wall_canvases[c].set_color(l, *self.display_colors[c][l])
        self.root.after(33, self._gui_render_loop)

    def _send_trigger_packet(self):
        pkt = bytearray(687); pkt[0], pkt[1] = 0x88, 0x01
        with self._press_lock: 
            for ch, idx in self.pressed_leds:
                # Offset 171 specific documentației
                pkt[2 + (ch-1)*171 + 1 + idx] = 0xCC 
        pkt[-1] = sum(pkt[:-1]) & 0xFF
        self._sock_send.sendto(pkt, ("127.0.0.1", self.send_port))

if __name__ == "__main__":
    root = tk.Tk(); root.geometry("600x500")
    app = EvilEyeSimulator(root); root.mainloop()