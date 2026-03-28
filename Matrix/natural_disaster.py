import socket
import threading
import time
import math
import random
import tkinter as tk
from Controller import NetworkManager

# ==========================================
# 1. CONFIGURAȚIE ECHIPĂ ȘI REȚEA
# ==========================================
NUM_PLAYERS = 5 # Dificultatea și numărul de insule se adaptează automat la acest număr!

WIDTH, HEIGHT = 16, 32 
TARGET_IP = "127.0.0.1"
PORT_SEND = 5001 
PORT_RECV = 5000 

COLORS = {
    "GRASS": (0, 80, 0),
    "ISLAND": (120, 120, 120),
    "WATER": (0, 0, 255),
    "METEOR_WARN": (255, 0, 0),
    "METEOR_IMPACT": (255, 100, 0),
    "CRATER": (40, 40, 40),
    "WHITE": (255, 255, 255),
    "SMOKE": (150, 150, 150)
}

class NaturalDisasterGame:
    def __init__(self):
        self.net = NetworkManager()
        self.net.target_ip = TARGET_IP
        self.net.send_port = PORT_SEND
        
        self.running = True
        
        # --- SISTEMUL DE SCOR ȘI VIEȚI ---
        self.score = 0
        self.lives = min(NUM_PLAYERS, 7) # Maxim 7 vieți
        
        # --- SECVENȚA DE JOCURI ---
        self.game_sequence = ["water", "meteors", "fire"]
        self.current_game_index = 0
        
        self.islands = []
        self.meteors = []         
        self.craters = [] 
        self.fire_pixels = set() 
        
        self.pressed_buttons = set() 
        self.active_splashes = []
        self.splashing_positions = set()

        self.digits = {
            '3': [(0,0), (1,0), (2,0), (2,1), (1,2), (2,2), (2,3), (2,4), (1,4), (0,4)],
            '2': [(0,0), (1,0), (2,0), (2,1), (0,2), (1,2), (2,2), (0,3), (0,4), (1,4), (2,4)],
            '1': [(1,0), (1,1), (1,2), (1,3), (1,4)]
        }
        self.all_corners = [(0, 0), (WIDTH-1, 0), (0, HEIGHT-1), (WIDTH-1, HEIGHT-1)]

        # --- DASHBOARD UI ---
        self.root = tk.Tk()
        self.root.title("LEDHACK - Dashboard")
        self.root.geometry("600x500")
        self.root.configure(bg="black")
        
        self.lbl_game = tk.Label(self.root, text="DISASTER SURVIVAL", font=("Consolas", 30, "bold"), bg="black", fg="white")
        self.lbl_game.pack(pady=20)
        
        self.lbl_lives = tk.Label(self.root, text="❤️" * self.lives, font=("Consolas", 35), bg="black", fg="red")
        self.lbl_lives.pack(pady=5)
        
        self.lbl_instruction = tk.Label(self.root, text="Se încarcă...", font=("Consolas", 18), bg="black", fg="yellow")
        self.lbl_instruction.pack(pady=10)
        
        self.lbl_score = tk.Label(self.root, text="SCOR: 0", font=("Consolas", 50, "bold"), bg="black", fg="#00FF00")
        self.lbl_score.pack(side="bottom", pady=40)

        threading.Thread(target=self.input_listener, daemon=True).start()
        threading.Thread(target=self.game_loop, daemon=True).start()
        self.root.mainloop()

    # ==========================================
    # LOGICĂ DE AFIȘARE ȘI RENDERIZARE
    # ==========================================
    def update_dashboard(self, status, instr, color="white"):
        self.root.after(0, lambda: self.lbl_game.config(text=status, fg=color))
        self.root.after(0, lambda: self.lbl_instruction.config(text=instr))
        self.root.after(0, lambda: self.lbl_score.config(text=f"SCOR: {self.score}"))
        self.root.after(0, lambda: self.lbl_lives.config(text="❤️" * max(0, self.lives)))

    def show_game_over(self):
        self.root.after(0, lambda: self.lbl_game.config(text="GAME OVER", fg="red"))
        self.root.after(0, lambda: self.lbl_instruction.config(text="Echipa a fost eliminată!", fg="white"))
        self.root.after(0, lambda: self.lbl_score.config(text=f"PUNCTAJ FINAL: {self.score}", fg="yellow"))
        self.root.after(0, lambda: self.lbl_lives.config(text="💀💀💀"))
        
        frame = bytearray(1536)
        for y in range(HEIGHT):
            for x in range(WIDTH): self.set_pixel_physical(frame, x, y, (150, 0, 0))
        self.net.send_packet(frame)

    def reset_entire_game(self):
        self.score = 0
        self.lives = min(NUM_PLAYERS, 7)
        self.current_game_index = 0 # O luăm mereu de la capăt când începe o echipă nouă
        self.update_dashboard("NOU JOC", "Pregătiți-vă!", "white")

    def set_pixel_physical(self, buffer, x, y, color):
        if not (0 <= x < WIDTH and 0 <= y < HEIGHT): return
        channel = y // 4
        row_in_ch = y % 4
        idx = (row_in_ch * 16 + x) if row_in_ch % 2 == 0 else (row_in_ch * 16 + (15 - x))
        offset = idx * 24 + channel
        if offset + 16 < len(buffer):
            buffer[offset], buffer[offset + 8], buffer[offset + 16] = color[1], color[0], color[2]

    def draw_base(self, frame):
        for y in range(HEIGHT):
            for x in range(WIDTH): self.set_pixel_physical(frame, x, y, COLORS["GRASS"])
        for (ix, iy, iw, ih) in self.islands:
            for x in range(ix, ix + iw):
                for y in range(iy, iy + ih): self.set_pixel_physical(frame, x, y, COLORS["ISLAND"])

    def draw_splashes(self, frame, base_color=COLORS["WHITE"]):
        for s in self.active_splashes[:]:
            sx, sy, life = s['x'], s['y'], s['life']
            if life >= 5: self.set_pixel_physical(frame, sx, sy, base_color)
            elif life >= 3:
                for dx, dy in [(0,0), (1,0), (-1,0), (0,1), (0,-1)]: self.set_pixel_physical(frame, sx + dx, sy + dy, base_color)
            elif life >= 1:
                for dx, dy in [(1,1), (-1,-1), (1,-1), (-1,1)]: self.set_pixel_physical(frame, sx + dx, sy + dy, base_color)
            s['life'] -= 1
            if s['life'] <= 0:
                self.active_splashes.remove(s)
                self.splashing_positions.discard((sx, sy))

    # ==========================================
    # LOGICĂ DE JOCURI
    # ==========================================
    def register_hit(self, px, py):
        """Înregistrează o coliziune, scade o viață și generează animația"""
        self.active_splashes.append({'x': px, 'y': py, 'life': 6})
        self.splashing_positions.add((px, py))
        self.lives -= 1
        self.root.after(0, lambda: self.lbl_lives.config(text="❤️" * max(0, self.lives)))

    # --- 1. APĂ ---
    def play_water(self):
        self.update_dashboard("INUNDAȚIE!", "Refugiază-te pe insule!", "#00AAFF")
        active_corners = random.sample(self.all_corners, k=random.randint(1, 3))
        max_dist = math.sqrt(WIDTH**2 + HEIGHT**2)
        
        for f in range(300):
            if self.lives <= 0: break 
            frame = bytearray(1536); self.draw_base(frame)
            water_radius = max_dist * (f / 300.0)
            
            # Desenăm apa
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    dist = min([math.sqrt((x-cx)**2 + (y-cy)**2) for cx, cy in active_corners])
                    if dist < water_radius:
                        on_island = any(ix <= x < ix+3 and iy <= y < iy+3 for ix, iy, iw, ih in self.islands)
                        if not on_island: self.set_pixel_physical(frame, x, y, COLORS["WATER"])
            
            # Detecție pași
            for px, py in self.pressed_buttons:
                if (px, py) in self.splashing_positions: continue
                dist = min([math.sqrt((px-cx)**2 + (py-cy)**2) for cx, cy in active_corners])
                on_island = any(ix <= px < ix+3 and iy <= py < iy+3 for ix, iy, iw, ih in self.islands)
                if dist < water_radius and not on_island:
                    self.register_hit(px, py)

            self.draw_splashes(frame, COLORS["WHITE"])
            self.net.send_packet(frame); time.sleep(0.04)
        return True

    # --- 2. METEORIȚI ---
    def play_meteors(self):
        self.update_dashboard("METEORIȚI!", "Evită exploziile!", "red")
        
        for f in range(350):
            if self.lives <= 0: break 
            frame = bytearray(1536); self.draw_base(frame)
            
            # Desenăm craterele vechi
            for c in self.craters[:]:
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]: self.set_pixel_physical(frame, c['x']+dx, c['y']+dy, COLORS["CRATER"])
                c['life'] -= 1
                if c['life'] <= 0: self.craters.remove(c)
                
            # Generăm meteoriți
            if f % 15 == 0: self.meteors.append({'x': random.randint(1, WIDTH-2), 'y': random.randint(1, HEIGHT-2), 'timer': 35})
                
            for m in self.meteors[:]:
                mx, my, timer = m['x'], m['y'], m['timer']
                if timer > 8: 
                    # Warning intermitent
                    if f % 4 == 0: self.set_pixel_physical(frame, mx, my, COLORS["METEOR_WARN"])
                elif timer > 0:
                    # Explozie portocalie
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]: self.set_pixel_physical(frame, mx+dx, my+dy, COLORS["METEOR_IMPACT"])
                    if timer == 1: self.craters.append({'x': mx, 'y': my, 'life': 100})
                    
                    # Coliziune cu jucătorii
                    for px, py in self.pressed_buttons:
                        if (px, py) in self.splashing_positions: continue
                        if abs(px - mx) <= 1 and abs(py - my) <= 1:
                            self.register_hit(px, py)
                            
                m['timer'] -= 1
                if m['timer'] <= -4: self.meteors.remove(m)
                
            self.draw_splashes(frame, COLORS["WHITE"])
            self.net.send_packet(frame); time.sleep(0.04)
        return True

    # --- 3. INCENDIU DE PĂDURE ---
    def play_fire(self):
        self.update_dashboard("INCENDIU!", "Calcă pe foc să-l stingi!", "orange")
        
        # Focare inițiale dinamice
        num_focare = max(2, NUM_PLAYERS // 2 + 1)
        for _ in range(num_focare):
            self.fire_pixels.add((random.randint(1, WIDTH-2), random.randint(1, HEIGHT-2)))
            
        # Dificultate adaptivă (Interval și Șansă)
        spread_interval = max(3, 12 - NUM_PLAYERS) 
        spread_chance = 0.05 + (NUM_PLAYERS * 0.03) 
        max_fire_pixels = int((WIDTH * HEIGHT) * 0.40) # Prag de 40% (aprox 204 pixeli)
        
        round_survived = True

        for f in range(350):
            if self.lives <= 0: break
            frame = bytearray(1536); self.draw_base(frame)
            
            # 1. Extinderea Focului
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
            
            # 2. Stingerea Focului (Interacțiune jucători)
            for px, py in list(self.pressed_buttons):
                if (px, py) in self.fire_pixels:
                    self.fire_pixels.remove((px, py))
                    self.score += 1 # Punct obținut prin stingere
                    self.root.after(0, lambda: self.lbl_score.config(text=f"SCOR: {self.score}"))
                    
                    if not any(s['x'] == px and s['y'] == py for s in self.active_splashes):
                        self.active_splashes.append({'x': px, 'y': py, 'life': 4})
                        self.splashing_positions.add((px, py))

            # 3. CONDIȚIA DE EȘEC (> 40%)
            if len(self.fire_pixels) > max_fire_pixels: 
                self.update_dashboard("FOC SCĂPAT DE SUB CONTROL!", "Prea mult foc! Se pierde o viață...", "red")
                self.lives -= 1
                self.root.after(0, lambda: self.lbl_lives.config(text="❤️" * max(0, self.lives)))
                
                for y in range(HEIGHT):
                    for x in range(WIDTH): self.set_pixel_physical(frame, x, y, (200, 0, 0))
                self.net.send_packet(frame)
                time.sleep(1.0)
                
                round_survived = False
                break

            # 4. Desenăm focul
            for fx, fy in self.fire_pixels:
                fire_color = (255, random.randint(20, 100), 0) 
                self.set_pixel_physical(frame, fx, fy, fire_color)

            self.draw_splashes(frame, COLORS["SMOKE"])
            self.net.send_packet(frame); time.sleep(0.04)
            
        return round_survived

    # ==========================================
    # ENGINE & LOOP PRINCIPAL
    # ==========================================
    def game_loop(self):
        while self.running:
            # Game Over Check
            if self.lives <= 0:
                self.show_game_over()
                time.sleep(10.0) 
                self.reset_entire_game()
                continue
            
            # Resetăm nivelul (inclusiv insulele adaptate la NUM_PLAYERS)
            self.active_splashes.clear()
            self.splashing_positions.clear()
            self.meteors.clear()
            self.craters.clear()
            self.fire_pixels.clear()
            
            min_islands = max(2, NUM_PLAYERS // 2 + 1)
            num_islands = random.randint(min_islands, min_islands + 1)
            self.islands = [[random.randint(1, WIDTH-4), random.randint(1, HEIGHT-4), 3, 3] for _ in range(num_islands)]
            
            # Countdown
            self.update_dashboard("PREGĂTIRE...", "Stai pe poziții!")
            for count in ['3', '2', '1']:
                for _ in range(25):
                    frame = bytearray(1536); self.draw_base(frame)
                    for px, py in self.digits[count]: self.set_pixel_physical(frame, 7+px, 14+py, COLORS["WHITE"])
                    self.net.send_packet(frame); time.sleep(0.04)

            # --- ALEGERE SECVENȚIALĂ A JOCULUI ---
            game_mode = self.game_sequence[self.current_game_index]
            
            # Trecem la următorul index (0 -> 1 -> 2 -> 0)
            self.current_game_index = (self.current_game_index + 1) % len(self.game_sequence)
            
            round_success = True
            if game_mode == "water": round_success = self.play_water()
            elif game_mode == "meteors": round_success = self.play_meteors()
            else: round_success = self.play_fire()

            # Scorul de supraviețuire (dacă runda s-a terminat cu bine)
            if self.lives > 0 and round_success:
                self.score += self.lives 
                self.update_dashboard("RUNDĂ TERMINATĂ!", f"+{self.lives} Puncte de Supraviețuire!", "green")
                time.sleep(3.0)

    def input_listener(self):
        """Ascultă UDP-ul de la Simulator sau Matrix Controller"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try: sock.bind(("0.0.0.0", PORT_RECV))
        except: return
            
        while self.running:
            try:
                data, _ = sock.recvfrom(2048)
                if len(data) >= 1373 and data[0] == 0x88:
                    current_pressed = set()
                    for ch in range(8):
                        base = 2 + ch * 171
                        for led in range(64):
                            if data[base + 1 + led] == 0xCC:
                                row, col = led // 16, led % 16
                                x = col if row % 2 == 0 else 15 - col
                                y = ch * 4 + row
                                current_pressed.add((x, y))
                    self.pressed_buttons = current_pressed
            except: pass

if __name__ == "__main__":
    NaturalDisasterGame()