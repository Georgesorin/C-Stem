# ui_natural.py
import tkinter as tk
import screeninfo

class DashboardUI:
    def __init__(self, on_start_callback):
        self.on_start_callback = on_start_callback
        
        # ========================================================
        # 1. ECRANUL OPERATORULUI (Monitorul 1)
        # ========================================================
        self.root = tk.Tk()
        self.root.title("LEDHACK - Matrix Operator")
        self.root.geometry("1024x768")
        self.root.configure(bg="black")
        
        # Operatorul poate fi și el Fullscreen dacă vrei
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", lambda event: self.root.attributes("-fullscreen", False))
        
        # ========================================================
        # 2. ECRANUL JUCĂTORILOR (Se mută automat pe Monitorul 2)
        # ========================================================
        self.room_window = tk.Toplevel(self.root)
        self.room_window.title("Matrix Dashboard - Sală")
        self.room_window.configure(bg="black")
        
        # Dezactivăm butonul X ca jucătorii să nu îl poată închide
        self.room_window.protocol("WM_DELETE_WINDOW", lambda: None)
        self._move_to_second_monitor()
        
        # Variabile pentru configurare
        self.selected_players = 2
        self.selected_difficulty = "Normal"
        self.selected_game = None
        
        # --- Construim ecranele pentru Monitorul 1 (Operator) ---
        self._build_setup_frame()
        self._build_tutorial_frame()
        self._build_operator_running_frame() 
        
        # --- Construim ecranele pentru Monitorul 2 (Jucători) ---
        self._build_standby_frame() 
        self._build_game_frame()    
        
        # Afișăm ecranele inițiale
        self.setup_frame.pack(fill="both", expand=True)
        self.standby_frame.pack(fill="both", expand=True)

    def _move_to_second_monitor(self):
        """Detectează monitoarele și mută fereastra de joc pe TV-ul din Sală"""
        try:
            monitors = screeninfo.get_monitors()
            if len(monitors) > 1:
                # Avem un al doilea ecran conectat (TV-ul din sală)
                m = monitors[0] # <--- Schimbă cifra în 0 dacă se inversează ecranele!
                self.room_window.geometry(f"{m.width}x{m.height}+{m.x}+{m.y}")
                self.room_window.overrideredirect(True) 
                self.room_window.attributes('-fullscreen', True) 
            else:
                # Dacă testezi acasă cu un singur ecran, îl lasă ca fereastră normală mică
                self.room_window.geometry("800x600") 
        except Exception as e:
            print(f"[UI] Eroare la detectarea monitoarelor: {e}")

    # ========================================================
    # INTERFEȚE MONITOR 1 (OPERATOR)
    # ========================================================
    def _build_setup_frame(self):
        self.setup_frame = tk.Frame(self.root, bg="black")
        tk.Label(self.setup_frame, text="MATRIX ARCADE (OPERATOR)", font=("Consolas", 55, "bold"), fg="white", bg="black").pack(pady=(30, 10))
        
        # --- 1. Configurare Jucători ---
        tk.Label(self.setup_frame, text="1. NUMĂR JUCĂTORI:", font=("Consolas", 20), fg="yellow", bg="black").pack(pady=(10, 0))
        players_frame = tk.Frame(self.setup_frame, bg="black")
        players_frame.pack()
        self.btn_players = {}
        for i in range(2, 8):
            lbl = tk.Label(players_frame, text=str(i), font=("Consolas", 25, "bold"), bg="#333", fg="white", width=3, cursor="hand2")
            lbl.bind("<Button-1>", lambda e, p=i: self._select_players(p))
            lbl.pack(side="left", padx=5, pady=5)
            self.btn_players[i] = lbl
        self._select_players(2) 
        
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
        self._select_diff("Normal") 
        
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
        
        btn_tnt = tk.Label(games_frame, text="TNT RUN", font=("Consolas", 30, "bold"), bg="#FFD700", fg="black", pady=10, cursor="hand2")
        btn_tnt.bind("<Button-1>", lambda e: self._show_tutorial("tnt"))
        btn_tnt.pack(pady=10, fill="x")

        # --- 4. BUTON EXIT ---
        btn_exit = tk.Label(self.setup_frame, text="IEȘIRE JOC", font=("Consolas", 20, "bold"), bg="#aa0000", fg="white", pady=5, padx=20, cursor="hand2")
        btn_exit.bind("<Button-1>", lambda e: self.root.destroy())
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
        
        btn_start = tk.Label(self.tutorial_frame, text="PORNEȘTE JOCUL ÎN SALĂ", font=("Consolas", 40, "bold"), bg="green", fg="white", pady=20, padx=20, cursor="hand2")
        btn_start.bind("<Button-1>", lambda e: self._start_game())
        btn_start.pack(pady=50)
        
        btn_back = tk.Label(self.tutorial_frame, text="Înapoi la Meniu", font=("Consolas", 20), bg="#333", fg="white", pady=10, padx=20, cursor="hand2")
        btn_back.bind("<Button-1>", lambda e: self.return_to_setup())
        btn_back.pack()

    def _build_operator_running_frame(self):
        """Ecranul pe care îl vede operatorul cât timp jucătorii sunt pe podea"""
        self.op_running_frame = tk.Frame(self.root, bg="black")
        tk.Label(self.op_running_frame, text="🎮 JOCUL RULEAZĂ ÎN SALĂ", font=("Consolas", 40, "bold"), fg="#0f0", bg="black").pack(pady=(100, 20))
        
        self.lbl_op_status = tk.Label(self.op_running_frame, text="Jucătorii sunt activi pe podea...", font=("Consolas", 25), fg="yellow", bg="black")
        self.lbl_op_status.pack(pady=30)
        
        # Butonul de RESET apare aici doar la Game Over
        self.btn_return = tk.Label(self.op_running_frame, text="RESET: ÎNAPOI LA MENIU", font=("Consolas", 30, "bold"), bg="#333", fg="white", pady=15, padx=30, cursor="hand2")
        self.btn_return.bind("<Button-1>", lambda e: self.return_to_setup())

    # ========================================================
    # INTERFEȚE MONITOR 2 (SALĂ / JUCĂTORI)
    # ========================================================
    def _build_standby_frame(self):
        """Apare pe ecranul din sală înainte să se dea Start"""
        self.standby_frame = tk.Frame(self.room_window, bg="black")
        tk.Label(self.standby_frame, text="MATRIX ARCADE", font=("Consolas", 80, "bold"), fg="white", bg="black").pack(expand=True)

    def _build_game_frame(self):
        """Dashboard-ul real care afișează scorul în timpul jocului"""
        self.game_frame = tk.Frame(self.room_window, bg="black")
        self.lbl_game = tk.Label(self.game_frame, text="JOC", font=("Consolas", 60, "bold"), bg="black", fg="white")
        self.lbl_game.pack(pady=30)
        
        self.lbl_lives = tk.Label(self.game_frame, text="", font=("Consolas", 70), bg="black", fg="red")
        self.lbl_lives.pack(pady=20)
        
        self.lbl_instruction = tk.Label(self.game_frame, text="Pregătire...", font=("Consolas", 40), bg="black", fg="yellow")
        self.lbl_instruction.pack(pady=20)
        
        self.lbl_score = tk.Label(self.game_frame, text="SCOR: 0", font=("Consolas", 70, "bold"), bg="black", fg="#00FF00")
        self.lbl_score.pack(side="bottom", pady=80)

    # ========================================================
    # LOGICA DE AFIȘARE ȘI ACTUALIZARE
    # ========================================================
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

    def _start_game(self):
        # Setăm ecranul 1 (Operator)
        self.tutorial_frame.pack_forget()
        self.lbl_op_status.config(text="Jucătorii sunt activi pe podea...", fg="yellow")
        self.btn_return.pack_forget() # Ascundem butonul de Reset până mor
        self.op_running_frame.pack(fill="both", expand=True)
        
        # Setăm ecranul 2 (Jucători)
        self.standby_frame.pack_forget()
        self.game_frame.pack(fill="both", expand=True)
        
        # Pornim efectiv logica Matrix
        self.on_start_callback(self.selected_game, self.selected_players, self.selected_difficulty)

    def update_dashboard(self, status, instr, color="white"):
        self.root.after(0, lambda: self.lbl_game.config(text=status, fg=color))
        self.root.after(0, lambda: self.lbl_instruction.config(text=instr))

    def update_score(self, score):
        self.root.after(0, lambda: self.lbl_score.config(text=f"SCOR: {score}"))

    def update_lives(self, lives):
        self.root.after(0, lambda: self.lbl_lives.config(text="❤️" * max(0, lives)))

    def show_game_over(self, score):
        # Actualizăm Ecranul 2 (Jucători)
        self.root.after(0, lambda: self.lbl_game.config(text="GAME OVER", fg="red"))
        self.root.after(0, lambda: self.lbl_instruction.config(text="Echipa a fost eliminată!", fg="white"))
        self.root.after(0, lambda: self.lbl_score.config(text=f"SCOR FINAL: {score}", fg="yellow"))
        self.root.after(0, lambda: self.lbl_lives.config(text="💀💀💀"))
        
        # Actualizăm Ecranul 1 (Operator) -> Îi dăm butonul de Reset
        self.root.after(0, lambda: self.lbl_op_status.config(text="ECHIPA A FOST ELIMINATĂ!", fg="red"))
        self.root.after(0, lambda: self.btn_return.pack(pady=30))

    def return_to_setup(self):
        # Resetăm Ecranul 1 (Operator)
        self.op_running_frame.pack_forget()
        self.setup_frame.pack(fill="both", expand=True)
        
        # Resetăm Ecranul 2 (Jucători - înapoi la logo)
        self.game_frame.pack_forget()
        self.standby_frame.pack(fill="both", expand=True)

    def run(self):
        self.root.mainloop()