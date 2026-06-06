"""Application startup for MM SimpleTools DokumentenSortierer Pro."""

import tkinter as tk

from app.gui import DokumentenSortiererProApp


def main():
    root = tk.Tk()
    DokumentenSortiererProApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
