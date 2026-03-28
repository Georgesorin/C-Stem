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
NUM_PLAYERS = 5 # Schimbă aici câți jucători sunt în echipă

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
    "WHITE": (255, 255, 255)
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
        
        self.islands = []
        self.meteors = []         
        self.craters = [] 
        
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
        
        # Indicator Vieți (Inimi)
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
    # LOGICĂ DE AFIȘARE
    # ==========================================
    def update_dashboard(self, status, instr, color="white"):
        self.root.after(0, lambda: self.lbl_game.config(text=status, fg=color))
        self.root.after(0, lambda: self.lbl_instruction.config(text=instr))
        self.root.after(0, lambda: self.lbl_score.config(text=f"SCOR: {self.score}"))
        self.root.after(0, lambda: self.lbl_lives.config(text="❤️" * max(0, self.lives)))

    def show_game_over(self):
        """Afișează ecranul de final de joc și oprește jocul 10 secunde"""
        self.root.after(0, lambda: self.lbl_game.config(text="GAME OVER", fg="red"))
        self.root.after(0, lambda: self.lbl_instruction.config(text="Echipa a fost eliminată!", fg="white"))
        self.root.after(0, lambda: self.lbl_score.config(text=f"PUNCTAJ FINAL: {self.score}", fg="yellow"))
        self.root.after(0, lambda: self.lbl_lives.config(text="💀💀💀"))
        
        # Facem podeaua roșie pentru efect vizual de Game Over
        frame = bytearray(1536)
        for y in range(HEIGHT):
            for x in range(WIDTH): self.set_pixel_physical(frame, x, y, (150, 0, 0))
        self.net.send_packet(frame)

    def reset_entire_game(self):
        """Resetează jocul complet pentru o nouă echipă"""
        self.score = 0
        self.lives = min(NUM_PLAYERS, 7)
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

    def draw_splashes(self, frame):
        for s in self.active_splashes[:]:
            sx, sy, life = s['x'], s['y'], s['life']
            if life >= 5: self.set_pixel_physical(frame, sx, sy, COLORS["WHITE"])
            elif life >= 3:
                for dx, dy in [(0,0), (1,0), (-1,0), (0,1), (0,-1)]: self.set_pixel_physical(frame, sx + dx, sy + dy, COLORS["WHITE"])
            elif life >= 1:
                for dx, dy in [(1,1), (-1,-1), (1,-1), (-1,1)]: self.set_pixel_physical(frame, sx + dx, sy + dy, COLORS["WHITE"])
            s['life'] -= 1
            if s['life'] <= 0:
                self.active_splashes.remove(s)
                self.splashing_positions.discard((sx, sy))

    # ==========================================
    # LOGICĂ DE JOC (APĂ ȘI METEORIȚI)
    # ==========================================
    def play_water(self):
        self.update_dashboard("INUNDAȚIE!", "Refugiază-te pe insule!", "#00AAFF")
        active_corners = random.sample(self.all_corners, k=random.randint(1, 3))
        max_dist = math.sqrt(WIDTH**2 + HEIGHT**2)
        
        for f in range(300):
            if self.lives <= 0: break # Oprire imediată dacă nu mai sunt vieți
            
            frame = bytearray(1536)
            self.draw_base(frame)
            
            water_radius = max_dist * (f / 300.0)
            
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    dist = min([math.sqrt((x-cx)**2 + (y-cy)**2) for cx, cy in active_corners])
                    if dist < water_radius:
                        on_island = any(ix <= x < ix+3 and iy <= y < iy+3 for ix, iy, iw, ih in self.islands)
                        if not on_island: self.set_pixel_physical(frame, x, y, COLORS["WATER"])
            
            for px, py in self.pressed_buttons:
                if (px, py) in self.splashing_positions: continue
                dist = min([math.sqrt((px-cx)**2 + (py-cy)**2) for cx, cy in active_corners])
                on_island = any(ix <= px < ix+3 and iy <= py < iy+3 for ix, iy, iw, ih in self.islands)
                
                if dist < water_radius and not on_island:
                    self.register_hit(px, py)

            self.draw_splashes(frame)
            self.net.send_packet(frame)
            time.sleep(0.04)

    def play_meteors(self):
        self.update_dashboard("METEORIȚI!", "Evită exploziile!", "red")
        
        for f in range(350):
            if self.lives <= 0: break # Oprire imediată dacă nu mai sunt vieți
            
            frame = bytearray(1536)
            self.draw_base(frame)
            
            for c in self.craters[:]:
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]: self.set_pixel_physical(frame, c['x']+dx, c['y']+dy, COLORS["CRATER"])
                c['life'] -= 1
                if c['life'] <= 0: self.craters.remove(c)
                
            if f % 15 == 0: 
                self.meteors.append({'x': random.randint(1, WIDTH-2), 'y': random.randint(1, HEIGHT-2), 'timer': 35})
                
            for m in self.meteors[:]:
                mx, my, timer = m['x'], m['y'], m['timer']
                if timer > 8: 
                    if f % 4 == 0: self.set_pixel_physical(frame, mx, my, COLORS["METEOR_WARN"])
                elif timer > 0:
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]: self.set_pixel_physical(frame, mx+dx, my+dy, COLORS["METEOR_IMPACT"])
                    if timer == 1: self.craters.append({'x': mx, 'y': my, 'life': 100})
                    
                    for px, py in self.pressed_buttons:
                        if (px, py) in self.splashing_positions: continue
                        if abs(px - mx) <= 1 and abs(py - my) <= 1:
                            self.register_hit(px, py)
                            
                m['timer'] -= 1
                if m['timer'] <= -4: self.meteors.remove(m)
                
            self.draw_splashes(frame)
            self.net.send_packet(frame)
            time.sleep(0.04)

    # ==========================================
    # SISTEM DE SCOR ȘI ENGINE
    # ==========================================
    def register_hit(self, px, py):
        """Scade o viață echipei și adaugă animația"""
        self.active_splashes.append({'x': px, 'y': py, 'life': 6})
        self.splashing_positions.add((px, py))
        
        self.lives -= 1
        self.root.after(0, lambda: self.lbl_lives.config(text="❤️" * max(0, self.lives)))

    def game_loop(self):
        while self.running:
            # Dacă am pierdut toate viețile în runda trecută
            if self.lives <= 0:
                self.show_game_over()
                time.sleep(10.0) # Așteptăm 10 secunde să vadă toți scorul
                self.reset_entire_game()
                continue
            
            # Resetăm harta pentru noua rundă
            self.active_splashes.clear()
            self.splashing_positions.clear()
            self.meteors.clear()
            self.craters.clear()
            self.islands = [[random.randint(1, WIDTH-4), random.randint(1, HEIGHT-4), 3, 3] for _ in range(4)]
            
            self.update_dashboard("PREGĂTIRE...", "Stai pe poziții!")
            for count in ['3', '2', '1']:
                for _ in range(25):
                    frame = bytearray(1536)
                    self.draw_base(frame)
                    for px, py in self.digits[count]: self.set_pixel_physical(frame, 7+px, 14+py, COLORS["WHITE"])
                    self.net.send_packet(frame)
                    time.sleep(0.04)

            # Rulăm jocul ales
            if random.choice(["water", "meteors"]) == "water":
                self.play_water()
            else:
                self.play_meteors()

            # La finalul rundei, dacă mai avem vieți adunăm scorul!
            if self.lives > 0:
                self.score += self.lives # Adăugăm +1 punct pentru fiecare viață rămasă
                self.update_dashboard("RUNDĂ TERMINATĂ!", f"+{self.lives} Puncte (Jucători Rămași)", "green")
                time.sleep(3.0)

    def input_listener(self):
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