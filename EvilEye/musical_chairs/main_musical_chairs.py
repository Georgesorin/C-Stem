# main_musical_chairs.py
import os
import time
import random
import threading
import subprocess
import psutil
import tkinter as tk
from tkinter import ttk, messagebox

from config_eye import *
from eye_io import EvilEyeHardware
from audio_manager_eye import EyeAudioManager 
from ui_eye import EyeDashboardUI            

class MusicalChairsOperator:
    def __init__(self):
        self.hw = EvilEyeHardware() 
        self.audio = EyeAudioManager() 
        self.ui = EyeDashboardUI("MUSICAL CHAIRS") 
        
        self.running = True
        self.score = 0
        self.lives = 5
        self.game_phase = "IDLE"   
        self.active_targets = {}   
        self.watching_walls = []   
        self.grace_period_end = 0
        
        self.music_paused = False 
        self.current_player = None # Gestionăm procesul mpv direct aici

        # Ne asigurăm că folderul "music" există (așa cum l-ai numit)
        if not os.path.exists("music"):
            os.makedirs("music")

        self.ui.update_lives(self.lives)
        if hasattr(self.ui, 'update_score'): self.ui.update_score(0)
        
        threading.Thread(target=self.game_loop, daemon=True).start()
        self.create_operator_controls()
        self.ui.run()

    def get_local_songs(self):
        """Citește toate fișierele mp3/wav din folderul 'music'"""
        if not os.path.exists("music"): return []
        return [f for f in os.listdir("music") if f.endswith(('.mp3', '.wav', '.m4a'))]

    def create_operator_controls(self):
        self.ctrl = tk.Toplevel()
        self.ctrl.title("Control Operator Musical Chairs")
        self.ctrl.geometry("350x300")
        self.ctrl.attributes("-topmost", True) 
        self.ctrl.configure(padx=10, pady=10)
        
        tk.Label(self.ctrl, text="1. ALEGEȚI MUZICA LOCALĂ", font=("Arial", 10, "bold")).pack(pady=(0, 5), anchor="w")
        
        self.songs = self.get_local_songs()
        self.song_combo = ttk.Combobox(self.ctrl, values=self.songs, state="readonly", font=("Arial", 10))
        if self.songs:
            self.song_combo.current(0)
        else:
            self.song_combo.set("Nicio melodie în folderul 'music'")
        self.song_combo.pack(fill=tk.X, pady=(0, 15))
        
        tk.Button(self.ctrl, text="🔄 Refresh Listă", command=self.refresh_song_list, font=("Arial", 8)).pack(anchor="e")

        tk.Label(self.ctrl, text="2. CONTROL RUNDĂ", font=("Arial", 10, "bold")).pack(pady=(5, 5), anchor="w")
        
        self.btn_start = tk.Button(self.ctrl, text="▶ START / RELUARE\n(Muzică ON, Ochi OFF)", 
                                   bg="#44bb44", fg="white", font=("Arial", 10, "bold"),
                                   command=self.operator_action_safe, width=30, height=3)
        self.btn_start.pack(pady=5)
        
        self.btn_stop = tk.Button(self.ctrl, text="👁 PAUZĂ / ÎNGHEȚ\n(Muzică OFF, Ochi ON)", 
                                  bg="#ff4444", fg="white", font=("Arial", 10, "bold"),
                                  command=self.operator_action_watching, width=30, height=3,
                                  state="disabled") 
        self.btn_stop.pack(pady=5)

    def refresh_song_list(self):
        self.songs = self.get_local_songs()
        self.song_combo['values'] = self.songs
        if self.songs: self.song_combo.current(0)

    def stop_music(self):
        """Oprește definitiv procesul MPV"""
        if self.current_player:
            try:
                self.current_player.terminate()
                self.current_player.wait(timeout=1)
            except:
                try: self.current_player.kill()
                except: pass
            self.current_player = None

    # ─────────────────────────────────────────────────────────────────────────────
    # ACȚIUNI OPERATOR ȘI MUZICĂ LOCALĂ (via MPV + PSUTIL)
    # ─────────────────────────────────────────────────────────────────────────────

    def operator_action_safe(self):
        if getattr(self, 'game_phase', '') == "SAFE": return

        # --- GESTIONARE MUZICĂ ---
        if self.music_paused and self.current_player:
            # RELUARE: Dezghetăm procesul MPV
            try:
                p = psutil.Process(self.current_player.pid)
                p.resume()
                self.music_paused = False
                print(">>> SAFE PHASE: Muzica a fost RELUATĂ.")
            except Exception as e:
                print(f"Eroare la reluare: {e}")
        else:
            # PORNIRE NOUĂ a melodiei de la început
            selected_song = self.song_combo.get()
            if not selected_song or selected_song == "Nicio melodie în folderul 'music'":
                messagebox.showwarning("Atenție", "Adaugă un mp3 în folderul 'music'!")
                return
            
            song_path = os.path.join("music", selected_song)
            self.stop_music()
            try:
                # Pornim MPV cu fișierul local
                self.current_player = subprocess.Popen(["mpv", "--no-video", song_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.music_paused = False
                print(f">>> SAFE PHASE: Muzica a pornit: {selected_song}")
            except Exception as e:
                messagebox.showerror("Eroare Audio", f"Nu s-a putut reda cu mpv: {e}")
                return

        # Setări Fază Safe
        self.game_phase = "SAFE"
        self.watching_walls = []
        self.spawn_game_targets()
        
        self.ui.update_eye_status("sleeping")
        self.ui.set_feedback_color(None)
        
        self.btn_stop.config(state="normal")
        self.btn_start.config(state="disabled")

    def operator_action_watching(self):
        if getattr(self, 'game_phase', '') != "SAFE": return

        self.game_phase = "WATCHING"
        self.active_targets = {} 
        
        # --- PAUZĂ: Înghețăm procesul MPV ---
        if self.current_player:
            try:
                p = psutil.Process(self.current_player.pid)
                p.suspend()
                self.music_paused = True
            except Exception as e:
                print(f"Eroare la pauză: {e}")

        self.watching_walls = random.sample([1, 2, 3, 4], random.randint(1, 2))
        self.grace_period_end = time.time() + 0.5 
        
        self.audio.play("eye_open")
        self.ui.update_eye_status("active")
        
        self.btn_stop.config(state="disabled") 
        self.btn_start.config(state="normal") 

        print(f">>> WATCHING: Muzica e pe pauză. Pereți activi {self.watching_walls}. Freeze!")

    # ─────────────────────────────────────────────────────────────────────────────
    # LOGICĂ JOC ȘI HARDWARE
    # ─────────────────────────────────────────────────────────────────────────────

    def spawn_game_targets(self):
        self.active_targets = {}
        for w in range(1, NUM_WALLS + 1):
            leds = random.sample(range(1, 11), 2)
            for l in leds:
                self.active_targets[(w, l)] = random.choice(MC_TARGET_COLORS)

    def _update_hardware(self):
        for w in range(1, NUM_WALLS + 1):
            self.hw.set_element(w, 0, (0, 0, 0)) 
            for i in range(1, 11): self.hw.set_element(w, i, (0, 0, 0)) 

        if self.game_phase == "SAFE":
            for (w, l), color in self.active_targets.items():
                self.hw.set_element(w, l, color)
        elif self.game_phase == "WATCHING":
            for w in self.watching_walls:
                self.hw.set_element(w, 0, (255, 0, 0))

    def game_loop(self):
        while self.running:
            start_tick = time.time()
            penalty_triggered = False

            # 1. VERIFICĂM SENZORUL DE MIȘCARE (OCHIUL FIZIC)
            if self.game_phase == "WATCHING" and time.time() > self.grace_period_end:
                for w in self.watching_walls:
                    # Starea 'True' a eye_states înseamnă că senzorul a detectat mișcare
                    if self.hw.eye_states[w]: 
                        penalty_triggered = True
                        break

            # 2. VERIFICĂM BUTOANELE APĂSATE
            if not penalty_triggered:
                for w in range(1, NUM_WALLS + 1):
                    for l in range(1, 11):
                        if self.hw.button_states[w][l]: 
                            
                            # Când e safe, butoanele îți dau puncte
                            if self.game_phase == "SAFE":
                                if (w, l) in self.active_targets:
                                    self.score += 10
                                    self.ui.root.after(0, lambda c=self.active_targets[(w,l)]: self.ui.set_feedback_color(c))
                                    del self.active_targets[(w, l)]
                                    self.audio.play("match")
                                    if hasattr(self.ui, 'update_score'):
                                        self.ui.update_score(self.score)
                                    
                                    # Spawnează imediat un nou buton colorat
                                    new_w = random.randint(1, NUM_WALLS)
                                    new_l = random.randint(1, 10)
                                    while (new_w, new_l) in self.active_targets:
                                        new_w = random.randint(1, NUM_WALLS)
                                        new_l = random.randint(1, 10)
                                    self.active_targets[(new_w, new_l)] = random.choice(MC_TARGET_COLORS)
                            
                            # Dacă apeși un buton pe peretele interzis
                            elif self.game_phase == "WATCHING":
                                if w in self.watching_walls and time.time() > self.grace_period_end:
                                    penalty_triggered = True
                                    break
                    if penalty_triggered: break

            # 3. APLICĂM PENALIZAREA O SINGURĂ DATĂ
            if penalty_triggered and self.game_phase == "WATCHING":
                self.lives -= 1
                self.audio.play("damage")
                self.ui.update_lives(self.lives)
                self.game_phase = "IDLE" 
                self._update_hardware() 
                self.ui.root.after(0, self.mc_auto_reset_to_safe) 
                
                if self.lives <= 0: 
                    self._handle_lose()

            self._update_hardware()
            time.sleep(max(0.01, 0.04 - (time.time() - start_tick)))

    def mc_auto_reset_to_safe(self):
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.ui.update_eye_status("sleeping")

    def _handle_lose(self):
        self.running = False
        self.stop_music()
        self.audio.play("game_over")
        self.ui.show_game_over(self.score)
        print("💀 GAME OVER!")

if __name__ == "__main__":
    tk._default_root = None 
    MusicalChairsOperator()