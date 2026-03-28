import tkinter as tk
import threading
import sys
import os
import time

# Asigurăm vizibilitatea modulelor
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Controller import LightService
from Simulator import EvilEyeSimulator
from display.outside_display import ControlPanel
from game_logic.memory_game import MemoryGame

class MasterLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Evil Eye Controller")
        # Fereastră mai mare la pornire
        self.root.geometry("400x700")
        self.root.configure(bg="#0b0b10")
        
        self.game_running = False

        self.network = LightService()
        self.network.set_device("127.0.0.1")
        self.network.start_receiver()
        self.network.start_polling()

        self.sim_window = tk.Toplevel(self.root)
        self.simulator = EvilEyeSimulator(self.sim_window)

        # UI-ul primește acum și resume_callback
        self.ui = ControlPanel(self.root, self.start_game, self.stop_game, self.resume_game, self.end_game)

        self.network.on_button_state = self._hardware_input_handler

    def _hardware_input_handler(self, ch, led, is_trig, is_disc):
        # 1. Verificăm dacă jocul există
        # 2. Verificăm dacă suntem în starea WAITING
        # 3. Verificăm dacă e apăsare (is_trig), nu eliberare
        if is_trig and hasattr(self, 'game') and self.game:
            if self.game.state == "WAITING":
                # Executăm pe thread-ul principal Tkinter
                self.root.after(0, lambda: self._process_press(ch, led))

    def _process_press(self, ch, led):
        result = self.game.check_press(ch, led)
        
        # Ignorăm dacă jocul a decis să nu proceseze (ex: e deja în fail sau showing)
        if result == "IGNORE":
            return

        # PASUL 1: Întotdeauna colorăm butonul apăsat în VERDE dacă e corect 
        # (indiferent dacă e ultimul sau nu)
        if result in ["STEP_CORRECT", "LEVEL_COMPLETE"]:
            self.network.set_led(ch, led, 0, 255, 0) # Verde pe buton
            # Îl stingem după 300ms
            self.root.after(300, lambda c=ch, l=led: self.network.set_led(c, l, 0, 0, 0))

        # PASUL 2: Procesăm logica de final de nivel sau final de joc
        if result == "LEVEL_COMPLETE":
            # Ochiul se face VERDE pentru succes la tot nivelul
            # Folosim un mic delay ca să nu se bată cu feedback-ul butonului
            self.root.after(100, lambda: self.network.set_led(ch, 0, 0, 255, 0))
            self.ui.update_status(f"Level {self.game.level} Won!", "#00ff88")
            
            # Așteptăm puțin să vadă succesul, apoi trecem la nivelul următor
            self.root.after(1500, self.run_next_round)
            
        elif result == "GAME_OVER":
            # Ochiul se face ROȘU pentru greșeală
            self.network.set_led(ch, 0, 255, 0, 0)
            self.ui.update_status("SEQUENCE FAILED!", "#ff1744")
            
            # Resetăm jocul și reluăm de la Nivelul 1 după o pauză
            self.game.reset()
            self.root.after(2000, self.run_next_round)

    def _play_sequence_thread(self):
        """Rulează secvența de memorat cu noile culori."""
        self.game.state = "SHOWING"
        self.network.all_off()
        time.sleep(0.5)
        
        steps = self.game.add_next_step()
        
        # PASUL A: Arătăm peretele activ folosind CYAN pe Ochi (LED 0)
        # Luăm peretele ultimului pas adăugat
        active_wall = steps[-1][0] 
        self.network.set_led(active_wall, 0, 0, 242, 255) # Cyan-ul tău neon
        time.sleep(1.2)
        
        # Stingem ochiul înainte de a începe butoanele (sau îl lăsăm aprins, cum preferi)
        self.network.set_led(active_wall, 0, 0, 0, 0)
        time.sleep(0.3)

        # PASUL B: Arătăm butoanele în ALBASTRU
        for w, l in steps:
            self.network.set_led(w, l, 0, 0, 255) # Albastru pur
            time.sleep(0.8)
            self.network.set_led(w, l, 0, 0, 0)
            time.sleep(0.2)
        
        self.game.state = "WAITING"
        self.root.after(0, lambda: self.ui.update_status("Input Required"))

    def start_game(self):
        # 1. Luăm numărul de jucători de pe butoanele de pe ControlPanel
        players = self.ui.players_var.get()
        
        # 2. Inițializăm motorul cu acest număr
        self.game = MemoryGame(num_players=players)
        
        # 3. Log în consolă pentru debug
        print(f"DEBUG: Start joc cu {players} jucători pe pereții: {self.game.active_walls}")
        
        self.game_running = True
        self.run_next_round()

    def stop_game(self):
        self.game_running = False
        if hasattr(self, 'game'):
            self.game.state = "PAUSED"
        self.network.all_off()

    def resume_game(self):
        self.game_running = True
        if hasattr(self, 'game'):
            self.game.state = "WAITING"
            # Reafișăm starea pentru jucători
            self.ui.update_status("Mission Resumed", "#00ff88")
            # Dacă vrei să re-arate secvența când dai resume, apelezi run_next_round()
            # Dacă vrei doar să poată continua apăsarea, nu mai apelezi nimic.

    def end_game(self):
        self.network.all_off()
        self.root.destroy()

    def run_next_round(self):
        if self.game_running:
            threading.Thread(target=self._play_sequence_thread, daemon=True).start()

    def _play_sequence_thread(self):
        time.sleep(1)
        steps = self.game.add_next_step()
        
        # Ochiul peretelui unde apare pasul nou
        new_wall = steps[-1][0]
        self.network.set_led(new_wall, 0, 255, 0, 0)
        time.sleep(1)
        self.network.all_off()
        time.sleep(0.5)

        # Redare secvență
        for w, l in steps:
            self.network.set_led(w, l, 0, 255, 255)
            time.sleep(0.7)
            self.network.set_led(w, l, 0, 0, 0)
            time.sleep(0.2)
        
        self.game.state = "WAITING"
        self.root.after(0, lambda: self.ui.update_status("Your turn!"))

if __name__ == "__main__":
    root = tk.Tk()
    app = MasterLauncher(root)
    root.mainloop()