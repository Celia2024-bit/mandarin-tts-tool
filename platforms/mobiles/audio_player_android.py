
# -*- coding: utf-8 -*-
"""
Android audio player stub. Replace stubs with real jnius-based MediaPlayer code
when running under python-for-android/Kivy.
"""

from audio_player_base import AudioPlayerBase

class AndroidAudioPlayer(AudioPlayerBase):
    """
    Android player placeholder. In production, use `jnius` to access
    android.media.MediaPlayer and implement the methods below.
    """

    def __init__(self):
        super().__init__()
        # Example (real code when on device):
        # from jnius import autoclass
        # MediaPlayer = autoclass('android.media.MediaPlayer')
        # self.player = MediaPlayer()
        self.player = None
        print("[Android] player stub initialized")

    def _load_audio(self, audio_path: str) -> bool:
        if self.player is None:
            print(f"[Android] Would load: {audio_path}")
            return True
        # Real impl example:
        # try:
        #     self.player.reset()
        #     self.player.setDataSource(audio_path)
        #     self.player.prepare()
        #     return True
        # except Exception as e:
        #     print(f"[Android] load failed: {e}")
        #     return False
        return True

    def _play_once(self):
        if self.player:
            # self.player.start()
            pass

    def _pause_playback(self):
        if self.player:
            # self.player.pause()
            pass

    def _resume_playback(self):
        if self.player:
            # self.player.start()
            pass

    def _stop_playback(self):
        if self.player:
            # self.player.stop()
            pass

    def _is_playing_audio(self) -> bool:
        # return bool(self.player and self.player.isPlaying())
        return False
