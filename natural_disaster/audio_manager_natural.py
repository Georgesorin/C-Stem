# audio_manager_natural.py
import os

class AudioManager:
    """
    Gestionează redarea efectelor sonore (SFX) și a muzicii de fundal (BGM).
    Include protecție (fallback) împotriva crash-urilor în cazul în care 
    placa audio sau modulele lipsesc de pe sistemul gazdă.
    """

    def __init__(self, base_dir="audio_natural"):
        self.enabled = False
        self.sounds = {} # dictionar pentru sunete
        self.base_dir = base_dir
        self.bgm_path = os.path.join(self.base_dir, "intense_background.wav")

        self._initialize_mixer()
        
        # Incarcam sunetele doar daca placa audio functioneaza
        if self.enabled:
            self._load_all_sounds()

    def _initialize_mixer(self):
        """Inițializează motorul audio în condiții de siguranță."""
        try:
            import pygame
            import pygame.mixer
            pygame.mixer.init()
            self.enabled = True
            print("[AUDIO] Motorul audio a fost inițializat cu succes.")
        except Exception as e:
            print(f"[AUDIO ERROR] Eroare la inițializarea plăcii audio. Jocul va rula pe mut: {e}")
            self.enabled = False

    def _load_all_sounds(self):
        """Încarcă și mapează toate efectele sonore necesare jocului."""
        # Mapare logica: "nume_in_joc" -> "nume_fisier.mp3"
        sound_files = {
            "splash": "lava.mp3",
            "countdown": "clock.mp3",
            "meteor_boom": "meteor.mp3",
            "fire_out": "fire.mp3",
            "damage": "damage_hit.wav", 
            "game_over": "game_over.mp3"
        }

        # Incarcam fiecare fisier din dictionar
        for name, filename in sound_files.items():
            path = os.path.join(self.base_dir, filename)
            self._load_sound(name, path)

        # Pregatim muzica de fundal separat
        if os.path.exists(self.bgm_path):
            import pygame
            pygame.mixer.music.load(self.bgm_path)
            pygame.mixer.music.set_volume(0.3)  # Volum redus (30%) pentru a auzi SFX-urile peste muzica
        else:
            print(f"[AUDIO WARNING] Muzica de fundal lipsă: {self.bgm_path}")

    def _load_sound(self, name, path):
        """Metodă privată pentru a încărca un SFX și a-i seta volumul."""
        if os.path.exists(path):
            import pygame
            try:
                sound = pygame.mixer.Sound(path)
                sound.set_volume(0.8)  # Volum standard (80%) pentru efecte
                self.sounds[name] = sound
            except Exception as e:
                print(f"[AUDIO ERROR] Fișier corupt sau format nesuportat ({path}): {e}")
        else:
            print(f"[AUDIO WARNING] Nu s-a găsit fișierul: {path}")

    # --- METODE PUBLICE (API-ul Clasei) ---

    def play(self, name):
        """Redă instant un efect sonor (dacă sistemul e activ și sunetul există)."""
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def stop(self, name):
        """Oprește forțat un singur efect sonor specific (ex: oprim ceasul la start)."""
        if self.enabled and name in self.sounds:
            self.sounds[name].stop()

    def stop_all_sfx(self):
        """Oprește absolut toate sunetele (perfect pentru momentul de Game Over)."""
        if self.enabled:
            import pygame
            pygame.mixer.stop()

    def play_bgm(self):
        """Pornește muzica de fundal într-o buclă infinită (-1)."""
        if self.enabled and os.path.exists(self.bgm_path):
            import pygame
            pygame.mixer.music.play(-1)

    def stop_bgm(self):
        """Oprește muzica de fundal."""
        if self.enabled:
            import pygame
            pygame.mixer.music.stop()