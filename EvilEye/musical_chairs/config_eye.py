# config_eye.py
import math
import random

WIDTH_WALL = 10 # 10 Butoane pe perete
HEIGHT_WALL = 1 # 1 Rând de butoane
NUM_WALLS = 4   # 4 Pereți

TARGET_IP = "127.0.0.1"
PORT_SEND = 5002 # Portul de trimitere (WIKI)
PORT_RECV = 5003 # Portul de primire senzori (WIKI)

CMD_PREFIX = 0x77 # Prefixul comenzii (WIKI)
TYPE_EYE = 0
TYPE_BUTTON = 1

COLORS = {
    "COVERED": (100, 100, 100), # Culoarea initială (Alb-Gri)
    "MATCHED": (0, 0, 0),       # Culoarea când sunt ghicite (oprit/negru)
    "WARNING": (255, 0, 0),     # Culoarea de pâlpâire avertizare ochi
    "EYE_CLOSED": (0, 20, 0),   # Culoarea ochiului închis (verde închis)
    "EYE_OPEN": (255, 100, 0),  # Culoarea ochiului deschis (portocaliu)
}

# Definim 20 de culori distincte pentru cele 20 de perechi (40 butoane)
PAIR_COLORS = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255),
    (255, 128, 0), (128, 0, 255), (255, 153, 204), (102, 255, 102), (0, 102, 204), (153, 76, 0),
    (102, 102, 102), (204, 255, 255), (255, 204, 204), (102, 153, 0), (0, 204, 102), (102, 0, 102),
    (255, 255, 153), (51, 51, 51)
]

# Configurație Timers
# Cât stau butoanele "întoarse" dacă nu s-au potrivit (secunde)
FLIP_BACK_TIME = 2.0 

# Cât timp Ochiul stă DESCHIS (trebuie să stai nemișcat)
EYE_ACTIVE_DURATION = 4.0 

# Cât timp pâlpâie pătrățelele ÎNAINTE să se deschidă Ochiul
EYE_WARNING_DURATION = 3.0 

# Intervalul de timp (secunde) între activările ochilor (aleatoriu)
EYE_COOLDOWN_RANGE = (10.0, 20.0)

# Adaugă la finalul config_eye.py
MC_TARGET_COLORS = [
    (0, 0, 255),   # Albastru
    (255, 255, 0), # Galben
    (0, 255, 255), # Cyan
    (255, 0, 255), # Magenta
    (255, 165, 0)  # Portocaliu
]