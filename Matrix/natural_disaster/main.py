# main.py
import time
import math
import random
import threading
from config import *
from matrix_io import MatrixHardware
from ui import DashboardUI
from audio_manager import AudioManager

class NaturalDisasterGame:
    def __init__(self):
        self.hw = MatrixHardware()
        # Îi pasăm UI-ului funcția pe care să o apeleze când se alege numărul de jucători
        self.ui = DashboardUI(self.start_game_logic) 
        
        self.audio = AudioManager()

        self.num_players = 2
        self.score = 0
        self.lives = 0
        
        self.game_sequence = ["lava", "meteors", "fire"]
        self.current_game_index = 0
        
        self.islands = []
        self.meteors = []         
        self.craters = [] 
        self.fire_pixels = set() 
        self.active_splashes = []
        self.splashing_positions = set()

        # START UI (Blochează firul principal aici)
        self.ui.run()

    def start_game_logic(self, players):
        """Această funcție este apelată AUTOMAT de UI când se apasă un buton"""
        self.num_players = players
        self.lives = min(players, 7)
        self.score = 0
        self.current_game_index = 0
        
        self.ui.update_dashboard("NOU JOC", f"Echipă: {players} Jucători. Succes!", "white")
        self.ui.update_score(self.score)
        self.ui.update_lives(self.lives)
        
        self.audio.play_bgm()

        # Pornim bucla de joc pe un fir secundar ca să nu blocăm interfața grafică
        threading.Thread(target=self.game_loop, daemon=True).start()

    # --- FUNCȚII DE DESENARE ---
    def draw_base(self, frame):
        for y in range(HEIGHT):
            for x in range(WIDTH): self.hw.set_pixel_physical(frame, x, y, COLORS["GRASS"])
        for (ix, iy, iw, ih) in self.islands:
            for x in range(ix, ix + iw):
                for y in range(iy, iy + ih): self.hw.set_pixel_physical(frame, x, y, COLORS["ISLAND"])

    def draw_splashes(self, frame, base_color=COLORS["WHITE"]):
        for s in self.active_splashes[:]:
            sx, sy, life = s['x'], s['y'], s['life']
            if life >= 5: self.hw.set_pixel_physical(frame, sx, sy, base_color)
            elif life >= 3:
                for dx, dy in [(0,0), (1,0), (-1,0), (0,1), (0,-1)]: self.hw.set_pixel_physical(frame, sx + dx, sy + dy, base_color)
            elif life >= 1:
                for dx, dy in [(1,1), (-1,-1), (1,-1), (-1,1)]: self.hw.set_pixel_physical(frame, sx + dx, sy + dy, base_color)
            s['life'] -= 1
            if s['life'] <= 0:
                self.active_splashes.remove(s)
                self.splashing_positions.discard((sx, sy))

    def register_hit(self, px, py, hit_type):
        self.active_splashes.append({'x': px, 'y': py, 'life': 6})
        self.splashing_positions.add((px, py))
        self.lives -= 1
        self.ui.update_lives(self.lives)

        self.audio.play(hit_type)

    # --- LOGICĂ JOCURI ---
    def play_lava(self):
        # UI-ul va arăta mesajul de erupție cu portocaliu
        self.ui.update_dashboard("ERUPȚIE DE LAVĂ!", "Refugiază-te pe insule!", "orange")
        
        # Lava pornește din 1-3 colțuri aleatorii
        active_corners = random.sample(ALL_CORNERS, k=random.randint(1, 3))
        max_dist = math.sqrt(WIDTH**2 + HEIGHT**2)
        
        for f in range(300):
            if self.lives <= 0: break 
            frame = bytearray(1536); self.draw_base(frame)
            
            # Calculăm raza expansiunii lavei
            lava_radius = max_dist * (f / 300.0)
            
            # 1. Desenăm lava
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    dist = min([math.sqrt((x-cx)**2 + (y-cy)**2) for cx, cy in active_corners])
                    if dist < lava_radius:
                        on_island = any(ix <= x < ix+3 and iy <= y < iy+3 for ix, iy, iw, ih in self.islands)
                        if not on_island: 
                            self.hw.set_pixel_physical(frame, x, y, COLORS["LAVA"])
            
            # 2. Verificăm coliziunea (dacă un jucător calcă în lavă)
            for px, py in self.hw.pressed_buttons:
                if (px, py) in self.splashing_positions: continue
                dist = min([math.sqrt((px-cx)**2 + (py-cy)**2) for cx, cy in active_corners])
                on_island = any(ix <= px < ix+3 and iy <= py < iy+3 for ix, iy, iw, ih in self.islands)
                
                # Dacă piciorul e în lavă și nu e pe insulă -> ARSURĂ!
                if dist < lava_radius and not on_island:
                    self.register_hit(px, py, "splash")

            # 3. Desenăm exploziile/splash-ul folosind culoarea LAVA_SPLASH (Galben aprins)
            self.draw_splashes(frame, COLORS["LAVA_SPLASH"])
            self.hw.send_frame(frame); time.sleep(0.04)
            
        return True

    def play_meteors(self):
        self.ui.update_dashboard("METEORIȚI!", "Evită zonele ROȘII!", "red")
        
        for f in range(350):
            if self.lives <= 0: break 
            frame = bytearray(1536); self.draw_base(frame)
            
            for c in self.craters[:]:
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]: self.hw.set_pixel_physical(frame, c['x']+dx, c['y']+dy, COLORS["CRATER"])
                c['life'] -= 1
                if c['life'] <= 0: self.craters.remove(c)
                
            if f % 15 == 0: self.meteors.append({'x': random.randint(1, WIDTH-2), 'y': random.randint(1, HEIGHT-2), 'timer': 50})
                
            for m in self.meteors[:]:
                mx, my, timer = m['x'], m['y'], m['timer']
                if timer > 10: 
                    if f % 4 == 0 or f % 4 == 1: 
                        for dx in [-1, 0, 1]:
                            for dy in [-1, 0, 1]:
                                if dx == 0 and dy == 0: self.hw.set_pixel_physical(frame, mx, my, COLORS["METEOR_WARN"]) 
                                else: self.hw.set_pixel_physical(frame, mx+dx, my+dy, (80, 0, 0)) 
                elif timer > 0:
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]: self.hw.set_pixel_physical(frame, mx+dx, my+dy, COLORS["METEOR_IMPACT"])
                    if timer == 1: 
                        self.craters.append({'x': mx, 'y': my, 'life': 100})
                        self.audio.play("meteor_boom")
                    
                    for px, py in self.hw.pressed_buttons:
                        if (px, py) in self.splashing_positions: continue
                        if abs(px - mx) <= 1 and abs(py - my) <= 1:
                            self.register_hit(px, py, "damage") 
                            
                m['timer'] -= 1
                if m['timer'] <= -4: self.meteors.remove(m)
                
            self.draw_splashes(frame, COLORS["WHITE"])
            self.hw.send_frame(frame); time.sleep(0.04)
        return True

    def play_fire(self):
        self.ui.update_dashboard("INCENDIU!", "Calcă pe foc să-l stingi!", "orange")
        
        num_focare = max(2, self.num_players // 2 + 1)
        for _ in range(num_focare):
            self.fire_pixels.add((random.randint(1, WIDTH-2), random.randint(1, HEIGHT-2)))
            
        spread_interval = max(3, 12 - self.num_players) 
        spread_chance = 0.05 + (self.num_players * 0.03) 
        max_fire_pixels = int((WIDTH * HEIGHT) * 0.40) 
        
        round_survived = True

        for f in range(350):
            if self.lives <= 0: break
            frame = bytearray(1536); self.draw_base(frame)
            
            if f % spread_interval == 0:
                new_fires = set()
                for fx, fy in self.fire_pixels:
                    for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                        nx, ny = fx+dx, fy+dy
                        if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                            on_island = any(ix <= nx < ix+3 and iy <= ny < iy+3 for ix, iy, iw, ih in self.islands)
                            if not on_island and random.random() < spread_chance: 
                                new_fires.add((nx, ny))
                self.fire_pixels.update(new_fires)
            
            for px, py in list(self.hw.pressed_buttons):
                if (px, py) in self.fire_pixels:
                    self.fire_pixels.remove((px, py))
                    self.score += 1 
                    self.ui.update_score(self.score)

                    self.audio.play("fire_out")
                    
                    if not any(s['x'] == px and s['y'] == py for s in self.active_splashes):
                        self.active_splashes.append({'x': px, 'y': py, 'life': 4})
                        self.splashing_positions.add((px, py))

            if len(self.fire_pixels) > max_fire_pixels: 
                self.ui.update_dashboard("FOC SCĂPAT DE SUB CONTROL!", "Prea mult foc! Se pierde o viață...", "red")
                self.lives -= 1
                self.ui.update_lives(self.lives)
                
                for y in range(HEIGHT):
                    for x in range(WIDTH): self.hw.set_pixel_physical(frame, x, y, (200, 0, 0))
                self.hw.send_frame(frame)
                time.sleep(1.0)
                
                round_survived = False
                break

            for fx, fy in self.fire_pixels:
                fire_color = (255, random.randint(20, 100), 0) 
                self.hw.set_pixel_physical(frame, fx, fy, fire_color)

            self.draw_splashes(frame, COLORS["SMOKE"])
            self.hw.send_frame(frame); time.sleep(0.04)
            
        return round_survived

    # --- ENGINE-UL JOCULUI ---
    def game_loop(self):
        while self.lives > 0:
            self.active_splashes.clear()
            self.splashing_positions.clear()
            self.meteors.clear()
            self.craters.clear()
            self.fire_pixels.clear()
            
            min_islands = max(2, self.num_players // 2 + 1)
            num_islands = random.randint(min_islands, min_islands + 1)
            self.islands = [[random.randint(1, WIDTH-4), random.randint(1, HEIGHT-4), 3, 3] for _ in range(num_islands)]
            
            self.ui.update_dashboard("PREGĂTIRE...", "Stai pe poziții!", "white")
            for count in ['3', '2', '1']:
                self.audio.stop("countdown")
                self.audio.play("countdown")
                for _ in range(25):
                    frame = bytearray(1536); self.draw_base(frame)
                    for px, py in DIGITS[count]: self.hw.set_pixel_physical(frame, 7+px, 14+py, COLORS["WHITE"])
                    self.hw.send_frame(frame); time.sleep(0.04)

            self.audio.stop("countdown") # 3. Închidem ceasul când pornește runda!

            game_mode = self.game_sequence[self.current_game_index]
            self.current_game_index = (self.current_game_index + 1) % len(self.game_sequence)
            
            round_success = True
            if game_mode == "lava": round_success = self.play_lava()
            elif game_mode == "meteors": round_success = self.play_meteors()
            else: round_success = self.play_fire()

            if self.lives > 0 and round_success:
                self.score += self.lives 
                self.ui.update_score(self.score)
                self.ui.update_dashboard("RUNDĂ TERMINATĂ!", f"+{self.lives} Puncte de Supraviețuire!", "green")
                time.sleep(3.0)

        # GAME OVER SEQUENCE
        self.audio.stop_bgm()
        self.audio.stop_all_sfx()
        self.audio.play("game_over")
        self.ui.show_game_over(self.score)
        

        # Facem podeaua roșie pentru 10 secunde
        frame = bytearray(1536)
        for y in range(HEIGHT):
            for x in range(WIDTH): self.hw.set_pixel_physical(frame, x, y, (150, 0, 0))
        self.hw.send_frame(frame)
        
        time.sleep(10.0) 
        self.ui.return_to_setup()

if __name__ == "__main__":
    NaturalDisasterGame()