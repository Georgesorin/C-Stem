# config_eye.py
import math
import random

WIDTH_WALL = 10 # 10 Butoane pe perete
HEIGHT_WALL = 1 # 1 Rând de butoane
NUM_WALLS = 4   # 4 Pereți

# MODIFICAT PENTRU HARDWARE REAL / CONFIGURAȚIA TEAM_COLLECT
TARGET_IP = "255.255.255.255" # Broadcast pentru a găsi matricea în rețea
PORT_SEND = 4626              # Portul de trimitere (conform Team_collect)
PORT_RECV = 7800              # Portul de primire senzori (conform Team_collect)

CMD_PREFIX = 0x77 
TYPE_EYE = 0
TYPE_BUTTON = 1

COLORS = {
    "COVERED": (100, 100, 100), 
    "MATCHED": (0, 0, 0),       
    "WARNING": (255, 0, 0),     
    "EYE_CLOSED": (0, 20, 0),   
    "EYE_OPEN": (255, 100, 0),  
}

# Culorile rămân aceleași
PAIR_COLORS = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255),
    (255, 128, 0), (128, 0, 255), (255, 153, 204), (102, 255, 102), (0, 102, 204), (153, 76, 0),
    (102, 102, 102), (204, 255, 255), (255, 204, 204), (102, 153, 0), (0, 204, 102), (102, 0, 102),
    (255, 255, 153), (51, 51, 51)
]

FLIP_BACK_TIME = 2.0 
EYE_ACTIVE_DURATION = 4.0 
EYE_WARNING_DURATION = 3.0 
EYE_COOLDOWN_RANGE = (10.0, 20.0)

MC_TARGET_COLORS = [
    (0, 0, 255),   
    (255, 255, 0), 
    (0, 255, 255), 
    (255, 0, 255), 
    (255, 165, 0)  
]