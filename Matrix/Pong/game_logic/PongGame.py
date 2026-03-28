import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Controller import *

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
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = 8.0   # Mijloc orizontal
        self.y = 16.0  # Mijloc vertical
        self.vx = 0.5  # Viteza pe X
        self.vy = 0.5  # Viteza pe Y

    def update(self, p1, p2):
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
            
        return None
    
class PongGame:
    def __init__(self):
        self.button_states = [False] * 512
        self.p1 = Player(1, RED)
        self.p2 = Player(2, BLUE)
        self.ball = Ball()
        self.running = True
        self.buffer = bytearray(16 * 32 * 3) # Buffer gol
        self.lock = threading.Lock()
        
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
            self.ball.update(self.p1, self.p2)
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
        self.buffer = bytearray(16 * 32 * 3)
        
        # 1. Borduri Verzi (Laterale)
        for y in range(32):
            self.set_led(self.buffer, 0, y, GREEN)
            self.set_led(self.buffer, 15, y, GREEN)

        # 2. Porti Rosii (Sus/Jos)
        for x in range(1, 15):
            self.set_led(self.buffer, x, 0, RED)
            self.set_led(self.buffer, x, 31, RED)

        # 3. Linie mijloc
        for x in range(1, 15):
            self.set_led(self.buffer, x, 15, (20, 20, 20))

        # 4. Palete (ORANGE conform imaginii tale)
        for i in range(self.p1.width):
            self.set_led(self.buffer, int(self.p1.x + i), self.p1.y, self.p1.color)
        for i in range(self.p2.width):
            self.set_led(self.buffer, int(self.p2.x + i), self.p2.y, self.p2.color)

        # 5. Minge
        self.set_led(self.buffer, int(self.ball.x), int(self.ball.y), WHITE)

        return self.buffer