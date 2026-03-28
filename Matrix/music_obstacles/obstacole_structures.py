import sys 
from dataclasses import dataclass, field
from typing import List, Tuple
BABY_BLUE = (137, 207, 240)

@dataclass
class obstacle:
    id: int
    x: int
    y: int
    speed: float
    # default red color
    color: Tuple[int, int, int] = (255, 0, 0) 
    # list with (x.y) for lit LEDs
    shape: List[Tuple[int, int]] = field(default_factory=list)

# line structure
@dataclass
class line(obstacle):
    def __post_init__(self):
        self.shape = [(i, 0) for i in range(16)]


# line structure
@dataclass
class column(obstacle):
    def __post_init__(self):
        self.shape = [(0, i) for i in range(32)]

# shuriken structure
@dataclass
class shuriken(obstacle):
    def __post_init__(self):
        self.shape = [(1, 0), (0, 1), (1, 1), (2, 1), (1, 2)]

# bubble structure
@dataclass
class bubble(obstacle):
    def __post_init__(self):
        self.shape = [
            (1, 0), (2, 0),
            (0, 1), (3, 1), (0, 2), (3, 2),
            (1, 3), (2, 3)
        ]

@dataclass
class arrow(obstacle):
    def __post_init__(self):
        self.shape = [
            (2, 0), (2, 1),           
            (0, 2), (2, 2), (4, 2),   
            (1, 3), (3, 3),           
            (2, 4)                    
        ]

@dataclass
class diag1(obstacle):
    def __post_init__(self):
        self.shape = [(4, 0), (3, 1), (2, 2), (1, 3), (0, 4)]

@dataclass
class diag2(obstacle):
    def __post_init__(self):
        self.shape = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]

@dataclass
class chess(obstacle):
    def __post_init__(self):
        self.shape = [
            (0, 0), (2, 0),
            (1, 1),
            (0, 2), (2, 2)
        ]

@dataclass
class diamond(obstacle):
    def __post_init__(self):
        self.shape = [
            (2, 0),
            (1, 1), (3, 1),
            (0, 2), (4, 2),
            (1, 3), (3, 3),
            (2, 4)
        ]

@dataclass
class island:
    id: int
    x: int
    y: int
    color: Tuple[int, int, int] = BABY_BLUE
    shape: List[Tuple[int, int]] = field(default_factory=lambda: [
        (dx, dy) for dy in range(3) for dx in range(3)
    ])

@dataclass 
class points:
    id: int
    x: int
    y: int
    color: Tuple[int, int, int]
    shape: List[Tuple[int, int]] = field(default_factory=lambda: [(0, 0)])