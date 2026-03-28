import tkinter as tk
import threading
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Controller import LightService
from Simulator import EvilEyeSimulator
from display.outside_display import ControlPanel
from game_logic.memory_game import MemoryGame

class MasterLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Evil Eye Controller")
        self.root.geometry("400x750")
        self.root.configure(bg="#0b0b10")
        
        self.game_running = False
        self.stop_timer_event = threading.Event()

        self.network = LightService()
        self.network.set_device("127.0.0.1")
        self.network.start_receiver()
        self.network.start_polling()

        self.sim_window = tk.Toplevel(self.root)
        self.simulator = EvilEyeSimulator(self.sim_window)

        self.ui = ControlPanel(self.root, self.start_game, self.stop_game, self.resume_game, self.end_game)
        self.network.on_button_state = self._hardware_input_handler

    def _hardware_input_handler(self, ch, led, is_trig, is_disc):
        if is_trig and hasattr(self, 'game') and self.game:
            if self.game.state == "WAITING":
                self.root.after(0, lambda: self._process_press(ch, led))

    def _process_press(self, ch, led):
        self.stop_timer_event.set() 
        result = self.game.check_press(ch, led)
        if result == "IGNORE": return

        # Feedback corect: Verde pe buton
        if result in ["STEP_CORRECT", "LEVEL_COMPLETE", "ULTIMATE_WIN"]:
            self.network.set_led(ch, led, 0, 255, 0)
            self.root.after(300, lambda c=ch, l=led: self.network.set_led(c, l, 0, 0, 0))

        if result == "LEVEL_COMPLETE":
            self.network.set_led(ch, 0, 0, 255, 0) # Ochi Verde scurt
            self.ui.update_status(f"Step {len(self.game.sequence)}/10 Complete", "#00ff88")
            self.root.after(1000, self.run_next_round)

        elif result == "ULTIMATE_WIN":
            self.game_running = False
            for wall in range(1, 5): self.network.set_led(wall, 0, 0, 255, 0)
            self.ui.show_full_screen_message("MISSION COMPLETE\nYOU WIN", "#00ff88")
            self.root.after(5000, self._reset_to_lobby)

        elif result == "GAME_OVER":
            self.game_running = False
            
            # 1. Colorăm butonul gresit în ROȘU fix
            self.network.set_led(ch, led, 255, 0, 0)
            
            # 2. Mesaj gigant pe ecran
            self.ui.show_full_screen_message("SYSTEM FAILURE\nYOU LOSE", "#ff2a6d")
            
            # 3. Pornim animația de "sclipocire" a ochilor pe un thread separat
            threading.Thread(target=self._alarm_strobe_thread, daemon=True).start()
            
            # 4. Reset după 4 secunde (timp în care ochii sclipesc)
            self.root.after(4000, self._reset_to_lobby)

    def _alarm_strobe_thread(self):
        """Efect de stroboscop roșu pentru toți ochii."""
        # Sclipim de 6 ori (3 secunde total)
        for _ in range(6):
            # Aprindem toți ochii (LED 0)
            for wall in range(1, 5):
                self.network.set_led(wall, 0, 255, 0, 0)
            time.sleep(0.3)
            
            # Stingem toți ochii
            for wall in range(1, 5):
                self.network.set_led(wall, 0, 0, 0, 0)
            time.sleep(0.2)

    def _reset_to_lobby(self):
        self.network.all_off()
        if hasattr(self, 'game'): self.game.reset()
        self.ui.hide_full_screen_message()
        self.ui.show_setup()

    def start_game(self):
        players = self.ui.players_var.get()
        self.game = MemoryGame(num_players=players)
        self.game_running = True
        self.run_next_round()

    def run_next_round(self):
        if self.game_running:
            threading.Thread(target=self._play_sequence_thread, daemon=True).start()

    def _play_sequence_thread(self):
        self.game.state = "SHOWING"
        self.network.all_off()
        time.sleep(0.5)
        
        new_wall, new_led = self.game.add_next_step()
        
        # Indicator Cyan pe Ochi
        self.network.set_led(new_wall, 0, 0, 242, 255)
        time.sleep(1.0)
        self.network.set_led(new_wall, 0, 0, 0, 0)
        time.sleep(0.2)

        # Arată noul buton (Albastru)
        self.network.set_led(new_wall, new_led, 0, 0, 255)
        time.sleep(1.0)
        self.network.set_led(new_wall, new_led, 0, 0, 0)
        
        self.game.state = "WAITING"
        self.root.after(0, lambda: self.ui.update_status("Your turn!"))

        self.stop_timer_event.clear()
        threading.Thread(target=self._round_timer_thread, daemon=True).start()

    def _round_timer_thread(self):
        start_time = time.time()
        timeout = 15  # Secunde totale
        warning_time = 5 # Ultimele 5 secunde
        
        while time.time() - start_time < timeout:
            # Dacă jucătorul a terminat runda sau a greșit, oprim timer-ul
            if self.stop_timer_event.is_set() or not self.game_running:
                return

            elapsed = time.time() - start_time
            remaining = timeout - elapsed

            # Actualizăm UI-ul cu timpul rămas (opțional)
            self.root.after(0, lambda r=remaining: self.ui.update_status(f"Time: {int(r)}s"))

            # Logica de sclipocire (Hint) în ultimele 5 secunde
            if remaining <= warning_time:
                # Aflăm care este peretele unde se află piesa curentă
                target_wall, _ = self.game.sequence[self.game.current_step]
                
                # Sclipici Cyan pe ochiul peretelui țintă
                self.network.set_led(target_wall, 0, 0, 242, 255)
                time.sleep(0.2)
                self.network.set_led(target_wall, 0, 0, 0, 0)
                time.sleep(0.2)
            else:
                time.sleep(0.1) # Verificare deasă a condițiilor

        # Dacă am ieșit din While, înseamnă că timpul a expirat
        if not self.stop_timer_event.is_set() and self.game_running:
            self.root.after(0, self._handle_timeout)

    def _handle_timeout(self):
        """Ce se întâmplă când expiră cele 15 secunde."""
        # Considerăm timeout-ul ca fiind un Game Over (Eșec)
        # Folosim peretele 1 ca referință pentru animația de fail dacă nu a apăsat nimic
        self._process_press(1, 99) # Trimitem un index de LED care nu există ca să forțăm FAIL

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

if __name__ == "__main__":
    root = tk.Tk()
    app = MasterLauncher(root)
    root.mainloop()