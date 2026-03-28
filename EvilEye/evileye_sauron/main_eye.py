# main_eye.py
import time
import math
import random
import threading
from config_eye import *
from eye_io import EvilEyeHardware
from audio_manager_eye import EyeAudioManager 
from ui_eye import EyeDashboardUI            

class GuessingGameEye:
    def __init__(self):
        self.hw = EvilEyeHardware()
        self.audio = EyeAudioManager() 
        self.ui = EyeDashboardUI("GUESSING GAME & THE EYE") 
        
        self.running = True
        self.score = 0
        self.hp = 3 
        
        self.total_buttons = 40
        self.button_map = {}
        self._generate_hidden_colors()
        
        self.currently_flipped_indices = [] 
        self.flip_back_time = 0             

        self.eye_phase = "sleeping" 
        self.eye_phase_timer = time.time() + random.uniform(*EYE_COOLDOWN_RANGE)
        
        self._clear_all_hardware()
        
        threading.Thread(target=self.game_loop, daemon=True).start()
        self.ui.run()

    def _clear_all_hardware(self):
        for w in range(1, NUM_WALLS + 1): 
            self.hw.set_element(w, 0, (0, 0, 0)) 
            for i in range(1, 11):               
                self.hw.set_element(w, i, COLORS["COVERED"])

    def _generate_hidden_colors(self):
        hidden_colors_pool = PAIR_COLORS + PAIR_COLORS
        random.shuffle(hidden_colors_pool) 

        for i in range(self.total_buttons):
            wall = (i // 10) + 1  
            button_id = (i % 10) + 1 
            self.button_map[i] = {
                "color_hidden": hidden_colors_pool[i],
                "state": "covered", 
                "wall": wall,
                "id": button_id
            }

    def _update_hardware_lights(self):
        current_time = time.time()

        for i in range(self.total_buttons):
            btn = self.button_map[i]
            final_color = COLORS["COVERED"] 
            
            if btn["state"] == "matched":
                final_color = COLORS["MATCHED"] 
            elif btn["state"] == "flipped":
                final_color = btn["color_hidden"] 
            
            if self.eye_phase == "warning" and btn["state"] == "covered":
                if int(current_time * 5) % 2 == 0:
                    final_color = COLORS["WARNING"]
                    
            self.hw.set_element(btn["wall"], btn["id"], final_color)

        eye_color = COLORS["EYE_OPEN"] if self.eye_phase == "active" else COLORS["EYE_CLOSED"]
        for w in range(1, NUM_WALLS + 1):
            self.hw.set_element(w, 0, eye_color)

    def _process_guessing_inputs(self):
        if self.flip_back_time > 0 and time.time() < self.flip_back_time:
            return

        if self.flip_back_time > 0 and time.time() >= self.flip_back_time:
            for idx in self.currently_flipped_indices:
                self.button_map[idx]["state"] = "covered"
            
            self.currently_flipped_indices.clear()
            self.flip_back_time = 0
            self.ui.set_first_click_color(None)
            self.ui.update_eye_status(self.eye_phase) 

        for i in range(self.total_buttons):
            btn = self.button_map[i]
            if btn["state"] == "covered": 
                if self.hw.button_states[btn["wall"]][btn["id"]]:
                    btn["state"] = "flipped"
                    self.currently_flipped_indices.append(i)
                    
                    self.audio.play("flip") 
                    self.ui.set_first_click_color(btn["color_hidden"])

                    if len(self.currently_flipped_indices) == 2:
                        self._check_color_match()
                    break 

    def _check_color_match(self):
        idx1, idx2 = self.currently_flipped_indices
        color1 = self.button_map[idx1]["color_hidden"]
        color2 = self.button_map[idx2]["color_hidden"]
        
        if color1 == color2:
            self.button_map[idx1]["state"] = "matched"
            self.button_map[idx2]["state"] = "matched"
            
            # ADAUGĂM 5 PUNCTE PENTRU FIECARE PERECHE GHICITĂ
            self.score += 5
            self.ui.update_stats(self.score, self.hp)
            
            self.audio.play("match") 
            self.currently_flipped_indices.clear()
            
            # 20 de perechi x 5 puncte = 100 de puncte pentru victorie
            if self.score >= 100:
                self._handle_win()
        else:
            self.audio.play("wrong") 
            self.flip_back_time = time.time() + FLIP_BACK_TIME

    def _process_eye_logic(self):
        current_time = time.time()
        if self.eye_phase == "off": return
        
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
                self.eye_phase = "sleeping" 
                self.eye_phase_timer = current_time + random.uniform(*EYE_COOLDOWN_RANGE)
            
            self.ui.update_eye_status(self.eye_phase)

        if self.eye_phase == "active":
            for w in range(1, NUM_WALLS + 1):
                if self.hw.eye_states[w]:
                    self._handle_motion_penalty()
                    break 

    def _handle_motion_penalty(self):
        self.hp -= 1
        self.ui.update_stats(self.score, self.hp) # <--- Trimitem scorul și noul HP
        
        self.audio.play("damage") 
        
        self.eye_phase = "sleeping" 
        self.eye_phase_timer = time.time() + random.uniform(*EYE_COOLDOWN_RANGE) + 3.0 

        self.ui.update_eye_status(self.eye_phase)

        if self.hp <= 0:
            self._handle_lose()

    def _handle_win(self):
        self.running = False
        self.eye_phase = "off"

        self.ui.update_eye_status(self.eye_phase)

        self.audio.play("win")
        
        for w in range(1, NUM_WALLS + 1):
            for i in range(1, 11): 
                self.hw.set_element(w, i, (0, 255, 0))
        print("🎉 VICTORIE!")

    def _handle_lose(self):
        self.running = False
        self.eye_phase = "off"

        self.ui.update_eye_status(self.eye_phase)

        self.audio.play("game_over")
        
        for w in range(1, NUM_WALLS + 1):
            for i in range(1, 11): 
                self.hw.set_element(w, i, (255, 0, 0))
        print("💀 GAME OVER!")

    # --- MAIN LOOP ---
    def game_loop(self):
        # Actualizăm interfața la start cu HP inițial (3) și Scor (0)
        self.ui.update_stats(self.score, self.hp)
        
        while self.running:
            start_tick = time.time()
            self._process_guessing_inputs()
            self._process_eye_logic()
            self._update_hardware_lights()
            time.sleep(max(0.01, 0.04 - (time.time() - start_tick)))

if __name__ == "__main__":
    GuessingGameEye()