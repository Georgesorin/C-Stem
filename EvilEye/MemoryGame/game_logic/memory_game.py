import random

class MemoryGame:
    def __init__(self, num_players=2):
        self.num_players = num_players
        self.level = 1
        self.sequence = []      # Lista de tupluri (wall_id, led_id)
        self.current_step = 0
        self.state = "IDLE"     
        
        # Stabilim pereții de start conform regulii primite
        self.base_walls = self._calculate_initial_walls(num_players)
        # Pereții care sunt efectiv folosiți în runda curentă
        self.active_walls = list(self.base_walls)

    def _calculate_initial_walls(self, players):
        """
        Regula transmisă:
        2-3 jucători: 1 perete
        4-5 jucători: 2 pereți
        6-7 jucători: 3 pereți
        8-10 jucători: 4 pereți
        """
        if players <= 3:
            return [1]
        elif players <= 5:
            return [1, 2]
        elif players <= 7:
            return [1, 2, 3]
        else:
            return [1, 2, 3, 4]

    def add_next_step(self):
        """
        Adaugă un pas nou. 
        OPȚIONAL: Putem adăuga un perete nou la fiecare 5 nivele dacă mai sunt disponibili.
        """
        # Verificăm dacă vrem să extindem numărul de pereți pe măsură ce nivelul crește
        # (Exemplu: la nivelul 5, dacă aveam doar 1 perete, mai adăugăm unul)
        if self.level % 5 == 0:
            current_max = max(self.active_walls)
            if current_max < 4:
                new_wall = current_max + 1
                if new_wall not in self.active_walls:
                    self.active_walls.append(new_wall)

        # Alegem un perete din lista de pereți activi pentru acest nivel
        wall = random.choice(self.active_walls)
        # Alegem un LED (1-10 pentru butoane, 0 e ochiul central)
        led = random.randint(1, 10)
        
        self.sequence.append((wall, led))
        self.current_step = 0
        return self.sequence

    def check_press(self, wall, led):
        if not self.sequence or self.state != "WAITING":
            return "IGNORE"

        target_wall, target_led = self.sequence[self.current_step]
        
        if wall == target_wall and led == target_led:
            self.current_step += 1
            if self.current_step >= len(self.sequence):
                return "LEVEL_COMPLETE"
            return "STEP_CORRECT"
        else:
            return "GAME_OVER"

    def reset(self):
        self.level = 1
        self.sequence = []
        self.current_step = 0
        self.active_walls = list(self.base_walls) # Resetăm la config inițială
        self.state = "IDLE"