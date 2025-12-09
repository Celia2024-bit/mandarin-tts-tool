
# -*- coding: utf-8 -*-
"""
Desktop audio player (Windows/macOS/Linux) using pygame.mixer.
"""

from typing import Optional
from audio_player_base import AudioPlayerBase

class PygameAudioPlayer(AudioPlayerBase):
    """
    Desktop implementation: pygame.mixer.music-based streaming playback.
    """

    def __init__(self):
        super().__init__()
        # Lazy import to avoid import errors on non-desktop platforms.
        import pygame
        # You may tweak init params for stability:
        # pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        pygame.mixer.init()
        self._pg = pygame

    # ------- platform-specific implementations -------
    def _load_audio(self, audio_path: str) -> bool:
        try:
            self._pg.mixer.music.load(audio_path)
            return True
        except Exception as e:
            print(f"[Desktop] Failed to load audio: {e}")
            return False

    def _play_once(self):
        self._pg.mixer.music.play()

    def _pause_playback(self):
        self._pg.mixer.music.pause()

    def _resume_playback(self):
        self._pg.mixer.music.unpause()

    def _stop_playback(self):
        self._pg.mixer.music.stop()

    def _is_playing_audio(self) -> bool:
        return self._pg.mixer.music.get_busy()
