# audio_manager_eye.py
import pygame
import os

class EyeAudioManager:
    def __init__(self):
        # Inițializăm motorul audio al computerului
        pygame.mixer.init()
        self.sounds = {}
        
        # Folderul unde pui fișierele .wav sau .mp3
        self.audio_dir = "audio_eye"
        
        # Încărcăm sunetele (verificăm dacă fișierul există înainte să dăm crash)
        self._load_sound("flip", "flip.mp3")           # Când se apasă un buton
        self._load_sound("match", "match.mp3")         # Când se ghicește o pereche
        self._load_sound("wrong", "faahh.mp3")         # Când culorile sunt diferite
        self._load_sound("warning", "warning.mp3")     # Pâlpâirea de avertizare ochi
        self._load_sound("eye_open", "eye_open.wav")   # Când ochii sunt ACTIVI (RĂU!)
        self._load_sound("damage", "damage.wav")       # Când ești prins mișcându-te
        self._load_sound("win", "win.mp3")             # Victorie
        self._load_sound("game_over", "game_over.mp3") # Înfrângere

    def _load_sound(self, name, filename):
        path = os.path.join(self.audio_dir, filename)
        if os.path.exists(path):
            sound = pygame.mixer.Sound(path)
            sound.set_volume(0.8) # Volum efecte (0.0 - 1.0)
            self.sounds[name] = sound
        else:
            print(f"[AUDIO WARNING] Nu s-a găsit fișierul: {path}")

    def play(self, name):
        """Redă instant un efect sonor"""
        if name in self.sounds:
            self.sounds[name].play()

    def stop(self, name):
        """Oprește un sunet care rulează (ex: ceasul/warning)"""
        if name in self.sounds:
            self.sounds[name].stop()