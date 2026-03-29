# ui_natural.py
import tkinter as tk

class DashboardUI:
    def __init__(self, on_start_callback):
        self.on_start_callback = on_start_callback
        
        self.root = tk.Tk()
        self.root.title("LEDHACK - Matrix Arcade")
        self.root.geometry("1024x768")
        self.root.configure(bg="black")
        
        # Modul Arcade (Fullscreen, fără margini)
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", lambda event: self.root.attributes("-fullscreen", False))
        
        # Variabile pentru configurare
        self.selected_players = 2
        self.selected_difficulty = "Normal"
        self.selected_game = None
        
        self._build_setup_frame()
        self._build_tutorial_frame()
        self._build_game_frame()
        
        self.setup_frame.pack(fill="both", expand=True)

    def _build_setup_frame(self):
        self.setup_frame = tk.Frame(self.root, bg="black")
        tk.Label(self.setup_frame, text="MATRIX ARCADE", font=("Consolas", 55, "bold"), fg="white", bg="black").pack(pady=(30, 10))
        
        # --- 1. Configurare Jucători ---
        tk.Label(self.setup_frame, text="1. NUMĂR JUCĂTORI:", font=("Consolas", 20), fg="yellow", bg="black").pack(pady=(10, 0))
        players_frame = tk.Frame(self.setup_frame, bg="black")
        players_frame.pack()
        self.btn_players = {}
        for i in range(2, 8):
            # FOLOSIM tk.Label IN LOC DE tk.Button PENTRU A FORȚA CULORILE PE MAC
            lbl = tk.Label(players_frame, text=str(i), font=("Consolas", 25, "bold"), bg="#333", fg="white", width=3, cursor="hand2")
            lbl.bind("<Button-1>", lambda e, p=i: self._select_players(p))
            lbl.pack(side="left", padx=5, pady=5)
            self.btn_players[i] = lbl
        self._select_players(2) # Selectat implicit
        
        # --- 2. Configurare Dificultate ---
        tk.Label(self.setup_frame, text="2. DIFICULTATE:", font=("Consolas", 20), fg="yellow", bg="black").pack(pady=(20, 0))
        diff_frame = tk.Frame(self.setup_frame, bg="black")
        diff_frame.pack()
        self.btn_diffs = {}
        for d in ["Easy", "Normal", "Hard"]:
            lbl = tk.Label(diff_frame, text=d, font=("Consolas", 20, "bold"), bg="#333", fg="white", width=8, cursor="hand2")
            lbl.bind("<Button-1>", lambda e, dif=d: self._select_diff(dif))
            lbl.pack(side="left", padx=10, pady=5)
            self.btn_diffs[d] = lbl
        self._select_diff("Normal") # Selectat implicit
        
        # --- 3. Selectare Joc ---
        tk.Label(self.setup_frame, text="3. SELECTEAZĂ JOCUL:", font=("Consolas", 20), fg="yellow", bg="black").pack(pady=(30, 10))
        games_frame = tk.Frame(self.setup_frame, bg="black")
        games_frame.pack(expand=True)
        
        btn_lava = tk.Label(games_frame, text="THE FLOOR IS LAVA", font=("Consolas", 30, "bold"), bg="#FF4500", fg="white", pady=10, cursor="hand2")
        btn_lava.bind("<Button-1>", lambda e: self._show_tutorial("lava"))
        btn_lava.pack(pady=10, fill="x")
        
        btn_meteors = tk.Label(games_frame, text="METEOR SHOWER", font=("Consolas", 30, "bold"), bg="#8B0000", fg="white", pady=10, cursor="hand2")
        btn_meteors.bind("<Button-1>", lambda e: self._show_tutorial("meteors"))
        btn_meteors.pack(pady=10, fill="x")
        
        # (Asta vine imediat sub butonul btn_meteors)
        btn_tnt = tk.Label(games_frame, text="TNT RUN", font=("Consolas", 30, "bold"), bg="#FFD700", fg="black", pady=10, cursor="hand2")
        btn_tnt.bind("<Button-1>", lambda e: self._show_tutorial("tnt"))
        btn_tnt.pack(pady=10, fill="x")

        # --- 4. BUTON DE IEȘIRE DIN JOC ---
        btn_exit = tk.Label(self.setup_frame, text="IEȘIRE JOC", font=("Consolas", 20, "bold"), bg="#aa0000", fg="white", pady=5, padx=20, cursor="hand2")
        btn_exit.bind("<Button-1>", lambda e: self.root.destroy()) # Distruge fereastra și închide aplicația
        btn_exit.pack(side="bottom", pady=25)

    def _select_players(self, p):
        self.selected_players = p
        for i, lbl in self.btn_players.items():
            lbl.config(bg="white" if i == p else "#333", fg="black" if i == p else "white")
            
    def _select_diff(self, d):
        self.selected_difficulty = d
        for dif, lbl in self.btn_diffs.items():
            lbl.config(bg="white" if dif == d else "#333", fg="black" if dif == d else "white")

    def _build_tutorial_frame(self):
        self.tutorial_frame = tk.Frame(self.root, bg="black")
        self.lbl_tut_title = tk.Label(self.tutorial_frame, text="TUTORIAL", font=("Consolas", 50, "bold"), fg="white", bg="black")
        self.lbl_tut_title.pack(pady=(50, 20))
        
        self.lbl_tut_desc = tk.Label(self.tutorial_frame, text="", font=("Consolas", 22), fg="yellow", bg="black", justify="center")
        self.lbl_tut_desc.pack(pady=30)
        
        btn_start = tk.Label(self.tutorial_frame, text="SUNTEM GATA! (START)", font=("Consolas", 40, "bold"), bg="green", fg="white", pady=20, padx=20, cursor="hand2")
        btn_start.bind("<Button-1>", lambda e: self._start_game())
        btn_start.pack(pady=50)
        
        btn_back = tk.Label(self.tutorial_frame, text="Înapoi la Meniu", font=("Consolas", 20), bg="#333", fg="white", pady=10, padx=20, cursor="hand2")
        btn_back.bind("<Button-1>", lambda e: self.return_to_setup())
        btn_back.pack()

    def _show_tutorial(self, game_mode):
        self.selected_game = game_mode
        self.setup_frame.pack_forget()
        
        if game_mode == "lava":
            self.lbl_tut_title.config(text="THE FLOOR IS LAVA", fg="#FF4500")
            self.lbl_tut_desc.config(text="SCOP: Supraviețuiți erupției vulcanice!\n\n1. Când începe runda, lava (ROȘU) se va extinde.\n2. Căutați și alergați pe INSULE (GRI).\n3. Dacă sunteți prinși în lavă, pierdeți o viață.\n\nEchipa împarte viețile. Supraviețuiți cât mai multe runde!")
        elif game_mode == "meteors":
            self.lbl_tut_title.config(text="METEOR SHOWER", fg="#8B0000")
            self.lbl_tut_desc.config(text="SCOP: Supraviețuiți ploii de meteoriți!\n\n1. Urmăriți zonele care clipesc ROȘU INTERMITENT.\n2. Evitați-le! Un meteorit va lovi curând acolo.\n3. Craterele lăsate în urmă (GRI) sunt sigure.\n\nAtenție, viteza crește progresiv de la o rundă la alta!")
        elif game_mode == "tnt":
            self.lbl_tut_title.config(text="TNT RUN", fg="#FFD700")
            self.lbl_tut_desc.config(text="SCOP: Fugi sau cazi!\n\n1. Podeaua este sigură (VERDE), dar se va surpa de îndată ce calci pe ea!\n2. Când o căsuță devine PORTOCALIE, înseamnă că o să cadă curând.\n3. Nu pica în prăpastie (ROȘU ÎNCHIS) sau pierzi o viață.\n4. Culege BĂNUȚII (GALBEN) pentru puncte bonus (+5)!\n\nNU STA PE LOC!")
            
        self.tutorial_frame.pack(fill="both", expand=True)

    def _build_game_frame(self):
        self.game_frame = tk.Frame(self.root, bg="black")
        self.lbl_game = tk.Label(self.game_frame, text="JOC", font=("Consolas", 40, "bold"), bg="black", fg="white")
        self.lbl_game.pack(pady=20)
        self.lbl_lives = tk.Label(self.game_frame, text="", font=("Consolas", 50), bg="black", fg="red")
        self.lbl_lives.pack(pady=10)
        self.lbl_instruction = tk.Label(self.game_frame, text="Pregătire...", font=("Consolas", 25), bg="black", fg="yellow")
        self.lbl_instruction.pack(pady=10)
        
        # BUTON DE ÎNTOARCERE LA MENIU DUPĂ GAME OVER
        self.btn_return = tk.Label(self.game_frame, text="ÎNAPOI LA MENIU", font=("Consolas", 30, "bold"), bg="#333", fg="white", pady=15, padx=30, cursor="hand2")
        self.btn_return.bind("<Button-1>", lambda e: self.return_to_setup())

        # (în interiorul funcției _build_game_frame)
        self.lbl_score = tk.Label(self.game_frame, text="SCOR: 0", font=("Consolas", 45, "bold"), bg="black", fg="#00FF00")
        self.lbl_score.pack(side="bottom", pady=50)

    def _start_game(self):
        self.tutorial_frame.pack_forget()
        self.game_frame.pack(fill="both", expand=True)
        
        # Ascundem butonul la începutul unui joc nou
        self.btn_return.pack_forget() 
        
        self.on_start_callback(self.selected_game, self.selected_players, self.selected_difficulty)

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
        self.root.after(0, lambda: self.lbl_score.config(text=f"SCOR FINAL: {score}", fg="yellow"))
        self.root.after(0, lambda: self.lbl_lives.config(text="💀💀💀"))
        
        # Afișăm butonul de întoarcere la meniu abia la Game Over
        self.root.after(0, lambda: self.btn_return.pack(pady=30))

    def return_to_setup(self):
        self.tutorial_frame.pack_forget()
        self.game_frame.pack_forget()
        self.setup_frame.pack(fill="both", expand=True)

    def run(self):
        self.root.mainloop()