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
MC_TARGET_COLORS = [(0, 0, 255), (255, 255, 0), (0, 255, 255)] # Fallback