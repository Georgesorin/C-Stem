import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Controller import *

import random

class Obstacle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.shape = [(0,0), (0,-1), (0,1), (-1,0), (1,0)] 

    def get_pixels(self):
        return [(self.x + dx, self.y + dy) for dx, dy in self.shape]

class Player:
    def __init__(self, player_id, color):
        self.player_id = player_id
        self.color = color
        self.y = 1 if player_id == 1 else 30
        self.x = 6  
        self.width = 4
        self.score = 0
    
    def move_to(self, target_x):
        new_x = target_x - 1
        
        if new_x < 1: 
            new_x = 1
        if new_x > 11: 
            new_x = 11 
        
        self.x = new_x

    def move(self, direction):
        current_time = time.time()

        new_x = self.x + direction
        print(f"Jucator {self.player_id} vrea sa se miste in directia {direction}")
        if 0 <= new_x <= (16 - self.width):
            self.x = new_x

class Ball:
    def __init__(self, base_speed=0.5, acceleration=0.05):
        self.base_speed = base_speed
        self.acceleration = acceleration
        self.x = 8
        self.y = 16
        self.vx = 0
        self.vy = 0
        self.reset()

    def reset(self):
        """Resetează mingea la centru și alege o direcție aleatorie."""
        self.x = 16 // 2
        self.y = 32 // 2
        
        # 1. Alegem aleatoriu jucătorul: -1 (Jucător 1, sus) sau 1 (Jucător 2, jos)
        direction_y = random.choice([-1, 1])
        
        # 2. Stabilim viteza pe verticală bazată pe direcția aleasă
        self.vy = self.base_speed * direction_y
        
        # 3. Adăugăm un unghi aleatoriu pe orizontală (X) ca să nu plece mereu drept
        self.vx = random.uniform(-0.3, 0.3)
        
        print(f"Mingea pleacă spre Jucătorul {'2 (Jos)' if direction_y > 0 else '1 (Sus)'}")

    def update(self, p1, p2, obstacles=[]):
        self.x += self.vx
        self.y += self.vy

        # Coliziune cu pereții laterali
        if self.x <= 0: 
            self.vx *= -1
            self.x = 0.1
        elif self.x >= 15: 
            self.vx *= -1
            self.x = 14.9

        # Coliziune Paletă Jucător 1 (Sus, y=1)
        if self.vy < 0 and 1.0 <= self.y <= 1.5: 
            if p1.x <= self.x <= p1.x + p1.width:
                self.vy *= -1
                self.y = 1.6 
                # Accelerare la fiecare lovitură
                self.vx *= 1.1
                self.vy *= 1.1

        # Coliziune Paletă Jucător 2 (Jos, y=30)
        if self.vy > 0 and 29.5 <= self.y <= 30.0: 
            if p2.x <= self.x <= p2.x + p2.width:
                self.vy *= -1
                self.y = 29.4
                self.vx *= 1.1
                self.vy *= 1.1
        
        # Gol pentru Jucătorul 2 (Mingea a ieșit pe sus)
        if self.y <= 0:
            p2.score += 1
            self.reset() # Aici se apelează logica random de plecare
            return "GOAL_P2"
        
        # Gol pentru Jucătorul 1 (Mingea a ieșit pe jos)
        if self.y >= 31:
            p1.score += 1
            self.reset() # Aici se apelează logica random de plecare
            return "GOAL_P1"
        
        # Coliziune Obstacole
        for obs in obstacles:
            for px, py in obs.get_pixels():
                if abs(self.x - px) < 0.8 and abs(self.y - py) < 0.8:
                    self.vy *= -1
                    self.vx += random.uniform(-0.1, 0.1)
                    return "HIT_OBSTACLE"
            
        return None
    
