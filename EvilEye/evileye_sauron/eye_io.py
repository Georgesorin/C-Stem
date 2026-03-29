# eye_io.py
import socket
import threading
import time
import random
import psutil
from config_eye import *

# ── Tabel Parolă Checksum ─────────────────────────────
PASSWORD_ARRAY = [
    35, 63, 187, 69, 107, 178, 92, 76, 39, 69, 205, 37, 223, 255, 165, 231,
    16, 220, 99, 61, 25, 203, 203, 155, 107, 30, 92, 144, 218, 194, 226, 88,
    196, 190, 67, 195, 159, 185, 209, 24, 163, 65, 25, 172, 126, 63, 224, 61,
    160, 80, 125, 91, 239, 144, 25, 141, 183, 204, 171, 188, 255, 162, 104, 225,
    186, 91, 232, 3, 100, 208, 49, 211, 37, 192, 20, 99, 27, 92, 147, 152,
    86, 177, 53, 153, 94, 177, 200, 33, 175, 195, 15, 228, 247, 18, 244, 150,
    165, 229, 212, 96, 84, 200, 168, 191, 38, 112, 171, 116, 121, 186, 147, 203,
    30, 118, 115, 159, 238, 139, 60, 57, 235, 213, 159, 198, 160, 50, 97, 201,
    253, 242, 240, 77, 102, 12, 183, 235, 243, 247, 75, 90, 13, 236, 56, 133,
    150, 128, 138, 190, 140, 13, 213, 18, 7, 117, 255, 45, 69, 214, 179, 50,
    28, 66, 123, 239, 190, 73, 142, 218, 253, 5, 212, 174, 152, 75, 226, 226,
    172, 78, 35, 93, 250, 238, 19, 32, 247, 223, 89, 123, 86, 138, 150, 146,
    214, 192, 93, 152, 156, 211, 67, 51, 195, 165, 66, 10, 10, 31, 1, 198,
    234, 135, 34, 128, 208, 200, 213, 169, 238, 74, 221, 208, 104, 170, 166, 36,
    76, 177, 196, 3, 141, 167, 127, 56, 177, 203, 45, 107, 46, 82, 217, 139,
    168, 45, 198, 6, 43, 11, 57, 88, 182, 84, 189, 29, 35, 143, 138, 171
]

def calc_checksum(data):
    idx = sum(data) & 0xFF
    return PASSWORD_ARRAY[idx] if idx < len(PASSWORD_ARRAY) else 0

def build_command_packet(data_id, msg_loc, payload, seq):
    internal = bytes([
        0x02, 0x00, 0x00, (data_id >> 8) & 0xFF, data_id & 0xFF,
        (msg_loc >> 8) & 0xFF, msg_loc & 0xFF, (len(payload) >> 8) & 0xFF, len(payload) & 0xFF,
    ]) + payload
    hdr = bytes([0x75, random.randint(0, 127), random.randint(0, 127), (len(internal) >> 8) & 0xFF, len(internal) & 0xFF])
    pkt = bytearray(hdr + internal)
    pkt[10] = (seq >> 8) & 0xFF; pkt[11] = seq & 0xFF
    pkt.append(calc_checksum(pkt))
    return bytes(pkt)

def build_start_packet(seq):
    pkt = bytearray([0x75, random.randint(0, 127), random.randint(0, 127), 0x00, 0x08, 0x02, 0x00, 0x00, 0x33, 0x44, (seq >> 8) & 0xFF, seq & 0xFF, 0x00, 0x00])
    pkt.append(calc_checksum(pkt))
    return bytes(pkt)

def build_end_packet(seq):
    pkt = bytearray([0x75, random.randint(0, 127), random.randint(0, 127), 0x00, 0x08, 0x02, 0x00, 0x00, 0x55, 0x66, (seq >> 8) & 0xFF, seq & 0xFF, 0x00, 0x00])
    pkt.append(calc_checksum(pkt))
    return bytes(pkt)

def build_fff0_packet(seq):
    payload = bytearray()
    for _ in range(4): payload += bytes([0x00, 0x0B])
    return build_command_packet(0x8877, 0xFFF0, bytes(payload), seq)

