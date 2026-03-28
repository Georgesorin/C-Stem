import socket
import threading
import time
import math
import random
from Controller import NetworkManager

WIDTH, HEIGHT = 16, 32 
TARGET_IP = "127.0.0.1"
PORT_SEND = 5001 
PORT_RECV = 5000 

class NaturalDisaster:
    def __init__(self):
        self.net = NetworkManager()
        self.net.target_ip = TARGET_IP
        self.net.send_port = PORT_SEND
        
        self.running = True
        self.active_splashes = [] 
        self.meteors = []         
        self.craters = [] # [x, y, viata_crater]
        self.pending_hits = set() 
        self.islands = [] 

        self.digits = {
            '3': [(0,0), (1,0), (2,0), (2,1), (1,2), (2,2), (2,3), (2,4), (1,4), (0,4)],
            '2': [(0,0), (1,0), (2,0), (2,1), (0,2), (1,2), (2,2), (0,3), (0,4), (1,4), (2,4)],
            '1': [(1,0), (1,1), (1,2), (1,3), (1,4)]
        }

        self.all_corners = [(0, 0), (WIDTH-1, 0), (0, HEIGHT-1), (WIDTH-1, HEIGHT-1)]
        threading.Thread(target=self.input_listener, daemon=True).start()

    def reset_round_data(self):
        self.active_corners = random.sample(self.all_corners, k=random.randint(1, 3))
        self.islands = []
        for _ in range(random.randint(3, 5)):
            ix, iy = random.randint(1, WIDTH-4), random.randint(1, HEIGHT-4)
            self.islands.append((ix, iy, 3, 3))
        self.meteors = []
        self.craters = [] 
        self.active_splashes = []
        self.pending_hits.clear()

    def set_pixel_physical(self, buffer, x, y, color):
        if not (0 <= x < WIDTH and 0 <= y < HEIGHT): return
        channel = y // 4
        row_in_ch = y % 4
        idx = (row_in_ch * 16 + x) if row_in_ch % 2 == 0 else (row_in_ch * 16 + (15 - x))
        offset = idx * 24 + channel
        if offset + 16 < len(buffer):
            buffer[offset], buffer[offset + 8], buffer[offset + 16] = color[1], color[0], color[2]

    def draw_digit(self, buffer, char, ox, oy, color):
        if char in self.digits:
            for px, py in self.digits[char]:
                self.set_pixel_physical(buffer, ox + px, oy + py, color)

    def draw_base_map(self, buffer):
        for y in range(HEIGHT):
            for x in range(WIDTH): self.set_pixel_physical(buffer, x, y, (0, 80, 0))
        for (ix, iy, iw, ih) in self.islands:
            for x in range(ix, ix + iw):
                for y in range(iy, iy + ih): 
                    self.set_pixel_physical(buffer, x, y, (120, 120, 120))

    def input_listener(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try: sock.bind(("0.0.0.0", PORT_RECV))
        except: return
        while self.running:
            try:
                data, _ = sock.recvfrom(2048)
                if len(data) >= 600 and data[0] == 0x88:
                    for ch in range(8):
                        base = 2 + ch * 171
                        for led in range(64):
                            if data[base + 1 + led] == 0xCC:
                                row, col = led // 16, led % 16
                                x = col if row % 2 == 0 else 15 - col
                                self.pending_hits.add((x, ch * 4 + row))
            except: pass

    def handle_explosions(self, frame, base_color=(255, 255, 255)):
        for s in self.active_splashes[:]:
            sx, sy, life = s[0], s[1], s[2]
            if life >= 5: self.set_pixel_physical(frame, sx, sy, base_color)
            elif life >= 3:
                for dx, dy in [(0,0), (1,0), (-1,0), (0,1), (0,-1)]:
                    self.set_pixel_physical(frame, sx + dx, sy + dy, base_color)
            elif life >= 1:
                for dx, dy in [(1,1), (-1,-1), (1,-1), (-1,1)]:
                    self.set_pixel_physical(frame, sx + dx, sy + dy, base_color)
            s[2] -= 1
            if s[2] <= 0: self.active_splashes.remove(s)

    def mode_water(self):
        print("🌊 INUNDAȚIE!")
        max_dist = math.sqrt(WIDTH**2 + HEIGHT**2)
        for f in range(300):
            frame = bytearray(1536)
            self.draw_base_map(frame)
            t = f / 300.0
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    d_edge = min([math.sqrt((x-cx)**2 + (y-cy)**2) for cx, cy in self.active_corners])
                    if d_edge < (max_dist * t):
                        on_island = any(ix <= x < ix+3 and iy <= y < iy+3 for ix, iy, iw, ih in self.islands)
                        if not on_island: self.set_pixel_physical(frame, x, y, (0, 0, 255))
            
            current_hits = list(self.pending_hits)
            self.pending_hits.clear()
            for px, py in current_hits:
                d_w = min([math.sqrt((px-cx)**2 + (py-cy)**2) for cx, cy in self.active_corners])
                if d_w < (max_dist * t) and not any(ix <= px < ix+3 and iy <= py < iy+3 for ix, iy, iw, ih in self.islands):
                    if not any(s[0] == px and s[1] == py for s in self.active_splashes):
                        self.active_splashes.append([px, py, 6])

            self.handle_explosions(frame, (255, 255, 255))
            self.net.send_packet(frame)
            time.sleep(0.04)

    def mode_meteors(self):
        print("☄️ PLOAIE DE METEORIȚI!")
        for f in range(400):
            frame = bytearray(1536)
            self.draw_base_map(frame)
            
            # 1. Desenăm Craterele (Gri închis, 3x3)
            for c in self.craters[:]:
                cx, cy, clife = c[0], c[1], c[2]
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        self.set_pixel_physical(frame, cx+dx, cy+dy, (40, 40, 40))
                c[2] -= 1
                if c[2] <= 0: self.craters.remove(c)

            if f % 12 == 0: 
                self.meteors.append([random.randint(1, WIDTH-2), random.randint(1, HEIGHT-2), 35])

            current_hits = list(self.pending_hits)
            self.pending_hits.clear()

            for m in self.meteors[:]:
                mx, my, timer = m[0], m[1], m[2]
                if timer > 8: # Warning
                    if f % 4 == 0: self.set_pixel_physical(frame, mx, my, (255, 0, 0))
                elif timer > 0: # IMPACT (3x3 Portocaliu)
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            self.set_pixel_physical(frame, mx+dx, my+dy, (255, 100, 0))
                    
                    if timer == 1: # Lăsăm craterul la ultimul cadru de impact
                        self.craters.append([mx, my, 120])
                    
                    for px, py in current_hits:
                        if abs(px - mx) <= 1 and abs(py - my) <= 1:
                            if not any(s[0] == px and s[1] == py for s in self.active_splashes):
                                self.active_splashes.append([px, py, 6])
                
                m[2] -= 1
                if m[2] <= -4: self.meteors.remove(m)

            self.handle_explosions(frame, (255, 200, 0)) 
            self.net.send_packet(frame)
            time.sleep(0.04)

    def run(self):
        while self.running:
            self.reset_round_data()
            dezastru = random.choice(["water", "meteors"])
            
            for count in ['3', '2', '1']:
                for _ in range(25):
                    frame = bytearray(1536)
                    for y in range(HEIGHT):
                        for x in range(WIDTH): self.set_pixel_physical(frame, x, y, (0, 80, 0))
                    self.draw_digit(frame, count, 7, 14, (255, 255, 255))
                    self.net.send_packet(frame)
                    time.sleep(0.04)

            if dezastru == "water": self.mode_water()
            else: self.mode_meteors()

            time.sleep(3.0) 

if __name__ == "__main__":
    NaturalDisaster().run()