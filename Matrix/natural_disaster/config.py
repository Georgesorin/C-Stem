# config.py

WIDTH, HEIGHT = 16, 32 
TARGET_IP = "127.0.0.1"
PORT_SEND = 5001 
PORT_RECV = 5000 

COLORS = {
    "GRASS": (0, 80, 0), 
    "ISLAND": (120, 120, 120), 
    "WATER": (0, 0, 255),
    "LAVA": (255, 30, 0),          # Roșu-Portocaliu aprins pentru lavă
    "LAVA_SPLASH": (255, 200, 0),  # Galben-Portocaliu strălucitor pentru când calci în ea
    "METEOR_WARN": (255, 0, 0), 
    "METEOR_IMPACT": (255, 100, 0),
    "CRATER": (40, 40, 40), 
    "WHITE": (255, 255, 255), 
    "SMOKE": (150, 150, 150)
}

DIGITS = {
    '3': [(0,0), (1,0), (2,0), (2,1), (1,2), (2,2), (2,3), (2,4), (1,4), (0,4)],
    '2': [(0,0), (1,0), (2,0), (2,1), (0,2), (1,2), (2,2), (0,3), (0,4), (1,4), (2,4)],
    '1': [(1,0), (1,1), (1,2), (1,3), (1,4)]
}

ALL_CORNERS = [(0, 0), (WIDTH-1, 0), (0, HEIGHT-1), (WIDTH-1, HEIGHT-1)]