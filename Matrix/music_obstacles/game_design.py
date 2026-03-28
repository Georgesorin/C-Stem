import threading
import time
import random
from song_search_engine import searchOnlineFiles, play_song
import state
from obstacole_structures import line, column, shuriken, arrow, bubble

# constants
BOARD_WIDTH = 16
BOARD_HEIGHT = 32
GREEN = (0, 255, 0)
RED = (255, 0, 0)


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

                self.root.after(0, lambda: self.start_game_countdown(url, title, 10))
            else:
                self.root.after(0, lambda: self.lbl_music_status.config(text="❌ Not found", fg="#ff4444"))
        except Exception as e:
            self.root.after(0, lambda: self.lbl_music_status.config(text="Error in search", fg="red"))

    def stop_music(self):
        if state.current_player:
            state.current_player.terminate()
            state.current_player = None
            self.lbl_music_status.config(text="⏹ Stopped", fg="#888")

    # ===================== obstacle methods ============================
    def update_and_draw_obstacles(self, frame_grid):
        for obs in self.active_obstacles:
            # move logic
            if isinstance(obs, column):
                obs.x += obs.speed 
            else:
                obs.y += obs.speed 
            
            # draw stuff
            for dx, dy in obs.shape:
                px, py = int(obs.x + dx), int(obs.y + dy)
                if 0 <= px < BOARD_WIDTH and 0 <= py < BOARD_HEIGHT:
                    frame_grid[(px, py)] = obs.color
        
        # clean stuff
        self.active_obstacles = [o for o in self.active_obstacles if o.y < BOARD_HEIGHT and o.x < BOARD_WIDTH]
    
    def spawn_random_obstacle(self):
        obs_types = [line, shuriken, arrow, bubble, column]
        chosen_type = random.choice(obs_types)
        new_id = int(time.time())
        
        if chosen_type == line:
            new_obs = chosen_type(id=new_id, x=0, y=-1, speed=0.5, color=RED)
        elif chosen_type == column:
            new_obs = chosen_type(id=new_id, x=-1, y=0, speed=0.5, color=RED)
        else:
            random_x = random.randint(1, 13)
            new_obs = chosen_type(id=new_id, x=random_x, y=-5, speed=0.5, color=RED)
            
        self.active_obstacles.append(new_obs)

    # ===================== game methods ============================
    def start_game_countdown(self, url, title, count):
        if not self.is_sending:
            self.toggle_sending()
            
        self.anim_var.set("Play Music")
        self.animation_mode = "Play Music"

        if count > 0:
            self.is_counting_down = True
            self.lbl_music_status.config(text=f"🚀 Game starts in {count}s...", fg="#ffaa00")
            self.root.after(1000, lambda: self.start_game_countdown(url, title, count - 1))
        else:
            self.is_counting_down = False
            self.active_obstacles = []
            self.lbl_music_status.config(text=f"🎵 Now playing: {title[:20]}", fg="#00ff00")
            play_song(url)