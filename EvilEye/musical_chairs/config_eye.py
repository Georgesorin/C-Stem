# config_eye.py
import math
import random

WIDTH_WALL = 10 
HEIGHT_WALL = 1 
NUM_WALLS = 4   

# CONFIGURAȚIA DIN JSON-UL TĂU
TARGET_IP = "255.255.255.255" 
PORT_SEND = 4626              # udp_port din imagine
PORT_RECV = 7800              # receiver_port din imagine

# Culorile pentru Matching Pairs
PAIR_COLORS = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255),
    (255, 128, 0), (128, 0, 255), (255, 153, 204), (102, 255, 102)
]

FLIP_BACK_TIME = 1.5 
MC_TARGET_COLORS = [(0, 0, 255), (255, 255, 0), (0, 255, 255)] # Fallback# config_eye.py
import math
import random

WIDTH_WALL = 10 
HEIGHT_WALL = 1 
NUM_WALLS = 4   

# MODIFICAT PENTRU HARDWARE REAL (conform notițelor tale)
TARGET_IP = "255.255.255.255" # Trimite către toate dispozitivele din rețea
PORT_SEND = 4626              # Portul de trimitere (Light commands)
PORT_RECV = 7800              # Portul de primire (Senzori)

CMD_PREFIX = 0x77 
TYPE_EYE = 0
TYPE_BUTTON = 1

COLORS = {
    "COVERED": (40, 40, 40),    # O culoare gri închis pentru butoanele neapăsate
    "MATCHED": (0, 0, 0),       
    "WARNING": (255, 0, 0),     
    "EYE_CLOSED": (0, 20, 0),   
    "EYE_OPEN": (255, 0, 0),  
}

PAIR_COLORS = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255),
    (255, 128, 0), (128, 0, 255), (255, 153, 204), (102, 255, 102), (0, 102, 204), (153, 76, 0),
    (102, 102, 102), (204, 255, 255), (255, 204, 204), (102, 153, 0), (0, 204, 102), (102, 0, 102),
    (255, 255, 153), (51, 51, 51)
]

FLIP_BACK_TIME = 1.0 
EYE_ACTIVE_DURATION = 4.0 
EYE_WARNING_DURATION = 3.0 
EYE_COOLDOWN_RANGE = (10.0, 20.0)