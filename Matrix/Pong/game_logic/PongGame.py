import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Controller import *

import random

class Obstacle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        # Forma de stea (pixeli relativi față de centru)
        self.shape = [(0,0), (0,-1), (0,1), (-1,0), (1,0)] 

    def get_pixels(self):
        return [(self.x + dx, self.y + dy) for dx, dy in self.shape]

#pozitia paletei, scorului playerului si indexul jucatorului(jucator 1 si 2), culoarea paletei(la alegere)
class Player:
    def __init__(self, player_id, color):
        self.player_id = player_id
        self.color = color
        self.y = 1 if player_id == 1 else 30
        self.x = 6  
        self.width = 4
        self.score = 0
    
    def move_to(self, target_x):
        # Calculăm noua poziție astfel încât target_x să fie MIJLOCUL
        # Scădem jumătate din lățime (4 // 2 = 2)
        new_x = target_x - 1
        
        # Limite pentru ca paleta să nu iasă din bordurile verzi (x=0 și x=15)
        # Marginea stângă minimă: 1
        # Marginea stângă maximă: 15 - 4 = 11
        if new_x < 1: 
            new_x = 1
        if new_x > 11: 
            new_x = 11 
        
        self.x = new_x

    def move(self, direction):
        # direction: -1 pentru stânga, 1 pentru dreapta
        current_time = time.time()
        #if current_time - self.last_move_time < 0.05: # Limitează la o mișcare la 50ms
        #    return

        new_x = self.x + direction
        print(f"Jucator {self.player_id} vrea sa se miste in directia {direction}")
        # Verificăm limitele: 0 este marginea stângă, 12 este marginea dreaptă (12+4=16)
        if 0 <= new_x <= (16 - self.width):
            self.x = new_x
        #    self.last_move_time = current_time

class Ball:
    def __init__(self, base_speed=0.5, acceleration=1.05):
        self.base_speed = base_speed
        self.acceleration = acceleration
        self.reset()

    def reset(self):
        self.x = 8.0   # Mijloc orizontal
        self.y = 16.0  # Mijloc vertical
        self.vx = self.base_speed
        self.vy = self.base_speed

    def update(self, p1, p2, obstacles=[]):
        self.x += self.vx
        self.y += self.vy

        # 1. Ricoșeu din bordurile VERZI (Laterale)
        # Verificăm 1.0 și 14.0 ca să nu intre peste pixelii verzi de la col 0 și col 15
        if self.x <= 1.0: 
            self.vx *= -1
            self.x = 1.1
        elif self.x >= 14.0: 
            self.vx *= -1
            self.x = 13.9

        # 2. Logică pentru paleta de SUS (Player 1 la y=1)
        if self.vy < 0:  # Mingea urcă spre P1
            if 1.0 <= self.y <= 1.5: 
                # Verificăm dacă X-ul mingii este între marginile paletei
                if p1.x <= self.x <= p1.x + p1.width:
                    self.vy *= -1
                    self.y = 1.6 
                    self.vx *= 1.05
                    self.vy *= 1.05

        # 3. Logică pentru paleta de JOS (Player 2 la y=30)
        if self.vy > 0:  # Mingea coboară spre P2
            if 29.5 <= self.y <= 30.0: 
                if p2.x <= self.x <= p2.x + p2.width:
                    self.vy *= -1
                    self.y = 29.4
                    self.vx *= 1.05
                    self.vy *= 1.05
        
        # 4. Verificare GOL (Mingea a trecut de palete și a atins bordura ROȘIE)
        if self.y <= 0: # A atins linia roșie de sus
            p2.score += 1
            self.reset()
            return "GOAL_P2"
        
        if self.y >= 31: # A atins linia roșie de jos
            p1.score += 1
            self.reset()
            return "GOAL_P1"
        
        for obs in obstacles:
            for px, py in obs.get_pixels():
                # Verificăm dacă mingea "atinge" un pixel al stelei (distanță mică)
                if abs(self.x - px) < 0.8 and abs(self.y - py) < 0.8:
                    # 1. Inversăm direcția pe axa Y (sus/jos)
                    self.vy *= -1
                    
                    # 2. ADĂUGĂM HAOS: Schimbăm puțin și viteza pe X (stânga/dreapta)
                    # random.uniform(-0.2, 0.2) face ca mingea să plece într-un unghi neașteptat
                    self.vx += random.uniform(-0.2, 0.2)
                    
                    # 3. ACCELERARE: Mingea prinde viteză când lovește un obiect
                    self.vx *= 1.1
                    self.vy *= 1.1
                    
                    # 4. ANTI-STICK: O mișcăm puțin în afara obiectului ca să nu se blocheze
                    self.y += self.vy * 2
                    
                    return "HIT_OBSTACLE"
            
        return None
    
