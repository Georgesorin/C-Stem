# ==============================================================================
# --- Logica Operator ---
# ==============================================================================
class EvilEyeOperator:
    def __init__(self):
        self.hw = EvilEyeHardware()
        self.running = True
        self.score, self.lives = 0, 5
        self.game_phase = "IDLE"
        self.hit_cooldown = 0
        self.music_file = None
        self.is_paused = False
        
        # Peretele pe care este ochiul activ la STOP
        self.active_eye_wall = None 

        self.root = tk.Tk()
        self.root.title("STAFF CONTROL - EVIL EYE")
        self.root.geometry("450x650")
        
        self.view = tk.Toplevel(self.root)
        self.view.title("SCOREBOARD")
        self.view.geometry("800x600")
        self.view.configure(bg="black")

        self.setup_staff_ui()
        self.setup_view_ui()
        threading.Thread(target=self.game_loop, daemon=True).start()

    def setup_staff_ui(self):
        tk.Label(self.root, text="👁️ EVIL EYE CONTROL", font=("Arial", 16, "bold")).pack(pady=20)
        
        conn_frame = tk.LabelFrame(self.root, text=" 1. Link Connection ", padx=10, pady=10)
        conn_frame.pack(padx=20, fill="x")
        
        tk.Label(conn_frame, text="Device IP:").pack(side=tk.LEFT)
        self.ip_entry = tk.Entry(conn_frame, width=15)
        self.ip_entry.insert(0, "169.254.182.11")
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Button(conn_frame, text="🔗 CONNECT", command=self._do_connect, bg="#34495e", fg="white").pack(side=tk.LEFT)
        
        self.lbl_status = tk.Label(self.root, text="Status: Deconectat", fg="gray")
        self.lbl_status.pack(pady=5)

        ttk.Separator(self.root, orient="horizontal").pack(fill="x", pady=10)

        tk.Button(self.root, text="📁 Încarcă Muzica", command=self._sel_music).pack()
        self.lbl_song = tk.Label(self.root, text="Niciun fișier", fg="blue"); self.lbl_song.pack(pady=5)

        self.btn_play = tk.Button(self.root, text="▶️ START", bg="green", command=self._action_play, state="disabled", height=2, width=25)
        self.btn_play.pack(pady=5)
        self.btn_stop = tk.Button(self.root, text="⏸️ STOP", bg="red", command=self._action_pause, state="disabled", height=2, width=25)
        self.btn_stop.pack(pady=5)

    def setup_view_ui(self):
        tk.Label(self.view, text="EVIL EYE", font=("Impact", 80), bg="black", fg="red").pack(pady=20)
        self.lbl_scr = tk.Label(self.view, text="SCOR: 0", font=("Arial", 60), bg="black", fg="white"); self.lbl_scr.pack()
        self.lbl_lvs = tk.Label(self.view, text="VIEȚI: 5", font=("Arial", 60), bg="black", fg="#ff4444"); self.lbl_lvs.pack()
        self.lbl_msg = tk.Label(self.view, text="STANDBY", font=("Arial", 40), bg="black", fg="gray"); self.lbl_msg.pack(pady=40)

    def _do_connect(self):
        ip = self.ip_entry.get()
        self.hw.connect(ip)
        self.lbl_status.config(text=f"✅ CONECTAT LA {ip}", fg="green")
        self.btn_play.config(state="normal")
        self.btn_stop.config(state="normal")

    def _sel_music(self):
        f = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav")])
        if f: self.music_file = f; self.lbl_song.config(text=os.path.basename(f))

    def _spawn_points(self, count):
        """Generează 'count' puncte pe butoanele 1-10, distribuite random pe pereți."""
        for _ in range(count):
            # Alegem un perete random din dictionar
            w = random.choice(list(self.hw.walls.values()))
            # Căutăm LED-uri libere (1-10) pe acest perete
            led_ids = [i for i in range(1, 11) if i not in w.active_points]
            if led_ids:
                w.active_points.add(random.choice(led_ids))

    def _action_play(self):
        self.game_phase = "SAFE"
        self.active_eye_wall = None
        
        if HAS_PYGAME and self.music_file:
            if self.is_paused: pygame.mixer.music.unpause() 
            else:
                pygame.mixer.music.load(self.music_file)
                pygame.mixer.music.play(-1)
            self.is_paused = False
        
        # Curățăm toți ochii și punctele vechi
        for w in self.hw.walls.values():
            w.eye_open = False
            w.active_points.clear()
            
        # Spawnăm 5 puncte simultan în cameră (poți modifica numărul)
        self._spawn_points(5)

    def _action_pause(self):
        self.game_phase = "WATCHING"
        if HAS_PYGAME:
            pygame.mixer.music.pause()
            self.is_paused = True
            
        # Curățăm punctele de colectare
        for w in self.hw.walls.values():
            w.active_points.clear()
            w.eye_open = False
            
        # Alegem random un singur perete (10, 11, 12, 13) pe care se deschide Ochiul
        self.active_eye_wall = random.choice([10, 11, 12, 13])
        self.hw.walls[self.active_eye_wall].eye_open = True

    def game_loop(self):
        while self.running:
            now = time.time()
            if self.game_phase == "SAFE":
                # Verificăm independent fiecare punct de pe fiecare perete
                for w in self.hw.walls.values():
                    hit_points = []
                    for p_id in w.active_points:
                        if w.buttons[p_id]: # Dacă un buton aprins e apăsat
                            hit_points.append(p_id)
                            w.buttons[p_id] = False # Consumăm apăsarea
                            self.score += 100
                            
                    # Pentru fiecare punct lovit, îl stingem și generăm altul NOU
                    for p_id in hit_points:
                        w.active_points.remove(p_id)
                        self._spawn_points(1)

            elif self.game_phase == "WATCHING":
                # Verificăm dacă se detectează mișcare DOAR pe peretele cu Ochiul deschis
                if self.active_eye_wall:
                    w = self.hw.walls[self.active_eye_wall]
                    # Dacă senzorul (0) sau orice buton a fost mișcat
                    if (w.buttons[0] or any(w.buttons[1:])) and now > self.hit_cooldown:
                        self.lives -= 1
                        self.hit_cooldown = now + 2.0

            self._update_hardware()
            self.root.after(0, self._update_ui)
            time.sleep(0.05)

    def _update_hardware(self):
        if not self.hw.running: return
        self.hw._seq = (self.hw._seq + 1) & 0xFFFF
        frame = bytearray(132)
        
        for l_idx in range(11):
            for ch_idx, w_id in enumerate([10, 11, 12, 13]):
                color = COLORS["OFF"]
                wall = self.hw.walls[w_id]
                
                if l_idx == 0 and wall.eye_open:
                    color = COLORS["EYE_RED"]
                elif l_idx in wall.active_points:
                    color = COLORS["TARGET_CYAN"]
                
                # Protocol v11 Intercalat (G, R, B)
                frame[l_idx * 12 + ch_idx] = color[1]
                frame[l_idx * 12 + 4 + ch_idx] = color[0]
                frame[l_idx * 12 + 8 + ch_idx] = color[2]

        try:
            ep = (self.hw.target_ip, PORT_SEND)
            self.hw.sock.sendto(build_packet(0x3344, self.hw._seq), ep)
            self.hw.sock.sendto(build_packet(0x8877, self.hw._seq, bytearray([0, 11]*4)), ep)
            self.hw.sock.sendto(build_packet(0x8877, 0, frame), ep)
            self.hw.sock.sendto(build_packet(0x5566, self.hw._seq), ep)
        except: pass

    def _update_ui(self):
        self.lbl_scr.config(text=f"SCOR: {self.score}")
        self.lbl_lvs.config(text=f"VIEȚI: {max(0, self.lives)}")
        if self.game_phase == "SAFE": 
            self.lbl_msg.config(text="CULEGE PUNCTELE!", fg="cyan")
        elif self.game_phase == "WATCHING": 
            self.lbl_msg.config(text=f"OCHI ACTIV: WALL {self.active_eye_wall}!", fg="red")

if __name__ == "__main__":
    EvilEyeOperator().root.mainloop()