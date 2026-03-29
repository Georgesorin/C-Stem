import socket
import time
import threading
import random
import os
import json
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, filedialog
from dataclasses import dataclass, field
from typing import List, Tuple

# ==============================================================================
# --- Configurări Căi și Fonturi ---
# ==============================================================================
current_script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_script_dir)
matrix_dir = os.path.join(parent_dir, 'Matrix')
if matrix_dir not in sys.path: sys.path.append(matrix_dir)

try:
    import matrix_font
    HAS_FONTS = True
except ImportError:
    HAS_FONTS = False

HAS_PYGAME = False
try:
    import pygame
    pygame.mixer.init()
    HAS_PYGAME = True
except: pass

def _load_config():
    cfg_path = os.path.join(current_script_dir, "config_game.json")
    defaults = {"device_ip": "127.0.0.1", "send_port": 6766, "recv_port": 6767}
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r") as f: return {**defaults, **json.load(f)}
        except: pass
    return defaults

CONFIG = _load_config()
UDP_SEND_IP, UDP_SEND_PORT, UDP_LISTEN_PORT = CONFIG["device_ip"], CONFIG["send_port"], CONFIG["recv_port"]
BOARD_WIDTH, BOARD_HEIGHT = 16, 32
FRAME_DATA_LENGTH = 8 * 64 * 3

# ==============================================================================
# --- Structuri și Logica Jocului ---
# ==============================================================================
@dataclass
class Obstacle:
    name: str
    x: float
    y: float
    speed: float
    dx: float
    dy: float
    shape: List[Tuple[int, int]] = field(default_factory=list)

    def get_absolute_pixels(self) -> List[Tuple[int, int]]:
        return [(int(self.x) + dx, int(self.y) + dy) for dx, dy in self.shape]

@dataclass
class BonusPoint:
    x: int
    y: int
    color: Tuple[int, int, int]
    fade: float = 0.0 # Nivel fade-in (0.0 -> 1.0) 

