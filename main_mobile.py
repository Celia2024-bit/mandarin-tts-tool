
# main_mobile.py
"""
Mobile entry point for Mandarin TTS Tool.
Initializes AppController and platform-specific audio player.
Replace `YourMobileUI` with your actual Kivy/BeeWare UI class.
"""

from platforms.mobiles.kivy_ui.py import KivyUI

if __name__ == "__main__":
    ui = KivyUI()

