# ui_eye.py
import tkinter as tk
from config_eye import *

class EyeDashboardUI:
    def __init__(self, title_text="EVIL EYE GAME"):
        self.root = tk.Tk()
        self.root.title("LEDHACK - Evil Eye Dashboard")
        self.root.geometry("1024x768") # Rezoluție mare pentru monitor secundar
        self.root.configure(bg="black")
        
        # Titlu Principal Gigant (Regula 6: Clear Feedback)
        tk.Label(self.root, text=title_text, font=("Consolas", 65, "bold"), fg="white", bg="black").pack(pady=(50, 20))
        
        # Container pentru HP și Scor
        stats_frame = tk.Frame(self.root, bg="black")
        stats_frame.pack(pady=30)
        
        self.lbl_score = tk.Label(stats_frame, text="Perechi: 0/20", font=("Consolas", 50, "bold"), fg="#00FF00", bg="black")
        self.lbl_score.pack(side="left", padx=60)
        
        self.lbl_lives = tk.Label(stats_frame, text="❤️❤️❤️", font=("Consolas", 50), fg="red", bg="black")
        self.lbl_lives.pack(side="left", padx=60)

        # Mesaj Instrucțiuni/Stare Ochi (Text FOARTE mare)
        self.lbl_status = tk.Label(self.root, text="Așteptare...", font=("Consolas", 40, "bold"), fg="yellow", bg="black")
        self.lbl_status.pack(expand=True) # Acest Label va fi centrat pe verticală
        
        # === CASUȚA "CULOAREA CĂUTATĂ" A FOST ȘTEARSĂ CONFORM CERINȚEI ===

        self._pulse_active = False # Stare pentru pâlpâirea ochiului activ

    def update_stats(self, score, lives):
        """Actualizează scorul și HP-ul în siguranță"""
        # Regula 6: Clear Feedback for Players
        score_text = f"Perechi: {score}/20"
        lives_text = "❤️" * lives if lives > 0 else "💀"
        self.root.after(0, lambda: self.lbl_score.config(text=score_text))
        self.root.after(0, lambda: self.lbl_lives.config(text=lives_text))

    def update_eye_status(self, phase):
        """Actualizează mesajul despre starea Ochiului"""
        #
        phase_map = {
            "sleeping": ("ZONA ESTE SIGURĂ", "green"),
            "warning": ("OCHII PÂLPÂIE - PREGĂTIRE FREEZE!", "orange"),
            "active": ("OCHI DESCHIȘI - NU TE MIȘCA!", "red"),
            "matched": ("PERECHE GHICITĂ!", "white"),
            "wrong": ("GRESIT - CAUTĂ ALTCEVA!", "white"),
            "damage": ("MIȘCARE DETECTATĂ! RESETARE ZONĂ.", "red"),
            "win": ("🎉 VICTORIE! ZONE SECURE 🎉", "#00FF00"),
            "game_over": ("💀 JOC TERMINAT 💀", "red")
        }
        
        text, color = phase_map.get(phase, ("Așteptare...", "white"))
        self.root.after(0, lambda: self.lbl_status.config(text=text, fg=color))
        
        # Gestionăm pâlpâirea pe ecran când ochiul e activ
        if phase == "active":
            self.start_eye_pulse()
        else:
            self.stop_eye_pulse()

    # --- Logică Pâlpâire UI pentru Ochi Activ (Pâlpâie tot fundalul) ---
    def start_eye_pulse(self):
        if not self._pulse_active:
            self._pulse_active = True
            self._pulse_rec_func() # Pornește bucla recursivă

    def stop_eye_pulse(self):
        """Oprește bucla și forțează fundalul negru (starea stins)"""
        self._pulse_active = False 
        self.root.after(0, lambda: self.root.config(bg="black")) # Ne asigurăm că rămâne negru

    def _pulse_rec_func(self):
        """Recursivitate pentru a face tot fundalul ecranului să pâlpâie (Regula 10 & Imersiune)"""
        if not self._pulse_active: return
        
        current_bg = self.root.cget("bg")
        next_bg = "red" if current_bg != "red" else "black"
        
        # Pâlpâire rapidă a fundalului (200ms)
        #
        self.root.config(bg=next_bg)
        self.root.after(200, self._pulse_rec_func)

    def run(self):
        """Asta blochează programul și ține fereastra deschisă"""
        self.root.mainloop()