class IslandSurvivorGame:
    def __init__(self):
        self.running = True
        self.state = 'LOBBY'
        self.lives = 5
        self.score = 0
        self.countdown_to_show = 0
        self.obstacles: List[Obstacle] = []
        self.bonus_points: List[BonusPoint] = [] 
        self.islands = [] # Lista de dict-uri cu {'x', 'y', 'fade'} 
        self.last_island_spawn = 0
        self.last_point_spawn = 0
        self.hit_cooldown = 0
        
        # State pentru fade butoane
        self.fade_levels = [[0.0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.press_colors = [[(255, 255, 255) for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        
        self.button_states = [[False for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.lock = threading.RLock()

    def reset(self):
        with self.lock:
            self.lives = 5
            self.score = 0
            self.obstacles = []
            self.bonus_points = []
            self.fade_levels = [[0.0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
            # Insule cu fade-in la start 
            self.islands = [{'x': 2, 'y': 5, 'fade': 0.0}, {'x': 11, 'y': 24, 'fade': 0.0}]
            self.last_island_spawn = time.time()
            for _ in range(10): self.spawn_point()
            self.state = 'PLAYING'

    def spawn_obstacle(self):
        names = ['shuriken', 'bubble', 'arrow', 'line', 'diamond', 'diag1', 'chess']
        name = random.choice(names)
        side = random.choice(['L', 'R', 'T', 'B'])
        if side == 'L': x, y, dx, dy = -4, random.randint(0, 31), 1, 0
        elif side == 'R': x, y, dx, dy = 16, random.randint(0, 31), -1, 0
        elif side == 'T': x, y, dx, dy = random.randint(0, 15), -4, 0, 1
        else: x, y, dx, dy = random.randint(0, 15), 32, 0, -1

        obs = Obstacle(name, x, y, 0.22, dx, dy)
        shapes = {
            'shuriken': [(1, 0), (0, 1), (1, 1), (2, 1), (1, 2)],
            'bubble': [(1, 0), (2, 0), (0, 1), (3, 1), (0, 2), (3, 2), (1, 3), (2, 3)],
            'arrow': [(2, 0), (2, 1), (0, 2), (2, 2), (4, 2), (1, 3), (3, 3), (2, 4)],
            'line': [(i, 0) for i in range(16)],
            'diamond': [(2, 0), (1, 1), (3, 1), (0, 2), (4, 2), (1, 3), (3, 3), (2, 4)],
            'diag1': [(4, 0), (3, 1), (2, 2), (1, 3), (0, 4)],
            'chess': [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)]
        }
        obs.shape = shapes.get(name, [(0,0)])
        self.obstacles.append(obs)

    def spawn_point(self):
        colors = [(255, 215, 0), (0, 255, 255), (255, 0, 255), (0, 255, 0), (255, 165, 0)]
        for _ in range(30):
            rx, ry = random.randint(1, 14), random.randint(1, 30)
            on_isl = any(i['x'] <= rx < i['x']+3 and i['y'] <= ry < i['y']+3 for i in self.islands)
            if not on_isl and not any(p.x == rx and p.y == ry for p in self.bonus_points):
                # Punct nou cu fade 0.0 
                self.bonus_points.append(BonusPoint(rx, ry, random.choice(colors), 0.0))
                break

    def tick(self):
        if self.state != 'PLAYING': return
        now = time.time()
        with self.lock:
            # Viteza globală de fade
            f_spd = 0.12

            # 1. Update Fade butoane
            for y in range(BOARD_HEIGHT):
                for x in range(BOARD_WIDTH):
                    if self.button_states[y][x]:
                        if self.fade_levels[y][x] == 0:
                             self.press_colors[y][x] = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
                        self.fade_levels[y][x] = min(1.0, self.fade_levels[y][x] + f_spd)
                    else:
                        self.fade_levels[y][x] = max(0.0, self.fade_levels[y][x] - f_spd)

            # 2. Update Fade-in Insule și Puncte 
            for isl in self.islands: isl['fade'] = min(1.0, isl['fade'] + f_spd)
            for p in self.bonus_points: p.fade = min(1.0, p.fade + f_spd)

            # 3. Gestionare Swap Insule
            if now - self.last_island_spawn > 4.5:
                if len(self.islands) > 1: self.islands.pop(0)
                self.islands.append({'x': random.randint(0, 13), 'y': random.randint(1, 28), 'fade': 0.0})
                self.last_island_spawn = now

            # 4. Obstacole
            if random.random() < 0.04: self.spawn_obstacle()
            for o in self.obstacles[:]:
                o.x += o.dx * o.speed; o.y += o.dy * o.speed
                if not (-10 < o.x < 26 and -10 < o.y < 42): self.obstacles.remove(o)

            # 5. Colectare Puncte
            for p in self.bonus_points[:]:
                if self.button_states[p.y][p.x]:
                    self.score += 100
                    self.bonus_points.remove(p)
                    self.spawn_point()
                    print(f"Scor: {self.score}")

            # 6. Sistem Damage
            if now > self.hit_cooldown:
                hit = False
                for y in range(BOARD_HEIGHT):
                    for x in range(BOARD_WIDTH):
                        if self.button_states[y][x]:
                            on_isl = any(i['x'] <= x < i['x']+3 and i['y'] <= y < i['y']+3 for i in self.islands)
                            if not on_isl:
                                for o in self.obstacles:
                                    if (x, y) in o.get_absolute_pixels():
                                        self.lives -= 1
                                        self.hit_cooldown = now + 1.0
                                        hit = True; break
                        if hit: break
                    if hit: break
            if self.lives <= 0: self.state = 'GAMEOVER'

    def set_led(self, buffer, x, y, color):
        if not (0 <= x < 16 and 0 <= y < 32): return
        ch, row = y // 4, y % 4
        idx = (row * 16 + x) if row % 2 == 0 else (row * 16 + (15 - x))
        off = idx * 24 + ch
        buffer[off], buffer[off+8], buffer[off+16] = color[1], color[0], color[2]

    def render(self):
        buffer = bytearray(FRAME_DATA_LENGTH)
        with self.lock:
            if self.state == 'WAITING' and self.countdown_to_show > 0:
                char = str(self.countdown_to_show)
                if HAS_FONTS and char in matrix_font.FONT_5x7:
                    for c_idx, col in enumerate(matrix_font.FONT_5x7[char]):
                        for r_idx in range(7):
                            if (col >> r_idx) & 1: self.set_led(buffer, 5+c_idx, 12+r_idx, (255, 255, 255))
            
            elif self.state == 'PLAYING':
                # Strat 1: Obstacole
                for o in self.obstacles:
                    for px, py in o.get_absolute_pixels(): self.set_led(buffer, px, py, (255, 0, 0))

                # Strat 2: Puncte Bonus (cu Fade-in) 
                for p in self.bonus_points:
                    fc = (int(p.color[0]*p.fade), int(p.color[1]*p.fade), int(p.color[2]*p.fade))
                    self.set_led(buffer, p.x, p.y, fc)

                # Strat 3: Fade butoane apăsate
                for y in range(BOARD_HEIGHT):
                    for x in range(BOARD_WIDTH):
                        lvl = self.fade_levels[y][x]
                        if lvl > 0:
                            bc = self.press_colors[y][x]
                            self.set_led(buffer, x, y, (int(bc[0]*lvl), int(bc[1]*lvl), int(bc[2]*lvl)))

                # Strat 4: Insule (cu Fade-in) 
                for isl in self.islands:
                    ic = (int(137*isl['fade']), int(207*isl['fade']), int(240*isl['fade']))
                    for dy in range(3):
                        for dx in range(3): self.set_led(buffer, isl['x']+dx, isl['y']+dy, ic)
            
            elif self.state == 'GAMEOVER':
                for y in range(BOARD_HEIGHT):
                    for x in range(BOARD_WIDTH): self.set_led(buffer, x, y, (255, 0, 0))
                face = [(5, 8), (6, 8), (9, 8), (10, 8), (5, 22), (6, 21), (7, 20), (8, 20), (9, 21), (10, 22)]
                for px, py in face: self.set_led(buffer, px, py, (0, 0, 0))
        return buffer

# --- Networking & GUI (Păstrat din versiunile anterioare) ---
class NetworkManager:
    def __init__(self, game):
        self.game, self.seq = game, 0
        self.sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_send.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock_recv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock_recv.bind(("0.0.0.0", UDP_LISTEN_PORT))
        except: pass

    def send_frame(self, data):
        self.seq = (self.seq + 1) & 0xFFFF
        st = bytearray([0x75, 0, 0, 0, 8, 2, 0, 0, 0x33, 0x44, (self.seq>>8)&0xFF, self.seq&0xFF, 0,0,0, 0x0E, 0])
        self.sock_send.sendto(st, (UDP_SEND_IP, UDP_SEND_PORT))
        cfg = bytearray([0x75, 0, 0, 0, 0x17, 2, 0, 0, 0x88, 0x77, 0xFF, 0xF0, 0, 16]) + bytearray([0, 64]*8) + bytearray([0x1E, 0])
        self.sock_send.sendto(cfg, (UDP_SEND_IP, UDP_SEND_PORT))
        h1 = bytearray([0x75, 0, 0, 3, 0xDE, 2, 0, 0, 0x88, 0x77, 0, 1, 3, 0xD8])
        self.sock_send.sendto(h1 + data[:984] + bytearray([0x1E, 0]), (UDP_SEND_IP, UDP_SEND_PORT))
        rem = data[984:]; p_len = len(rem)
        h2 = bytearray([0x75, 0, 0, (p_len+9)>>8, (p_len+9)&0xFF, 2, 0, 0, 0x88, 0x77, 0, 2, p_len>>8, p_len&0xFF])
        self.sock_send.sendto(h2 + rem + bytearray([0x36, 0]), (UDP_SEND_IP, UDP_SEND_PORT))
        en = bytearray([0x75, 0, 0, 0, 8, 2, 0, 0, 0x55, 0x66, (self.seq>>8)&0xFF, self.seq&0xFF, 0,0,0, 0x0E, 0])
        self.sock_send.sendto(en, (UDP_SEND_IP, UDP_SEND_PORT))

    def listen(self):
        while self.game.running:
            try:
                data, _ = self.sock_recv.recvfrom(2048)
                if len(data) >= 1373 and data[0] == 0x88:
                    for ch in range(8):
                        off = 2 + (ch * 171) + 1
                        for i in range(64):
                            r, c = i // 16, i % 16
                            x = c if r % 2 == 0 else 15 - c
                            y = ch * 4 + r
                            if y < 32 and x < 16: self.game.button_states[y][x] = (data[off+i] == 0xCC)
            except: pass

class GameGUI:
    def __init__(self, root, game, net):
        self.root, self.game, self.net = root, game, net
        self.root.title("Island Survivor Control"); self.root.geometry("400x450")
        self.music, self.cd = "", 10
        tk.Button(root, text="Alege Muzica", command=self.sel).pack(pady=20)
        self.l_m = tk.Label(root, text="Nicio piesa", fg="gray"); self.l_m.pack()
        self.l_c = tk.Label(root, text="", font=("Arial", 40, "bold"), fg="red"); self.l_c.pack(pady=20)
        self.b_s = tk.Button(root, text="START", command=self.go, bg="green", height=2, width=15); self.b_s.pack()

    def sel(self):
        f = filedialog.askopenfilename(); 
        if f: self.music = f; self.l_m.config(text=os.path.basename(f))

    def go(self):
        if not self.music: return
        self.cd = 10; self.b_s.config(state=tk.DISABLED); self.game.state = 'WAITING'; self.tick_gui()

    def tick_gui(self):
        if self.cd > 0:
            self.l_c.config(text=str(self.cd)); self.game.countdown_to_show = self.cd
            self.cd -= 1; self.root.after(1000, self.tick_gui)
        else:
            self.l_c.config(text="FIGHT!")
            if HAS_PYGAME: pygame.mixer.music.load(self.music); pygame.mixer.music.play()
            else: subprocess.Popen(["afplay", self.music])
            self.game.reset(); self.b_s.config(state=tk.NORMAL)

if __name__ == "__main__":
    g = IslandSurvivorGame(); n = NetworkManager(g)
    threading.Thread(target=lambda: [n.send_frame(g.render()) or time.sleep(0.04) for _ in iter(int, 1) if g.running], daemon=True).start()
    threading.Thread(target=lambda: [g.tick() or time.sleep(0.05) for _ in iter(int, 1) if g.running], daemon=True).start()
    threading.Thread(target=n.listen, daemon=True).start()
    r = tk.Tk(); app = GameGUI(r, g, n); r.mainloop(); g.running = False