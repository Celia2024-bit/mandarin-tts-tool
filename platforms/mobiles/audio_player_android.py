# -*- coding: utf-8 -*-
"""
audio_player_android.py
Android implementation using Pyjnius to wrap the native MediaPlayer.
"""

from typing import Optional
from audio_player_base import AudioPlayerBase

# 尝试导入 Pyjnius 依赖
try:
    from jnius import autoclass
    MediaPlayer = autoclass('android.media.MediaPlayer')
    File = autoclass('java.io.File')
    FileInputStream = autoclass('java.io.FileInputStream')
    # Java 接口，用于设置完成监听器
    OnCompletionListener = autoclass('android.media.MediaPlayer$OnCompletionListener')

    class CompletionListener(OnCompletionListener):
        def __init__(self, player):
            self.player = player
        def onCompletion(self, mp):
            # 这是一个在原生线程中执行的回调
            self.player._is_playing_native = False
            # 通常需要切换回 Python 主线程执行其他逻辑，这里简化
            print("[Android] Playback completed by native callback.")

except ImportError:
    # 模拟类，供桌面端测试结构
    print("[Android] Pyjnius not found. Using simulation mode.")
    MediaPlayer = type('MediaPlayer', (object,), {'create': lambda *a: None, 'setDataSource': lambda *a: None, 
                                                  'prepare': lambda *a: None, 'start': lambda *a: None, 
                                                  'pause': lambda *a: None, 'stop': lambda *a: None,
                                                  'isPlaying': lambda: False})
    CompletionListener = object


class AndroidAudioPlayer(AudioPlayerBase):
    """
    Android implementation: Wraps Android's native MediaPlayer.
    """

    def __init__(self):
        super().__init__()
        self._media_player: Optional[MediaPlayer] = None
        self._is_playing_native = False # 用于辅助 AudioPlayerBase 的 _playback_loop

    # ------- platform-specific implementations -------
    def _load_audio(self, audio_path: str) -> bool:
        self._stop_playback() # 停止并释放之前的资源
        try:
            self._media_player = MediaPlayer()
            # 确保文件存在
            if not File(audio_path).exists():
                 print(f"[Android] Audio file not found: {audio_path}")
                 return False
            
            # 使用 FileInputStream 设置数据源，更稳定
            fis = FileInputStream(audio_path)
            self._media_player.setDataSource(fis.getFD())
            self._media_player.prepare()
            fis.close()

            # 设置完成监听器，用于更新 _is_playing_native 状态
            self._media_player.setOnCompletionListener(CompletionListener(self))
            self._is_playing_native = False
            return True
        except Exception as e:
            print(f"[Android] Failed to load/prepare audio: {e}")
            self._media_player = None
            return False

    def _play_once(self):
        if self._media_player:
            self._media_player.start()
            self._is_playing_native = True
        else:
            print("[Android] MediaPlayer not loaded.")

    def _pause_playback(self):
        if self._media_player and self._media_player.isPlaying():
            self._media_player.pause()

    def _resume_playback(self):
        if self._media_player:
            self._media_player.start()

    def _stop_playback(self):
        if self._media_player:
            try:
                self._media_player.stop()
                self._media_player.release() # 释放资源
            except Exception as e:
                print(f"[Android] Stop/release error: {e}")
            finally:
                self._media_player = None
                self._is_playing_native = False

    def _is_playing_audio(self) -> bool:
        # 使用自定义状态机或尝试调用原生 API
        if self._media_player:
            # 1. 理论上应该直接使用原生回调来设置 _is_playing_native
            # 2. 或者在 Android 环境下，直接使用 self._media_player.isPlaying()
            return self._is_playing_native or self._media_player.isPlaying()
        return False
    
    def cleanup(self):
        self.stop()
        super().cleanup()