# ── Funcții Discovery rețea ──────────────────────────
def get_local_interfaces():
    results = []
    try:
        import ipaddress
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET and addr.address != "127.0.0.1":
                    try:
                        net = ipaddress.IPv4Network(f"{addr.address}/{addr.netmask}", strict=False)
                        bcast = str(net.broadcast_address)
                    except: bcast = "255.255.255.255"
                    results.append((iface, addr.address, bcast))
    except: pass
    results.append(("Simulator Local", "127.0.0.1", "127.0.0.1"))
    return results

def build_discovery_packet():
    r1, r2 = random.randint(0, 127), random.randint(0, 127)
    payload = bytearray([0x0A, 0x02, *b"KX-HC04", 0x03, 0x00, 0x00, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x14])
    pkt = bytearray([0x67, r1, r2, len(payload)]) + payload
    pkt.append(calc_checksum(pkt))
    return bytes(pkt), r1, r2

def run_discovery(bind_ip: str, broadcast_ip: str, timeout: float = 3.0):
    pkt, rand1, rand2 = build_discovery_packet()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(0.5)

    try: sock.bind((bind_ip if bind_ip != "127.0.0.1" else "0.0.0.0", 7800))
    except:
        try: sock.bind(("0.0.0.0", 7800))
        except: return None

    try: sock.sendto(pkt, (broadcast_ip, 4626))
    except: return None

    found = None
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            data, addr = sock.recvfrom(1024)
            if len(data) >= 30 and data[0] == 0x68 and data[1] == rand1 and data[2] == rand2:
                found = addr[0]
                break
        except: pass

    sock.close()
    return found

# ── Clasa Hardware Complet Independentă ───────────────────
class EvilEyeHardware:
    def __init__(self):
        self.running = False
        self.eye_states = {w: False for w in range(1, 5)}
        self.button_states = {w: {l: False for l in range(11)} for w in range(1, 5)}
        self._led_states = {}
        self._seq = 0

    def connect(self, target_ip: str, is_physical: bool):
        self.target_ip = target_ip
        self.is_physical = is_physical
        
        # DEFINIM PORTURILE CORECT (Asta stricase Controller.py!)
        if self.is_physical:
            self.send_port = 4626
            self.recv_port = 7800
        else:
            self.send_port = PORT_SEND # Setat în config_eye.py
            self.recv_port = PORT_RECV # Setat în config_eye.py
            
        self.sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_send.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        self.running = True
        threading.Thread(target=self.input_listener, daemon=True).start()
        threading.Thread(target=self.output_streamer, daemon=True).start()

    def disconnect(self):
        self.running = False

    def set_element(self, wall: int, led: int, color: tuple):
        self._led_states[(wall, led)] = color

    def output_streamer(self):
        while self.running:
            self._seq = (self._seq + 1) & 0xFFFF
            frame = bytearray(132)
            for (ch, led), (r, g, b) in self._led_states.items():
                ch_idx = ch - 1
                if 0 <= ch_idx < 4 and 0 <= led < 11:
                    if self.is_physical:
                        # PENTRU FIZIC: Aplicăm corecția GRB (Inversăm Roșu cu Verde)
                        frame[led * 12 + ch_idx] = g
                        frame[led * 12 + 4 + ch_idx] = r
                    else:
                        # PENTRU SIMULATOR: Rămâne normal RGB
                        frame[led * 12 + ch_idx] = r
                        frame[led * 12 + 4 + ch_idx] = g
                        
                    frame[led * 12 + 8 + ch_idx] = b

            ep = (self.target_ip, self.send_port)
            try:
                self.sock_send.sendto(build_start_packet(self._seq), ep)
                time.sleep(0.008)
                self.sock_send.sendto(build_fff0_packet(self._seq), ep)
                time.sleep(0.008)
                self.sock_send.sendto(build_command_packet(0x8877, 0x0000, bytes(frame), self._seq), ep)
                time.sleep(0.008)
                self.sock_send.sendto(build_end_packet(self._seq), ep)
            except: pass
            
            time.sleep(0.06)

    def input_listener(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try: sock.bind(("0.0.0.0", self.recv_port))
        except: return
        
        while self.running:
            try:
                data, _ = sock.recvfrom(1024)
                if len(data) == 687 and data[0] == 0x88:
                    for ch in range(1, 5):
                        base = 2 + (ch - 1) * 171
                        for led in range(11):
                            is_pressed = (data[base + 1 + led] == 0xCC)
                            if led == 0: self.eye_states[ch] = is_pressed
                            else: self.button_states[ch][led] = is_pressed
            except: pass
