
# -*- coding: utf-8 -*-
"""
iOS audio player stub. Replace with pyobjus/BeeWare AVAudioPlayer integration
when running on iOS.
"""

from audio_player_base import AudioPlayerBase

class IOSAudioPlayer(AudioPlayerBase):
    """
    iOS player placeholder. In production, use pyobjus/BeeWare to call
    AVAudioPlayer and implement the methods below.
    """

    def __init__(self):
        super().__init__()
        # Example (pseudo):
        # from pyobjus import autoclass
        # NSURL = autoclass('NSURL')
        # AVAudioPlayer = autoclass('AVAudioPlayer')
        self.player = None
        print("[iOS] player stub initialized")

    def _load_audio(self, audio_path: str) -> bool:
        print(f"[iOS] Would load: {audio_path}")
        return True

    def _play_once(self):
        pass

    def _pause_playback(self):
        pass

    def _resume_playback(self):
        pass

    def _stop_playback(self):
        pass

    def _is_playing_audio(self) -> bool:
        return False
