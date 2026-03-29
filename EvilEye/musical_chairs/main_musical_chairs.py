# main_musical_chairs.py
import os
import time
import random
import threading
import socket
import tkinter as tk
from tkinter import ttk, messagebox
import pygame 

from config_eye import *
from eye_io import EvilEyeHardware, run_discovery # Folosim funcția de discovery din eye_io
from audio_manager_eye import EyeAudioManager 
from ui_eye import EyeDashboardUI            

class MusicalChairsOperator:
    def __init__(self):
        self.hw = EvilEyeHardware() 
        self.audio = EyeAudioManager() 
        self.ui = EyeDashboardUI("MUSICAL CHAIRS") 
        
        # Protecție Audio
        self.mixer_works = False
        try:
            import pygame.mixer
            pygame.mixer.init()
            self.mixer_works = True
        except: self.mixer_works = False

        self.running = True
        self.score = 0
        self.lives = 5
        self.game_phase = "IDLE"   
        self.grid_colors = {}   
        self.revealed = set()   
        self.first_selection = None 
        self.watching_walls = []   
        self.grace_period_end = 0

        if not os.path.exists("music"): os.makedirs("music")
        self.ui.update_lives(self.lives)
        
        threading.Thread(target=self.game_loop, daemon=True).start()
        self.create_operator_controls()
        self.ui.run()

    def create_operator_controls(self):
        self.ctrl = tk.Toplevel()
        self.ctrl.title("Hardware Discovery & Play")
        self.ctrl.geometry("400x450")
        self.ctrl.configure(bg="#1a1a1a", padx=15, pady=15)

        # --- LOGICA DE DISCOVERY CARE A FUNCȚIONAT ---
        tk.Label(self.ctrl, text="1. CONECTARE HARDWARE", fg="white", bg="#1a1a1a", font=("Arial", 10, "bold")).pack(anchor="w")
        
        # Selector interfață (Ethernet/WiFi)
        self.iface_combo = ttk.Combobox(self.ctrl, state="readonly", width=40)
        self.iface_combo.pack(pady=5)
        self._refresh_ifaces()

        self.btn_discover = tk.Button(self.ctrl, text="🔍 DISCOVER DEVICE", bg="#2c3e50", fg="white", 
                                     command=self.do_discovery, font=("Arial", 9, "bold"))
        self.btn_discover.pack(fill=tk.X, pady=5)

        self.lbl_net_status = tk.Label(self.ctrl, text="Status: Deconectat", fg="gray", bg="#1a1a1a")
        self.lbl_net_status.pack()

        ttk.Separator(self.ctrl, orient='horizontal').pack(fill='x', pady=15)

        # --- LOGICA DE JOC ---
        tk.Label(self.ctrl, text="2. ALEGE MELODIA ȘI START", fg="white", bg="#1a1a1a", font=("Arial", 10, "bold")).pack(anchor="w")
        self.songs = [f for f in os.listdir("music") if f.endswith(('.mp3', '.wav'))]
        self.song_combo = ttk.Combobox(self.ctrl, values=self.songs, state="readonly")
        if self.songs: self.song_combo.current(0)
        self.song_combo.pack(fill=tk.X, pady=5)
        
        self.btn_start = tk.Button(self.ctrl, text="▶ START JOC", bg="#27ae60", fg="white",
                                   font=("Arial", 11, "bold"), command=self.operator_action_safe, height=2, state="disabled")
        self.btn_start.pack(fill=tk.X, pady=10)
        
        self.btn_stop = tk.Button(self.ctrl, text="👁 STOP (OCHI)", bg="#e74c3c", fg="white",
                                  command=self.operator_action_watching, height=2, state="disabled") 
        self.btn_stop.pack(fill=tk.X, pady=5)

    def _refresh_ifaces(self):
        import psutil
        ifaces = []
        for name, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET and addr.address != "127.0.0.1":
                    ifaces.append((name, addr.address))
        self.iface_list = ifaces
        self.iface_combo['values'] = [f"{n} ({a})" for n, a in ifaces]
        if ifaces: self.iface_combo.current(0)

    def do_discovery(self):
        idx = self.iface_combo.current()
        if idx < 0: return
        _, local_ip = self.iface_list[idx]
        
        self.lbl_net_status.config(text="Se caută hardware...", fg="orange")
        self.ctrl.update()
        
        # Apelăm funcția de discovery
        found_ip = run_discovery(local_ip, "255.255.255.255")
        
        if found_ip:
            self.lbl_net_status.config(text=f"✅ CONECTAT: {found_ip}", fg="#2ecc71")
            self.hw.target_ip = found_ip # CRITIC: Actualizăm IP-ul în serviciul de trimitere
            self.btn_start.config(state="normal")
            # Flash scurt de confirmare pe hardware
            for w in range(1, 5): self.hw.set_element(w, 0, (255, 255, 255))
            self.ctrl.after(500, lambda: [self.hw.set_element(w, 0, (0,0,0)) for w in range(1,5)])
        else:
            self.lbl_net_status.config(text="❌ NU S-A GĂSIT DISPOZITIV", fg="#e74c3c")

    def generate_pairs(self):
        self.grid_colors.clear()
        self.revealed.clear()
        all_coords = [(w, l) for w in range(1, 5) for l in range(1, 11)]
        random.shuffle(all_coords)
        selected_colors = random.sample(PAIR_COLORS, 5)
        for color in selected_colors:
            if len(all_coords) >= 2:
                self.grid_colors[all_coords.pop()] = color
                self.grid_colors[all_coords.pop()] = color

    def operator_action_safe(self):
        if self.game_phase == "SAFE": return
        self.game_phase = "SAFE"
        self.generate_pairs()
        self.ui.update_eye_status("sleeping")
        self.btn_stop.config(state="normal")
        self.btn_start.config(state="disabled")

    def operator_action_watching(self):
        if self.game_phase != "SAFE": return
        self.game_phase = "WATCHING"
        self.watching_walls = random.sample([1, 2, 3, 4], random.randint(1, 2))
        self.grace_period_end = time.time() + 0.5 
        self.audio.play("eye_open")
        self.ui.update_eye_status("active")
        self.btn_stop.config(state="disabled") 
        self.btn_start.config(state="normal") 

    def _update_hardware(self):
        """TRIMITEREA DATELOR CĂTRE LED-URI"""
        for w in range(1, 5):
            # 1. Ochiul (LED 0)
            eye_col = (255, 0, 0) if w in self.watching_walls and self.game_phase == "WATCHING" else (0,0,0)
            self.hw.set_element(w, 0, eye_col)
            
            # 2. Butoanele (LED 1-10)
            for i in range(1, 11):
                if (w, i) in self.revealed:
                    col = self.grid_colors.get((w, i), (0,0,0))
                elif (w, i) in self.grid_colors and self.game_phase == "SAFE":
                    col = COLORS["COVERED"] # Gri vizibil
                else:
                    col = (0, 0, 0)
                self.hw.set_element(w, i, col)

    def game_loop(self):
        while self.running:
            penalty = False
            if self.game_phase == "WATCHING" and time.time() > self.grace_period_end:
                for w in self.watching_walls:
                    if self.hw.eye_states[w]: penalty = True; break
            
            if not penalty and self.game_phase == "SAFE":
                for w in range(1, 5):
                    for l in range(1, 11):
                        if self.hw.button_states[w][l]:
                            self.handle_button_press(w, l)
                            time.sleep(0.1)
            
            if penalty:
                self.lives -= 1
                self.audio.play("damage")
                self.ui.update_lives(self.lives)
                self.game_phase = "IDLE"
                self.revealed.clear()
                self.ui.root.after(0, lambda: [self.btn_start.config(state="normal"), self.btn_stop.config(state="disabled")])

            self._update_hardware()
            time.sleep(0.05)

    def handle_button_press(self, w, l):
        if (w, l) not in self.grid_colors or (w, l) in self.revealed: return
        color = self.grid_colors[(w, l)]
        self.revealed.add((w, l))
        self.audio.play("flip")
        self.ui.set_feedback_color(color)

        if self.first_selection is None: self.first_selection = (w, l)
        else:
            w1, l1 = self.first_selection
            if self.grid_colors[(w1, l1)] == color:
                self.score += 20
                self.ui.update_score(self.score)
                self.audio.play("match")
                self.first_selection = None
            else:
                def flip_back(p1=(w1, l1), p2=(w, l)):
                    self.revealed.discard(p1); self.revealed.discard(p2)
                self.audio.play("wrong")
                self.ctrl.after(1000, flip_back)
                self.first_selection = None

if __name__ == "__main__":
    MusicalChairsOperator()