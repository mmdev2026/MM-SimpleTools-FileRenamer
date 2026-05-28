"""Application startup for MM SimpleTools FileRenamer."""

import tkinter as tk

from app.gui import FileRenamerApp


def main():
    root = tk.Tk()
    FileRenamerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
