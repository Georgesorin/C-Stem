# main_natural.py
import time
import math
import random
import threading
from config_natural import *
from matrix_io_natural import MatrixHardware
from ui_natural import DashboardUI
from audio_manager_natural import AudioManager

class NaturalDisasterGame:
    def __init__(self):
        self.hw = MatrixHardware()
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

        self.ui.run()

    def start_game_logic(self, players):
        self.num_players = players
        self.lives = min(players, 7)
        self.score = 0
        self.current_game_index = 0
        
        self.ui.update_dashboard("NOU JOC", f"Echipă: {players} Jucători. Succes!", "white")
        self.ui.update_score(self.score)
        self.ui.update_lives(self.lives)
        
        self.audio.play_bgm()

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
        self.ui.update_dashboard("ERUPȚIE DE LAVĂ!", "Refugiază-te pe insule!", "orange")
        active_corners = random.sample(ALL_CORNERS, k=random.randint(1, 3))
        max_dist = math.sqrt(WIDTH**2 + HEIGHT**2)
        
        # LAVA EXTREMĂ: Reducem dramatic numărul de frame-uri. 
        # La 2 jucători va avea doar 50 de frame-uri să umple ecranul!
        total_frames = int(50 + (self.num_players * 15)) 
        
        for f in range(total_frames):
            if self.lives <= 0: break 
            frame = bytearray(1536); self.draw_base(frame)
            
            lava_radius = max_dist * (f / float(total_frames))
            
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    dist = min([math.sqrt((x-cx)**2 + (y-cy)**2) for cx, cy in active_corners])
                    if dist < lava_radius:
                        on_island = any(ix <= x < ix+3 and iy <= y < iy+3 for ix, iy, iw, ih in self.islands)
                        if not on_island: 
                            self.hw.set_pixel_physical(frame, x, y, COLORS["LAVA"])
            
            for px, py in self.hw.pressed_buttons:
                if (px, py) in self.splashing_positions: continue
                dist = min([math.sqrt((px-cx)**2 + (py-cy)**2) for cx, cy in active_corners])
                on_island = any(ix <= px < ix+3 and iy <= py < iy+3 for ix, iy, iw, ih in self.islands)
                if dist < lava_radius and not on_island:
                    self.register_hit(px, py, "splash")

            self.draw_splashes(frame, COLORS["LAVA_SPLASH"])
            self.hw.send_frame(frame)
            
            # Pauză minimă, lăsăm hardware-ul să meargă la viteză maximă
            time.sleep(0.005) 
            
        return True

    def play_meteors(self):
        self.ui.update_dashboard("METEORIȚI!", "Evită zonele ROȘII!", "red")
        
        # METEORIȚI EXTREMI:
        # Apar foarte des (la 4-8 frame-uri)
        spawn_rate = max(4, 2 + self.num_players) 
        # Timp de reacție super scurt (sub o secundă fizică)
        meteor_timer = max(10, 8 + self.num_players * 2) 
        
        for f in range(250):
            if self.lives <= 0: break 
            frame = bytearray(1536); self.draw_base(frame)
            
            for c in self.craters[:]:
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]: self.hw.set_pixel_physical(frame, c['x']+dx, c['y']+dy, COLORS["CRATER"])
                c['life'] -= 1
                if c['life'] <= 0: self.craters.remove(c)
                
            if f % spawn_rate == 0: 
                self.meteors.append({'x': random.randint(1, WIDTH-2), 'y': random.randint(1, HEIGHT-2), 'timer': meteor_timer})
                
            for m in self.meteors[:]:
                mx, my, timer = m['x'], m['y'], m['timer']
                
                if timer > 5: # Clipesc roșu intermitent mult mai scurt
                    if f % 2 == 0: 
                        for dx in [-1, 0, 1]:
                            for dy in [-1, 0, 1]:
                                if dx == 0 and dy == 0: self.hw.set_pixel_physical(frame, mx, my, COLORS["METEOR_WARN"]) 
                                else: self.hw.set_pixel_physical(frame, mx+dx, my+dy, (80, 0, 0)) 
                elif timer > 0: # IMPACT!
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]: self.hw.set_pixel_physical(frame, mx+dx, my+dy, COLORS["METEOR_IMPACT"])
                    if timer == 1: 
                        self.craters.append({'x': mx, 'y': my, 'life': 60})
                        self.audio.play("meteor_boom")
                    
                    for px, py in self.hw.pressed_buttons:
                        if (px, py) in self.splashing_positions: continue
                        if abs(px - mx) <= 1 and abs(py - my) <= 1:
                            self.register_hit(px, py, "damage") 
                            
                m['timer'] -= 1
                if m['timer'] <= -3: self.meteors.remove(m)
                
            self.draw_splashes(frame, COLORS["WHITE"])
            self.hw.send_frame(frame)
            
            # Pauză minimă
            time.sleep(0.005)
            
        return True

    def play_fire(self):
        self.ui.update_dashboard("INCENDIU!", "Calcă pe foc să-l stingi!", "orange")
        
        # FOC EXTREM: Începe din MAI MULTE locuri simultan
        num_focare = max(3, self.num_players + 1)
        for _ in range(num_focare):
            self.fire_pixels.add((random.randint(1, WIDTH-2), random.randint(1, HEIGHT-2)))
            
        # Se răspândește infernal de repede (la fiecare 1-2 frame-uri)
        spread_interval = max(1, self.num_players - 1) 
        # Șansă mai mare să "sară" pe alt pixel
        spread_chance = max(0.1, 0.20 - (self.num_players * 0.01)) 
        
        max_fire_pixels = int((WIDTH * HEIGHT) * 0.35) # Dacă acoperă 35% din podea, pierzi
        round_survived = True

        for f in range(250):
            if self.lives <= 0: break
            frame = bytearray(1536); self.draw_base(frame)
            
            if len(self.fire_pixels) == 0:
                for _ in range(max(2, self.num_players)):
                    self.fire_pixels.add((random.randint(1, WIDTH-2), random.randint(1, HEIGHT-2)))

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
            self.hw.send_frame(frame)
            
            # Pauză minimă
            time.sleep(0.005)
            
        return round_survived

    def play_success_animation(self):
        """Ploaie de artificii verzi și galbene pentru a sărbători terminarea rundei"""
        for f in range(60): 
            frame = bytearray(1536)
            self.draw_base(frame) 
            
            for _ in range(25):
                rx = random.randint(0, WIDTH-1)
                ry = random.randint(0, HEIGHT-1)
                c = random.choice([(0, 255, 0), (255, 255, 0), (50, 200, 50)])
                self.hw.set_pixel_physical(frame, rx, ry, c)
                
            self.hw.send_frame(frame)
            time.sleep(0.04)

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
            
            # --- MODIFICARE AICI: Cronometru pe fundal negru! ---
            for count in ['3', '2', '1']:
                self.audio.stop("countdown")
                self.audio.play("countdown")
                for _ in range(25):
                    frame = bytearray(1536) # Creăm cadrul, rămâne complet NEGRU
                    # NU mai desenăm baza (iarba/insulele) în timpul cronometrului
                    for px, py in DIGITS[count]: 
                        self.hw.set_pixel_physical(frame, 7+px, 14+py, COLORS["WHITE"])
                    self.hw.send_frame(frame)
                    time.sleep(0.04)
            # ---------------------------------------------------

            self.audio.stop("countdown") 

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
                
                self.play_success_animation()

        # GAME OVER SEQUENCE
        self.audio.stop_bgm()
        self.audio.stop_all_sfx()
        self.audio.play("game_over")
        self.ui.show_game_over(self.score)
        
        frame = bytearray(1536)
        for y in range(HEIGHT):
            for x in range(WIDTH): self.hw.set_pixel_physical(frame, x, y, (150, 0, 0))
        self.hw.send_frame(frame)
        
        time.sleep(10.0) 
        self.ui.return_to_setup()

if __name__ == "__main__":
    NaturalDisasterGame()