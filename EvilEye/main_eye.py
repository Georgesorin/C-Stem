# main_eye.py
import time
import math
import random
import threading
from config_eye import *
from eye_io import EvilEyeHardware
from audio_manager_eye import EyeAudioManager # Importăm Audio
from ui_eye import EyeDashboardUI            # Importăm UI

class GuessingGameEye:
    def __init__(self):
        self.hw = EvilEyeHardware()
        self.audio = EyeAudioManager() # Inițializăm Audio Manager
        
        # Inițializăm UI-ul
        self.ui = EyeDashboardUI("GUESSING GAME & THE EYE") 
        
        self.running = True
        self.score = 0
        self.hp = 3 
        
        # Mapare logică: index_global (0-39) -> {culoare_ascunsa, stare, wall, id}
        self.total_buttons = 40
        self.button_map = {}
        self._generate_hidden_colors()
        
        # Stări logică Guessing
        self.currently_flipped_indices = [] # Salvează 0, 1 sau 2 indici întorși
        self.flip_back_time = 0             # Timestamp când trebuie întoarse înapoi

        # Stări logică Ochi
        self.eye_phase = "sleeping" # "sleeping", "warning", "active"
        self.eye_phase_timer = time.time() + random.uniform(*EYE_COOLDOWN_RANGE)
        
        # Curățăm harta fizică la start
        self._clear_all_hardware()
        
        # Pornim bucla de joc pe un thread secundar
        threading.Thread(target=self.game_loop, daemon=True).start()
        
        # START UI (Blochează firul principal aici)
        self.ui.run()

    # --- SETUP ȘI RENDERIZARE ---
    def _clear_all_hardware(self):
        """Închide toți ochii și face toate butoanele albe la start"""
        for w in range(1, NUM_WALLS + 1): # Pereții sunt 1, 2, 3, 4
            self.hw.set_element(w, 0, (0, 0, 0)) # Ochiul este mereu 0
            for i in range(1, 11):               # Butoanele sunt 1-10
                self.hw.set_element(w, i, COLORS["COVERED"])

    def _generate_hidden_colors(self):
        """Generează 20 de perechi de culori și le mapează aleatoriu pe cele 40 butoane"""
        hidden_colors_pool = PAIR_COLORS + PAIR_COLORS
        random.shuffle(hidden_colors_pool) # Amestecăm perechile

        for i in range(self.total_buttons):
            wall = (i // 10) + 1  # Va da 1, 2, 3 sau 4
            button_id = (i % 10) + 1 # Va da 1, 2... până la 10
            
            self.button_map[i] = {
                "color_hidden": hidden_colors_pool[i],
                "state": "covered", # "covered", "flipped", "matched"
                "wall": wall,
                "id": button_id
            }

    def _update_hardware_lights(self):
        """Redă stările logice pe pereții fizici"""
        current_time = time.time()

        # 1. & 2. Logică Butoane și Avertizare
        for i in range(self.total_buttons):
            btn = self.button_map[i]
            final_color = COLORS["COVERED"] # Default (ascuns)
            
            if btn["state"] == "matched":
                final_color = COLORS["MATCHED"] # Ghicit -> Oprit
            elif btn["state"] == "flipped":
                final_color = btn["color_hidden"] # Întors -> Arată culoarea
            
            # Pâlpâire dacă ochiul se pregătește să se deschidă și butonul e încă neghicit
            if self.eye_phase == "warning" and btn["state"] == "covered":
                if int(current_time * 5) % 2 == 0:
                    final_color = COLORS["WARNING"]
                    
            self.hw.set_element(btn["wall"], btn["id"], final_color)

        # 3. Desenăm Ochii
        eye_color = COLORS["EYE_OPEN"] if self.eye_phase == "active" else COLORS["EYE_CLOSED"]
        for w in range(1, NUM_WALLS + 1):
            self.hw.set_element(w, 0, eye_color)

    # --- LOGICĂ JOC (GUESSING & EYE) ---
    def _process_guessing_inputs(self):
        """Verifică ce butoane au fost apăsate de jucători"""
        # Dacă așteptăm timer-ul de flip_back, nu procesăm alte apăsări
        if self.flip_back_time > 0 and time.time() < self.flip_back_time:
            return

        # Dacă tocmai am întors înapoi butoanele, curățăm lista
        if self.flip_back_time > 0 and time.time() >= self.flip_back_time:
            for idx in self.currently_flipped_indices:
                self.button_map[idx]["state"] = "covered"
            
            self.currently_flipped_indices.clear()
            self.flip_back_time = 0
            
            # === ȘTERS APELUL CATRE UI PENTRU CULOAREA CĂUTATĂ ===
            self.ui.update_eye_status(self.eye_phase) # Revenim la starea ochiului

        # Verificăm toate cele 40 butoane
        for i in range(self.total_buttons):
            btn = self.button_map[i]
            if btn["state"] == "covered": # Dacă e ascuns
                # Citim starea fizică din eye_io
                if self.hw.button_states[btn["wall"]][btn["id"]]:
                    
                    # Îl întoarcem
                    btn["state"] = "flipped"
                    self.currently_flipped_indices.append(i)
                    
                    self.audio.play("flip") # Sunet Click
                    
                    # === ȘTERS APELUL CATRE UI PENTRU CULOAREA CĂUTATĂ ===

                    # Dacă am întors MAXIM 2, verificăm potrivirea
                    if len(self.currently_flipped_indices) == 2:
                        self._check_color_match()
                    break # Procesăm doar o apăsare pe cadru

    def _check_color_match(self):
        """Verifică dacă cele 2 butoane întoarse au aceeași culoare ascunsă"""
        idx1, idx2 = self.currently_flipped_indices
        color1 = self.button_map[idx1]["color_hidden"]
        color2 = self.button_map[idx2]["color_hidden"]
        
        if color1 == color2:
            # S-au potrivit! Rămân oprite (Regula Win)
            self.button_map[idx1]["state"] = "matched"
            self.button_map[idx2]["state"] = "matched"
            self.score += 1
            self.ui.update_stats(self.score, self.hp)
            self.ui.update_eye_status("matched")
            
            self.audio.play("match") # Sunet Pereche Ghicită
            
            self.currently_flipped_indices.clear()
            
            # Verificăm dacă echipa a câștigat
            if self.score == 20:
                self._handle_win()
        else:
            # Nu s-au potrivit. Pornim timer-ul de întoarcere înapoi
            self.audio.play("wrong") # Sunet GRESIT
            self.ui.update_eye_status("wrong")
            self.flip_back_time = time.time() + FLIP_BACK_TIME

    def _process_eye_logic(self):
        """Gestionează ciclul de viață al Ochiului (Sleeping -> Warning -> Active)"""
        current_time = time.time()
        
        # Dacă jocul e pe pauză (Win/Lose), nu procesăm
        if self.eye_phase == "off": return
        
        # 1. Schimbarea fazelor bazate pe Timer
        if current_time >= self.eye_phase_timer:
            if self.eye_phase == "sleeping":
                self.eye_phase = "warning"
                self.eye_phase_timer = current_time + EYE_WARNING_DURATION
                self.audio.play("warning") 
                
            elif self.eye_phase == "warning":
                self.eye_phase = "active"
                self.eye_phase_timer = current_time + EYE_ACTIVE_DURATION
                self.audio.play("eye_open") 
                
            elif self.eye_phase == "active":
                self.eye_phase = "sleeping" # SE ÎNCHIDE OCHIUL
                self.eye_phase_timer = current_time + random.uniform(*EYE_COOLDOWN_RANGE)
                # ui_eye se va ocupa de facut fundalul negru la apelul de mai jos
            
            # Actualizăm mesajul de pe ecran
            self.ui.update_eye_status(self.eye_phase)

        # 2. Verificarea mișcării în faza ACTIVĂ
        if self.eye_phase == "active":
            for w in range(1, NUM_WALLS + 1):
                # Dacă oricare ochi detectează mișcare
                #
                if self.hw.eye_states[w]:
                    self._handle_motion_penalty()
                    break # Nu scădem mai multe vieți pe cadru

    def _handle_motion_penalty(self):
        """Când senzorul de mișcare detectează ceva în faza Activă"""
        self.hp -= 1
        self.ui.update_stats(self.score, self.hp)
        self.ui.update_eye_status("damage")
        
        self.audio.play("damage") # Sunet Pedeapsă
        
        # Resetăm imediat starea ochiului (pauză mai lungă)
        self.eye_phase = "sleeping" 
        self.eye_phase_timer = time.time() + random.uniform(*EYE_COOLDOWN_RANGE) + 3.0 

        if self.hp <= 0:
            self._handle_lose()

    def _handle_win(self):
        """Logica când toate cele 20 de perechi sunt ghicite"""
        self.running = False
        self.eye_phase = "off"
        self.ui.update_eye_status("win")
        self.audio.play("win")
        
        # Inundăm pereții cu verde
        for w in range(1, NUM_WALLS + 1):
            for i in range(1, 11): 
                self.hw.set_element(w, i, (0, 255, 0))
        print("🎉 VICTORIE!")

    def _handle_lose(self):
        """Logica când echipa a pierdut toate viețile"""
        self.running = False
        self.eye_phase = "off"
        self.ui.update_eye_status("game_over")
        self.audio.play("game_over")
        
        # Inundăm pereții cu roșu
        for w in range(1, NUM_WALLS + 1):
            for i in range(1, 11): 
                self.hw.set_element(w, i, (255, 0, 0))
        print("💀 GAME OVER!")

    # --- MAIN LOOP ---
    def game_loop(self):
        """Loop-ul principal care rulează la 25 FPS (40ms)"""
        # Actualizăm interfața la start cu HP inițial
        #
        self.ui.update_stats(0, 3)
        self.ui.update_eye_status("sleeping")
        
        while self.running:
            start_tick = time.time()
            
            # 1. Procesăm intrările (Guessing)
            self._process_guessing_inputs()
            
            # 2. Procesăm logica de Ochi/Statues
            self._process_eye_logic()
            
            # 3. Actualizăm rețeaua (Lights/Ochi)
            self._update_hardware_lights()
            
            # Păstrăm stabilitatea la aprox 25 FPS
            time.sleep(max(0.01, 0.04 - (time.time() - start_tick)))

if __name__ == "__main__":
    GuessingGameEye()