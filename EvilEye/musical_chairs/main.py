import os
import time
import random
import threading
import socket
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from dataclasses import dataclass, field
from typing import List, Tuple

# ==============================================================================
# --- Configurații Globale (Înlocuiesc config_eye.py) ---
# ==============================================================================
PORT_SEND = 4626 # Portul de control lumini (Simulator IN)
PORT_RECV = 7800 # Portul de recepție butoane (Simulator OUT)

COLORS = {
    "EYE_OPEN": (255, 0, 0),    # Roșu (Ochi deschis)
    "EYE_CLOSED": (0, 40, 0),   # Verde stins (Ochi închis)
    "POINT": (0, 255, 255),     # Cyan (Punct bonus)
    "OFF": (0, 0, 0)
}

# ==============================================================================
# --- Logica de Rețea (Conform snippet-ului tău) ---
# ==============================================================================
PASSWORD_ARRAY = [
    35, 63, 187, 69, 107, 178, 92, 76, 39, 69, 205, 37, 223, 255, 165, 231,
    16, 220, 99, 61, 25, 203, 203, 155, 107, 30, 92, 144, 218, 194, 226, 88,
    196, 190, 67, 195, 159, 185, 209, 24, 163, 65, 25, 172, 126, 63, 224, 61,
    160, 80, 125, 91, 239, 144, 25, 141, 183, 204, 171, 188, 255, 162, 104, 225,
    186, 91, 232, 3, 100, 208, 49, 211, 37, 192, 20, 99, 27, 92, 147, 152,
    86, 177, 53, 153, 94, 177, 200, 33, 175, 195, 15, 228, 247, 18, 244, 150,
    165, 229, 212, 96, 84, 200, 168, 191, 38, 112, 171, 116, 121, 186, 147, 203,
    30, 118, 115, 159, 238, 139, 60, 57, 235, 213, 159, 198, 160, 50, 97, 201,
    253, 242, 240, 77, 102, 12, 183, 235, 243, 247, 75, 90, 13, 236, 56, 133,
    150, 128, 138, 190, 140, 13, 213, 18, 7, 117, 255, 45, 69, 214, 179, 50,
    28, 66, 123, 239, 190, 73, 142, 218, 253, 5, 212, 174, 152, 75, 226, 226,
    172, 78, 35, 93, 250, 238, 19, 32, 247, 223, 89, 123, 86, 138, 150, 146,
    214, 192, 93, 152, 156, 211, 67, 51, 195, 165, 66, 10, 10, 31, 1, 198,
    234, 135, 34, 128, 208, 200, 213, 169, 238, 74, 221, 208, 104, 170, 166, 36,
    76, 177, 196, 3, 141, 167, 127, 56, 177, 203, 45, 107, 46, 82, 217, 139,
    168, 45, 198, 6, 43, 11, 57, 88, 182, 84, 189, 29, 35, 143, 138, 171
]

def calc_checksum(data):
    idx = sum(data) & 0xFF
    return PASSWORD_ARRAY[idx] if idx < len(PASSWORD_ARRAY) else 0

def build_fff0_packet(seq):
    payload = bytearray()
    for _ in range(4): payload += bytes([0x00, 0x0B])
    internal = bytes([0x02, 0, 0, 0x88, 0x77, 0xFF, 0xF0, 0, len(payload)]) + payload
    hdr = bytes([0x75, 0, 0, (len(internal)>>8)&0xFF, len(internal)&0xFF])
    pkt = bytearray(hdr + internal)
    pkt[10], pkt[11] = (seq >> 8) & 0xFF, seq & 0xFF
    pkt.append(calc_checksum(pkt))
    return bytes(pkt)

