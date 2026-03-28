import tkinter as tk

class ControlPanel:
    def __init__(self, parent, start_callback, stop_callback, resume_callback, end_callback):
        self.parent = parent
        self.parent.configure(bg="#0b0b10")
        
        # Callbacks
        self.external_start = start_callback
        self.external_stop = stop_callback
        self.external_resume = resume_callback
        self.external_end = end_callback

        # Culori Temă (Neon Palette)
        self.C_BG = "#0b0b10"
        self.C_ACCENT = "#00f2ff"  
        self.C_GREEN = "#00ff88"   
        self.C_RED = "#ff2a6d"     
        self.C_AMBER = "#ffab00"
        self.C_CARD = "#161625"    

        # Container Principal cu limitare de lățime vizuală
        self.main_container = tk.Frame(parent, bg=self.C_BG, padx=50)
        self.main_container.pack(fill="both", expand=True)

        # --- HEADER ---
        self.header_label = tk.Label(self.main_container, text="NEON MEMORY", 
                                     font=("Segoe UI", 28, "bold"), 
                                     bg=self.C_BG, fg=self.C_ACCENT)
        self.header_label.pack(pady=(50, 30))
        
        # --- CONFIG FRAME (Selecție Jucători) ---
        self.config_frame = tk.Frame(self.main_container, bg=self.C_BG)
        self.config_frame.pack(fill="x")

        player_container = tk.Frame(self.config_frame, bg=self.C_CARD, padx=20, pady=25, 
                                     highlightbackground="#222", highlightthickness=1)
        player_container.pack(fill="x")

        tk.Label(player_container, text="OPERATORS ON SITE", font=("Segoe UI", 9, "bold"), 
                 bg=self.C_CARD, fg="#8b8b9b").pack(pady=(0, 15))
        
        self.players_var = tk.IntVar(value=2)
        self.player_btns = {}
        grid_frame = tk.Frame(player_container, bg=self.C_CARD)
        grid_frame.pack()

        for i in range(2, 11):
            btn = tk.Button(grid_frame, text=str(i), width=4, font=("Segoe UI", 10, "bold"),
                            bg="#222235", fg="white", relief="flat", cursor="hand2",
                            command=lambda v=i: self._select_players(v))
            row, col = (i-2)//5, (i-2)%5
            btn.grid(row=row, column=col, padx=4, pady=4)
            self.player_btns[i] = btn
        
        self._select_players(2)

        self.btn_start = tk.Button(self.config_frame, text="INITIATE MISSION", 
                                   bg=self.C_GREEN, fg="#0b0b10",
                                   font=("Segoe UI", 12, "bold"), relief="flat", height=2,
                                   cursor="hand2", command=self._internal_start)
        self.btn_start.pack(fill="x", pady=40)

        # --- CONTROLS FRAME (Aici am reparat aspectul) ---
        self.controls_frame = tk.Frame(self.main_container, bg=self.C_BG)
        # Nu îi dăm pack încă, va fi gestionat de _internal_start

        # Container intern pentru a grupa butoanele strâns, nu lăbărțat
        self.button_group = tk.Frame(self.controls_frame, bg=self.C_BG)
        self.button_group.pack(expand=True) # Centrare verticală

        self.btn_stop = tk.Button(self.button_group, text="PAUSE SYSTEM", 
                                  bg=self.C_AMBER, fg="#0b0b10",
                                  font=("Segoe UI", 11, "bold"), relief="flat", 
                                  width=25, height=2, command=self._internal_stop)
        
        self.btn_resume = tk.Button(self.button_group, text="RESUME MISSION", 
                                    bg=self.C_GREEN, fg="#0b0b10",
                                    font=("Segoe UI", 11, "bold"), relief="flat", 
                                    width=25, height=2, command=self._internal_resume)

        self.btn_end = tk.Button(self.button_group, text="ABORT GAME", 
                                 bg="#1a1a1a", fg=self.C_RED,
                                 font=("Segoe UI", 10, "bold"), relief="flat", 
                                 width=25, height=1, command=end_callback)
        
        # Spacer între butoane în interiorul grupului
        self.btn_end.pack(pady=(15, 0)) # End Game va fi sub butonul de Stop/Resume

        # --- STATUS BAR ---
        self.lbl_status = tk.Label(self.main_container, text="● SYSTEM READY", 
                                   font=("Consolas", 9), bg=self.C_BG, fg=self.C_ACCENT)
        self.lbl_status.pack(side="bottom", pady=30)

    def _internal_start(self):
        self.config_frame.pack_forget()
        self.controls_frame.pack(fill="both", expand=True) # Ocupă spațiul rămas
        self._show_stop_button()
        self.external_start()

    def _show_stop_button(self):
        self.btn_resume.pack_forget()
        self.btn_stop.pack(before=self.btn_end, pady=(0, 10))

    def _show_resume_button(self):
        self.btn_stop.pack_forget()
        self.btn_resume.pack(before=self.btn_end, pady=(0, 10))

    def _internal_stop(self):
        self._show_resume_button()
        self.update_status("System Paused", self.C_AMBER)
        self.external_stop()

    def _internal_resume(self):
        self._show_stop_button()
        self.update_status("Mission Active", self.C_GREEN)
        self.external_resume()

    def show_setup(self):
        """Resetare UI la starea de configurare"""
        self.controls_frame.pack_forget()
        self.config_frame.pack(fill="x")
        self.update_status("Ready", self.C_ACCENT)

    def _select_players(self, value):
        self.players_var.set(value)
        for num, btn in self.player_btns.items():
            if num == value:
                btn.config(bg=self.C_ACCENT, fg=self.C_BG)
            else:
                btn.config(bg="#222235", fg="white")

    def update_status(self, message, color=None):
        self.lbl_status.config(text=f"● {message.upper()}", fg=color or self.C_ACCENT)