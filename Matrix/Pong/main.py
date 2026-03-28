import time
import threading
from PongGame import PongGame  # Presupunem că PongGame, Player și Ball sunt în pong.py
from Controller import NetworkManager

def main():
    # 1. Inițializăm motorul jocului
    game = PongGame()

    # 2. Inițializăm rețeaua și îi dăm acces la obiectul game
    # NetworkManager va citi automat game.render() și va scrie în game.button_states
    net = NetworkManager(game)
    
    print("Pornire rețea...")
    net.start_bg()

    print("Jocul a început! Rulează pe matrice...")
    
    try:
        while game.running:
            # Executăm logica fizică (mișcare minge, verificare coliziuni, citire butoane)
            game.tick()
            
            # Controlăm viteza logicii (aprox 60 FPS pentru fluiditate)
            # NetworkManager oricum trimite la matrice cu viteza lui separată
            time.sleep(0.2) 
            
    except KeyboardInterrupt:
        print("\nJoc oprit de utilizator.")
    finally:
        game.running = False
        net.running = False
        print("Ieșire...")

if __name__ == "__main__":
    main()