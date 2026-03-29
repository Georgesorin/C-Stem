import tkinter as tk
from tkinter import ttk
import threading
import socket

class ControlPanel:
    def __init__(self, parent, network_service, interfaces_list, start_callback, stop_callback, resume_callback, end_callback):
        self.parent = parent
        self.network = network_service
        self._ifaces_cache = interfaces_list

        self.C_BG = "#0b0b10"
        self.C_ACCENT = "#00f2ff"  
        self.C_GREEN = "#00ff88"   
        self.C_RED = "#ff2a6d"     
        self.C_AMBER = "#ffab00"
        self.C_CARD = "#161625"  

        self.external_start = start_callback
        self.external_stop = stop_callback
        self.external_resume = resume_callback
        self.external_end = end_callback  

        # 1. CREĂM MAI ÎNTÂI CONTAINERUL (AICI ERA PROBLEMA)
        self.main_container = tk.Frame(parent, bg=self.C_BG, padx=50)
        self.main_container.pack(fill="both", expand=True)

        tk.Label(self.main_container, text="NEON MEMORY", font=("Segoe UI", 32, "bold"), 
                 bg=self.C_BG, fg=self.C_ACCENT).pack(pady=(60, 40))

        # 2. ACUM PUTEM PUNE NETWORK SETUP ÎN self.main_container
        labels = [f"{n} ({ip})" for n, ip, _ in self._ifaces_cache]
        
        net_frame = tk.LabelFrame(self.main_container, text=" NETWORK SETUP ", bg="#161625", fg="white")
        net_frame.pack(fill="x", pady=10)

        self.iface_var = tk.StringVar()
        self.iface_combo = ttk.Combobox(net_frame, textvariable=self.iface_var, state="readonly", values=labels)
        self.iface_combo.pack(fill="x", padx=5, pady=5)
        if labels: self.iface_combo.current(0)

        self.btn_connect = tk.Button(net_frame, text="🔍 DISCOVER & CONNECT", command=self._manual_discovery, 
                                     bg="#222235", fg="#00f2ff", relief="flat")
        self.btn_connect.pack(fill="x", padx=5, pady=5)
        
        # Adăugăm și label-ul de status pentru rețea ca să nu dea eroare mai târziu
        self.lbl_net_status = tk.Label(net_frame, text="Status: Ready", bg="#161625", fg="gray")
        self.lbl_net_status.pack()

        # ... restul codului (player_card, setup_area, etc.) ...

        # --- SETUP AREA (PLAYERS) ---
        self.config_frame = tk.Frame(self.main_container, bg=self.C_BG)
        self.config_frame.pack(fill="x")

        player_card = tk.Frame(self.config_frame, bg=self.C_CARD, padx=20, pady=25, 
                                highlightbackground="#222", highlightthickness=1)
        player_card.pack(fill="x")

        tk.Label(player_card, text="OPERATORS ON SITE", font=("Segoe UI", 10, "bold"), 
                 bg=self.C_CARD, fg="#8b8b9b").pack(pady=(0, 15))
        
        self.players_var = tk.IntVar(value=2)
        self.player_btns = {}
        grid = tk.Frame(player_card, bg=self.C_CARD)
        grid.pack()

        for i in range(2, 11):
            btn = tk.Button(grid, text=str(i), width=4, font=("Segoe UI", 10, "bold"),
                            bg="#222235", fg="white", relief="flat", cursor="hand2",
                            command=lambda v=i: self._select_players(v))
            btn.grid(row=(i-2)//5, column=(i-2)%5, padx=4, pady=4)
            self.player_btns[i] = btn
        
        self._select_players(2)

        self.btn_start = tk.Button(self.config_frame, text="START MISSION", bg=self.C_GREEN, fg="#0b0b10",
                                   font=("Segoe UI", 13, "bold"), relief="flat", height=2,
                                   command=self._internal_start)
        self.btn_start.pack(fill="x", pady=40)

        # --- ACTIVE CONTROLS (PAUSE/RESUME) ---
        self.controls_frame = tk.Frame(self.main_container, bg=self.C_BG)

        self.btn_stop = tk.Button(self.controls_frame, text="PAUSE SYSTEM", bg=self.C_AMBER, 
                                  fg="#0b0b10", font=("Segoe UI", 12, "bold"), relief="flat",
                                  width=25, height=2, command=self._internal_stop)
        
        self.btn_resume = tk.Button(self.controls_frame, text="RESUME MISSION", bg=self.C_GREEN, 
                                    fg="#0b0b10", font=("Segoe UI", 12, "bold"), relief="flat",
                                    width=25, height=2, command=self._internal_resume)

        self.btn_end = tk.Button(self.controls_frame, text="ABORT GAME", bg="#1a1a1a", 
                                 fg=self.C_RED, font=("Segoe UI", 10, "bold"), relief="flat",
                                 width=25, height=1, command=end_callback)
        self.btn_end.pack(side="bottom", pady=(20, 0))

        # --- OVERLAY & STATUS ---
        self.overlay_frame = tk.Frame(parent, bg=self.C_BG)
        self.lbl_result = tk.Label(self.overlay_frame, text="", font=("Segoe UI", 30, "bold"), 
                                   bg=self.C_BG, justify="center")
        self.lbl_result.pack(expand=True)

        self.lbl_status = tk.Label(self.main_container, text="● READY", font=("Consolas", 10), 
                                   bg=self.C_BG, fg=self.C_ACCENT)
        self.lbl_status.pack(side="bottom", pady=40)

    # --- LOGIC METHODS ---

    def _manual_discovery(self):
        idx = self.iface_combo.current()
        if idx < 0 or not self._ifaces_cache: return

        name, ip, bcast = self._ifaces_cache[idx]
        self.lbl_net_status.config(text=f"Scanning on {name}...", fg="orange")
        self.parent.update_idletasks()

        def scan():
            # Această funcție folosește funcția globală build_discovery_packet
            found_ip = self._run_discovery_silent(ip, bcast) 
            
            if found_ip:
                self.parent.after(0, lambda: self._on_connection_success(found_ip))
            else:
                self.parent.after(0, lambda: self._on_connection_fail())

        threading.Thread(target=scan, daemon=True).start()

    def _on_connection_success(self, ip):
        if self.network:
            self.network.set_device(ip)
        self.lbl_net_status.config(text=f"✅ Connected to: {ip}", fg=self.C_GREEN)

    def _on_connection_fail(self):
        if self.network:
            self.network.set_device("127.0.0.1")
        self.lbl_net_status.config(text="⚠️ No device. Using Simulator", fg="yellow")

    def _run_discovery_silent(self, local_ip, bcast_ip):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(1.5)
        
        # Asigură-te că build_discovery_packet() este definită în main.py
        try:
            pkt, r1, r2 = build_discovery_packet()
            sock.sendto(pkt, (bcast_ip, 4626))
            data, addr = sock.recvfrom(1024)
            if len(data) >= 30 and data[0] == 0x68:
                return addr[0]
        except:
            pass
        finally:
            sock.close()
        return None

    def _internal_start(self):
        self.config_frame.pack_forget()
        self.controls_frame.pack(fill="both", expand=True)
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
        self.update_status("Paused", self.C_AMBER)
        self.external_stop()

    def _internal_resume(self):
        self._show_stop_button()
        self.update_status("Active", self.C_GREEN)
        self.external_resume()

    def show_full_screen_message(self, message, color):
        self.lbl_result.config(text=message, fg=color)
        self.overlay_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.parent.update()

    def hide_full_screen_message(self):
        self.overlay_frame.place_forget()

    def show_setup(self):
        self.controls_frame.pack_forget()
        self.config_frame.pack(fill="x")
        self.update_status("Ready", self.C_ACCENT)

    def _select_players(self, value):
        self.players_var.set(value)
        for num, btn in self.player_btns.items():
            btn.config(bg=self.C_ACCENT if num == value else "#222235", 
                       fg=self.C_BG if num == value else "white")

    def update_status(self, message, color=None):
        self.lbl_status.config(text=f"● {message.upper()}", fg=color or self.C_ACCENT)