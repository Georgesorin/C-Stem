# audio_manager.py
import pygame
import os

class AudioManager:
    def __init__(self):
        # Inițializăm motorul audio
        pygame.mixer.init()
        
        # Dicționar pentru a stoca toate efectele sonore (SFX)
        self.sounds = {}
        
        # Încărcăm sunetele (dacă fișierul nu există, trece peste fără a da crash)
        self._load_sound("splash", "audio/lava.mp3")
        self._load_sound("countdown", "audio/clock.mp3")
        self._load_sound("meteor_boom", "audio/meteor.mp3")
        self._load_sound("fire_out", "audio/fire.mp3")
        self._load_sound("damage", "audio/damage_hit.wav")
        self._load_sound("game_over", "audio/game_over.mp3")
        
        # Pregătim muzica de fundal (BGM)
        self.bgm_path = "audio/intense_background.wav"
        if os.path.exists(self.bgm_path):
            pygame.mixer.music.load(self.bgm_path)
            pygame.mixer.music.set_volume(0.3) # Dăm muzica mai încet ca să se audă efectele

    def _load_sound(self, name, path):
        """Încarcă un sunet doar dacă fișierul există fizic în folder"""
        if os.path.exists(path):
            sound = pygame.mixer.Sound(path)
            sound.set_volume(0.8) # Volumul pentru efecte sonore
            self.sounds[name] = sound
        else:
            print(f"[AUDIO WARNING] Nu s-a găsit fișierul: {path}")

    def play(self, name):
        """Redă instant un efect sonor dacă el a fost încărcat"""
        if name in self.sounds:
            self.sounds[name].play()

	    
    def stop(self, name):
        """Oprește forțat un singur efect sonor specific (ex: ceasul)"""
        if name in self.sounds:
            self.sounds[name].stop()

    def stop_all_sfx(self):
        """Târâie "siguranța" la toate sunetele (perfect pentru Game Over)"""
        pygame.mixer.stop()

    def play_bgm(self):
        """Pornește muzica de fundal în buclă infinită (-1)"""
        if os.path.exists(self.bgm_path):
            pygame.mixer.music.play(-1)

    def stop_bgm(self):
        """Oprește muzica de fundal"""
        pygame.mixer.music.stop()