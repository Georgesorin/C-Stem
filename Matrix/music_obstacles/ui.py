import tkinter as tk

class DashboardUI(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("LEDHACK - Game Dashboard")
        self.geometry("800x600")
        self.configure(bg="black")
        
        self._build_game_frame()
        self.game_frame.pack(fill="both", expand=True)

    def _build_game_frame(self):
        self.game_frame = tk.Frame(self, bg="black")
        
        self.lbl_game = tk.Label(self.game_frame, text="MATRIX SURVIVAL", font=("Consolas", 45, "bold"), bg="black", fg="white")
        self.lbl_game.pack(pady=40)
        
        self.lbl_lives = tk.Label(self.game_frame, text="❤️" * 5, font=("Consolas", 40), bg="black", fg="red")
        self.lbl_lives.pack(pady=20)
        
        self.lbl_instruction = tk.Label(self.game_frame, text="Așteptare jucători...", font=("Consolas", 20), bg="black", fg="yellow")
        self.lbl_instruction.pack(pady=10)
        
        self.lbl_score = tk.Label(self.game_frame, text="SCOR: 0", font=("Consolas", 60, "bold"), bg="black", fg="#00FF00")
        self.lbl_score.pack(side="bottom", pady=50)

    def update_dashboard(self, status, instr, color="white"):
        self.lbl_game.config(text=status, fg=color)
        self.lbl_instruction.config(text=instr)

    def update_score(self, score):
        self.lbl_score.config(text=f"SCOR: {score}")

    def update_lives(self, lives):
        if lives > 0:
            self.lbl_lives.config(text="❤️" * lives)
        else:
            self.lbl_lives.config(text="💀💀💀")

    def show_game_over(self, score):
        self.lbl_game.config(text="GAME OVER", fg="red")
        self.lbl_instruction.config(text="Ai rămas fără vieți!", fg="white")
        self.lbl_score.config(text=f"PUNCTAJ FINAL: {score}", fg="yellow")
        self.lbl_lives.config(text="💀💀💀")
        
    def reset_dashboard(self):
        self.lbl_game.config(text="MATRIX SURVIVAL", fg="white")
        self.lbl_instruction.config(text="Jocul este în desfășurare...", fg="yellow")
        self.lbl_score.config(text="SCOR: 0", fg="#00FF00")
        self.lbl_lives.config(text="❤️" * 5)