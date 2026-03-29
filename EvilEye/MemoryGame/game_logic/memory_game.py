import random
import threading

class MemoryGame:
    def __init__(self, num_players=2):
        self.num_players = num_players
        self.max_steps = 10
        self.level = 1
        self.sequence = []      
        self.current_step = 0
        self.state = "IDLE"     
        self.active_walls = self._get_initial_walls(num_players)
        self.timer_thread = None
        self.stop_timer_event = threading.Event()

    def _get_initial_walls(self, players):
        if players <= 3: return [1]
        if players <= 5: return [1, 2]
        if players <= 7: return [1, 2, 3]
        return [1, 2, 3, 4]

    def add_next_step(self):
        wall = random.choice(self.active_walls)
        led = random.randint(1, 10)
        
        self.sequence.append((wall, led))
        self.current_step = 0
        return (wall, led)

    def check_press(self, wall, led):
        if self.state != "WAITING" or self.current_step >= len(self.sequence):
            return "IGNORE"

        target_wall, target_led = self.sequence[self.current_step]
        
        if wall == target_wall and led == target_led:
            self.current_step += 1
            if self.current_step >= len(self.sequence):
                if len(self.sequence) >= self.max_steps:
                    return "ULTIMATE_WIN"
                return "LEVEL_COMPLETE"
            return "STEP_CORRECT"
        else:
            self.state = "FAIL" 
            return "GAME_OVER"

    def reset(self):
        self.level = 1
        self.sequence = []
        self.current_step = 0
        self.state = "IDLE"