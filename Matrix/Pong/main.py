import sys
import tkinter as tk

# --- IMPORTURILE CURATE ---
from display.outside_display import OutsideDisplay, COLORS
from display.inside_display import InsideDisplay
from game_logic.PongGame import PongGame
from Controller import NetworkManager 
from Simulator import *
import pygame

HAS_AUDIO = False
try:
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
    HAS_AUDIO = True
    print("🔊 Sistem audio inițializat cu succes.")
except Exception as e:
    print(f"⚠️ Atenție: Mixerul audio nu a putut fi pornit ({e}). Jocul va rula fără sunet.")

class MasterLauncher:
    def __init__(self, root):
        pygame.mixer.init()
        self.root = root
        self.root.title("Pong LED Matrix - Master Controller")
        self.root.geometry("500x750")
        self.root.configure(bg="#000000")
        
        self.is_paused = False
        self.update_job = None

        # --- CREARE FEREASTRĂ STADION ---
        self.arena_window = tk.Toplevel(self.root)
        self.arena_window.title("STADIUM VIEW")
        self.arena_window.geometry("800x600+600+100") 
        self.arena_window.configure(bg="black")

        # --- CONECTAREA UI-ULUI EXTERN ---
        # Aici instanțiem display-ul și îi spunem ce funcții să ruleze când se apasă butoanele
        self.ui = OutsideDisplay(self.root, self.on_start, self.on_stop, self.toggle_pause)
        
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)
        self.is_paused = False
        self.update_job = None

        # --- ÎNCĂRCARE SUNET CU VERIFICARE ---
        self.snd_fail = None
        if HAS_AUDIO:
            sound_path = os.path.join("game_logic", "sfx", "fail.wav")
            if os.path.exists(sound_path):
                self.snd_fail = pygame.mixer.Sound(sound_path)
            else:
                print(f"❌ Fișierul de sunet nu a fost găsit la: {sound_path}")

        from Controller import CONFIG as NET_CONFIG
        print("\n" + "="*30)
        print(f"🚀 PORNIRE JOC: {datetime.now().strftime('%H:%M:%S')}")
        print(f"📡 DESTINAȚIE IP: {NET_CONFIG.get('device_ip')}")
        print(f"📤 PORT TRIMITERE (Imagine): {NET_CONFIG.get('send_port')}")
        print(f"📥 PORT RECEPȚIE (Butoane): {NET_CONFIG.get('recv_port')}")
        print("="*30 + "\n")
        # ------------------------

    def on_start(self):
        """Pornirea meciului și crearea ferestrelor."""
        # 1. Datele din UI
        setup = self.ui.get_selected_setup()
        
        # 2. CREARE / RECREARE FEREASTRĂ STADION
        # Dacă fereastra există deja, o închidem ca să pornim de la zero
        if hasattr(self, 'arena_window') and self.arena_window.winfo_exists():
            self.arena_window.destroy()
        
        self.arena_window = tk.Toplevel(self.root)
        self.arena_window.title("STADIUM VIEW")
        self.arena_window.geometry("800x600+600+100") 
        self.arena_window.configure(bg="black")

        # 3. Creăm logica și afișajul stadionului
        self.game_engine = PongGame(
            level=setup["difficulty"], 
            p1_rgb=setup["p1_color"], 
            p2_rgb=setup["p2_color"], 
            total_rounds=setup["rounds"]
        )
        
        self.stadium_gui = InsideDisplay(
            container=self.arena_window,
            p1_color_hex=COLORS[self.ui.p1_color_name][3],
            p2_color_hex=COLORS[self.ui.p2_color_name][3],
            difficulty=setup["difficulty"],
            total_rounds=setup["rounds"]
        )

        # 4. Restul pornirii (Simulator, Network, Countdown)
        if hasattr(self, 'sim_window') and self.sim_window.winfo_exists():
            self.sim_window.destroy()
        self.sim_window = tk.Toplevel(self.root)
        self.game_window = MatrixSimulator(self.sim_window)

        self.net_manager = NetworkManager(self.game_engine)
        self.net_manager.start_bg()
        
        self.ui.show_game_controls()
        self.is_paused = False
        self.run_countdown(3)

    def run_countdown(self, seconds):
        if seconds > 0:
            self.stadium_gui.set_pause_status(True, custom_text=str(seconds))
            self.game_engine.state = "COUNTDOWN"
            self.game_engine.current_digit = seconds
            self.root.after(1000, lambda: self.run_countdown(seconds - 1))
        else:
            self.stadium_gui.set_pause_status(False)
            self.game_engine.state = "PLAYING"
            self.update_loop()

    def update_loop(self):
        if self.update_job:
            self.root.after_cancel(self.update_job)
            self.update_job = None

        if not self.is_paused:
            status = self.game_engine.tick()
            
            # Luăm scorul curent
            s1, s2 = self.game_engine.p1.score, self.game_engine.p2.score
            
            # --- MODIFICARE AICI ---
            # Nu mai facem update la self.ui.lbl_score (am șters-o)
            # Actualizăm DOAR ecranul de Stadion
            self.stadium_gui.update_score(s1, s2)
            
            # Update Scorul de SETURI și Runda pe stadion
            self.stadium_gui.update_round_display(
                self.game_engine.current_round, 
                self.game_engine.total_rounds,
                self.game_engine.rounds_won_p1,
                self.game_engine.rounds_won_p2
            )

            if status:
                if status.startswith("WINNER"):
                    self.trigger_winner_sequence(status)
                    return
                elif status and status.startswith("GOAL"):
                    # Redă un sunet de frecvență joasă (400Hz) timp de 500ms
                    self.snd_fail.play()
                elif status.startswith("ROUND_OVER"):
                    # Apelăm handler-ul de final de rundă creat anterior
                    self.handle_round_end(status)
                    return

        # Programăm următorul cadru la ~16ms (60 FPS)
        self.update_job = self.root.after(16, self.update_loop)

    def handle_round_end(self, status):
        total_needed = self.ui.rounds_var.get()
        
        # Actualizăm afișajul de seturi pe stadion
        self.stadium_gui.update_round_display(
            self.game_engine.current_round, 
            total_needed,
            self.game_engine.rounds_won_p1,
            self.game_engine.rounds_won_p2
        )

        # Verificăm dacă cineva a câștigat majoritatea rundelor
        # (Ex: dacă se joacă 3 runde, cine are 2 câștigă)
        limit = (total_needed // 2) + 1
        
        if self.game_engine.rounds_won_p1 >= limit or self.game_engine.rounds_won_p2 >= limit:
            winner = "P1" if self.game_engine.rounds_won_p1 > self.game_engine.rounds_won_p2 else "P2"
            self.trigger_winner_sequence(f"WINNER_{winner}")
        elif self.game_engine.current_round < total_needed:
            # Trecem la runda următoare
            self.game_engine.current_round += 1
            self.game_engine.reset_for_new_round()
            
            # Anunțăm noua rundă pe ecran
            self.stadium_gui.set_pause_status(True, custom_text=f"START ROUND {self.game_engine.current_round}")
            self.root.after(2000, lambda: self.run_countdown(3))
        else:
            # Caz de egalitate sau final de runde (dacă nu e sistem de "cel mai bun din X")
            winner = "P1" if self.game_engine.rounds_won_p1 > self.game_engine.rounds_won_p2 else "P2"
            self.trigger_winner_sequence(f"WINNER_{winner}")

    def trigger_winner_sequence(self, status):
        winner_id = 1 if "P1" in status else 2
        self.game_engine.winner = winner_id
        self.game_engine.state = "GAME_OVER_EXPLOSION"
        
        self.stadium_gui.set_pause_status(True, custom_text=f"WINNER P{winner_id}!")
        self.root.after(2500, self.show_win_lose_text)

    def show_win_lose_text(self):
        self.game_engine.state = "GAME_OVER_TEXT"
        self.root.after(4000, self.on_stop)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.stadium_gui.set_pause_status(self.is_paused)
        
        if hasattr(self, 'game_engine'):
            if self.is_paused:
                self.game_engine.state = "PAUSED"
            else:
                self.game_engine.state = "PLAYING"

    def on_stop(self):
        """Oprește jocul și închide ferestrele secundare."""
        # Oprim loop-ul de update
        if self.update_job: 
            self.root.after_cancel(self.update_job)
            self.update_job = None
            
        # Oprim rețeaua
        if hasattr(self, 'net_manager'): 
            self.net_manager.running = False

        # ÎNCHIDEM ferestrele (Simulator + Stadion)
        if hasattr(self, 'sim_window') and self.sim_window.winfo_exists():
            self.sim_window.destroy()
            
        if hasattr(self, 'arena_window') and self.arena_window.winfo_exists():
            self.arena_window.destroy()
            
        # Revenim la meniul principal de Control
        self.ui.setup_ui()
    def cleanup(self):
        self.on_stop()
        self.root.destroy()
        sys.exit()

if __name__ == "__main__":
    root = tk.Tk()
    app = MasterLauncher(root)
    root.mainloop()