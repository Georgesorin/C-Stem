import tkinter as tk

BG_BLACK = "#000000"
CARD_BG = "#121212"
ACCENT_GREEN = "#00c853"
TEXT_COLOR = "#ffffff"

def rgb_to_hex(rgb):
    """Transformă (255, 165, 0) în '#ffa500'"""
    return '#%02x%02x%02x' % rgb

class InsideDisplay:
    def __init__(self, container, p1_color_hex, p2_color_hex, difficulty, total_rounds):
        self.container = container
        
        # Datele meciului
        self.p1_color = rgb_to_hex(p1_color_hex) if isinstance(p1_color_hex, tuple) else p1_color_hex
        self.p2_color = rgb_to_hex(p2_color_hex) if isinstance(p2_color_hex, tuple) else p2_color_hex
        self.difficulty = difficulty
        self.total_rounds = total_rounds
        
        self.setup_ui()

    def setup_ui(self):
        # 0. MAIN FRAME (Peretele principal)
        self.main_frame = tk.Frame(self.container, bg=BG_BLACK)
        self.main_frame.pack(fill="both", expand=True)

        # 1. HEADER: Difficulty & Round Info
        header_frame = tk.Frame(self.main_frame, bg=BG_BLACK, pady=20)
        header_frame.pack(fill="x")

        # Difficulty Badge
        diff_label = tk.Label(header_frame, text=f"MODE: {self.difficulty.upper()}", 
                             bg="#222", fg=ACCENT_GREEN, font=("Segoe UI", 10, "bold"),
                             padx=15, pady=5)
        diff_label.pack(side="left", padx=20)

        # Round & Sets Tracker (Aici am adăugat logica de Seturi)
        info_frame = tk.Frame(header_frame, bg=BG_BLACK)
        info_frame.pack(side="right", padx=20)

        self.lbl_round_info = tk.Label(info_frame, text=f"ROUND 1 / {self.total_rounds}", 
                                       bg=BG_BLACK, fg="yellow", font=("Segoe UI", 14, "bold"))
        self.lbl_round_info.pack()

        self.lbl_sets = tk.Label(info_frame, text="SETS: P1 [0] - [0] P2", 
                                 bg=BG_BLACK, fg="white", font=("Segoe UI", 12))
        self.lbl_sets.pack()

        # 2. MAIN SCOREBOARD
        score_container = tk.Frame(self.main_frame, bg=BG_BLACK, pady=50)
        score_container.pack(fill="x")

        # Player 1 Side
        p1_side = tk.Frame(score_container, bg=BG_BLACK)
        p1_side.pack(side="left", expand=True)
        
        tk.Label(p1_side, text="PLAYER 1", bg=BG_BLACK, fg="#555", font=("Segoe UI", 10, "bold")).pack()
        self.lbl_p1_score = tk.Label(p1_side, text="0", bg=BG_BLACK, fg=self.p1_color, font=("Consolas", 80, "bold"))
        self.lbl_p1_score.pack()

        # VS Divider
        tk.Label(score_container, text="VS", bg=BG_BLACK, fg="#222", font=("Segoe UI", 24, "italic bold")).pack(side="left")

        # Player 2 Side
        p2_side = tk.Frame(score_container, bg=BG_BLACK)
        p2_side.pack(side="left", expand=True)

        tk.Label(p2_side, text="PLAYER 2", bg=BG_BLACK, fg="#555", font=("Segoe UI", 10, "bold")).pack()
        self.lbl_p2_score = tk.Label(p2_side, text="0", bg=BG_BLACK, fg=self.p2_color, font=("Consolas", 80, "bold"))
        self.lbl_p2_score.pack()

        # 3. FOOTER: Visual Polish
        footer = tk.Frame(self.main_frame, bg=CARD_BG, height=2)
        footer.pack(fill="x", padx=40, pady=20)
        
        tk.Label(self.main_frame, text="LIVE STADIUM FEED", bg=BG_BLACK, fg="#333", font=("Segoe UI", 8, "bold")).pack()

        # 4. OVERLAY FRAME (Pentru pauze, 3-2-1 și mesaje de rundă)
        self.overlay_frame = tk.Frame(self.container, bg=BG_BLACK)
        self.lbl_pause_overlay = tk.Label(self.overlay_frame, text="", bg="#ff6d00", fg="black", font=("Segoe UI", 40, "bold"), pady=20)
        self.lbl_pause_overlay.pack(fill="x", pady=150)

    # --- METODELE CURATE DE ACTUALIZARE ---

    def update_score(self, s1, s2):
        if hasattr(self, 'lbl_p1_score') and self.lbl_p1_score.winfo_exists():
            self.lbl_p1_score.config(text=str(s1))
        if hasattr(self, 'lbl_p2_score') and self.lbl_p2_score.winfo_exists():
            self.lbl_p2_score.config(text=str(s2))

    def update_round_display(self, current, total, sets_p1, sets_p2):
        if hasattr(self, 'lbl_round_info') and self.lbl_round_info.winfo_exists():
            self.lbl_round_info.config(text=f"ROUND {current} / {total}")
        if hasattr(self, 'lbl_sets') and self.lbl_sets.winfo_exists():
            self.lbl_sets.config(text=f"SETS: P1 [{sets_p1}] - [{sets_p2}] P2")

    def set_pause_status(self, is_paused, custom_text=None):
        if is_paused or custom_text:
            self.main_frame.pack_forget()
            self.overlay_frame.pack(fill="both", expand=True)
            display_text = custom_text if custom_text else "GAME STOPPED"
            self.lbl_pause_overlay.config(text=display_text)
        else:
            self.overlay_frame.pack_forget()
            self.main_frame.pack(fill="both", expand=True)