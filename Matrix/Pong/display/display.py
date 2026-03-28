import tkinter as tk
from tkinter import ttk

# UI Colors
BG_BLACK = "#000000"
CARD_BG = "#121212"
ACCENT_GREEN = "#00c853"
ACCENT_RED = "#ff1744"
ACCENT_ORANGE = "#ff6d00"
TEXT_COLOR = "#ffffff"

# Game Colors
COLORS = {
    "Orange": (255, 165, 0, "#ffa500"),
    "Blue": (0, 0, 255, "#0000ff"),
    "Red": (255, 0, 0, "#ff0000"),
    "Magenta": (255, 0, 255, "#ff00ff"),
    "White": (255, 255, 255, "#ffffff")
}

class MatrixGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pong LED Matrix - Pro Controller")
        self.root.geometry("500x700")
        self.root.configure(bg=BG_BLACK)
        
        # Selection State
        self.p1_color = "Red"
        self.p2_color = "Blue"
        self.difficulty = "Normal"
        
        self.setup_ui()

    def create_card(self, parent, title):
        frame = tk.Frame(parent, bg=CARD_BG, padx=15, pady=15, highlightbackground="#333333", highlightthickness=1)
        frame.pack(fill="x", padx=20, pady=10)
        label = tk.Label(frame, text=title, bg=CARD_BG, fg="#888888", font=("Segoe UI", 10, "bold"))
        label.pack(anchor="w", pady=(0, 10))
        return frame

    def setup_ui(self):
        # --- HEADER ---
        header = tk.Label(self.root, text="PONG MATRIX \nOPTION PANEL", bg=BG_BLACK, fg=TEXT_COLOR, font=("Segoe UI", 18, "bold"), pady=20)
        header.pack()

        # --- PLAYER 1 SECTION ---
        p1_frame = self.create_card(self.root, "PLAYER 1 COLOR")
        self.p1_btns = self.create_color_buttons(p1_frame, "p1")

        # --- PLAYER 2 SECTION ---
        p2_frame = self.create_card(self.root, "PLAYER 2 COLOR")
        self.p2_btns = self.create_color_buttons(p2_frame, "p2")

        # --- DIFFICULTY SECTION ---
        diff_frame = self.create_card(self.root, "DIFFICULTY LEVEL")
        self.diff_btns = {}
        btn_container = tk.Frame(diff_frame, bg=CARD_BG)
        btn_container.pack(fill="x")
        
        for d in ["Easy", "Normal", "Hard"]:
            btn = tk.Button(btn_container, text=d, command=lambda val=d: self.select_diff(val),
                           bg="#222222", fg="white", relief="flat", font=("Segoe UI", 9),
                           padx=10, pady=5, width=10, activebackground="#444444")
            btn.pack(side="left", padx=5, expand=True, fill="x")
            self.diff_btns[d] = btn
        self.select_diff("Normal")

        # --- ROUNDS SECTION ---
        rounds_frame = self.create_card(self.root, "TOTAL ROUNDS (MAX 5)")
        self.rounds_var = tk.IntVar(value=3)
        # Limit set to max 5
        spin = tk.Spinbox(rounds_frame, from_=1, to=5, textvariable=self.rounds_var, 
                         bg=BG_BLACK, fg="white", buttonbackground="#333333", 
                         relief="flat", font=("Segoe UI", 14, "bold"), width=10, justify="center")
        spin.pack()

        # --- CONTROL BUTTONS ---
        final_ctrl = tk.Frame(self.root, bg=BG_BLACK, pady=30)
        final_ctrl.pack(fill="x", padx=20)

        self.btn_start = tk.Button(final_ctrl, text="START GAME", bg=ACCENT_GREEN, fg="black", 
                                  font=("Segoe UI", 12, "bold"), relief="flat", pady=12, command=self.on_start)
        self.btn_start.pack(fill="x", pady=5)

        sub_btns = tk.Frame(final_ctrl, bg=BG_BLACK)
        sub_btns.pack(fill="x", pady=5)

        tk.Button(sub_btns, text="RESTART", bg=ACCENT_ORANGE, fg="black", font=("Segoe UI", 10, "bold"),
                  relief="flat", width=15, command=self.on_restart).pack(side="left", expand=True, fill="x", padx=(0,5))
        
        tk.Button(sub_btns, text="STOP", bg=ACCENT_RED, fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", width=15, command=self.on_stop).pack(side="left", expand=True, fill="x", padx=(5,0))

    def create_color_buttons(self, parent, player_tag):
        btns = {}
        container = tk.Frame(parent, bg=CARD_BG)
        container.pack(fill="x")
        for name, info in COLORS.items():
            btn = tk.Button(container, bg=info[3], width=3, height=1, relief="flat",
                           command=lambda n=name, p=player_tag: self.select_color(p, n))
            btn.pack(side="left", padx=8, pady=5, expand=True)
            btns[name] = btn
        return btns

    def select_color(self, player, color_name):
        if player == "p1":
            self.p1_color = color_name
            for name, btn in self.p1_btns.items():
                btn.config(highlightthickness=3 if name == color_name else 0, highlightbackground="white")
        else:
            self.p2_color = color_name
            for name, btn in self.p2_btns.items():
                btn.config(highlightthickness=3 if name == color_name else 0, highlightbackground="white")

    def select_diff(self, val):
        self.difficulty = val
        for name, btn in self.diff_btns.items():
            if name == val:
                btn.config(bg=ACCENT_GREEN, fg="black")
            else:
                btn.config(bg="#222222", fg="white")

    def on_start(self):
        print(f"GAME STARTED: P1={self.p1_color}, P2={self.p2_color}, Diff={self.difficulty}, Rounds={self.rounds_var.get()}")

    def on_restart(self): print("Restarting mission...")
    def on_stop(self): print("Mission aborted.")

if __name__ == "__main__":
    root = tk.Tk()
    app = MatrixGUI(root) # Corrected class reference
    root.mainloop()