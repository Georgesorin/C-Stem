# main_musical_chairs.py
import os
import time
import random
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import pygame 

from config_eye import *
from eye_io import EvilEyeHardware
from audio_manager_eye import EyeAudioManager 
from ui_eye import EyeDashboardUI            

class MusicalChairsOperator:
    def __init__(self):
        self.hw = EvilEyeHardware() 
        self.audio = EyeAudioManager() 
        self.ui = EyeDashboardUI("MUSICAL CHAIRS") 
        
        # Protecție Python 3.14
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
        
        # Logica Matching Pairs
        self.grid_colors = {}   
        self.revealed = set()   
        self.first_selection = None 
        
        self.watching_walls = []   
        self.grace_period_end = 0
        self.music_paused = False 

        if not os.path.exists("music"): os.makedirs("music")
        self.ui.update_lives(self.lives)
        
        threading.Thread(target=self.game_loop, daemon=True).start()
        self.create_operator_controls()
        self.ui.run()

   # main_musical_chairs.py - Secțiunea create_operator_controls actualizată
    def create_operator_controls(self):
        self.ctrl = tk.Toplevel()
        self.ctrl.title("Hardware Setup & Discovery")
        self.ctrl.geometry("450x500")
        self.ctrl.configure(bg="#1a1a1a", padx=15, pady=15)
        
        # 1. SELECTARE INTERFAȚĂ (Cea mai importantă parte din Team_collect)
        tk.Label(self.ctrl, text="1. ALEGE PLACA DE REȚEA (INTERFAȚA)", fg="white", bg="#1a1a1a", font=("Arial", 9, "bold")).pack(anchor="w")
        self.iface_var = tk.StringVar()
        self.iface_combo = ttk.Combobox(self.ctrl, textvariable=self.iface_var, state="readonly", width=45)
        self.iface_combo.pack(pady=5)
        self.refresh_interfaces()
        
        # 2. DISCOVERY (Butonul care "trezește" ochiul)
        tk.Label(self.ctrl, text="2. GĂSEȘTE DISPOZITIVUL", fg="white", bg="#1a1a1a", font=("Arial", 9, "bold")).pack(anchor="w", pady=(10,0))
        self.ip_var = tk.StringVar(value=TARGET_IP)
        ip_frame = tk.Frame(self.ctrl, bg="#1a1a1a")
        ip_frame.pack(fill="x", pady=5)
        tk.Entry(ip_frame, textvariable=self.ip_var, width=20).pack(side="left", padx=5)
        tk.Button(ip_frame, text="🔍 DISCOVER", command=self.discover_device, bg="#2c3e50", fg="white").pack(side="left")

        self.lbl_status = tk.Label(self.ctrl, text="Status: Ready", fg="gray", bg="#1a1a1a")
        self.lbl_status.pack(pady=5)

        ttk.Separator(self.ctrl, orient='horizontal').pack(fill='x', pady=15)

        # 3. CONTROL JOC
        tk.Label(self.ctrl, text="3. PORNEȘTE JOCUL", fg="white", bg="#1a1a1a", font=("Arial", 9, "bold")).pack(anchor="w")
        self.btn_start = tk.Button(self.ctrl, text="▶ START MUSICAL CHAIRS", bg="#27ae60", fg="white", font=("Arial", 11, "bold"), 
                                   command=self.operator_action_safe, height=2, state="disabled")
        self.btn_start.pack(fill="x", pady=10)

    def refresh_interfaces(self):
        """Folosește logica din Team_collect pentru a găsi IP-urile locale"""
        import psutil
        ifaces = []
        for name, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET and addr.address != "127.0.0.1":
                    ifaces.append((name, addr.address, "255.255.255.255")) # Simplificat broadcast
        
        self.iface_list = ifaces
        self.iface_combo['values'] = [f"{n} ({a})" for n, a, b in ifaces]
        if ifaces: self.iface_combo.current(0)

    def discover_device(self):
        """Logica de Discovery care îți confirmă conexiunea"""
        idx = self.iface_combo.current()
        if idx < 0: return
        name, ip, bcast = self.iface_list[idx]
        
        self.lbl_status.config(text="Scanning network...", fg="orange")
        self.ctrl.update()
        
        from eye_io import run_discovery
        found_ip = run_discovery(ip, bcast)
        
        if found_ip:
            self.ip_var.set(found_ip)
            self.lbl_status.config(text=f"✅ CONNECTED TO {found_ip}", fg="#2ecc71")
            self.btn_start.config(state="normal")
            # Actualizăm IP-ul global pentru trimiterea de pachete
            import config_eye
            config_eye.TARGET_IP = found_ip
        else:
            self.lbl_status.config(text="❌ NO DEVICE FOUND. Check cable!", fg="#e74c3c")

   
    def _all_off(self):
        for w in range(1, 5):
            for l in range(0, 11): self.hw.set_element(w, l, (0, 0, 0))

    def generate_pairs(self):
        """Logica Matching: 5 perechi pe cei 4 pereți"""
        self.grid_colors.clear()
        self.revealed.clear()
        self.first_selection = None
        all_coords = [(w, l) for w in range(1, 5) for l in range(1, 11)]
        random.shuffle(all_coords)
        selected_colors = random.sample(PAIR_COLORS, 5)
        for color in selected_colors:
            if len(all_coords) >= 2:
                self.grid_colors[all_coords.pop()] = color
                self.grid_colors[all_coords.pop()] = color

    def operator_action_safe(self):
        if self.game_phase == "SAFE": return
        if self.mixer_works:
            if self.music_paused: pygame.mixer.music.unpause()
            else:
                sel = self.song_combo.get()
                if sel:
                    pygame.mixer.music.load(os.path.join("music", sel))
                    pygame.mixer.music.play()
            self.music_paused = False

        self.game_phase = "SAFE"
        self.generate_pairs()
        self.ui.update_eye_status("sleeping")
        self.btn_stop.config(state="normal")
        self.btn_start.config(state="disabled")

    def operator_action_watching(self):
        if self.game_phase != "SAFE": return
        self.game_phase = "WATCHING"
        if self.mixer_works:
            pygame.mixer.music.pause()
            self.music_paused = True
        self.watching_walls = random.sample([1, 2, 3, 4], random.randint(1, 2))
        self.grace_period_end = time.time() + 0.5 
        self.audio.play("eye_open")
        self.ui.update_eye_status("active")
        self.btn_stop.config(state="disabled") 
        self.btn_start.config(state="normal") 

    def _update_hardware(self):
        for w in range(1, 5):
            self.hw.set_element(w, 0, (255, 0, 0) if w in self.watching_walls and self.game_phase == "WATCHING" else (0,0,0))
            for i in range(1, 11):
                col = self.grid_colors.get((w, i), (0,0,0)) if (w, i) in self.revealed else (0,0,0)
                self.hw.set_element(w, i, col)

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
                if len(self.revealed) == len(self.grid_colors): self.ctrl.after(1000, self.generate_pairs)
            else:
                def flip_back(p1=(w1, l1), p2=(w, l)):
                    self.revealed.discard(p1); self.revealed.discard(p2)
                self.audio.play("wrong")
                self.ctrl.after(int(FLIP_BACK_TIME * 1000), flip_back)
                self.first_selection = None

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
                            time.sleep(0.2)
            if penalty:
                self.lives -= 1
                self.audio.play("damage")
                self.ui.update_lives(self.lives)
                self.game_phase = "IDLE"
                self.revealed.clear()
                self.ui.root.after(0, self.mc_auto_reset_to_safe)
                if self.lives <= 0: 
                    self.running = False
                    self.ui.show_game_over(self.score)
            self._update_hardware()
            time.sleep(0.05)

    def mc_auto_reset_to_safe(self):
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.ui.update_eye_status("sleeping")

if __name__ == "__main__":
    MusicalChairsOperator()