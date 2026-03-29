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
        
        # --- PROTECȚIE AUDIO PENTRU PYTHON 3.14 ---
        self.mixer_works = False
        try:
            import pygame.mixer
            pygame.mixer.init()
            self.mixer_works = True
        except (ImportError, NotImplementedError, Exception):
            self.mixer_works = False

        self.running = True
        self.score = 0
        self.lives = 5
        self.game_phase = "IDLE"   
        
        # Logica de Perechi (Matching)
        self.grid_colors = {}   # (wall, led) -> RGB
        self.revealed = set()   # Perechi găsite sau butoane active
        self.first_selection = None # Reține primul click dintr-o încercare
        
        self.watching_walls = []   
        self.grace_period_end = 0
        self.music_paused = False 

        if not os.path.exists("music"): os.makedirs("music")
        self.ui.update_lives(self.lives)
        
        threading.Thread(target=self.game_loop, daemon=True).start()
        self.create_operator_controls()
        self.ui.run()

    def get_local_songs(self):
        if not os.path.exists("music"): return []
        return [f for f in os.listdir("music") if f.endswith(('.mp3', '.wav', '.m4a'))]

    def create_operator_controls(self):
        self.ctrl = tk.Toplevel()
        self.ctrl.title("Control Joc")
        self.ctrl.geometry("350x300")
        self.ctrl.attributes("-topmost", True) 
        
        tk.Label(self.ctrl, text="ALEGEȚI MELODIA", font=("Arial", 10, "bold")).pack(pady=5)
        self.songs = self.get_local_songs()
        self.song_combo = ttk.Combobox(self.ctrl, values=self.songs, state="readonly")
        if self.songs: self.song_combo.current(0)
        self.song_combo.pack(fill=tk.X, padx=10, pady=5)
        
        self.btn_start = tk.Button(self.ctrl, text="▶ START (Muzică ON / Task PAIRS)", bg="#44bb44", command=self.operator_action_safe, height=3)
        self.btn_start.pack(fill=tk.X, padx=10, pady=5)
        
        self.btn_stop = tk.Button(self.ctrl, text="👁 STOP (Muzică OFF / FREEZE)", bg="#ff4444", command=self.operator_action_watching, height=3, state="disabled") 
        self.btn_stop.pack(fill=tk.X, padx=10, pady=5)

    def generate_pairs(self):
        """Generează 5 perechi de culori distribuite aleatoriu pe cei 4 pereți"""
        self.grid_colors.clear()
        self.revealed.clear()
        self.first_selection = None
        
        all_coords = [(w, l) for w in range(1, 5) for l in range(1, 11)]
        random.shuffle(all_coords)
        
        # Folosim culorile din PAIR_COLORS definite în config_eye.py
        selected_colors = random.sample(PAIR_COLORS, 5)
        
        for color in selected_colors:
            if len(all_coords) >= 2:
                c1 = all_coords.pop()
                c2 = all_coords.pop()
                self.grid_colors[c1] = color
                self.grid_colors[c2] = color

    def operator_action_safe(self):
        if self.game_phase == "SAFE": return
        
        if self.mixer_works:
            if self.music_paused: pygame.mixer.music.unpause()
            else:
                selected = self.song_combo.get()
                if selected:
                    try:
                        pygame.mixer.music.load(os.path.join("music", selected))
                        pygame.mixer.music.play()
                    except: pass
            self.music_paused = False

        self.game_phase = "SAFE"
        self.generate_pairs() # Inițializăm tabla de joc
        self.ui.update_eye_status("sleeping")
        self.ui.set_feedback_color(None)
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
            self.hw.set_element(w, 0, (0,0,0))
            for i in range(1, 11):
                # Afișăm LED-ul doar dacă este în setul 'revealed'
                color = self.grid_colors.get((w, i), (0,0,0)) if (w, i) in self.revealed else (0,0,0)
                self.hw.set_element(w, i, color)
        
        if self.game_phase == "WATCHING":
            for w in self.watching_walls:
                self.hw.set_element(w, 0, (255, 0, 0))

    def handle_button_press(self, w, l):
        """Logica de Matching: Deschide un buton și verifică dacă se potrivește cu precedentul"""
        if (w, l) not in self.grid_colors or (w, l) in self.revealed:
            return

        color = self.grid_colors[(w, l)]
        self.revealed.add((w, l))
        self.audio.play("flip") # Sunet de întoarcere
        self.ui.set_feedback_color(color) # Afișăm culoarea pe Dashboard

        if self.first_selection is None:
            self.first_selection = (w, l)
        else:
            w1, l1 = self.first_selection
            if self.grid_colors[(w1, l1)] == color:
                # MATCH!
                self.score += 20
                self.ui.update_score(self.score)
                self.audio.play("match")
                self.first_selection = None
                # Dacă s-au găsit toate, regenerăm
                if len(self.revealed) == len(self.grid_colors):
                    self.root.after(1000, self.generate_pairs)
            else:
                # GREȘIT! Le închidem după FLIP_BACK_TIME
                def flip_back(p1=(w1, l1), p2=(w, l)):
                    self.revealed.discard(p1)
                    self.revealed.discard(p2)
                    self._update_hardware()
                
                self.audio.play("wrong")
                self.root.after(int(FLIP_BACK_TIME * 1000), flip_back)
                self.first_selection = None

    def game_loop(self):
        while self.running:
            penalty = False
            # 1. Senzor mișcare (Watching)
            if self.game_phase == "WATCHING" and time.time() > self.grace_period_end:
                for w in self.watching_walls:
                    if self.hw.eye_states[w]: penalty = True; break
            
            # 2. Apăsări butoane (Safe)
            if not penalty and self.game_phase == "SAFE":
                for w in range(1, 5):
                    for l in range(1, 11):
                        if self.hw.button_states[w][l]:
                            self.handle_button_press(w, l)
                            time.sleep(0.2) # Debounce
            
            # 3. Penalizare
            if penalty:
                self.lives -= 1
                self.audio.play("damage")
                self.ui.update_lives(self.lives)
                self.game_phase = "IDLE"
                self.revealed.clear() # Resetăm progresul la lovitură
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