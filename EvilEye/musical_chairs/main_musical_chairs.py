# main_musical_chairs.py  –  Musical Chairs operator
import os
import time
import random
import threading
import socket
import tkinter as tk
from tkinter import ttk, messagebox

from config_eye import *
from eye_io import EvilEyeHardware, run_discovery, get_local_interfaces
from audio_manager_eye import EyeAudioManager
from ui_eye import EyeDashboardUI


class MusicalChairsOperator:
    def __init__(self):
        self.hw    = EvilEyeHardware()
        self.audio = EyeAudioManager()
        self.ui    = EyeDashboardUI("MUSICAL CHAIRS")

        # Protecție pentru modulul audio pygame.mixer
        self.mixer_works = False
        try:
            import pygame
            import pygame.mixer
            pygame.mixer.init()
            self.mixer_works = True
        except Exception:
            self.mixer_works = False

        self.running         = True
        self.score           = 0
        self.lives           = 5
        self.game_phase      = "IDLE"

        # Starea logicii de Matching-Pairs
        self.grid_colors     = {}   # (wall, led) -> RGB
        self.revealed        = set() # Butoane întoarse curent sau perechi ghicite
        self.first_selection = None # Prima selecție dintr-o încercare de potrivire

        self.watching_walls  = []
        self.grace_period_end = 0
        self.music_paused    = False

        if not os.path.exists("music"):
            os.makedirs("music")

        self.ui.update_lives(self.lives)

        # Pornim bucla principală de rețea și logică
        threading.Thread(target=self.game_loop, daemon=True).start()
        self.create_operator_controls()
        self.ui.run()

    # ── Panoul de Control al Operatorului ─────────────────────────────────────
    def create_operator_controls(self):
        self.ctrl = tk.Toplevel()
        self.ctrl.title("Hardware Setup & Discovery")
        self.ctrl.geometry("460x560")
        self.ctrl.configure(bg="#1a1a1a", padx=15, pady=15)

        # ── 1. Selectare Interfață Rețea ──
        tk.Label(self.ctrl, text="1. ALEGE PLACA DE REȚEA",
                 fg="white", bg="#1a1a1a",
                 font=("Arial", 9, "bold")).pack(anchor="w")

        self._iface_var   = tk.StringVar()
        self._iface_combo = ttk.Combobox(self.ctrl, textvariable=self._iface_var,
                                         state="readonly", width=50)
        self._iface_combo.pack(pady=5)
        self._ifaces_cache = []
        self._refresh_interfaces()

        # ── 2. Descoperire Dispozitiv (Discovery) ──
        tk.Label(self.ctrl, text="2. GĂSEȘTE DISPOZITIVUL",
                 fg="white", bg="#1a1a1a",
                 font=("Arial", 9, "bold")).pack(anchor="w", pady=(10, 0))

        self._ip_var = tk.StringVar(value="127.0.0.1")
        ip_frame = tk.Frame(self.ctrl, bg="#1a1a1a")
        ip_frame.pack(fill="x", pady=5)
        tk.Entry(ip_frame, textvariable=self._ip_var, width=20).pack(side="left", padx=5)
        tk.Button(ip_frame, text="🔍 DISCOVER",
                  command=self._discover_device,
                  bg="#2c3e50", fg="white").pack(side="left")

        self.lbl_status = tk.Label(self.ctrl, text="Status: aștept discovery…",
                                   fg="gray", bg="#1a1a1a")
        self.lbl_status.pack(pady=5)

        ttk.Separator(self.ctrl, orient="horizontal").pack(fill="x", pady=12)

        # ── 3. Selecție Muzică ──
        tk.Label(self.ctrl, text="3. MUZICĂ (opțional)",
                 fg="white", bg="#1a1a1a",
                 font=("Arial", 9, "bold")).pack(anchor="w")

        self._song_var   = tk.StringVar()
        self._song_combo = ttk.Combobox(self.ctrl, textvariable=self._song_var,
                                        state="readonly", width=50)
        self._song_combo.pack(pady=5)
        self._refresh_songs()

        ttk.Separator(self.ctrl, orient="horizontal").pack(fill="x", pady=12)

        # ── 4. Controale Joc ──
        tk.Label(self.ctrl, text="4. CONTROL JOC",
                 fg="white", bg="#1a1a1a",
                 font=("Arial", 9, "bold")).pack(anchor="w")

        btn_frame = tk.Frame(self.ctrl, bg="#1a1a1a")
        btn_frame.pack(fill="x", pady=8)

        self.btn_start = tk.Button(
            btn_frame, text="▶  START (Muzică / SAFE)",
            bg="#27ae60", fg="white",
            font=("Arial", 10, "bold"),
            command=self._operator_action_safe,
            state="disabled", height=2,
        )
        self.btn_start.pack(fill="x", pady=3)

        self.btn_stop = tk.Button(
            btn_frame, text="👁  WATCHING (Ochi Activ)",
            bg="#c0392b", fg="white",
            font=("Arial", 10, "bold"),
            command=self._operator_action_watching,
            state="disabled", height=2,
        )
        self.btn_stop.pack(fill="x", pady=3)

        self.lbl_ctrl_info = tk.Label(self.ctrl, text="",
                                      fg="#aaaaaa", bg="#1a1a1a",
                                      font=("Arial", 9))
        self.lbl_ctrl_info.pack(pady=6)

        self.ctrl.protocol("WM_DELETE_WINDOW", self._on_ctrl_close)

    def _refresh_interfaces(self):
        ifaces = get_local_interfaces()
        self._ifaces_cache = ifaces
        labels = [f"{n}  ({ip})" for n, ip, _ in ifaces]
        self._iface_combo["values"] = labels if labels else ["(nicio interfață găsită)"]
        if labels:
            self._iface_combo.current(0)

    def _refresh_songs(self):
        songs = []
        if os.path.exists("music"):
            songs = [f for f in os.listdir("music")
                     if f.lower().endswith((".mp3", ".ogg", ".wav"))]
        self._song_combo["values"] = songs if songs else ["(niciun fișier în /music)"]
        if songs:
            self._song_combo.current(0)

    def _discover_device(self):
        idx = self._iface_combo.current()
        if idx < 0 or idx >= len(self._ifaces_cache):
            self.lbl_status.config(text="⚠ Selectează o interfață.", fg="orange")
            return

        name, ip, bcast = self._ifaces_cache[idx]
        self.lbl_status.config(text=f"Scanez pe {name} ({ip})…", fg="orange")
        self.ctrl.update_idletasks()

        found_ip = run_discovery(ip, bcast)
        if found_ip:
            self._ip_var.set(found_ip)
            self.lbl_status.config(text=f"✅ Conectat la {found_ip}", fg="#2ecc71")
            # Activăm conexiunea hardware
            self.hw.connect(found_ip)
            self.btn_start.config(state="normal")
        else:
            # --- MODIFICARE AICI: Fallback la SIMULATOR ---
            self.lbl_status.config(
                text="⚠ Niciun device. Trecem pe SIMULATOR (127.0.0.1)", 
                fg="yellow"
            )
            self._ip_var.set("127.0.0.1")
            self.hw.connect("127.0.0.1") # Forțăm conectarea pe simulator!
            self.btn_start.config(state="normal")

    def _operator_action_safe(self):
        """Muzica pornește, ochiul adoarme → faza SAFE (Matching Pairs)."""
        if self.game_phase == "SAFE":
            return

        self.game_phase = "SAFE"
        self.generate_pairs()
        self.ui.update_eye_status("sleeping")
        self.btn_stop.config(state="normal")
        self.btn_start.config(state="disabled")
        self._update_ctrl_info()

        # --- SINCRONIZARE PERFECTĂ ---
        # Forțăm aplicarea culorilor pe hardware fix acum, înainte să pornească muzica!
        self._update_hardware()

        if self.mixer_works:
            import pygame
            sel = self._song_combo.get()
            song_path = os.path.join("music", sel) if sel else None
            if song_path and os.path.exists(song_path):
                if self.music_paused:
                    pygame.mixer.music.unpause()
                else:
                    pygame.mixer.music.load(song_path)
                    pygame.mixer.music.play(-1)
            self.music_paused = False

    def _operator_action_watching(self):
        """Muzica se oprește, ochiul se deschide → faza WATCHING."""
        if self.game_phase != "SAFE":
            return

        self.game_phase = "WATCHING"
        if self.mixer_works:
            import pygame
            pygame.mixer.music.pause()
            self.music_paused = True

        self.watching_walls    = random.sample([1, 2, 3, 4], random.randint(1, 2))
        self.grace_period_end  = time.time() + 0.5
        self.audio.play("eye_open")
        self.ui.update_eye_status("active")
        self.btn_stop.config(state="disabled")
        self.btn_start.config(state="normal")
        self._update_ctrl_info()

    def _update_ctrl_info(self):
        self.lbl_ctrl_info.config(
            text=f"Scor: {self.score}  |  Vieți: {self.lives}  |  Faza: {self.game_phase}"
        )

    def generate_pairs(self):
        """Logica de generare a 5 perechi de culori."""
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

    def handle_button_press(self, w, l):
        """Logica de matching: 'prima nu merge (doar se aprinde), a doua deschide'."""
        if (w, l) not in self.grid_colors or (w, l) in self.revealed:
            return

        color = self.grid_colors[(w, l)]
        self.revealed.add((w, l))
        self.audio.play("flip")
        self.ui.set_feedback_color(color)

        if self.first_selection is None:
            self.first_selection = (w, l)
        else:
            w1, l1 = self.first_selection
            if self.grid_colors[(w1, l1)] == color:
                # Pereche corectă!
                self.score += 20
                self.ui.update_score(self.score)
                self.audio.play("match")
                self.first_selection = None
                # Dacă am găsit toate perechile, regenerăm tabla
                if len(self.revealed) == len(self.grid_colors):
                    self.ctrl.after(1000, self.generate_pairs)
            else:
                # Greșit! Le întoarcem după un delay
                def flip_back(p1=(w1, l1), p2=(w, l)):
                    self.revealed.discard(p1)
                    self.revealed.discard(p2)
                self.audio.play("wrong")
                self.ctrl.after(int(FLIP_BACK_TIME * 1000), flip_back)
                self.first_selection = None

        self._update_ctrl_info()

    # ── Ieșire Hardware ───────────────────────────────────────────────────────
    def _all_off(self):
        for w in range(1, 5):
            for l in range(0, 11):
                self.hw.set_element(w, l, (0, 0, 0))

    def _update_hardware(self):
        """Aplică culorile pe LED-urile fizice folosind constantele din config."""
        current_time = time.time()
        for w in range(1, 5):
            # LED 0 = Ochiul (Verde închis la IDLE, Roșu la WATCHING)
            if self.game_phase == "WATCHING" and w in self.watching_walls:
                eye_col = COLORS["EYE_OPEN"]
            else:
                eye_col = COLORS["EYE_CLOSED"]
            self.hw.set_element(w, 0, eye_col)

            # LED-urile 1-10 = Butoanele (Pressure tiles)
            for l in range(1, 11):
                final_color = (0, 0, 0)
                
                if (w, l) in self.revealed:
                    # Dacă butonul este întors, arătăm culoarea sa
                    final_color = self.grid_colors.get((w, l), (0, 0, 0))
                elif (w, l) in self.grid_colors and self.game_phase == "SAFE":
                    # Dacă este un buton activ dar neîntors, arătăm culoarea COVERED (Gri)
                    final_color = COLORS["COVERED"]
                
                # Efectul de avertizare intermitentă din main_eye.py
                if self.game_phase == "WATCHING" and (w, l) in self.grid_colors:
                    if int(current_time * 5) % 2 == 0:
                        final_color = COLORS["WARNING"]

                self.hw.set_element(w, l, final_color)

    # ── Bucla Principală de Joc (Background thread) ──────────────────────────
    def game_loop(self):
        while self.running:
            start_tick = time.time()
            penalty = False

            # 1. Verificăm senzorii de mișcare (WATCHING phase)
            if self.game_phase == "WATCHING" and time.time() > self.grace_period_end:
                for w in self.watching_walls:
                    if self.hw.eye_states.get(w, False):
                        penalty = True
                        break

            # 2. Verificăm butoanele apăsate (SAFE phase)
            if not penalty and self.game_phase == "SAFE":
                for w in range(1, 5):
                    for l in range(1, 11):
                        # Folosim logica din main_eye: verificăm dacă e apăsat în hardware
                        if self.hw.button_states[w].get(l, False):
                            self.handle_button_press(w, l)
                            # Debounce scurt pentru a preveni înregistrările multiple
                            time.sleep(0.1)

            # 3. Executăm penalizarea dacă jucătorul s-a mișcat
            if penalty:
                self.lives -= 1
                self.audio.play("damage")
                self.ui.update_lives(self.lives)
                self.game_phase = "IDLE"
                self.revealed.clear()
                self.ctrl.after(0, self._auto_reset_to_safe)

                if self.lives <= 0:
                    self.running = False
                    self._all_off()
                    self.ctrl.after(0, self._show_game_over)
                    break

            # 4. Actualizăm luminile fizice
            self._update_hardware()
            
            # Rata de refresh optimă
            time.sleep(max(0.01, 0.05 - (time.time() - start_tick)))

    def _auto_reset_to_safe(self):
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.ui.update_eye_status("sleeping")
        self._update_ctrl_info()

    def _show_game_over(self):
        self.audio.play("game_over")
        self.ui.update_eye_status("sleeping")
        messagebox.showinfo("GAME OVER",
                            f"Jocul s-a terminat!\nScor final: {self.score}",
                            parent=self.ctrl)

    def _on_ctrl_close(self):
        self.running = False
        self.hw.disconnect()
        self._all_off()
        self.ctrl.destroy()
        self.ui.root.destroy()


if __name__ == "__main__":
    MusicalChairsOperator()
