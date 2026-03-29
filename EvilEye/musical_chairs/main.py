import os
import time
import random
import threading
import socket
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from dataclasses import dataclass, field
from typing import List, Tuple

# --- Inițializare Pygame (Suport pentru Resume) ---
HAS_PYGAME = False
try:
    import pygame
    pygame.mixer.init()
    HAS_PYGAME = True
except:
    print("[!] Eroare Pygame: Muzica nu va funcționa.")

# ==============================================================================
# --- Configurații Globale & Protocol ---
# ==============================================================================
PORT_SEND = 4626 
PORT_RECV = 7800 

COLORS = {
    "EYE_RED": (255, 0, 0),     # Ochiul care te vede
    "POINT_CYAN": (0, 255, 255),# Puncte bonus
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
# --- Clasa Hardware ---
# ==============================================================================
class EvilEyeHardware:
    def __init__(self):
        self.running = False
        self.eye_states = {w: False for w in range(1, 5)} 
        self.button_states = {w: {l: False for l in range(1, 11)} for w in range(1, 5)}
        self._led_states = {}
        self._seq = 0

    def connect(self, target_ip):
        self.target_ip = target_ip
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.running = True
        threading.Thread(target=self.input_listener, daemon=True).start()
        threading.Thread(target=self.output_streamer, daemon=True).start()

    def set_element(self, wall, led, color):
        self._led_states[(wall, led)] = color

    def output_streamer(self):
        while self.running:
            self._seq = (self._seq + 1) & 0xFFFF
            frame = bytearray(132) 
            for (ch, led), (r, g, b) in self._led_states.items():
                ch_idx = ch - 1
                if 0 <= ch_idx < 4 and 0 <= led < 11:
                    # Mapare G-R-B (Dacă culorile sunt inversate, schimbă r cu g aici)
                    frame[led * 12 + ch_idx] = g 
                    frame[led * 12 + 4 + ch_idx] = r
                    frame[led * 12 + 8 + ch_idx] = b

            ep = (self.target_ip, PORT_SEND)
            try:
                self.sock.sendto(build_packet(0x3344, self._seq), ep)
                time.sleep(0.005)
                fff0_pld = bytearray([0, 11] * 4)
                self.sock.sendto(build_packet(0x8877, self._seq, fff0_pld), ep)
                time.sleep(0.005)
                self.sock.sendto(build_packet(0x8877, 0, frame), ep)
                time.sleep(0.005)
                self.sock.sendto(build_packet(0x5566, self._seq), ep)
            except: pass
            time.sleep(0.05)

    def input_listener(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try: sock.bind(("0.0.0.0", PORT_RECV))
        except: return
        while self.running:
            try:
                data, _ = sock.recvfrom(2048)
                if len(data) >= 687 and data[0] == 0x88:
                    for ch in range(1, 5):
                        base = 2 + (ch - 1) * 171
                        for led in range(11):
                            val = (data[base + 1 + led] == 0xCC)
                            if led == 0: self.eye_states[ch] = val
                            else: self.button_states[ch][led] = val
            except: pass

# ==============================================================================
# --- Logica Operator & Joc ---
# ==============================================================================
class EvilEyeOperator:
    def __init__(self):
        self.running = True
        self.hw = EvilEyeHardware()
        self.score, self.lives = 0, 5
        self.game_phase = "IDLE"
        self.hit_cooldown = 0
        self.bonus_points = []
        self.music_file = None
        self.is_music_paused = False 
        self.loss_sound_played = False
        self.active_watching_wall = 0 

        self.root = tk.Tk()
        self.root.title("STAFF CONTROL - EVIL EYE")
        self.root.geometry("450x550")
        
        self.view = tk.Toplevel(self.root)
        self.view.title("SCOREBOARD")
        self.view.geometry("800x600")
        self.view.configure(bg="black")

        self.setup_staff_ui()
        self.setup_view_ui()
        threading.Thread(target=self.game_loop, daemon=True).start()

    def setup_staff_ui(self):
        tk.Label(self.root, text="👁️ EVIL EYE CONTROL", font=("Arial", 14, "bold")).pack(pady=15)
        self._ip_var = tk.StringVar(value="169.254.182.11")
        tk.Entry(self.root, textvariable=self._ip_var, width=20).pack()
        tk.Button(self.root, text="🔗 CONNECT", command=self._connect, bg="#34495e", fg="white").pack(pady=5)
        self.lbl_status = tk.Label(self.root, text="Status: Deconectat", fg="gray"); self.lbl_status.pack()

        ttk.Separator(self.root, orient="horizontal").pack(fill="x", pady=10)
        
        tk.Button(self.root, text="📁 Încarcă Muzica", command=self._sel_music).pack()
        self.lbl_song = tk.Label(self.root, text="Niciun fișier", fg="blue"); self.lbl_song.pack(pady=5)

        self.btn_play = tk.Button(self.root, text="▶️ PLAY (Safe Mode)", bg="#27ae60", fg="white", 
                                  command=self._action_safe, state="disabled", height=2, width=25)
        self.btn_play.pack(pady=5)
        
        self.btn_stop = tk.Button(self.root, text="⏸️ STOP (WATCHING)", bg="#c0392b", fg="white", 
                                  command=self._action_watching, state="disabled", height=2, width=25)
        self.btn_stop.pack(pady=5)

    def setup_view_ui(self):
        tk.Label(self.view, text="EVIL EYE", font=("Impact", 80), bg="black", fg="#ff3333").pack(pady=30)
        self.lbl_score_v = tk.Label(self.view, text="SCOR: 0", font=("Arial", 60), bg="black", fg="white"); self.lbl_score_v.pack()
        self.lbl_lives_v = tk.Label(self.view, text="VIEȚI: 5", font=("Arial", 60), bg="black", fg="#ff4444"); self.lbl_lives_v.pack()
        self.lbl_msg_v = tk.Label(self.view, text="STANDBY", font=("Arial", 40), bg="black", fg="#555555"); self.lbl_msg_v.pack(pady=40)

    def _connect(self):
        self.hw.connect(self._ip_var.get())
        self.lbl_status.config(text=f"✅ CONECTAT", fg="green")
        self.btn_play.config(state="normal"); self.btn_stop.config(state="normal")

    def _sel_music(self):
        f = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav")])
        if f: self.music_file = f; self.lbl_song.config(text=os.path.basename(f))

    def _action_safe(self):
        self.game_phase = "SAFE"
        self.active_watching_wall = 0 
        if HAS_PYGAME and self.music_file:
            if self.is_music_paused: pygame.mixer.music.unpause() 
            else:
                pygame.mixer.music.load(self.music_file)
                pygame.mixer.music.play(-1)
            self.is_music_paused = False
        if not self.bonus_points: [self.spawn_point() for _ in range(10)]

    def _action_watching(self):
        self.game_phase = "WATCHING"
        self.active_watching_wall = random.randint(1, 4) 
        if HAS_PYGAME:
            pygame.mixer.music.pause()
            self.is_music_paused = True

    def spawn_point(self):
        clrs = [(0,255,255), (255,0,255), (0,255,0), (255,255,0)]
        self.bonus_points.append({'wall': random.randint(1, 4), 'led': random.randint(1, 10), 
                                 'color': random.choice(clrs), 'fade': 0.0})

    def game_loop(self):
        while self.running:
            now = time.time()
            if self.game_phase in ["SAFE", "WATCHING"]:
                for p in self.bonus_points: p['fade'] = min(1.0, p['fade'] + 0.1)
                
                penalty = False
                for w in range(1, 5):
                    # Colectare puncte (toate butoanele active)
                    for l in range(1, 11):
                        if self.hw.button_states[w][l]:
                            for p in self.bonus_points[:]:
                                if p['wall'] == w and p['led'] == l:
                                    self.score += 100; self.bonus_points.remove(p); self.spawn_point()
                    
                    # LOGICA PENALIZARE - Doar peretele roșu are senzorul activ
                    if self.game_phase == "WATCHING" and w == self.active_watching_wall:
                        # Verificăm LED 0 (senzor) sau orice alt buton de pe acel perete
                        if self.hw.eye_states[w] or any(self.hw.button_states[w].values()):
                            penalty = True

                if penalty and now > self.hit_cooldown:
                    self.lives -= 1
                    self.hit_cooldown = now + 2.0
                    if self.lives <= 0: self.game_phase = "GAMEOVER"; self._play_loss()

            self._update_hardware()
            self.root.after(0, self._update_ui)
            time.sleep(0.05)

    def _update_hardware(self):
        for w in range(1, 5):
            # Ochiul este ROȘU doar pe peretele activ, restul sunt STINȘI
            if self.game_phase == "WATCHING" and w == self.active_watching_wall:
                eye_col = COLORS["EYE_RED"]
            else:
                eye_col = COLORS["OFF"]
            
            self.hw.set_element(w, 0, eye_col)
            for l in range(1, 11): self.hw.set_element(w, l, (0,0,0))
            
        for p in self.bonus_points:
            c, f = p['color'], p['fade']
            self.hw.set_element(p['wall'], p['led'], (int(c[0]*f), int(c[1]*f), int(c[2]*f)))

    def _update_ui(self):
        self.lbl_score_v.config(text=f"SCOR: {self.score}")
        self.lbl_lives_v.config(text=f"VIEȚI: {max(0, self.lives)}")
        if self.game_phase == "SAFE": 
            self.lbl_msg_v.config(text="CULEGE PUNCTELE!", fg="cyan")
        elif self.game_phase == "WATCHING": 
            self.lbl_msg_v.config(text=f"OCHI ACTIV: PERETE {self.active_watching_wall}! 👁️", fg="red")
        elif self.game_phase == "GAMEOVER": 
            self.lbl_msg_v.config(text="AI FOST PRINS!", fg="white")

    def _play_loss(self):
        if not self.loss_sound_played and self.music_file:
            self.loss_sound_played = True
            if HAS_PYGAME:
                pygame.mixer.music.stop()
                m_dir = os.path.dirname(self.music_file)
                try:
                    for f in os.listdir(m_dir):
                        if "sad trombone" in f.lower():
                            pygame.mixer.music.load(os.path.join(m_dir, f))
                            pygame.mixer.music.play(); break
                except: pass

if __name__ == "__main__":
    EvilEyeOperator().root.mainloop()