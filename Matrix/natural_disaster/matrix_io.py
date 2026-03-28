# matrix_io.py
import socket
import threading
from Controller import NetworkManager
from config import *

class MatrixHardware:
    def __init__(self):
        self.net = NetworkManager()
        self.net.target_ip = TARGET_IP
        self.net.send_port = PORT_SEND
        self.pressed_buttons = set()
        self.running = True
        
        # Pornim listener-ul pentru senzori în fundal
        threading.Thread(target=self.input_listener, daemon=True).start()

    def set_pixel_physical(self, buffer, x, y, color):
        """Traduce coordonatele X, Y în formatul Zig-Zag necesar podelei"""
        if not (0 <= x < WIDTH and 0 <= y < HEIGHT): return
        channel = y // 4
        row_in_ch = y % 4
        idx = (row_in_ch * 16 + x) if row_in_ch % 2 == 0 else (row_in_ch * 16 + (15 - x))
        offset = idx * 24 + channel
        if offset + 16 < len(buffer):
            buffer[offset], buffer[offset + 8], buffer[offset + 16] = color[1], color[0], color[2]

    def send_frame(self, frame):
        """Trimite cadrul calculat către rețea"""
        self.net.send_packet(frame)

    def input_listener(self):
        """Ascultă UDP-ul de la podea și actualizează set-ul de butoane apăsate"""
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