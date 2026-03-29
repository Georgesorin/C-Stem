import tkinter as tk

# --- CULORI UI ---
BG_BLACK = "#000000"
CARD_BG = "#121212"
ACCENT_GREEN = "#00c853"
ACCENT_RED = "#ff1744"
ACCENT_ORANGE = "#ff6d00"
TEXT_COLOR = "#ffffff"

COLORS = {
    "Orange":  (255, 165, 0, "#ffa500"),
    "Blue":    (0, 0, 255, "#0000ff"),
    "Red":     (255, 0, 0, "#ff0000"),
    "Magenta": (255, 0, 255, "#ff00ff"),
    "White":   (255, 255, 255, "#ffffff")
}

class OutsideDisplay:
    def __init__(self, parent, start_callback, stop_callback, pause_callback):
        self.parent = parent
        # Funcții primite din main.py
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.pause_callback = pause_callback
        
        # State Selecție
        self.p1_color_name = "Red"
        self.p2_color_name = "Blue"
        self.difficulty = "Normal"
        self.rounds_var = tk.IntVar(value=3)
        self.container = None
        
        self.setup_ui()

    def get_selected_setup(self):
        """Colectează toate opțiunile alese în interfață și le trimite către joc."""
        p1_rgb = COLORS[self.p1_color_name][0:3]
        p2_rgb = COLORS[self.p2_color_name][0:3]
        
        return {
            "p1_color": p1_rgb,
            "p2_color": p2_rgb,
            "difficulty": self.difficulty,
            "rounds": self.rounds_var.get()
        }

    def create_card(self, parent, title):
        frame = tk.Frame(parent, bg=CARD_BG, padx=15, pady=15, highlightbackground="#333", highlightthickness=1)
        frame.pack(fill="x", padx=20, pady=10)
        tk.Label(frame, text=title, bg=CARD_BG, fg="#888", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        return frame

    def setup_ui(self):
        if self.container:
            self.container.destroy()
            
        self.container = tk.Frame(self.parent, bg=BG_BLACK)
        self.container.pack(fill="both", expand=True)

        tk.Label(self.container, text="PONG MATRIX\nCONTROL PANEL", bg=BG_BLACK, fg=TEXT_COLOR, 
                 font=("Segoe UI", 18, "bold"), pady=20).pack()

        p1_f = self.create_card(self.container, "PLAYER 1 COLOR")
        self.p1_btns = self.create_color_buttons(p1_f, "p1")

        p2_f = self.create_card(self.container, "PLAYER 2 COLOR")
        self.p2_btns = self.create_color_buttons(p2_f, "p2")

        diff_f = self.create_card(self.container, "DIFFICULTY LEVEL")
        self.diff_btns = {}
        d_box = tk.Frame(diff_f, bg=CARD_BG)
        d_box.pack(fill="x")
        for d in ["Easy", "Normal", "Hard"]:
            btn = tk.Button(d_box, text=d, command=lambda v=d: self.select_diff(v),
                           bg="#222", fg="white", relief="flat", width=10)
            btn.pack(side="left", padx=5, expand=True, fill="x")
            self.diff_btns[d] = btn
        self.select_diff("Normal")

        rounds_frame = self.create_card(self.container, "TOTAL ROUNDS")
        tk.Spinbox(rounds_frame, from_=1, to=5, textvariable=self.rounds_var, 
                   bg=BG_BLACK, fg="white", font=("Segoe UI", 14, "bold"), width=10, justify="center").pack()

        self.btn_start = tk.Button(self.container, text="START GAME", bg=ACCENT_GREEN, fg="black", 
                                  font=("Segoe UI", 12, "bold"), relief="flat", pady=12, command=self.start_callback)
        self.btn_start.pack(fill="x", padx=20, pady=20)

    def create_color_buttons(self, parent, p_tag):
        btns = {}
        box = tk.Frame(parent, bg=CARD_BG)
        box.pack(fill="x")
        for name, info in COLORS.items():
            btn = tk.Button(box, bg=info[3], width=3, relief="flat",
                           command=lambda n=name, t=p_tag: self.select_color(t, n))
            btn.pack(side="left", padx=8, expand=True)
            btns[name] = btn
        return btns

    def select_color(self, p, name):
        if p == "p1": self.p1_color_name = name
        else: self.p2_color_name = name
        self.update_visuals()

    def update_visuals(self):
        for name, btn in self.p1_btns.items():
            btn.config(highlightthickness=3 if name == self.p1_color_name else 0, highlightbackground="white")
        for name, btn in self.p2_btns.items():
            btn.config(highlightthickness=3 if name == self.p2_color_name else 0, highlightbackground="white")

    def select_diff(self, val):
        self.difficulty = val
        for name, btn in self.diff_btns.items():
            btn.config(bg=ACCENT_GREEN if name == val else "#222", fg="black" if name == val else "white")

    def show_game_controls(self):
        """Afișează doar butoanele de control în timpul jocului."""
        self.container.destroy()
        self.container = tk.Frame(self.parent, bg=BG_BLACK)
        self.container.pack(fill="both", expand=True)

        tk.Label(self.container, text="GAME IN PROGRESS", 
                 font=("Segoe UI", 14, "bold"), bg=BG_BLACK, fg="#444").pack(pady=60)

        tk.Button(self.container, text="STOP / PAUSE", bg=ACCENT_ORANGE, 
                  font=("Segoe UI", 12, "bold"),
                  command=self.pause_callback, pady=10).pack(fill="x", padx=40, pady=10)

        tk.Button(self.container, text="END GAME", bg=ACCENT_RED, fg="white", 
                  font=("Segoe UI", 12, "bold"),
                  command=self.stop_callback, pady=10).pack(fill="x", padx=40, pady=10)