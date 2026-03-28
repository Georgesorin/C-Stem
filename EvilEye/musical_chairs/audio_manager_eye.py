# audio_manager_eye.py
import os

class EyeAudioManager:
    def __init__(self):
        self.enabled = False
        try:
            import pygame
            import pygame.mixer  # Aici dădea crash de fapt!
            pygame.mixer.init()
            self.enabled = True
        except Exception as e: # Prindem ABSOLUT orice eroare legată de lipsa modulelor
            print(f"[AUDIO ERROR] Efectele sonore dezactivate (lipsă modul pygame.mixer): {e}")
            self.enabled = False
            
        self.sounds = {}
        self.audio_dir = "audio_eye"
        
        # Încărcăm sunetele doar dacă mixerul a fost încărcat cu succes
        if self.enabled:
            self._load_sound("flip", "flip.mp3")
            self._load_sound("match", "match.mp3")
            self._load_sound("wrong", "faahh.mp3")
            self._load_sound("warning", "warning.mp3")
            self._load_sound("eye_open", "eye_open.wav")
            self._load_sound("damage", "damage.wav")
            self._load_sound("win", "win.mp3")
            self._load_sound("game_over", "game_over.mp3")

    def _load_sound(self, name, filename):
        if not self.enabled: return 
        path = os.path.join(self.audio_dir, filename)
        if os.path.exists(path):
            import pygame
            sound = pygame.mixer.Sound(path)
            sound.set_volume(0.8)
            self.sounds[name] = sound

    def play(self, name):
        """Redă un sunet doar dacă mixerul este activ"""
        if self.enabled and name in self.sounds:
            self.sounds[name].play()