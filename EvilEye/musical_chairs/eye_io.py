# eye_io.py - Adaugă aceste funcții pentru Discovery
def build_discovery_packet():
    import random
    rand1, rand2 = random.randint(0, 127), random.randint(0, 127)
    # Payload-ul standard Evil Eye pentru identificare
    payload = bytearray([0x0A, 0x02, *b"KX-HC04", 0x03, 0x00, 0x00, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x14])
    pkt = bytearray([0x67, rand1, rand2, len(payload)]) + payload
    pkt.append(calc_checksum(pkt))
    return bytes(pkt), rand1, rand2

def run_discovery(bind_ip, broadcast_ip, timeout=3.0):
    """Logica exactă de scanare din Team_collect.py"""
    pkt, r1, r2 = build_discovery_packet()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(0.5)
    
    try: sock.bind((bind_ip if bind_ip != "127.0.0.1" else "0.0.0.0", 7800))
    except: return None

    try: sock.sendto(pkt, (broadcast_ip, 4626))
    except: return None

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            data, addr = sock.recvfrom(1024)
            # Verificăm antetul 0x68 și ID-ul pachetului
            if len(data) >= 30 and data[0] == 0x68 and data[1] == r1 and data[2] == r2:
                sock.close()
                return addr[0]
        except: continue
    sock.close()
    return None