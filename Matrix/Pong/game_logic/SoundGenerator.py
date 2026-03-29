import wave
import math
import struct
import random
import os

SFX_DIR = "_sfx"

def save_wav(filename, data, sample_rate=44100):
    if not os.path.exists(SFX_DIR):
        os.makedirs(SFX_DIR)
        
    path = os.path.join(SFX_DIR, filename)
    with wave.open(path, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(1)
        f.setframerate(sample_rate)
        f.writeframes(data)
    print(f"Generated {path}")

def generate_tone(freq, duration, vol=0.5, type='sine', slide=0):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    data = bytearray()
    
    for i in range(n_samples):
        t = i / sample_rate
        cur_freq = freq + slide * t
        
        if type == 'sine':
            val = math.sin(2 * math.pi * cur_freq * t)
        elif type == 'square':
            val = 1.0 if math.sin(2 * math.pi * cur_freq * t) > 0 else -1.0
        elif type == 'saw':
            val = 2.0 * (t * cur_freq - math.floor(0.5 + t * cur_freq))
        elif type == 'noise':
            val = random.uniform(-1, 1)
            
        scaled = int((val * vol + 1.0) * 127.5)
        scaled = max(0, min(255, scaled))
        data.append(scaled)
        
    return data

def mix(data1, data2):
    length = min(len(data1), len(data2))
    mixed = bytearray()
    for i in range(length):
        val1 = data1[i] - 128
        val2 = data2[i] - 128
        m = val1 + val2
        m = max(-128, min(127, m))
        mixed.append(m + 128)
    return mixed

def generate_all():
    press_ok = generate_tone(880, 0.05, vol=0.3, type='sine') 
    save_wav("press_ok.wav", press_ok)

    fail = generate_tone(400, 0.6, vol=0.4, type='saw', slide=-300)
    save_wav("fail.wav", fail)

    hint = generate_tone(1200, 0.03, vol=0.2, type='sine')
    save_wav("hint.wav", hint)

    note1 = generate_tone(523, 0.1, type='sine')
    note2 = generate_tone(659, 0.1, type='sine')
    note3 = generate_tone(783, 0.3, type='sine', slide=200)
    win = note1 + note2 + note3
    save_wav("victory.wav", win)

if __name__ == "__main__":
    generate_all()
