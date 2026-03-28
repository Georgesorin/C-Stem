# ui.py
import tkinter as tk

class DashboardUI:
    def __init__(self, on_start_callback):
        self.on_start_callback = on_start_callback
        
        self.root = tk.Tk()
        self.root.title("LEDHACK - Setup & Dashboard")
        self.root.geometry("800x600")
        self.root.configure(bg="black")
        
        self._build_setup_frame()
        self._build_game_frame()
        
        self.setup_frame.pack(fill="both", expand=True)

    def _build_setup_frame(self):
        self.setup_frame = tk.Frame(self.root, bg="black")
        tk.Label(self.setup_frame, text="DISASTER SURVIVAL", font=("Consolas", 45, "bold"), fg="white", bg="black").pack(pady=(40, 10))
        tk.Label(self.setup_frame, text="Selectează numărul de jucători:", font=("Consolas", 22), fg="yellow", bg="black").pack(pady=10)
        
        btn_frame = tk.Frame(self.setup_frame, bg="black")
        btn_frame.pack(pady=10, expand=True) 
        
        for i in range(2, 8): 
            btn = tk.Button(btn_frame, text=str(i), font=("Consolas", 55, "bold"), bg="white", fg="black", width=2, height=1, relief="raised", bd=5, activebackground="#DDDDDD", command=lambda players=i: self._handle_start(players))
            btn.grid(row=(i-2)//3, column=(i-2)%3, padx=25, pady=20)

    def _build_game_frame(self):
        self.game_frame = tk.Frame(self.root, bg="black")
        self.lbl_game = tk.Label(self.game_frame, text="DISASTER SURVIVAL", font=("Consolas", 35, "bold"), bg="black", fg="white")
        self.lbl_game.pack(pady=20)
        self.lbl_lives = tk.Label(self.game_frame, text="", font=("Consolas", 40), bg="black", fg="red")
        self.lbl_lives.pack(pady=10)
        self.lbl_instruction = tk.Label(self.game_frame, text="Pregătire...", font=("Consolas", 20), bg="black", fg="yellow")
        self.lbl_instruction.pack(pady=10)
        self.lbl_score = tk.Label(self.game_frame, text="SCOR: 0", font=("Consolas", 60, "bold"), bg="black", fg="#00FF00")
        self.lbl_score.pack(side="bottom", pady=50)

    def _handle_start(self, players):
        """Tranziția de la Setup la Joc"""
        self.setup_frame.pack_forget()
        self.game_frame.pack(fill="both", expand=True)
        self.on_start_callback(players) # Anunță main.py că a început jocul!

    def update_dashboard(self, status, instr, color="white"):
        self.root.after(0, lambda: self.lbl_game.config(text=status, fg=color))
        self.root.after(0, lambda: self.lbl_instruction.config(text=instr))

    def update_score(self, score):
        self.root.after(0, lambda: self.lbl_score.config(text=f"SCOR: {score}"))

    def update_lives(self, lives):
        self.root.after(0, lambda: self.lbl_lives.config(text="❤️" * max(0, lives)))

    def show_game_over(self, score):
        self.root.after(0, lambda: self.lbl_game.config(text="GAME OVER", fg="red"))
        self.root.after(0, lambda: self.lbl_instruction.config(text="Echipa a fost eliminată!", fg="white"))
        self.root.after(0, lambda: self.lbl_score.config(text=f"PUNCTAJ FINAL: {score}", fg="yellow"))
        self.root.after(0, lambda: self.lbl_lives.config(text="💀💀💀"))

    def return_to_setup(self):
        self.game_frame.pack_forget()
        self.setup_frame.pack(fill="both", expand=True)

    def run(self):
        """Asta blochează programul și ține fereastra deschisă"""
        self.root.mainloop()