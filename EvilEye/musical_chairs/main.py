import os
import time
import random
import threading
import socket
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# --- Inițializare Pygame (Gestionare robustă a erorilor de Mixer) ---
HAS_PYGAME = False
try:
    import pygame
    # Încercăm să inițializăm mixerul separat
    pygame.mixer.init()
    HAS_PYGAME = True
except Exception as e:
    print(f"[!] Mixerul audio nu a putut fi pornit (Resume/Pause indisponibil): {e}")

# ==============================================================================
# --- Configurații Porturi Hardware ---
# ==============================================================================
PORT_SEND = 4626 
PORT_RECV = 7800 

COLORS = {
    "EYE_RED": (255, 0, 0),      
    "TARGET_CYAN": (0, 255, 255), 
    "OFF": (0, 0, 0)
}

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
    return PASSWORD_ARRAY[sum(data) & 0xFF]

def build_packet(cmd, seq, payload=b""):
    internal = bytearray([0x02, 0, 0, (cmd >> 8) & 0xFF, cmd & 0xFF, 0, 0, (len(payload) >> 8) & 0xFF, len(payload) & 0xFF]) + payload
    hdr = bytearray([0x75, random.randint(0, 127), random.randint(0, 127), (len(internal) >> 8) & 0xFF, len(internal) & 0xFF])
    pkt = hdr + internal
    pkt[10], pkt[11] = (seq >> 8) & 0xFF, seq & 0xFF
    pkt.append(calc_checksum(pkt))
    return pkt

# ==============================================================================
# --- Structuri Wall (10, 11, 12, 13) ---
# ==============================================================================
class Wall:
    def __init__(self, wall_id):
        self.wall_id = wall_id
        self.eye_open = False 
        self.active_led = -1 
        self.buttons = [False] * 11 

class EvilEyeHardware:
    def __init__(self):
        self.target_ip = "169.254.182.11"
        self.running = False
        self.walls = {id: Wall(id) for id in [10, 11, 12, 13]}
        self._seq = 0
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def connect(self, ip):
        self.target_ip = ip
        if not self.running:
            self.running = True
            threading.Thread(target=self.input_listener, daemon=True).start()

    def input_listener(self):
        recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try: recv_sock.bind(("0.0.0.0", PORT_RECV))
        except: return
        while self.running:
            try:
                data, _ = recv_sock.recvfrom(2048)
                if len(data) >= 687 and data[0] == 0x88:
                    for i, w_id in enumerate([10, 11, 12, 13]):
                        base = 2 + i * 171
                        for led in range(11):
                            self.walls[w_id].buttons[led] = (data[base + 1 + led] == 0xCC)
            except: pass

