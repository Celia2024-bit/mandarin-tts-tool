
# main_desktop.py
"""
Desktop entry point for Mandarin TTS Tool.
Loads Tkinter UI from platforms/desktop and starts the event loop.
"""

from platforms.desktop.tkinter_ui import TkinterUI

if __name__ == "__main__":
    ui = TkinterUI()
    ui.run()
