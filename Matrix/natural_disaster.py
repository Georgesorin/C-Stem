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
        self.player_positions = set() 
        self.active_splashes = [] # [x, y, viata]

        self.font = {
            '3': [(0,0), (1,0), (2,0), (2,1), (1,2), (2,2), (2,3), (2,4), (1,4), (0,4)],
            '2': [(0,0), (1,0), (2,0), (2,1), (0,2), (1,2), (2,2), (0,3), (0,4), (1,4), (2,4)],
            '1': [(1,0), (1,1), (1,2), (1,3), (1,4)]
        }

        self.all_corners = [(0, 0), (WIDTH-1, 0), (0, HEIGHT-1), (WIDTH-1, HEIGHT-1)]
        self.islands = []
        self.reset_round()

        threading.Thread(target=self.input_listener, daemon=True).start()

    def reset_round(self):
        self.active_corners = random.sample(self.all_corners, k=random.randint(1, 3))
        self.islands = []
        for _ in range(random.randint(3, 5)):
            ix, iy = random.randint(1, WIDTH-4), random.randint(1, HEIGHT-4)
            self.islands.append((ix, iy, 3, 3))

    def set_pixel_physical(self, buffer, x, y, color):
        if not (0 <= x < WIDTH and 0 <= y < HEIGHT): return
        channel = y // 4
        row_in_ch = y % 4
        idx = (row_in_ch * 16 + x) if row_in_ch % 2 == 0 else (row_in_ch * 16 + (15 - x))
        offset = idx * 24 + channel
        if offset + 16 < len(buffer):
            buffer[offset], buffer[offset + 8], buffer[offset + 16] = color[1], color[0], color[2]

    def draw_digit(self, buffer, digit, ox, oy, color):
        if digit in self.font:
            for px, py in self.font[digit]:
                self.set_pixel_physical(buffer, ox + px, oy + py, color)

    def input_listener(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", PORT_RECV))
        while self.running:
            try:
                data, _ = sock.recvfrom(2048)
                if len(data) >= 600 and data[0] == 0x88:
                    new_pos = set()
                    for ch in range(8):
                        base = 2 + ch * 171
                        for led in range(64):
                            if data[base + 1 + led] == 0xCC:
                                row, col = led // 16, led % 16
                                x = col if row % 2 == 0 else 15 - col
                                new_pos.add((x, ch * 4 + row))
                    self.player_positions = new_pos
            except: pass

    def run(self):
        max_dist = math.sqrt(WIDTH**2 + HEIGHT**2)
        
        while self.running:
            # --- FAZA 1: TIMER (3 secunde) ---
            self.reset_round()
            self.active_splashes = [] # Curățăm splash-urile de runda trecută
            
            for countdown in ['3', '2', '1']:
                for _ in range(25):
                    frame = bytearray(1536)
                    # Fundal Verde
                    for y in range(HEIGHT):
                        for x in range(WIDTH): self.set_pixel_physical(frame, x, y, (0, 100, 0))
                    self.draw_digit(frame, countdown, 7, 14, (255, 255, 255))
                    self.net.send_packet(frame)
                    time.sleep(0.04)

            # --- FAZA 2: DEZASTRU (300 de cadre / ~12 secunde) ---
            for f in range(300):
                frame = bytearray(1536)
                t = f / 300.0

                for y in range(HEIGHT):
                    for x in range(WIDTH): self.set_pixel_physical(frame, x, y, (0, 100, 0))
                
                for (ix, iy, iw, ih) in self.islands:
                    for x in range(ix, ix + iw):
                        for y in range(iy, iy + ih): self.set_pixel_physical(frame, x, y, (120, 120, 120))

                for y in range(HEIGHT):
                    for x in range(WIDTH):
                        d_edge = min([math.sqrt((x-cx)**2 + (y-cy)**2) for cx, cy in self.active_corners])
                        if d_edge < (max_dist * t):
                            on_island = any(ix <= x < ix+iw and iy <= y < iy+ih for ix, iy, iw, ih in self.islands)
                            if not on_island: self.set_pixel_physical(frame, x, y, (0, 0, 255))

                for px, py in self.player_positions:
                    d_water = min([math.sqrt((px-cx)**2 + (py-cy)**2) for cx, cy in self.active_corners])
                    on_safe = any(ix <= px < ix+iw and iy <= py < iy+ih for ix, iy, iw, ih in self.islands)
                    if d_water < (max_dist * t) and not on_safe:
                        if not any(s[0] == px and s[1] == py for s in self.active_splashes):
                            self.active_splashes.append([px, py, 6])

                for s in self.active_splashes[:]:
                    sx, sy, life = s[0], s[1], s[2]
                    if life >= 5: self.set_pixel_physical(frame, sx, sy, (255, 255, 255))
                    elif life >= 3:
                        for dx, dy in [(0,0), (1,0), (-1,0), (0,1), (0,-1)]:
                            self.set_pixel_physical(frame, sx + dx, sy + dy, (200, 200, 255))
                    elif life >= 1:
                        for dx, dy in [(1,1), (-1,-1), (1,-1), (-1,1)]:
                            self.set_pixel_physical(frame, sx + dx, sy + dy, (150, 150, 255))
                    s[2] -= 1
                    if s[2] <= 0: self.active_splashes.remove(s)

                self.net.send_packet(frame)
                time.sleep(0.04)

            # --- FAZA 3: PAUZĂ (Respiro după dezastru) ---
            # Lăsăm ultima imagine (ecranul plin de apă) timp de 3 secunde
            print("🏁 Dezastrul s-a terminat. Respiro...")
            time.sleep(3.0) 

if __name__ == "__main__":
    NaturalDisaster().run()