import threading
import time
import random
from song_search_engine import searchOnlineFiles, play_song
import state
from obstacole_structures import line, column, shuriken, arrow, bubble, diag1, diag2, diamond, chess, island, points

# constants
BOARD_WIDTH = 16
BOARD_HEIGHT = 32
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BABY_BLUE = (137, 207, 240)


class GameDesignMixin:
    # ===================== border =====================
    def draw_border(self, grid):
        for x in range(BOARD_WIDTH):
            grid[(x, 0)] = GREEN
            grid[(x, BOARD_HEIGHT - 1)] = GREEN
        for y in range(BOARD_HEIGHT):
            grid[(0, y)] = GREEN
            grid[(BOARD_WIDTH - 1, y)] = GREEN

    # ===================== search_engine methods =====================
    def start_music_search(self):
        query = self.music_search_var.get().strip()
        if not query: return
        
        self.lbl_music_status.config(text="🔍 Searching...", fg="#ffaa00")
        threading.Thread(target=self._music_worker, args=(query,), daemon=True).start()

    def _music_worker(self, query):
        try:
            results = searchOnlineFiles(query, limit=1)
            if results and 'url' in results[0]:
                url = results[0]['url']
                title = results[0]['title']
                
                self.root.after(0, lambda: self.start_intro(url, title, 5))
            else:
                self.root.after(0, lambda: self.lbl_music_status.config(text="❌ Not found", fg="#ff4444"))
        except Exception as e:
            self.root.after(0, lambda: self.lbl_music_status.config(text="Error in search", fg="red"))

    def stop_music(self):
        if state.current_player:
            state.current_player.terminate()
            state.current_player = None
            self.lbl_music_status.config(text="⏹ Stopped", fg="#888")

    # ===================== INTRO SEQUENCE =====================
    def start_intro(self, url, title, count):
        if not self.is_sending:
            self.toggle_sending()
            
        self.anim_var.set("Intro Sequence")
        self.animation_mode = "Intro Sequence"
        self.intro_words = ["HAVE", "FUN", ":)"]
        self.intro_word_index = 0
        self.intro_alpha = 0.0
        self.intro_fade_dir = 1
        
        self.lbl_music_status.config(text="✨ Get ready...", fg="#00ff00")
        self._intro_tick(url, title, count)

    def _intro_tick(self, url, title, count):
        if getattr(self, 'animation_mode', '') != "Intro Sequence":
            return
            
        self.intro_alpha += 0.05 * self.intro_fade_dir
        
        if self.intro_alpha >= 1.0:
            self.intro_alpha = 1.0
            self.intro_fade_dir = -1 
            self.root.after(600, lambda: self._intro_tick(url, title, count)) 
            return
            
        elif self.intro_alpha <= 0.0:
            self.intro_alpha = 0.0
            self.intro_fade_dir = 1 
            self.intro_word_index += 1
            
            if self.intro_word_index >= len(self.intro_words):
                self.start_game_countdown(url, title, count)
                return
            else:
                self.root.after(300, lambda: self._intro_tick(url, title, count)) 
                return

        self.root.after(50, lambda: self._intro_tick(url, title, count))


    # ===================== obstacle methods ============================
    def update_and_draw_obstacles(self, frame_grid):
        for obs in self.active_obstacles:
            if isinstance(obs, column):
                obs.x += obs.speed  
            
            elif isinstance(obs, (bubble, diag1, diag2)):
                obs.x += obs.speed  
                obs.y += obs.speed 
            else:
                obs.y += obs.speed  
            
            for dx, dy in obs.shape:
                px, py = int(obs.x + dx), int(obs.y + dy)
                if 0 <= px < BOARD_WIDTH and 0 <= py < BOARD_HEIGHT:
                    is_hidden_by_island = False
                    for isl in self.active_islands:
                        if isl.x <= px < isl.x + 3 and isl.y <= py < isl.y + 3:
                            is_hidden_by_island = True
                            break
                    if not is_hidden_by_island:
                        frame_grid[(px, py)] = obs.color
        
        self.active_obstacles = [o for o in self.active_obstacles if o.y < BOARD_HEIGHT and o.x < BOARD_WIDTH]
    
    def spawn_random_obstacle(self):
        obs_types = [line, shuriken, arrow, bubble, column, diag1, diag2, diamond, chess]
        chosen_type = random.choice(obs_types)
        id_unic = int(time.time() * 250) 
        
        if chosen_type == line:
            new_obs = chosen_type(id=id_unic, x=0, y=-1, speed=0.5, color=RED)
        elif chosen_type == column:
            new_obs = chosen_type(id=id_unic, x=-1, y=0, speed=0.5, color=RED)
        elif chosen_type in [bubble, diag1]:
            random_row = random.randint(0, BOARD_HEIGHT - 1)
            new_obs = chosen_type(id=id_unic, x=1, y=random_row, speed=0.5, color=RED)
        else:
            random_col = random.randint(1, 10)
            new_obs = chosen_type(id=id_unic, x=random_col, y=-5, speed=0.5, color=RED)
            
        self.active_obstacles.append(new_obs)

    # ===================== island methods ============================
    def manage_islands(self):
        if not self.is_sending or getattr(self, 'is_counting_down', False) or getattr(self, 'animation_mode', '') != "Play Music":
            self.root.after(1000, self.manage_islands)
            return

        if len(self.active_islands) >= 2:
            self.active_islands.pop(0)

        id_unic = int(time.time() * 1000)
        rx = random.randint(1, BOARD_WIDTH - 4)
        ry = random.randint(1, BOARD_HEIGHT - 4)
        
        new_isl = island(id=id_unic, x=rx, y=ry)
        self.active_islands.append(new_isl)

        self.root.after(10000, self.manage_islands)

    def draw_islands(self, frame_grid):
        for isl in self.active_islands:
            if not hasattr(isl, 'alpha'): isl.alpha = 0.0
            if isl.alpha < 1.0:
                isl.alpha += 0.05 

            faded_island_color = (
                int(isl.color[0] * isl.alpha),
                int(isl.color[1] * isl.alpha),
                int(isl.color[2] * isl.alpha)
            )

            for dx, dy in isl.shape:
                px, py = int(isl.x + dx), int(isl.y + dy)
                if 0 <= px < BOARD_WIDTH and 0 <= py < BOARD_HEIGHT:
                    frame_grid[(px, py)] = faded_island_color

    # ===================== points methods ===========================
    def spawn_point(self):
        if getattr(self, 'animation_mode', '') != "Play Music":
            return
            
        if hasattr(self, 'active_points') and len(self.active_points) >= getattr(self, 'max_points', 5):
            return  
            
        id_unic = int(time.time() * 1000)
        
        valid_position = False
        rx, ry = 0, 0
        attempts = 0
        
        while not valid_position and attempts < 20:
            rx = random.randint(1, BOARD_WIDTH - 2)
            ry = random.randint(1, BOARD_HEIGHT - 2)
            
            is_on_island = False
            for isl in self.active_islands:
                if isl.x <= rx < isl.x + 3 and isl.y <= ry < isl.y + 3:
                    is_on_island = True
                    break
            
            if not is_on_island:
                valid_position = True
            attempts += 1

        if valid_position:
            random_color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
            
            new_pt = points(id=id_unic, x=rx, y=ry, color=random_color)
            if not hasattr(self, 'active_points'): self.active_points = []
            self.active_points.append(new_pt)

    def draw_points(self, frame_grid):
        if hasattr(self, 'active_points'):
            for pt in self.active_points:
                px, py = int(pt.x), int(pt.y)
                if 0 <= px < BOARD_WIDTH and 0 <= py < BOARD_HEIGHT:
                    frame_grid[(px, py)] = pt.color

    # ===================== game methods ============================
    def start_game_countdown(self, url, title, count):
        if not self.is_sending:
            self.toggle_sending()
            
        self.anim_var.set("Play Music")
        self.animation_mode = "Play Music"
        
        self.current_countdown = count

        if count > 0:
            self.is_counting_down = True
            self.lbl_music_status.config(text=f"🚀 Jocul începe în {count}s...", fg="#ffaa00")
            self.root.after(1000, lambda: self.start_game_countdown(url, title, count - 1))
        else:
            self.is_counting_down = False
            self.active_obstacles = []
            self.lives = 5
            self.score = 0 
            
            if hasattr(self, 'dashboard') and getattr(self.dashboard, 'winfo_exists', lambda: False)():
                self.dashboard.reset_dashboard()
                
            self.next_spawn_in = random.randint(20, 40)
            self.lbl_music_status.config(text=f"🎵 Now playing: {title[:20]}", fg="#00ff00")
            play_song(url)

    def game_over(self):
        print("💀 GAME OVER!")
        self.stop_music() 
        
        play_song("https://youtu.be/LukyMYp2noo")
        
        self.active_obstacles.clear()
        self.active_points.clear()
        self.active_islands.clear()
        
        self.animation_mode = "Game Over Fade" 
        self.game_over_alpha = 0.0 
        
        self.lbl_music_status.config(text="💀 GAME OVER! Ai rămas fără vieți.", fg="#ff0000")
        
        if hasattr(self, 'dashboard') and getattr(self.dashboard, 'winfo_exists', lambda: False)():
            self.dashboard.show_game_over(getattr(self, 'score', 0))