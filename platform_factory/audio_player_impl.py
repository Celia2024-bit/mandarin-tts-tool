
# -*- coding: utf-8 -*-
"""
Factory: choose platform implementation at runtime.
- Desktop: pygame
- Android: python-for-android/Kivy (ANDROID_ROOT in env)
- iOS: Pyto/BeeWare (sys.platform == 'ios' or platform.machine contains iPhone/iPad)
"""

import os
import sys
import platform

from interface.audio_player_base import AudioPlayerBase

# Import modules lazily (to avoid import errors on non-matching platforms)
def _is_android() -> bool:
    # python-for-android typically runs with sys.platform == 'linux' and ANDROID_ROOT in env
    return sys.platform.startswith('linux') and ('ANDROID_ROOT' in os.environ or os.environ.get('PYTHON_FOR_ANDROID') == '1')

def _is_ios() -> bool:
    # Pyto sets sys.platform == 'ios'; BeeWare may run on darwin with iPhone/iPad machine
    if sys.platform == 'ios':
        return True
    if sys.platform == 'darwin':
        mach = platform.machine().lower()
        return ('iphone' in mach) or ('ipad' in mach)
    return False

def create_audio_player() -> AudioPlayerBase:
    """
    Returns the best AudioPlayerBase implementation for the current platform.
    """
    if _is_android():
        from audio_player_android import AndroidAudioPlayer
        return AndroidAudioPlayer()
    elif _is_ios():
        from audio_player_ios import IOSAudioPlayer
        return IOSAudioPlayer()
    else:
        # Desktop default; handle missing pygame gracefully
        try:
            from audio_player_desktop import PygameAudioPlayer
            return PygameAudioPlayer()
        except Exception as e:
            # As a last resort, fallback to a no-op stub to avoid crashes
            print(f"[Factory] Desktop player failed to init ({e}). Using a safe no-op stub.")
            class _NoopPlayer(AudioPlayerBase):
                def _load_audio(self, p: str) -> bool: return False
                def _play_once(self): pass
                def _pause_playback(self): pass
                def _resume_playback(self): pass
                def _stop_playback(self): pass
                def _is_playing_audio(self) -> bool: return False
            return _NoopPlayer()

# Optional quick test
if __name__ == "__main__":
    import time
    player = create_audio_player()
    print(f"[Factory] Created player: {type(player).__name__}")
    # Replace with a valid local file to test
    test_audio = "./Test/test.mp3"
    try:
        started = player.play(test_audio, repeat_count=2, interval_ms=1000)
        if started:
            time.sleep(2)
            player.pause()
            time.sleep(1)
            player.resume()
            time.sleep(2)
        player.stop()
    except Exception as e:
        print(f"[Factory] Test error: {e}")
