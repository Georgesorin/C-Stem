# eye_io.py  –  hardware abstraction for Musical Chairs
# Uses the same LightService from Controller.py that Team_collect.py uses.
# Provides:
#   EvilEyeHardware  – thin wrapper (set_element, eye_states, button_states)
#   run_discovery    – broadcast scan, returns device IP or None

import socket
import time
import random

# ── Checksum table (copied from Team_collect.py) ─────────────────────────────
_PASSWORD_ARRAY = [
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
    168, 45, 198, 6, 43, 11, 57, 88, 182, 84, 189, 29, 35, 143, 138, 171,
]

def _calc_sum(data: bytes | bytearray) -> int:
    return _PASSWORD_ARRAY[sum(data) & 0xFF]


# ── Discovery helpers ─────────────────────────────────────────────────────────

def _build_discovery_packet():
    """Build the 0x67 Evil Eye discovery broadcast packet (same as Team_collect)."""
    rand1 = random.randint(0, 127)
    rand2 = random.randint(0, 127)
    payload = bytearray([0x0A, 0x02, *b"KX-HC04", 0x03,
                         0x00, 0x00, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x14])
    pkt = bytearray([0x67, rand1, rand2, len(payload)]) + payload
    pkt.append(_calc_sum(pkt))
    return bytes(pkt), rand1, rand2


def run_discovery(bind_ip: str, broadcast_ip: str, timeout: float = 3.0):
    """
    Broadcast a discovery packet and return the first responding device IP,
    or None if nothing answers within `timeout` seconds.
    Mirrors _run_discovery() in Team_collect.py exactly.
    """
    pkt, rand1, rand2 = _build_discovery_packet()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(0.5)

    # Bind on the receive port (7800) – try the specific IP first, fall back to 0.0.0.0
    try:
        sock.bind((bind_ip if bind_ip != "127.0.0.1" else "0.0.0.0", 7800))
    except OSError:
        try:
            sock.bind(("0.0.0.0", 7800))
        except OSError:
            sock.close()
            return None

    try:
        sock.sendto(pkt, (broadcast_ip, 4626))
    except OSError:
        sock.close()
        return None

    found = None
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            data, addr = sock.recvfrom(1024)
            if (len(data) >= 30 and data[0] == 0x68
                    and data[1] == rand1 and data[2] == rand2):
                found = addr[0]
                break
        except socket.timeout:
            continue
        except OSError:
            break

    sock.close()
    return found


def get_local_interfaces():
    """Return [(iface_name, ip, broadcast), ...] – mirrors Team_collect._get_local_interfaces."""
    results = []
    try:
        import psutil, ipaddress
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET and addr.address != "127.0.0.1":
                    try:
                        net = ipaddress.IPv4Network(
                            f"{addr.address}/{addr.netmask}", strict=False)
                        bcast = str(net.broadcast_address)
                    except Exception:
                        bcast = "255.255.255.255"
                    results.append((iface, addr.address, bcast))
    except ImportError:
        try:
            ip = socket.gethostbyname(socket.gethostname())
            if ip != "127.0.0.1":
                results.append(("default", ip, "255.255.255.255"))
        except Exception:
            pass
    results.append(("loopback (simulator)", "127.0.0.1", "127.0.0.1"))
    return results


# ── Hardware wrapper ──────────────────────────────────────────────────────────

class EvilEyeHardware:
    """
    Thin wrapper around LightService (from Controller.py).
    Exposes the same interface that main_musical_chairs.py expects:
      - set_element(wall, led, (r, g, b))
      - eye_states    {1: bool, 2: bool, 3: bool, 4: bool}
      - button_states {wall: {led: bool, ...}, ...}
    """

    def __init__(self):
        self.eye_states    = {w: False for w in range(1, 5)}
        self.button_states = {w: {l: False for l in range(11)} for w in range(1, 5)}
        self._connected    = False

        # Import LightService exactly like Team_collect.py does
        try:
            from Controller import LightService
            self._svc = LightService()
            self._svc.on_button_state = self._on_event
            self._svc.on_status       = lambda msg: None
        except Exception as e:
            print(f"[HW] LightService not available: {e}")
            self._svc = None

    # ── Event callback from LightService ─────────────────────────────────────
    def _on_event(self, ch: int, led: int, is_triggered: bool, is_disconnected: bool):
        if is_disconnected:
            return
        if led == 0:
            self.eye_states[ch] = is_triggered
        else:
            if ch in self.button_states and led in self.button_states[ch]:
                self.button_states[ch][led] = is_triggered

    # ── Connection control ────────────────────────────────────────────────────
    def connect(self, ip: str):
        """Set the device IP and start receiver + polling (like Team_collect's _on_setup_start)."""
        if self._svc is None:
            return
        self._svc.set_device(ip)
        self._svc.start_receiver()
        self._svc.start_polling()
        self._connected = True

    def disconnect(self):
        if self._svc and self._connected:
            self._svc.stop_polling()
            self._svc.stop_receiver()
            self._connected = False

    # ── LED control ───────────────────────────────────────────────────────────
    def set_element(self, wall: int, led: int, color: tuple):
        """Send a single LED colour to the hardware."""
        if self._svc and self._connected:
            r, g, b = color
            self._svc.set_led(wall, led, r, g, b)
