import tkinter as tk
from Controller import MatrixGUI
import sys

def main():
    root = tk.Tk()
    
    app = MatrixGUI(root)
    
    print("Aplicația Matrix LED a pornit!")
    
    # Pornim bucla principală a interfeței grafice
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAplicația a fost închisă din terminal.")
        sys.exit(0)