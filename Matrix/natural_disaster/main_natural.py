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
    """
    Motorul principal al jocului (Game Engine).
    Gestionează starea rundelor, comunicarea cu interfața grafică (UI),
    sistemul audio și logica individuală a celor 3 mini-jocuri.
    """

    def __init__(self):
        # 1. Inițializare Module (Hardware, UI, Audio)
        self.hw = MatrixHardware()
        self.ui = DashboardUI(self.start_game_logic) 
        self.audio = AudioManager()

        # 2. Setări Joc (Se actualizează din meniul principal)
        self.current_game_mode = None
        self.num_players = 2
        self.difficulty = "Normal"
        
        # 3. Statistici Jucători
        self.score = 0  # Reprezintă numărul de runde supraviețuite
        self.lives = 0
        
        # 4. Entități Joc (Elementele de pe podea)
        self.islands = []
        self.meteors = []         
        self.craters = [] 
        self.fire_pixels = set() 
        self.active_splashes = []
        self.splashing_positions = set()

        # Blocăm firul principal (Main Thread) cu interfața grafică
        self.ui.run()

    # ==========================================
    # CONTROLUL FLUXULUI DE JOC
    # ==========================================

    def start_game_logic(self, game_mode, players, difficulty):
        """
        Funcție apelată automat de interfața grafică când se apasă START.
        Primește parametrii selectați de jucători și pornește firul de execuție al jocului.
        """
        self.current_game_mode = game_mode
        self.num_players = players
        self.difficulty = difficulty
        self.lives = min(players, 7) # Maxim 7 vieți, indiferent de câți jucători sunt
        self.score = 0
        
        # Actualizăm UI-ul cu noile date
        self.ui.update_dashboard("PREGĂTIRE", f"Mod: {difficulty} | Jucători: {players}", "white")
        self.ui.update_score(self.score)
        self.ui.update_lives(self.lives)
        
        self.audio.play_bgm()

        # Pornim bucla de joc pe un fir de execuție separat (Background Thread)
        # Astfel, interfața grafică nu va "îngheța" în timp ce rulează animațiile.
        threading.Thread(target=self.game_loop, daemon=True).start()

    def _reset_round_state(self):
        """Curăță toate pericolele de pe podea înainte de o nouă rundă."""
        self.active_splashes.clear()
        self.splashing_positions.clear()
        self.meteors.clear()
        self.craters.clear()
        self.fire_pixels.clear()
        
        # Generăm insule noi pentru runda următoare
        min_islands = max(2, self.num_players // 2 + 1)
        num_islands = random.randint(min_islands, min_islands + 1)
        self.islands = [[random.randint(1, WIDTH-4), random.randint(1, HEIGHT-4), 3, 3] for _ in range(num_islands)]

    def get_difficulty_multiplier(self):
        """
        [BONUS STONE] - Ajustează viteza și cantitatea pericolelor dinamic.
        Returnează un coeficient: < 1 înseamnă mai rapid, > 1 înseamnă mai lent.
        """
        if self.difficulty == "Easy": return 1.5
        elif self.difficulty == "Hard": return 0.6
        return 1.0 # Normal

    # ==========================================
    # SISTEM DE DESENARE ȘI INTERACȚIUNE
    # ==========================================

    def _draw_base(self, frame):
        """Desenează elementele statice (iarba și insulele sigure)."""
        for y in range(HEIGHT):
            for x in range(WIDTH): 
                self.hw.set_pixel_physical(frame, x, y, COLORS["GRASS"])
                
        for (ix, iy, iw, ih) in self.islands:
            for x in range(ix, ix + iw):
                for y in range(iy, iy + ih): 
                    self.hw.set_pixel_physical(frame, x, y, COLORS["ISLAND"])

    def _draw_splashes(self, frame, base_color=COLORS["WHITE"]):
        """Efect vizual de stropi/explozie când un jucător este lovit."""
        for s in self.active_splashes[:]:
            sx, sy, life = s['x'], s['y'], s['life']
            if life >= 5: 
                self.hw.set_pixel_physical(frame, sx, sy, base_color)
            elif life >= 3:
                for dx, dy in [(0,0), (1,0), (-1,0), (0,1), (0,-1)]: 
                    self.hw.set_pixel_physical(frame, sx + dx, sy + dy, base_color)
            elif life >= 1:
                for dx, dy in [(1,1), (-1,-1), (1,-1), (-1,1)]: 
                    self.hw.set_pixel_physical(frame, sx + dx, sy + dy, base_color)
            
            s['life'] -= 1
            if s['life'] <= 0:
                self.active_splashes.remove(s)
                self.splashing_positions.discard((sx, sy))

    def _register_hit(self, px, py, hit_type):
        """Procesează logica de daună (pierde o viață, redă sunet, creează explozie)."""
        self.active_splashes.append({'x': px, 'y': py, 'life': 6})
        self.splashing_positions.add((px, py))
        
        self.lives -= 1
        self.ui.update_lives(self.lives)
        self.audio.play(hit_type)

    def _play_success_animation(self):
        """Animație de victorie la finalul fiecărei runde (Scântei verzi)."""
        for f in range(60): 
            frame = bytearray(1536)
            self._draw_base(frame) 
            for _ in range(25):
                rx, ry = random.randint(0, WIDTH-1), random.randint(0, HEIGHT-1)
                c = random.choice([(0, 255, 0), (255, 255, 0), (50, 200, 50)])
                self.hw.set_pixel_physical(frame, rx, ry, c)
            self.hw.send_frame(frame)
            time.sleep(0.01)

    # ==========================================
    # LOGICA MINIJOCURILOR (Cele 3 Jocuri Matrix)
    # ==========================================

    def play_lava(self):
        self.ui.update_dashboard("ERUPȚIE DE LAVĂ!", "Refugiază-te pe insule!", "orange")
        active_corners = random.sample(ALL_CORNERS, k=random.randint(1, 3))
        max_dist = math.sqrt(WIDTH**2 + HEIGHT**2)
        
        diff_mult = self.get_difficulty_multiplier()
        # --- JOC MAI LENT: Am crescut baza de la 120 la 160 de cadre. Lava curge mai domol!
        total_frames = int((160 + (self.num_players * 20)) * diff_mult)
        
        for f in range(total_frames):
            if self.lives <= 0: break 
            frame = bytearray(1536)
            self._draw_base(frame)
            
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
                    self._register_hit(px, py, "splash")

            self._draw_splashes(frame, COLORS["LAVA_SPLASH"])
            self.hw.send_frame(frame)
            time.sleep(0.02) 
            
        return True

    def play_meteors(self):
        self.ui.update_dashboard("METEORIȚI!", "Evită zonele ROȘII!", "red")
        diff_mult = self.get_difficulty_multiplier()
        
        # --- JOC MAI LENT ---
        # Apar mai rar (am crescut de la 7 la 10)
        spawn_rate = max(6, int((10 + self.num_players) * diff_mult)) 
        # Timp mai mare de avertizare (am crescut de la 35 la 45). Ai timp lejer să fugi.
        meteor_timer = max(25, int((45 + self.num_players * 4) * diff_mult))
        
        for f in range(250):
            if self.lives <= 0: break 
            frame = bytearray(1536)
            self._draw_base(frame)
            
            for c in self.craters[:]:
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]: self.hw.set_pixel_physical(frame, c['x']+dx, c['y']+dy, COLORS["CRATER"])
                c['life'] -= 1
                if c['life'] <= 0: self.craters.remove(c)
                
            if f % spawn_rate == 0: 
                self.meteors.append({'x': random.randint(1, WIDTH-2), 'y': random.randint(1, HEIGHT-2), 'timer': meteor_timer})
                
            for m in self.meteors[:]:
                mx, my, timer = m['x'], m['y'], m['timer']
                
                if timer > 8: 
                    if f % 3 == 0: 
                        for dx in [-1, 0, 1]:
                            for dy in [-1, 0, 1]:
                                if dx == 0 and dy == 0: self.hw.set_pixel_physical(frame, mx, my, COLORS["METEOR_WARN"]) 
                                else: self.hw.set_pixel_physical(frame, mx+dx, my+dy, (80, 0, 0)) 
                elif timer > 0:
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]: self.hw.set_pixel_physical(frame, mx+dx, my+dy, COLORS["METEOR_IMPACT"])
                        
                    if timer == 1: 
                        self.craters.append({'x': mx, 'y': my, 'life': 60})
                        self.audio.play("meteor_boom")
                    
                    for px, py in self.hw.pressed_buttons:
                        if (px, py) in self.splashing_positions: continue
                        if abs(px - mx) <= 1 and abs(py - my) <= 1:
                            self._register_hit(px, py, "damage") 
                            
                m['timer'] -= 1
                if m['timer'] <= -3: self.meteors.remove(m)
                
            self._draw_splashes(frame, COLORS["WHITE"])
            self.hw.send_frame(frame)
            time.sleep(0.02)
            
        return True

    def play_fire(self):
        self.ui.update_dashboard("INCENDIU!", "Calcă pe foc să-l stingi!", "orange")
        diff_mult = self.get_difficulty_multiplier()
        
        num_focare = max(2, self.num_players // 2 + 1)
        for _ in range(num_focare):
            self.fire_pixels.add((random.randint(1, WIDTH-2), random.randint(1, HEIGHT-2)))
            
        # --- JOC MAI LENT ---
        # Focul "sare" de la o căsuță la alta mai rar (baza crescută la 5)
        spread_interval = max(3, int((5 + self.num_players) * diff_mult)) 
        # Șansa ca focul să se extindă a scăzut (de la 0.12 la 0.09)
        spread_chance = max(0.03, (0.09 - (self.num_players * 0.01)) / diff_mult) 
        
        max_fire_pixels = int((WIDTH * HEIGHT) * 0.45) 
        round_survived = True

        for f in range(250):
            if self.lives <= 0: break
            frame = bytearray(1536)
            self._draw_base(frame)
            
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

            self._draw_splashes(frame, COLORS["SMOKE"])
            self.hw.send_frame(frame)
            time.sleep(0.02)
            
        return round_survived

    # ==========================================
    # BUCLA PRINCIPALĂ A MOTORULUI
    # ==========================================

    def game_loop(self):
        """Rulează continuu atâta timp cât jucătorii mai au vieți."""
        while self.lives > 0:
            self._reset_round_state()
            
            # --- 1. NUMĂRĂTOAREA INVERSĂ ---
            self.ui.update_dashboard("PREGĂTIRE...", "Stai pe poziții!", "white")
            for count in ['3', '2', '1']:
                self.audio.stop("countdown")
                self.audio.play("countdown")
                for _ in range(25):
                    frame = bytearray(1536)
                    for px, py in DIGITS[count]: 
                        self.hw.set_pixel_physical(frame, 7+px, 14+py, COLORS["WHITE"])
                    self.hw.send_frame(frame)
                    time.sleep(0.04)

            self.audio.stop("countdown") 
            
            # --- 2. RULAREA RUNDEI ---
            round_success = True
            
            if self.current_game_mode == "lava": 
                round_success = self.play_lava()
            elif self.current_game_mode == "meteors": 
                round_success = self.play_meteors()
            elif self.current_game_mode == "fire": 
                round_success = self.play_fire()

            # --- 3. VERIFICARE REZULTAT ---
            if self.lives > 0 and round_success:
                self.score += 1 
                self.ui.update_score(self.score)
                self.ui.update_dashboard("RUNDĂ SUPRAVIEȚUITĂ!", "Pregătiți-vă pentru următoarea!", "green")
                self._play_success_animation()

        # --- 4. GAME OVER SEQUENCE ---
        self.audio.stop_bgm()
        self.audio.stop_all_sfx()
        self.audio.play("game_over")
        self.ui.show_game_over(self.score)
        
        # Facem toată podeaua roșie permanent la Game Over
        frame = bytearray(1536)
        for y in range(HEIGHT):
            for x in range(WIDTH): 
                self.hw.set_pixel_physical(frame, x, y, (150, 0, 0))
        self.hw.send_frame(frame)
        
        # Aici firul de execuție se termină pașnic.
        # Ecranul rămâne cu Game Over până când jucătorul apasă
        # butonul "Înapoi la Meniu" din interfața grafică.

if __name__ == "__main__":
    NaturalDisasterGame()