class PongGame:
    def __init__(self, level="Normal", p1_rgb=(255,0,0), p2_rgb=(0,0,255), total_rounds=3):
        obs_counts = {"Easy": 0, "Normal": 2, "Hard": 5}
        count = obs_counts.get(level, 2)
        self.color_buttons = []
        
        self.obstacles = []
        for _ in range(count):
            ox = random.randint(3, 12)
            oy = random.randint(10, 20)
            self.obstacles.append(Obstacle(ox, oy))
        configs = {
            "Easy":   {"speed": 0.1, "accel": 0.5},
            "Normal": {"speed": 0.2, "accel": 0.75},
            "Hard":   {"speed": 0.3, "accel": 0.75}
        }
        cfg = configs.get(level, configs["Normal"])
        self.total_rounds = total_rounds
        self.button_states = [False] * 512
        self.p1 = Player(1, p1_rgb)
        self.p2 = Player(2, p2_rgb)
        self.ball = Ball(base_speed=cfg["speed"], acceleration=cfg["accel"])
        self.running = True
        self.buffer = bytearray(16 * 32 * 3)
        self.lock = threading.Lock()
        self.running = True
        self.buffer = bytearray(16 * 32 * 3)
        self.lock = threading.Lock()
        self.current_round = 1
        self.rounds_won_p1 = 0
        self.rounds_won_p2 = 0
        
        self.state = "COUNTDOWN" 
        self.current_digit = 3
        self.goal_loser = 0

    def _preset_btn(self, parent, text, r, g, b, fg_col):
        btn = tk.Button(parent, text=text, 
                        bg="#1a1a1a", fg=fg_col, 
                        font=("Consolas", 10, "bold"),
                        relief="flat", padx=10, pady=5, 
                        cursor="hand2", anchor="w")
        
    def apply():
        for b in self.color_buttons:
            b.config(bg="#1a1a1a", relief="flat", highlightthickness=0)
            
        btn.config(bg="#333333", 
                       highlightbackground=fg_col, 
                       highlightcolor=fg_col, 
                       highlightthickness=2)
            
        self._sv_r.set(str(r))
        self._sv_g.set(str(g))
        self._sv_b.set(str(b))
        self._update_preview()

        btn.config(command=apply)
        btn.pack(fill=tk.X, padx=8, pady=2)
        self.color_buttons.append(btn)

    def reset_for_new_round(self):
        self.p1.score = 0
        self.p2.score = 0
        self.ball.reset()
        self.state = "COUNTDOWN"
    
    def draw_round_small(self, round_num, color):
        small_font = {
            'R': [(0,0), (0,1), (0,2), (0,3), (0,4), (1,0), (2,1), (1,2), (2,3), (2,4)],
            '1': [(1,0), (1,1), (1,2), (1,3), (1,4)],
            '2': [(0,0), (1,0), (2,0), (2,1), (1,2), (0,3), (0,4), (1,4), (2,4)],
            '3': [(0,0), (1,0), (2,0), (2,1), (1,2), (2,3), (0,4), (1,4), (2,4)]
        }
        
        for dx, dy in small_font['R']:
            self.set_led(self.buffer, 5 + dx, 25 + dy, color)
            
        r_str = str(round_num)
        if r_str in small_font:
            for dx, dy in small_font[r_str]:
                self.set_led(self.buffer, 9 + dx, 25 + dy, color)
    
    def draw_round_full(self, round_num, color):
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

        letters = [('R', 0), ('O', 3), ('U', 6), ('N', 9), ('D', 12)]
        for char, x_off in letters:
            for dx, dy in font[char]:
                self.set_led(self.buffer, x_off + dx, 18 + dy, color)

        r_str = str(round_num)
        if r_str in font:
            for dx, dy in font[r_str]:
                # Centrat orizontal (x=7)
                self.set_led(self.buffer, 7 + dx, 26 + dy, color)

    def draw_digit(self, digit, color, y_offset=13):
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
            for dx, dy in points:
                self.set_led(self.buffer, 6 + dx, y_offset + dy, color)

    def draw_stop(self, color):
        letters = {
            'S': [(0,0),(1,0),(2,0),(0,1),(0,2),(1,2),(2,2),(2,3),(0,4),(1,4),(2,4)],
            'T': [(0,0),(1,0),(2,0),(1,1),(1,2),(1,3),(1,4)],
            'O': [(0,0),(1,0),(2,0),(0,1),(2,1),(0,2),(2,2),(0,3),(2,3),(0,4),(1,4),(2,4)],
            'P': [(0,0),(1,0),(2,0),(0,1),(2,1),(0,2),(1,2),(2,2),(0,3),(0,4)]
        }
        
        word = [('S', 0), ('T', 4), ('O', 8), ('P', 12)] 

        self.buffer = bytearray(16 * 32 * 3) 
        
        for char, x_offset in word:
            for dx, dy in letters[char]:
                # Centrat pe Y (rândul 13)
                self.set_led(self.buffer, x_offset + dx, 13 + dy, color)

    def draw_explosion_animation(self):
        import random
        self.buffer = bytearray(16 * 32 * 3)
        colors = [(255, 255, 255), (255, 215, 0), (255, 69, 0), (0, 255, 255)] 
        for _ in range(40):
            rx = random.randint(0, 15)
            ry = random.randint(0, 31)
            rc = random.choice(colors)
            self.set_led(self.buffer, rx, ry, rc)

    def draw_win_lose(self, winner_id):
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
        
        y_p1, y_p2 = 5, 21 
        
        if winner_id == 1:
            win_y, lose_y = y_p1, y_p2
            win_color, lose_color = (0, 255, 0), (255, 0, 0)
        else:
            lose_y, win_y = y_p1, y_p2
            lose_color, win_color = (255, 0, 0), (0, 255, 0)

        for dx, dy in letters['W']: self.set_led(self.buffer, 2 + dx, win_y + dy, win_color)
        for dx, dy in letters['I']: self.set_led(self.buffer, 8 + dx, win_y + dy, win_color)
        for dx, dy in letters['N']: self.set_led(self.buffer, 10 + dx, win_y + dy, win_color)

        for dx, dy in letters['L']: self.set_led(self.buffer, 1 + dx, lose_y + dy, lose_color)
        for dx, dy in letters['O']: self.set_led(self.buffer, 5 + dx, lose_y + dy, lose_color)
        for dx, dy in letters['S']: self.set_led(self.buffer, 9 + dx, lose_y + dy, lose_color)
        for dx, dy in letters['E']: self.set_led(self.buffer, 13 + dx, lose_y + dy, lose_color)
        
    def get_real_coords(self, index):
        strip = index // 16
        x_raw = index % 16
        
        y_map = {0: 0, 1: 1, 2: 30, 3: 31}
        y_real = y_map.get(strip, 0)
        
        if y_real % 2 == 0:
            x_real = x_raw
        else:
            x_real = 15 - x_raw
            
        return x_real, y_real
    
    def get_coords_512(self, index):
        y = index // 16
        x_raw = index % 16

        if y % 2 == 0:
            x = x_raw
        else:
            x = 15 - x_raw
        return x, y

    def tick(self):
        with self.lock:
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
        if not (0 <= target_x < 16 and 0 <= target_y < 32):
            return

        r, g, b = color
        channel = target_y // 4
        row = target_y % 4
        
        idx = (row * 16 + target_x) if row % 2 == 0 else (row * 16 + (15 - target_x))
        
        offset = idx * 24 + channel 
        if offset + 16 < len(buffer):
            buffer[offset] = g
            buffer[offset + 8] = r
            buffer[offset + 16] = b

    def get_coords_from_index(self, index):
        y = index // 16
        x_raw = index % 16
        
        if y % 2 == 0:
            x = x_raw
        else:
            x = 15 - x_raw
        return x, y

    def render(self):
        self.buffer = bytearray(16 * 32 * 3)

        if self.state == "COUNTDOWN":
            colors = {3: (255,0,0), 2: (255,255,0), 1: (0,255,0)}
            c_digit = self.current_digit
            c_color = colors.get(c_digit, (255,255,255))
            self.draw_digit(c_digit, c_color, y_offset=2) 

            self.draw_round_full(self.current_round, (0, 255, 255))
            
            return self.buffer

        if self.state == "GAME_OVER_EXPLOSION":
            self.draw_explosion_animation()
            return self.buffer

        elif self.state == "GAME_OVER_TEXT":
            self.draw_win_lose(getattr(self, 'winner', 1))
            return self.buffer

        elif self.state == "PAUSED":
            self.draw_stop((255, 165, 0))
            return self.buffer

        elif self.state == "PLAYING":
            for y in range(32):
                self.set_led(self.buffer, 0, y, (0, 255, 0))
                self.set_led(self.buffer, 15, y, (0, 255, 0))
            for obs in self.obstacles:
                for px, py in obs.get_pixels():
                    self.set_led(self.buffer, int(px), int(py), (255, 215, 0))

            for x in range(1, 15):
                self.set_led(self.buffer, x, 15, (0, 255, 255))

            for x in range(1, 15):
                self.set_led(self.buffer, x, 15, (20, 20, 20))

            for i in range(self.p1.width):
                self.set_led(self.buffer, int(self.p1.x + i), self.p1.y, self.p1.color)
            for i in range(self.p2.width):
                self.set_led(self.buffer, int(self.p2.x + i), self.p2.y, self.p2.color)

            self.set_led(self.buffer, int(self.ball.x), int(self.ball.y), (255, 255, 255))

            return self.buffer
        
        return self.buffer