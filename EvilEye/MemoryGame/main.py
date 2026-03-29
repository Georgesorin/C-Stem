import tkinter as tk
import threading
import sys
import os
import time
import pygame
import psutil
import socket
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Controller import LightService
from display.outside_display import ControlPanel
from game_logic.memory_game import MemoryGame


def build_discovery_packet():
    rand1, rand2 = random.randint(0, 127), random.randint(0, 127)
    payload = bytearray([0x0A, 0x02, *b"KX-HC04", 0x03, 0x00, 0x00, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x14])
    pkt = bytearray([0x67, rand1, rand2, len(payload)]) + payload
    pkt.append(calc_sum(pkt))
    return pkt, rand1, rand2

def run_discovery_flow():
    interfaces = get_local_interfaces()
    if not interfaces:
        print("No active network interfaces found.")
        return None
    print("\n--- Network Selection ---")
    for i, (iface, ip, bcast) in enumerate(interfaces):
        print(f"[{i}] {iface} - {ip}")
    try:
        choice = int(input("\nSelect interface number: "))
        sel = interfaces[choice]
    except:
        sel = interfaces[0]
        print("Invalid choice, defaulting to 0.")
    print(f"Using {sel[0]} ({sel[1]})")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try: sock.bind((sel[1], 7800))
    except: pass
    
    pkt, r1, r2 = build_discovery_packet()
    try: sock.sendto(pkt, (sel[2], 4626))
    except: return None
    
    print("🔍 Listening for devices...")
    sock.settimeout(0.5)
    end_time = time.time() + 3
    devices = []
    while time.time() < end_time:
        try:
            data, addr = sock.recvfrom(1024)
            if len(data) >= 30 and data[0] == 0x68 and data[1] == r1 and data[2] == r2:
                if addr[0] not in [d['ip'] for d in devices]:
                    model = data[6:13].decode(errors='ignore').strip('\x00')
                    devices.append({'ip': addr[0], 'model': model})
                    print(f"✅ Found {model} at {addr[0]}")
        except socket.timeout: continue
        except: pass
    sock.close()
    if devices:
        print(f"Targeting {devices[0]['ip']}\n")
        return devices[0]['ip']
    print("No devices found, using default config.\n")
    return None

def get_local_interfaces():
    import socket, psutil
    interfaces = [("Loopback", "127.0.0.1", "127.0.0.1")]
    
    # Adresa specifică pe care o cauți (clasa peretelui LED)
    manual_target = ("Ethernet-LED", "169.254.182.11", "169.254.255.255")
    
    try:
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    ip = addr.address
                    if not ip.startswith("127."):
                        bcast = ".".join(ip.split('.')[:-1]) + ".255"
                        interfaces.append((iface, ip, bcast))
    except: pass
    
    # Dacă nu a fost găsită nicio adresă din clasa 169, o adăugăm forțat pentru selecție
    if not any(ip.startswith("169.254") for _, ip, _ in interfaces):
        interfaces.append(manual_target)
        
    return list(set(interfaces))

def calc_sum(data):
    return sum(data) & 0xFF

class MasterLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Neon Memory Controller")
        self.root.geometry("450x850") 
        self.root.configure(bg="#0b0b10")
        
        # Detectăm interfețele CHIAR AICI
        self.available_interfaces = get_local_interfaces()
        
        self.game_running = False
        self.stop_timer_event = threading.Event()

        # Networking
        self.network = LightService()
        self.network.start_receiver()
        self.network.start_polling()

        # Audio
        self.audio_ok = False
        try:
            pygame.mixer.init()
            self.audio_ok = True
        except: pass
        self._load_all_sounds()

        # UI - Trimitem lista de interfețe ca argument nou
        self.ui = ControlPanel(
            self.root, 
            self.network, 
            self.available_interfaces, # <--- Pasăm lista aici
            self.start_game, 
            self.stop_game, 
            self.resume_game, 
            self.end_game
        )
        
        self.network.on_button_state = self._hardware_input_handler

    def _load_all_sounds(self):
        self.snd_press = self.snd_fail = self.snd_hint = self.snd_win = self.snd_your_turn = None
        if not self.audio_ok: return

        # Obținem calea absolută a folderului unde se află main.py
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        sfx_map = {
            "press": "game_logic/_sfx/press_ok.wav",
            "fail": "game_logic/_sfx/fail.wav",
            "hint": "game_logic/_sfx/hint.wav",
            "win": "game_logic/_sfx/victory.wav",
            "your_turn": "game_logic/_sfx/15_sec_count.wav"
        }

        for attr, rel_path in sfx_map.items():
            abs_path = os.path.join(base_path, rel_path) # Cale completă
            if os.path.exists(abs_path):
                try:
                    # Inițializăm sunetul cu un bitrate standard
                    setattr(self, f"snd_{attr}", pygame.mixer.Sound(abs_path))
                except Exception as e:
                    print(f"⚠️ Eroare fișier {attr}: {e}")
            else:
                print(f"❌ Lipsă: {abs_path}")


    def _hardware_input_handler(self, ch, led, is_trig, is_disc):
        if is_trig and hasattr(self, 'game') and self.game:
            # Verificăm starea direct aici pentru rapiditate
            if self.game.state == "WAITING":
                self.root.after(0, lambda: self._process_press(ch, led))

    def _process_press(self, ch, led):
        if self.snd_fail:
            self.snd_fail.play()
        if not hasattr(self, 'game') or self.game.state != "WAITING":
            return

        if self.snd_your_turn:
            self.current_turn_channel = self.snd_your_turn.play()
        else:
            self.current_turn_channel = None    
        self.stop_timer_event.set() 

        result = self.game.check_press(ch, led)
        
        if result == "IGNORE": 
            return

        if result in ["STEP_CORRECT", "LEVEL_COMPLETE", "ULTIMATE_WIN"]:
            self.snd_press.play()
            self.network.set_led(ch, led, 0, 255, 0)
            self.root.after(300, lambda c=ch, l=led: self.network.set_led(c, l, 0, 0, 0))

        if result == "LEVEL_COMPLETE":
            self.network.set_led(ch, 0, 0, 255, 0) 
            self.ui.update_status(f"Step {len(self.game.sequence)}/10 Complete", "#00ff88")
            self.root.after(1000, self.run_next_round)

        elif result == "ULTIMATE_WIN":
            self.snd_win.play()
            self.game_running = False
            for wall in range(1, 5): self.network.set_led(wall, 0, 0, 255, 0)
            self.ui.show_full_screen_message("MISSION COMPLETE\nYOU WIN", "#00ff88")
            self.root.after(5000, self._reset_to_lobby)

        elif result == "GAME_OVER":
            if self.snd_fail:
                self.snd_fail.play()
            self.game_running = False
            self.network.set_led(ch, led, 255, 0, 0)
            self.ui.show_full_screen_message("SYSTEM FAILURE\nYOU LOSE", "#ff2a6d")
            threading.Thread(target=self._alarm_strobe_thread, daemon=True).start()
            self.root.after(4000, self._reset_to_lobby)

    def _play_sequence_thread(self):
        self.game.state = "SHOWING"
        self.network.all_off()
        time.sleep(0.5)
        
        new_wall, new_led = self.game.add_next_step()
        print(f"DEBUG: Aprindem Wall {new_wall}, LED {new_led}")
        
        self.network.set_led(new_wall, 0, 0, 242, 255)
        time.sleep(1.0)
        self.network.set_led(new_wall, 0, 0, 0, 0)
        time.sleep(0.2)

        self.network.set_led(new_wall, new_led, 0, 0, 255)
        time.sleep(1.0)
        self.network.set_led(new_wall, new_led, 0, 0, 0)
        
        self.game.state = "WAITING"
        self.current_turn_channel = self.snd_your_turn.play()
        
        self.root.after(0, lambda: self.ui.update_status("Your turn!"))

        self.stop_timer_event.clear()
        threading.Thread(target=self._round_timer_thread, daemon=True).start()

    def _alarm_strobe_thread(self):
        """Efect de stroboscop roșu pentru toți ochii."""
        for _ in range(6):
            for wall in range(1, 5):
                self.network.set_led(wall, 0, 255, 0, 0)
            time.sleep(0.3)
            
            for wall in range(1, 5):
                self.network.set_led(wall, 0, 0, 0, 0)
            time.sleep(0.2)

    def _reset_to_lobby(self):
        self.network.all_off()
        if hasattr(self, 'game'): self.game.reset()
        self.ui.hide_full_screen_message()
        self.ui.show_setup()

    def start_game(self):
        self.play_background_music() # <-- Muzica pornește când apeși START
        players = self.ui.players_var.get()
        self.game = MemoryGame(num_players=players)
        self.game_running = True
        self.run_next_round()

    def run_next_round(self):
        if self.game_running:
            print("DEBUG: Pornim secvența următoare...")
            threading.Thread(target=self._play_sequence_thread, daemon=True).start()

    def _round_timer_thread(self):
        start_time = time.time()
        timeout = 15
        warning_time = 5
        
        while time.time() - start_time < timeout:
            if self.stop_timer_event.is_set() or not self.game_running:
                return

            elapsed = time.time() - start_time
            remaining = timeout - elapsed

            self.root.after(0, lambda r=remaining: self.ui.update_status(f"Time: {int(r)}s"))

            if remaining <= warning_time:
                target_wall, _ = self.game.sequence[self.game.current_step]
                
                self.network.set_led(target_wall, 0, 0, 242, 255)
                self.snd_hint.play()
                time.sleep(0.2)
                self.network.set_led(target_wall, 0, 0, 0, 0)
                time.sleep(0.2)
            else:
                time.sleep(0.1)

        if not self.stop_timer_event.is_set() and self.game_running:
            self.root.after(0, self._handle_timeout)

    def _handle_timeout(self):
        self.snd_fail.play()
        self._process_press(1, 99)

    def stop_game(self):
        self.game_running = False
        if self.game: self.game.state = "PAUSED"
        self.network.all_off()

    def resume_game(self):
        self.game_running = True
        if self.game:
            self.game.state = "WAITING"
            self.ui.update_status("Resumed", "#00ff88")

    def end_game(self):
        self.network.all_off()
        self.root.destroy()

    def play_background_music(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_path, "game_logic/_sfx/background.mp3") 
        if os.path.exists(path) and self.audio_ok:
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
                print(f"🎵 Muzica on: {path}")
            except Exception as e:
                print(f"⚠️ Error music: {e}")
        else:
            print(f"❌ Music not found: {path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MasterLauncher(root)
    
    print("🖥️ Mod pornire: Verifică Network Setup în interfață")
    app.network.set_device("127.0.0.1") 
        
    root.mainloop()