# ==============================================================================
# --- Management Hardware (Conform snippet-ului tău) ---
# ==============================================================================
class EvilEyeHardware:
    def __init__(self):
        self.running = False
        self.eye_states = {w: False for w in range(1, 5)}
        self.button_states = {w: {l: False for l in range(11)} for w in range(1, 5)}
        self._led_states = {}
        self._seq = 0

    def connect(self, target_ip, is_physical):
        self.target_ip, self.is_physical = target_ip, is_physical
        self.send_port = PORT_SEND
        self.recv_port = PORT_RECV
        self.sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_send.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.running = True
        threading.Thread(target=self.input_listener, daemon=True).start()
        threading.Thread(target=self.output_streamer, daemon=True).start()

    def set_element(self, wall, led, color):
        self._led_states[(wall, led)] = color

    def output_streamer(self):
        while self.running:
            self._seq = (self._seq + 1) & 0xFFFF
            frame = bytearray(132) # 4 walls * 11 leds * 3 colors
            for (ch, led), (r, g, b) in self._led_states.items():
                ch_idx = ch - 1
                if 0 <= ch_idx < 4 and 0 <= led < 11:
                    # Logica de intercalare a culorilor conform simulatorului
                    frame[led * 12 + ch_idx] = r
                    frame[led * 12 + 4 + ch_idx] = g
                    frame[led * 12 + 8 + ch_idx] = b

            ep = (self.target_ip, self.send_port)
            try:
                # Trimitere pachet date simplificat pt simulator
                internal = bytes([0x02, 0, 0, 0x88, 0x77, 0, 1, 0, len(frame)]) + frame
                hdr = bytes([0x75, 0, 0, (len(internal)>>8)&0xFF, len(internal)&0xFF])
                pkt = bytearray(hdr + internal)
                pkt.append(calc_checksum(pkt))
                self.sock_send.sendto(pkt, ep)
            except: pass
            time.sleep(0.06)

    def input_listener(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try: sock.bind(("0.0.0.0", self.recv_port))
        except: return
        while self.running:
            try:
                data, _ = sock.recvfrom(1024)
                if len(data) >= 687 and data[0] == 0x88:
                    for ch in range(1, 5):
                        base = 2 + (ch - 1) * 171
                        for led in range(11):
                            is_pressed = (data[base + 1 + led] == 0xCC)
                            if led == 0: self.eye_states[ch] = is_pressed
                            else: self.button_states[ch][led] = is_pressed
            except: pass

# ==============================================================================
# --- Logica Jocului Evil Eye (Clasa Operator) ---
# ==============================================================================
class EvilEyeOperator:
    def __init__(self):
        self.hw = EvilEyeHardware()
        self.running = True
        self.score = 0
        self.lives = 5
        self.game_phase = "IDLE" # IDLE, SAFE, WATCHING
        self.hit_cooldown = 0
        
        self.bonus_points = [] # Lista de (wall, led, color, fade)
        self.loss_sound_played = False
        self.music_process = None

        self.setup_gui()
        threading.Thread(target=self.game_loop, daemon=True).start()

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("STAFF CONTROL - EVIL EYE")
        self.root.geometry("450x550")
        
        # Fereastra Scoreboard
        self.view = tk.Toplevel(self.root)
        self.view.title("SCOREBOARD")
        self.view.geometry("800x600")
        self.view.configure(bg="black")

        self.setup_staff_ui()
        self.setup_view_ui()

    def setup_staff_ui(self):
        tk.Label(self.root, text="👁️ EVIL EYE CONTROL", font=("Arial", 16, "bold")).pack(pady=20)
        self._ip_var = tk.StringVar(value="127.0.0.1")
        tk.Entry(self.root, textvariable=self._ip_var).pack()
        tk.Button(self.root, text="🔗 CONNECT TO SIMULATOR", command=self._connect).pack(pady=5)
        
        self.lbl_status = tk.Label(self.root, text="Status: Deconectat", fg="gray")
        self.lbl_status.pack()

        tk.Button(self.root, text="📁 Alege Muzica", command=self._sel_music).pack(pady=10)
        self.lbl_song = tk.Label(self.root, text="Nicio piesă", fg="blue"); self.lbl_song.pack()

        self.btn_play = tk.Button(self.root, text="▶️ PLAY (Safe)", bg="green", command=self._action_safe, state="disabled", height=2, width=20)
        self.btn_play.pack(pady=5)
        self.btn_stop = tk.Button(self.root, text="⏸️ STOP (Watching)", bg="red", command=self._action_watching, state="disabled", height=2, width=20)
        self.btn_stop.pack(pady=5)

    def setup_view_ui(self):
        tk.Label(self.view, text="EVIL EYE", font=("Impact", 80), bg="black", fg="red").pack(pady=30)
        self.lbl_score_v = tk.Label(self.view, text="SCOR: 0", font=("Arial", 60), bg="black", fg="white"); self.lbl_score_v.pack()
        self.lbl_lives_v = tk.Label(self.view, text="VIEȚI: 5", font=("Arial", 60), bg="black", fg="#ff4444"); self.lbl_lives_v.pack()
        self.lbl_msg_v = tk.Label(self.view, text="STANDBY", font=("Arial", 40), bg="black", fg="gray"); self.lbl_msg_v.pack(pady=40)

    def _connect(self):
        self.hw.connect(self._ip_var.get(), is_physical=False)
        self.lbl_status.config(text="✅ CONECTAT", fg="green")
        self.btn_play.config(state="normal")
        self.btn_stop.config(state="normal")

    def _sel_music(self):
        f = filedialog.askopenfilename()
        if f: self.music_file = f; self.lbl_song.config(text=os.path.basename(f))

    def _action_safe(self):
        self.game_phase = "SAFE"
        if hasattr(self, 'music_file'):
            if self.music_process: self.music_process.terminate()
            self.music_process = subprocess.Popen(["afplay", self.music_file])
        if not self.bonus_points: 
            for _ in range(10): self.spawn_point()

    def _action_watching(self):
        self.game_phase = "WATCHING"
        if self.music_process: 
            self.music_process.terminate()
            self.music_process = None

    def spawn_point(self):
        clrs = [(0,255,255), (255,0,255), (0,255,0), (255,255,0)]
        w, l = random.randint(1, 4), random.randint(1, 10)
        self.bonus_points.append({'wall': w, 'led': l, 'color': random.choice(clrs), 'fade': 0.0})

    def game_loop(self):
        while self.running:
            now = time.time()
            if self.game_phase != "IDLE":
                # 1. Update Fade puncte
                for p in self.bonus_points: p['fade'] = min(1.0, p['fade'] + 0.1)

                # 2. Verificare Colectare & Penalizare
                penalty = False
                for w in range(1, 5):
                    for l in range(1, 11):
                        if self.hw.button_states[w][l]:
                            # Colectare în faza SAFE
                            for p in self.bonus_points[:]:
                                if p['wall'] == w and p['led'] == l:
                                    self.score += 100
                                    self.bonus_points.remove(p)
                                    self.spawn_point()
                            # Penalizare în faza WATCHING
                            if self.game_phase == "WATCHING" and now > self.hit_cooldown:
                                penalty = True

                if penalty:
                    self.lives -= 1
                    self.hit_cooldown = now + 1.5
                    if self.lives <= 0: 
                        self.game_phase = "GAMEOVER"
                        self._play_loss()

            self._update_hardware()
            self._update_ui()
            time.sleep(0.05)

    def _update_hardware(self):
        eye_col = COLORS["EYE_OPEN"] if self.game_phase == "WATCHING" else COLORS["EYE_CLOSED"]
        for w in range(1, 5):
            self.hw.set_element(w, 0, eye_col)
            for l in range(1, 11): self.hw.set_element(w, l, (0,0,0))
        
        for p in self.bonus_points:
            c = p['color']
            f = p['fade']
            final_c = (int(c[0]*f), int(c[1]*f), int(c[2]*f))
            self.hw.set_element(p['wall'], p['led'], final_c)

    def _update_ui(self):
        self.lbl_score_v.config(text=f"SCOR: {self.score}")
        self.lbl_lives_v.config(text=f"VIEȚI: {max(0, self.lives)}")
        if self.game_phase == "SAFE": self.lbl_msg_v.config(text="CULEGE PUNCTELE!", fg="cyan")
        elif self.game_phase == "WATCHING": self.lbl_msg_v.config(text="NU TE MIȘCA! 👁️", fg="red")
        elif self.game_phase == "GAMEOVER": self.lbl_msg_v.config(text="JOC TERMINAT!", fg="white")

    def _play_loss(self):
        if not self.loss_sound_played:
            self.loss_sound_played = True
            m_dir = os.path.dirname(self.music_file)
            for f in os.listdir(m_dir):
                if "sad trombone" in f.lower():
                    subprocess.Popen(["afplay", os.path.join(m_dir, f)])
                    break

if __name__ == "__main__":
    app = EvilEyeOperator()
    app.root.mainloop()