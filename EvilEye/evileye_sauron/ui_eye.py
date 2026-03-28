# ui_eye.py
import tkinter as tk
from config_eye import *

class EyeDashboardUI:
    def __init__(self, title_text="EVIL EYE GAME"):
        self.root = tk.Tk()
        self.root.title("LEDHACK - Evil Eye Dashboard")
        self.root.geometry("1024x768") 
        self.root.configure(bg="black")
        
        # 1. Titlu Principal Gigant
        tk.Label(self.root, text=title_text, font=("Consolas", 65, "bold"), fg="white", bg="black").pack(pady=(40, 10))
        
        # 2. Afișarea Vieților (Adăugat la cerere)
        self.lbl_lives = tk.Label(self.root, text="❤️❤️❤️", font=("Consolas", 50), fg="red", bg="black")
        self.lbl_lives.pack(pady=(0, 20))

        # 3. PĂTRATUL URIAȘ DE CULOARE
        self.pnl_first_click_color = tk.Frame(self.root, bg="black", width=500, height=500, relief="solid", bd=8)
        self.pnl_first_click_color.pack_propagate(False)
        self.pnl_first_click_color.pack(expand=True, pady=20)
        
        self._pulse_active = False 

    def update_lives(self, lives):
        """Actualizează HP-ul pe ecran"""
        lives_text = "❤️" * lives if lives > 0 else "💀"
        self.root.after(0, lambda: self.lbl_lives.config(text=lives_text))

    def update_eye_status(self, phase):
        """Gestionează doar pâlpâirea vizuală pe ecran, fără text suplimentar"""
        if phase == "active":
            self.start_eye_pulse()
        else:
            self.stop_eye_pulse()

    def set_first_click_color(self, rgb_color):
        """Setează culoarea ultimului buton apăsat în pătratul mare"""
        hex_color = '#%02x%02x%02x' % rgb_color if rgb_color else "black"
        self.root.after(0, lambda: self.pnl_first_click_color.config(bg=hex_color))

    # --- Logică Pâlpâire UI pentru Ochi Activ ---
    def start_eye_pulse(self):
        if not self._pulse_active:
            self._pulse_active = True
            self._pulse_rec_func() 

    def stop_eye_pulse(self):
        self._pulse_active = False 
        self.root.after(0, lambda: self.pnl_first_click_color.config(bg="black"))

    def _pulse_rec_func(self):
        if not self._pulse_active: return
        current_color = self.pnl_first_click_color.cget("bg")
        next_color = "red" if current_color != "red" else "black"
        self.pnl_first_click_color.config(bg=next_color)
        self.root.after(200, self._pulse_rec_func)

    def run(self):
        self.root.mainloop()