class PongGame:
    def __init__(self, level="Normal", p1_rgb=(255,0,0), p2_rgb=(0,0,255), total_rounds=3):
        obs_counts = {"Easy": 0, "Normal": 2, "Hard": 5}
        count = obs_counts.get(level, 2)
        
        self.obstacles = []
        for _ in range(count):
            # Generăm coordonate random (evităm marginile și paletele)
            ox = random.randint(3, 12)
            oy = random.randint(10, 20)
            self.obstacles.append(Obstacle(ox, oy))
        configs = {
            "Easy":   {"speed": 0.3, "accel": 1.02},
            "Normal": {"speed": 0.5, "accel": 1.05},
            "Hard":   {"speed": 0.8, "accel": 1.10}
        }
        cfg = configs.get(level, configs["Normal"])
        self.total_rounds = total_rounds
        self.button_states = [False] * 512
        self.p1 = Player(1, p1_rgb)
        self.p2 = Player(2, p2_rgb)
        self.ball = Ball(base_speed=cfg["speed"], acceleration=cfg["accel"])
        self.running = True
        self.buffer = bytearray(16 * 32 * 3) # Buffer gol
        self.lock = threading.Lock()
        self.running = True
        self.buffer = bytearray(16 * 32 * 3) # Buffer gol
        self.lock = threading.Lock()
        self.current_round = 1
        # Scoruri pe runde (câte runde a câștigat fiecare)
        self.rounds_won_p1 = 0
        self.rounds_won_p2 = 0
        
        
        # --- ADAUGĂ ASTA ---
        self.state = "COUNTDOWN" 
        self.current_digit = 3
        self.goal_loser = 0

    def reset_for_new_round(self):
        """Resetează doar scorul de puncte și mingea, păstrând rundele."""
        self.p1.score = 0
        self.p2.score = 0
        self.ball.reset()
        self.state = "COUNTDOWN"
    
    def draw_round_small(self, round_num, color):
        """Desenează 'R' și numărul rundei cu un font foarte mic (3x5)."""
        # Matrice 3x5 pentru litera R și cifre
        small_font = {
            'R': [(0,0), (0,1), (0,2), (0,3), (0,4), (1,0), (2,1), (1,2), (2,3), (2,4)],
            '1': [(1,0), (1,1), (1,2), (1,3), (1,4)],
            '2': [(0,0), (1,0), (2,0), (2,1), (1,2), (0,3), (0,4), (1,4), (2,4)],
            '3': [(0,0), (1,0), (2,0), (2,1), (1,2), (2,3), (0,4), (1,4), (2,4)]
        }
        
        # Desenăm 'R' la coordonatele (x=5, y=25)
        for dx, dy in small_font['R']:
            self.set_led(self.buffer, 5 + dx, 25 + dy, color)
            
        # Desenăm cifra rundei lângă 'R' la (x=9, y=25)
        r_str = str(round_num)
        if r_str in small_font:
            for dx, dy in small_font[r_str]:
                self.set_led(self.buffer, 9 + dx, 25 + dy, color)
    
    def draw_round_full(self, round_num, color):
        """Desenează 'ROUND' la y=18 și cifra sub ea la y=26."""
        font = {
            'R': [(0,0), (0,1), (0,2), (0,3), (0,4), (1,0), (2,1), (1,2), (2,3)],
            'O': [(0,0), (1,0), (2,0), (0,1), (2,1), (0,2), (2,2), (0,3), (2,3), (0,4), (1,4), (2,4)],
            'U': [(0,0), (2,0), (0,1), (2,1), (0,2), (2,2), (0,3), (2,3), (0,4), (1,4), (2,4)],
            'N': [(0,0), (0,1), (0,2), (0,3), (0,4), (1,1), (2,0), (2,1), (2,2), (2,3), (2,4)],
            'D': [(0,0), (1,0), (0,1), (2,1), (0,2), (2,2), (0,3), (2,3), (0,4), (1,4)],
            '1': [(1,0), (1,1), (1,2), (1,3), (1,4)],
            '2': [(0,0), (1,0), (2,0), (2,1), (0,2), (1,2), (2,2), (0,3), (0,4), (1,4), (2,4)],
            '3': [(0,0), (1,0), (2,0), (2,1), (1,2), (2,3), (0,4), (1,4), (2,4)]
        }

        # ROUND la y=18 (cam pe la mijlocul ecranului)
        letters = [('R', 0), ('O', 3), ('U', 6), ('N', 9), ('D', 12)]
        for char, x_off in letters:
            for dx, dy in font[char]:
                self.set_led(self.buffer, x_off + dx, 18 + dy, color)

        # CIFRA la y=26 (jos, dar cu spațiu față de ROUND)
        r_str = str(round_num)
        if r_str in font:
            for dx, dy in font[r_str]:
                # Centrat orizontal (x=7)
                self.set_led(self.buffer, 7 + dx, 26 + dy, color)

    def draw_digit(self, digit, color, y_offset=13): # Am adăugat y_offset implicit 13
        """Desenează cifrele pe matrice la înălțimea dorită."""
        digits = {
            '3': [(0,0), (1,0), (2,0), (2,1), (0,2), (1,2), (2,2), (2,3), (0,4), (1,4), (2,4)],
            '2': [(0,0), (1,0), (2,0), (2,1), (0,2), (1,2), (2,2), (0,3), (0,4), (1,4), (2,4)],
            '1': [(1,0), (1,1), (1,2), (1,3), (1,4)],
            '4': [(0,0), (2,0), (0,1), (2,1), (0,2), (1,2), (2,2), (2,3), (2,4)], # Am adăugat și 4/5 just in case
            '5': [(0,0), (1,0), (2,0), (0,1), (0,2), (1,2), (2,2), (2,3), (0,4), (1,4), (2,4)]
        }
        
        digit_str = str(digit)
        if digit_str in digits:
            points = digits[digit_str]
            # x_offset=6 rămâne pentru centrare orizontală
            for dx, dy in points:
                self.set_led(self.buffer, 6 + dx, y_offset + dy, color)

    def draw_stop(self, color):
        """Desenează cuvântul STOP centrat pe matrice."""
        letters = {
            'S': [(0,0),(1,0),(2,0),(0,1),(0,2),(1,2),(2,2),(2,3),(0,4),(1,4),(2,4)],
            'T': [(0,0),(1,0),(2,0),(1,1),(1,2),(1,3),(1,4)],
            'O': [(0,0),(1,0),(2,0),(0,1),(2,1),(0,2),(2,2),(0,3),(2,3),(0,4),(1,4),(2,4)],
            'P': [(0,0),(1,0),(2,0),(0,1),(2,1),(0,2),(1,2),(2,2),(0,3),(0,4)]
        }
        
        # Coordonatele de start (X) pentru fiecare literă
        word = [('S', 0), ('T', 4), ('O', 8), ('P', 12)] 

        self.buffer = bytearray(16 * 32 * 3) # Curățăm ecranul (negru)
        
        for char, x_offset in word:
            for dx, dy in letters[char]:
                # Centrat pe Y (rândul 13)
                self.set_led(self.buffer, x_offset + dx, 13 + dy, color)

    def draw_explosion_animation(self):
        """O explozie masivă pe toată matricea la final de joc."""
        import random
        self.buffer = bytearray(16 * 32 * 3)
        colors = [(255, 255, 255), (255, 215, 0), (255, 69, 0), (0, 255, 255)] # Culori festive
        for _ in range(40): # 40 de scântei pe cadru
            rx = random.randint(0, 15)
            ry = random.randint(0, 31)
            rc = random.choice(colors)
            self.set_led(self.buffer, rx, ry, rc)

    def draw_win_lose(self, winner_id):
        """Desenează WIN pe jumătatea câștigătorului și LOSE pe cealaltă."""
        self.buffer = bytearray(16 * 32 * 3)
        
        letters = {
            'W': [(0,0),(0,1),(0,2),(0,3),(1,4),(2,3),(3,4),(4,0),(4,1),(4,2),(4,3)],
            'I': [(0,0),(0,1),(0,2),(0,3),(0,4)],
            'N': [(0,0),(0,1),(0,2),(0,3),(0,4),(1,1),(2,2),(3,0),(3,1),(3,2),(3,3),(3,4)],
            'L': [(0,0),(0,1),(0,2),(0,3),(0,4),(1,4),(2,4)],
            'O': [(0,0),(1,0),(2,0),(0,1),(2,1),(0,2),(2,2),(0,3),(2,3),(0,4),(1,4),(2,4)],
            'S': [(0,0),(1,0),(2,0),(0,1),(0,2),(1,2),(2,2),(2,3),(0,4),(1,4),(2,4)],
            'E': [(0,0),(1,0),(2,0),(0,1),(0,2),(1,2),(0,3),(0,4),(1,4),(2,4)]
        }
        
        # P1 e sus (rândurile 0-15), P2 e jos (rândurile 16-31)
        y_p1, y_p2 = 5, 21 
        
        if winner_id == 1:
            win_y, lose_y = y_p1, y_p2
            win_color, lose_color = (0, 255, 0), (255, 0, 0) # WIN Verde, LOSE Roșu
        else:
            lose_y, win_y = y_p1, y_p2
            lose_color, win_color = (255, 0, 0), (0, 255, 0)

        # Desenăm WIN (x_offsets: W=2, I=8, N=10)
        for dx, dy in letters['W']: self.set_led(self.buffer, 2 + dx, win_y + dy, win_color)
        for dx, dy in letters['I']: self.set_led(self.buffer, 8 + dx, win_y + dy, win_color)
        for dx, dy in letters['N']: self.set_led(self.buffer, 10 + dx, win_y + dy, win_color)

        # Desenăm LOSE (x_offsets: L=1, O=5, S=9, E=13)
        for dx, dy in letters['L']: self.set_led(self.buffer, 1 + dx, lose_y + dy, lose_color)
        for dx, dy in letters['O']: self.set_led(self.buffer, 5 + dx, lose_y + dy, lose_color)
        for dx, dy in letters['S']: self.set_led(self.buffer, 9 + dx, lose_y + dy, lose_color)
        for dx, dy in letters['E']: self.set_led(self.buffer, 13 + dx, lose_y + dy, lose_color)
        
    def get_real_coords(self, index):
        # Determinăm "fâșia" (0, 1, 2 sau 3) din pachetul de 64
        strip = index // 16
        x_raw = index % 16
        
        # Mapăm fâșia la rândul real al matricei (y)
        # 0 -> rândul 0, 1 -> rândul 1, 2 -> rândul 30, 3 -> rândul 31
        y_map = {0: 0, 1: 1, 2: 30, 3: 31}
        y_real = y_map.get(strip, 0)
        
        # Aplicăm logica Zig-Zag:
        # Dacă rândul real este impar (1, 31), X-ul este inversat
        if y_real % 2 == 0:
            x_real = x_raw
        else:
            x_real = 15 - x_raw
            
        return x_real, y_real
    
    def get_coords_512(self, index):
        y = index // 16   # Rândul real (0 - 31)
        x_raw = index % 16 # Coloana brută (0 - 15)

        # Zig-Zag: Rândurile impare (1, 3, 5... 31) sunt inversate
        if y % 2 == 0:
            x = x_raw
        else:
            x = 15 - x_raw
        return x, y

    def tick(self):
        with self.lock:
            # 1. CAPTURĂM statusul mingii (ex: "GOAL_P1", "GOAL_P2" sau None)
            status = self.ball.update(self.p1, self.p2, self.obstacles)
            
            found_p1 = False
            found_p2 = False

            for i in range(512):
                if self.button_states[i]:
                    x, y = self.get_coords_512(i)
                    if y < 16 and not found_p1:
                        self.p1.move_to(x)
                        found_p1 = True
                    elif y >= 16 and not found_p2:
                        self.p2.move_to(x)
                        found_p2 = True
                if found_p1 and found_p2: break
            
            if self.p1.score >= 11:
                self.rounds_won_p1 += 1
                return self.check_match_winner()
            
            if self.p2.score >= 11:
                self.rounds_won_p2 += 1
                return self.check_match_winner()

            return status
        
    def check_match_winner(self):
        """Decide dacă meciul s-a terminat sau doar runda."""
        # Calculăm de câte runde e nevoie pentru a câștiga (ex: 2 din 3)
        needed_to_win = (self.total_rounds // 2) + 1
        
        if self.rounds_won_p1 >= needed_to_win:
            return "WINNER_P1"
        if self.rounds_won_p2 >= needed_to_win:
            return "WINNER_P2"
        
        self.p1.score = 0
        self.p2.score = 0
        self.ball.reset()
        self.state = "COUNTDOWN"
        return f"ROUND_OVER_{self.current_round}"

    def set_led(self, buffer, target_x, target_y, color):
        # Aceasta este funcția de ZIG-ZAG pe care ai trimis-o tu
        # O folosim pentru a DESENA pe matrice
        if not (0 <= target_x < 16 and 0 <= target_y < 32):
            return

        r, g, b = color
        channel = target_y // 4
        row = target_y % 4
        
        # Logica ZIG-ZAG pentru desen:
        idx = (row * 16 + target_x) if row % 2 == 0 else (row * 16 + (15 - target_x))
        
        offset = idx * 24 + channel 
        if offset + 16 < len(buffer):
            buffer[offset] = g      # Green/Red Swap conform funcției tale
            buffer[offset + 8] = r
            buffer[offset + 16] = b

    def get_coords_from_index(self, index):
        # Aceasta este INVERSA funcției de mai sus
        # O folosim pentru a descifra unde a apasat jucătorul
        y = index // 16
        x_raw = index % 16
        
        # Dacă rândul e impar (1, 3, 5...), indexarea e inversă (Zig-Zag)
        if y % 2 == 0:
            x = x_raw
        else:
            x = 15 - x_raw
        return x, y

    def render(self):
        self.buffer = bytearray(16 * 32 * 3) # Curățăm mereu la începutul cadrului

        if self.state == "COUNTDOWN":
            # 1. Numărătoarea (3, 2, 1) sus de tot (y=2)
            colors = {3: (255,0,0), 2: (255,255,0), 1: (0,255,0)}
            c_digit = self.current_digit
            c_color = colors.get(c_digit, (255,255,255))
            self.draw_digit(c_digit, c_color, y_offset=2) 

            # 2. Textul "ROUND" la mijloc și cifra jos (funcția de mai sus)
            # Folosim Cyan pentru un contrast bun
            self.draw_round_full(self.current_round, (0, 255, 255))
            
            return self.buffer

        # --- DACA SUNTEM LA FINAL DE JOC ---
        if self.state == "GAME_OVER_EXPLOSION":
            self.draw_explosion_animation()
            return self.buffer

        elif self.state == "GAME_OVER_TEXT":
            # self.winner va fi setat din main.py
            self.draw_win_lose(getattr(self, 'winner', 1))
            return self.buffer

        # --- DACA SUNTEM IN PAUZA ---
        elif self.state == "PAUSED":
            # Desenăm STOP cu culoarea Portocalie
            self.draw_stop((255, 165, 0))
            return self.buffer

        # --- DACA JUCAM (PLAYING) ---
        elif self.state == "PLAYING":
            # 1. Borduri Verzi (Laterale)
            for y in range(32):
                self.set_led(self.buffer, 0, y, (0, 255, 0))
                self.set_led(self.buffer, 15, y, (0, 255, 0))
            for obs in self.obstacles:
                for px, py in obs.get_pixels():
                    self.set_led(self.buffer, int(px), int(py), (255, 215, 0))

            # 2. Porti Rosii (Sus/Jos)
            for x in range(1, 15):
                self.set_led(self.buffer, x, 15, (0, 255, 255))

            # 3. Linie mijloc
            for x in range(1, 15):
                self.set_led(self.buffer, x, 15, (20, 20, 20))

            # 4. Palete
            for i in range(self.p1.width):
                self.set_led(self.buffer, int(self.p1.x + i), self.p1.y, self.p1.color)
            for i in range(self.p2.width):
                self.set_led(self.buffer, int(self.p2.x + i), self.p2.y, self.p2.color)

            # 5. Minge
            self.set_led(self.buffer, int(self.ball.x), int(self.ball.y), (255, 255, 255))

            return self.buffer
        
        return self.buffer