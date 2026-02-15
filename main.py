import tkinter as tk
from src.gui import BackupRestoreGUI

if __name__ == "__main__":
    root = tk.Tk()
    app = BackupRestoreGUI(root)
    root.mainloop()
