import tkinter as tk
import socket
import threading
import time
import struct
import json
import os

def _load_config():
    cfg_path = "config_game.json"
    defaults = {"send_port": 6767, "recv_port": 6766, "device_ip": "127.0.0.1"}
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r") as f:
                cfg = json.load(f)
                return {"send_port": cfg.get("recv_port", 6767), "recv_port": cfg.get("send_port", 6766), "device_ip": cfg.get("device_ip", "127.0.0.1")}
        except: pass
    return defaults

CONFIG = _load_config()
BOARD_WIDTH, BOARD_HEIGHT = 16, 32
NUM_CHANNELS, LEDS_PER_CHANNEL = 8, 64

class SandrunSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Matrix Simulator - Port: {CONFIG['recv_port']}")
        self.root.configure(bg="#1a1a1a")
        self.cell_size, self.running = 20, True
        self.frame_buffer = bytearray(NUM_CHANNELS * LEDS_PER_CHANNEL * 3)
        self.pressed_leds = set()
        
        self.canvas = tk.Canvas(root, width=BOARD_WIDTH*self.cell_size, height=BOARD_HEIGHT*self.cell_size, bg="black", highlightthickness=0)
        self.canvas.pack(padx=10, pady=10)
        self.rects = {(x, y): self.canvas.create_rectangle(x*self.cell_size, y*self.cell_size, (x+1)*self.cell_size, (y+1)*self.cell_size, fill="black", outline="#222") for y in range(BOARD_HEIGHT) for x in range(BOARD_WIDTH)}
        
        self.canvas.bind("<ButtonPress-1>", self.on_click); self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        self.sock_listen = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock_listen.bind(("0.0.0.0", CONFIG["recv_port"]))
        self.sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_send.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        threading.Thread(target=self.network_loop, daemon=True).start()

    def network_loop(self):
        while self.running:
            try:
                data, _ = self.sock_listen.recvfrom(2048)
                if data[0] == 0x75 and len(data) >= 12:
                    cmd = struct.unpack(">H", data[8:10])[0]
                    if cmd == 0x8877:
                        pkt_idx = struct.unpack(">H", data[10:12])[0]
                        if pkt_idx == 0xFFF0: continue # Fix: Ignoră pachetul FFF0
                        chunk = data[14:-2]
                        off = (pkt_idx - 1) * 984
                        self.frame_buffer[off:off+len(chunk)] = chunk
                    elif cmd == 0x5566: self.root.after(0, self.update_display)
            except: pass

    def update_display(self):
        for led_pos in range(LEDS_PER_CHANNEL):
            for ch in range(NUM_CHANNELS):
                off = led_pos * 24 + ch
                g, r, b = self.frame_buffer[off], self.frame_buffer[off+8], self.frame_buffer[off+16]
                row = led_pos // 16
                x = (led_pos % 16) if row % 2 == 0 else (15 - (led_pos % 16))
                y = ch * 4 + row
                if 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT:
                    self.canvas.itemconfig(self.rects[(x, y)], fill="#%02x%02x%02x" % (r, g, b))

    def on_click(self, event):
        x, y = int(event.x // self.cell_size), int(event.y // self.cell_size)
        if 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT:
            row_in_ch = y % 4
            led = (row_in_ch * 16 + x) if row_in_ch % 2 == 0 else (row_in_ch * 16 + (15 - x))
            self.pressed_leds.add((y // 4, led)); self.send_input()

    def on_release(self, event):
        self.pressed_leds.clear(); self.send_input()

    def send_input(self):
        pkt = bytearray(1373); pkt[0] = 0x88
        for ch, led in self.pressed_leds: pkt[2 + ch * 171 + 1 + led] = 0xCC
        pkt[-1] = sum(pkt[:-1]) & 0xFF
        self.sock_send.sendto(pkt, ("127.0.0.1", CONFIG["send_port"]))

if __name__ == "__main__":
    root = tk.Tk(); SandrunSimulator(root); root.mainloop()