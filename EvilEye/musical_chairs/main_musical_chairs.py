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

    def create_operator_controls(self):
        self.ctrl = tk.Toplevel()
        self.ctrl.title("Control Hardware")
        self.ctrl.geometry("380x400")
        self.ctrl.attributes("-topmost", True) 
        self.ctrl.configure(padx=10, pady=10)

        # Buton Verificare Rețea
        tk.Label(self.ctrl, text="PAS 1: TESTARE CONEXIUNE", font=("Arial", 9, "bold")).pack(pady=5)
        self.btn_check = tk.Button(self.ctrl, text="🔍 CHECK CONNECTION (Flash All)", 
                                   bg="#333", fg="white", font=("Arial", 10, "bold"),
                                   command=self.check_connection_flash)
        self.btn_check.pack(fill=tk.X, pady=5)

        ttk.Separator(self.ctrl, orient='horizontal').pack(fill='x', pady=10)

        tk.Label(self.ctrl, text="PAS 2: ALEGEȚI MELODIA", font=("Arial", 9, "bold")).pack(pady=5)
        self.songs = [f for f in os.listdir("music") if f.endswith(('.mp3', '.wav'))]
        self.song_combo = ttk.Combobox(self.ctrl, values=self.songs, state="readonly")
        if self.songs: self.song_combo.current(0)
        self.song_combo.pack(fill=tk.X, pady=5)
        
        self.btn_start = tk.Button(self.ctrl, text="▶ START JOC (Muzică ON)", bg="#44bb44", fg="white",
                                   font=("Arial", 11, "bold"), command=self.operator_action_safe, height=2)
        self.btn_start.pack(fill=tk.X, pady=10)
        
        self.btn_stop = tk.Button(self.ctrl, text="👁 PAUZĂ (Ochi ROȘU)", bg="#ff4444", fg="white",
                                  font=("Arial", 11, "bold"), command=self.operator_action_watching, height=2, state="disabled") 
        self.btn_stop.pack(fill=tk.X, pady=5)

    def check_connection_flash(self):
        """Trimite un semnal de test: toți pereții se aprind ALB timp de 1 secundă"""
        print(f">>> Trimitere test către {TARGET_IP}:{PORT_SEND}...")
        for w in range(1, 5):
            for l in range(0, 11): self.hw.set_element(w, l, (255, 255, 255))
        
        # Verificăm dacă primim ceva de la senzori
        if any(self.hw.eye_states.values()) or any(any(w) for w in self.hw.button_states.values()):
            messagebox.showinfo("Conexiune", "Hardware-ul răspunde! Senzorii sunt activi.")
        
        self.ctrl.after(1000, self._all_off)

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