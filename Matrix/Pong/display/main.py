import tkinter as tk
from display import MatrixGUI

if __name__ == "__main__":
    root = tk.Tk()
    # Acum Python știe ce este MatrixGUI pentru că l-ai importat mai sus
    app = MatrixGUI(root) 
    print("Fereastra simulatorului ar trebui să apară acum...")
    root.mainloop()