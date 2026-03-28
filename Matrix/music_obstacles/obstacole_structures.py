import sys 
from dataclasses import dataclass, field
from typing import List, Tuple

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

# arrow structure
@dataclass
class arrow(obstacle):
    def __post_init__(self):
        self.shape = [(1, 0), (0, 1), (1, 1), (2, 1), (1, 2), (1, 3)]

# bubble structure
@dataclass
class bubble(obstacle):
    def __post_init__(self):
        self.shape = [
            (1, 0), (2, 0),
            (0, 1), (3, 1), (0, 2), (3, 2),
            (1, 3), (2, 3)
        ]