# ==============================================================================
# --- Logica Operator ---
# ==============================================================================
class EvilEyeOperator:
    def __init__(self):
        self.hw = EvilEyeHardware()
        self.running = True
        self.score, self.lives = 0, 5
        self.game_phase = "IDLE"
        self.hit_cooldown = 0
        self.music_file = None
        self.is_paused = False
        self.active_target = (None, None)

        self.root = tk.Tk()
        self.root.title("STAFF CONTROL - EVIL EYE")
        self.root.geometry("450x650")
        
        self.view = tk.Toplevel(self.root)
        self.view.title("SCOREBOARD")
        self.view.geometry("800x600")
        self.view.configure(bg="black")

        self.setup_staff_ui()
        self.setup_view_ui()
        threading.Thread(target=self.game_loop, daemon=True).start()

    def setup_staff_ui(self):
        tk.Label(self.root, text="👁️ EVIL EYE CONTROL", font=("Arial", 16, "bold")).pack(pady=20)
        
        conn_frame = tk.LabelFrame(self.root, text=" 1. Link Connection ", padx=10, pady=10)
        conn_frame.pack(padx=20, fill="x")
        
        tk.Label(conn_frame, text="Device IP:").pack(side=tk.LEFT)
        self.ip_entry = tk.Entry(conn_frame, width=15)
        self.ip_entry.insert(0, "169.254.182.11")
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Button(conn_frame, text="🔗 CONNECT", command=self._do_connect, bg="#34495e", fg="white").pack(side=tk.LEFT)
        
        self.lbl_status = tk.Label(self.root, text="Status: Deconectat", fg="gray")
        self.lbl_status.pack(pady=5)

        # FIX: Folosim ttk.Separator pentru a evita AttributeError
        ttk.Separator(self.root, orient="horizontal").pack(fill="x", pady=10)

        tk.Button(self.root, text="📁 Încarcă Muzica", command=self._sel_music).pack()
        self.lbl_song = tk.Label(self.root, text="Niciun fișier", fg="blue"); self.lbl_song.pack(pady=5)

        self.btn_play = tk.Button(self.root, text="▶️ START", bg="green", command=self._action_play, state="disabled", height=2, width=25)
        self.btn_play.pack(pady=5)
        self.btn_stop = tk.Button(self.root, text="⏸️ STOP", bg="red", command=self._action_pause, state="disabled", height=2, width=25)
        self.btn_stop.pack(pady=5)

    def setup_view_ui(self):
        tk.Label(self.view, text="EVIL EYE", font=("Impact", 80), bg="black", fg="red").pack(pady=20)
        self.lbl_scr = tk.Label(self.view, text="SCOR: 0", font=("Arial", 60), bg="black", fg="white"); self.lbl_scr.pack()
        self.lbl_lvs = tk.Label(self.view, text="VIEȚI: 5", font=("Arial", 60), bg="black", fg="#ff4444"); self.lbl_lvs.pack()
        self.lbl_msg = tk.Label(self.view, text="STANDBY", font=("Arial", 40), bg="black", fg="gray"); self.lbl_msg.pack(pady=40)

    def _do_connect(self):
        ip = self.ip_entry.get()
        self.hw.connect(ip)
        self.lbl_status.config(text=f"✅ CONECTAT LA {ip}", fg="green")
        self.btn_play.config(state="normal")
        self.btn_stop.config(state="normal")

    def _sel_music(self):
        f = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav")])
        if f: self.music_file = f; self.lbl_song.config(text=os.path.basename(f))

    def _spawn_target(self):
        for w in self.hw.walls.values(): w.active_led = -1; w.eye_open = False
        w_id = random.choice([10, 11, 12, 13])
        l_id = random.randint(0, 10)
        self.active_target = (w_id, l_id)
        if l_id == 0: self.hw.walls[w_id].eye_open = True
        else: self.hw.walls[w_id].active_led = l_id

    def _action_play(self):
        self.game_phase = "SAFE"
        if HAS_PYGAME and self.music_file:
            if self.is_paused: pygame.mixer.music.unpause() 
            else:
                pygame.mixer.music.load(self.music_file)
                pygame.mixer.music.play(-1)
            self.is_paused = False
        self._spawn_target()

    def _action_pause(self):
        self.game_phase = "WATCHING"
        if HAS_PYGAME:
            pygame.mixer.music.pause()
            self.is_paused = True
        for w in self.hw.walls.values(): w.active_led = -1; w.eye_open = False
        w_id = random.choice([10, 11, 12, 13])
        self.hw.walls[w_id].eye_open = True
        self.active_target = (w_id, 0)

    def game_loop(self):
        while self.running:
            now = time.time()
            if self.game_phase == "SAFE":
                w_id, l_id = self.active_target
                if w_id and self.hw.walls[w_id].buttons[l_id]:
                    self.score += 100
                    self.hw.walls[w_id].buttons[l_id] = False 
                    self._spawn_target()
            elif self.game_phase == "WATCHING":
                w_id, _ = self.active_target
                if self.hw.walls[w_id].buttons[0] and now > self.hit_cooldown:
                    self.lives -= 1
                    self.hit_cooldown = now + 2.0

            self._update_hardware()
            self.root.after(0, self._update_ui)
            time.sleep(0.05)

    def _update_hardware(self):
        if not self.hw.running: return
        self.hw._seq = (self.hw._seq + 1) & 0xFFFF
        frame = bytearray(132)
        for l in range(11):
            for i, w_id in enumerate([10, 11, 12, 13]):
                color = COLORS["OFF"]
                wall = self.hw.walls[w_id]
                if l == 0 and wall.eye_open:
                    color = COLORS["EYE_RED"] if self.game_phase == "WATCHING" else COLORS["TARGET_CYAN"]
                elif l == wall.active_led:
                    color = COLORS["TARGET_CYAN"]
                
                frame[l * 12 + i] = color[1] # G
                frame[l * 12 + 4 + i] = color[0] # R
                frame[l * 12 + 8 + i] = color[2] # B

        try:
            ep = (self.hw.target_ip, PORT_SEND)
            self.hw.sock.sendto(build_packet(0x3344, self.hw._seq), ep)
            self.hw.sock.sendto(build_packet(0x8877, self.hw._seq, bytearray([0, 11]*4)), ep)
            self.hw.sock.sendto(build_packet(0x8877, 0, frame), ep)
            self.hw.sock.sendto(build_packet(0x5566, self.hw._seq), ep)
        except: pass

    def _update_ui(self):
        self.lbl_scr.config(text=f"SCOR: {self.score}")
        self.lbl_lvs.config(text=f"VIEȚI: {max(0, self.lives)}")
        if self.game_phase == "SAFE": self.lbl_msg.config(text="CULEGE PUNCTELE!", fg="cyan")
        elif self.game_phase == "WATCHING": 
            w_id, _ = self.active_target
            self.lbl_msg.config(text=f"OCHI ACTIV: WALL {w_id}!", fg="red")

if __name__ == "__main__":
    EvilEyeOperator().root.mainloop()