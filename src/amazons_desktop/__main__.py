"""Desktop startup and Windows DPI configuration."""
import ctypes
import sys
import tkinter as tk
from .ui.app import App


def main():
    if sys.platform == 'win32':
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
