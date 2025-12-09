
# -*- coding: utf-8 -*-
"""
audio_player_impl.py
具体播放器实现（pygame 桌面端实现 + Android/iOS stub）以及工厂函数。
"""

import os
import sys

# 导入抽象基类
from audio_player_base import AudioPlayerBase


# ==================== Pygame 实现（桌面） ====================
class PygameAudioPlayer(AudioPlayerBase):
    """
    基于 pygame.mixer 的桌面端播放器实现（Windows/macOS/Linux）。
    """

    def __init__(self):
        super().__init__()
        import pygame  # 延迟导入，避免非桌面环境报错
        pygame.mixer.init()
        self.pygame = pygame

    def _load_audio(self, audio_path: str) -> bool:
        try:
            self.pygame.mixer.music.load(audio_path)
            return True
        except Exception as e:
            print(f"Failed to load audio: {e}")
            return False

    def _play_once(self):
        self.pygame.mixer.music.play()

    def _pause_playback(self):
        self.pygame.mixer.music.pause()

    def _resume_playback(self):
        self.pygame.mixer.music.unpause()

    def _stop_playback(self):
        self.pygame.mixer.music.stop()

    def _is_playing_audio(self) -> bool:
        return self.pygame.mixer.music.get_busy()


# ==================== Android 实现（Stub） ====================
class AndroidAudioPlayer(AudioPlayerBase):
    """
    Android 播放器（示例 stub），真实实现可通过 jnius 访问 MediaPlayer。
    需要 python-for-android/Kivy 环境。
    """

    def __init__(self):
        super().__init__()
        # 在真实环境中：
        # from jnius import autoclass
        # MediaPlayer = autoclass('android.media.MediaPlayer')
        # self.player = MediaPlayer()
        self.player = None
        print("Android player stub initialized")

    def _load_audio(self, audio_path: str) -> bool:
        if self.player is None:
            print(f"Would load: {audio_path}")
            return True
        # 真实实现示意：
        # try:
        #     self.player.reset()
        #     self.player.setDataSource(audio_path)
        #     self.player.prepare()
        #     return True
        # except Exception:
        #     return False
        return True

    def _play_once(self):
        if self.player:
            pass  # self.player.start()

    def _pause_playback(self):
        if self.player:
            pass  # self.player.pause()

    def _resume_playback(self):
        if self.player:
            pass  # self.player.start()

    def _stop_playback(self):
        if self.player:
            pass  # self.player.stop()

    def _is_playing_audio(self) -> bool:
        if self.player:
            return False  # return self.player.isPlaying()
        return False


# ==================== iOS 实现（Stub） ====================
class IOSAudioPlayer(AudioPlayerBase):
    """
    iOS 播放器（示例 stub），真实实现可通过 pyobjus/BeeWare 访问 AVAudioPlayer。
    """

    def __init__(self):
        super().__init__()
        # 真实环境示意：
        # from pyobjus import autoclass
        # NSURL = autoclass('NSURL')
        # AVAudioPlayer = autoclass('AVAudioPlayer')
        self.player = None
        print("iOS player stub initialized")

    def _load_audio(self, audio_path: str) -> bool:
        print(f"Would load: {audio_path}")
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


# ==================== 工厂函数 ====================
def create_audio_player() -> AudioPlayerBase:
    """
    根据当前平台创建合适的播放器实例。
    - 桌面（默认）：pygame
    - Android（检测 ANDROID_ROOT 环境变量）：AndroidAudioPlayer
    - iOS（可根据实际运行环境补充更精确检测）：IOSAudioPlayer
    """
    # 简易环境检测（你可以在实际项目里根据打包/运行环境精细化判断逻辑）
    is_android = sys.platform.startswith('linux') and ('ANDROID_ROOT' in os.environ)
    is_ios = (sys.platform == 'darwin' and 'iphone' in sys.platform)  # 示例判断，实际需替换更可靠方式

    if is_android:
        return AndroidAudioPlayer()
    elif is_ios:
        return IOSAudioPlayer()
    else:
        # 默认桌面
        return PygameAudioPlayer()


# ==================== 简单测试（可选） ====================
if __name__ == "__main__":
    import time
    print("Testing Audio Player Implementations")

    player = create_audio_player()
    print(f"Created player: {type(player).__name__}")

    # 使用真实音频文件测试（自行替换路径）
    test_audio = "./Test/test.mp3"
    try:
        started = player.play(test_audio, repeat_count=2, interval_ms=1000)
        if started:
            time.sleep(5)
            player.pause()
            time.sleep(2)
            player.resume()
            time.sleep(3)
        player.stop()
    except Exception as e:
        print(f"Test error: {e}")
