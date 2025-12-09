# -*- coding: utf-8 -*-
"""
audio_player_ios.py
iOS implementation using PyObjus to wrap the native AVAudioPlayer.
"""

from typing import Optional
from audio_player_base import AudioPlayerBase

# 尝试导入 PyObjus 依赖
try:
    from pyobjus import autoclass, objc_str
    from pyobjus.objc_py_types import ObjcList
    from pyobjus.protocols import ObjcProtocol
    
    # 导入 iOS 核心类
    AVAudioPlayer = autoclass('AVAudioPlayer')
    NSURL = autoclass('NSURL')
    NSString = autoclass('NSString')
    NSError = autoclass('NSError')
    
    # 实现 AVAudioPlayerDelegate 协议
    class AVAudioPlayerDelegateProtocol(ObjcProtocol):
        protocols = ['AVAudioPlayerDelegate']
        
        def audioPlayerDidFinishPlaying_successfully_(self, player, success):
            # 这个方法会在原生播放完成时回调
            print(f"[iOS] Playback finished successfully: {success}")
            # 需要在 Python 线程中更新状态，这里简化
            if player._py_ref:
                player._py_ref._is_playing_native = False
    
    delegate = AVAudioPlayerDelegateProtocol.alloc().init()

except ImportError:
    # 模拟类，供桌面端测试结构
    print("[iOS] PyObjus not found. Using simulation mode.")
    AVAudioPlayer = type('AVAudioPlayer', (object,), {'initWithContentsOfURL_error_': lambda *a: None,
                                                      'play': lambda *a: False, 'pause': lambda *a: None, 
                                                      'stop': lambda *a: None, 'isPlaying': lambda: False})


class IOSAudioPlayer(AudioPlayerBase):
    """
    iOS implementation: Wraps iOS's native AVAudioPlayer.
    """

    def __init__(self):
        super().__init__()
        self._player: Optional[AVAudioPlayer] = None
        self._is_playing_native = False

    # ------- platform-specific implementations -------
    def _load_audio(self, audio_path: str) -> bool:
        self._stop_playback()
        try:
            file_url = NSURL.fileURLWithPath_(objc_str(audio_path))
            error = NSError.alloc().init()
            
            # 初始化 AVAudioPlayer
            self._player = AVAudioPlayer.alloc().initWithContentsOfURL_error_(file_url, error)
            
            if not self._player:
                print(f"[iOS] Failed to initialize AVAudioPlayer: {error.localizedDescription}")
                return False
            
            # 绑定委托，并保存 Python 引用
            self._player.delegate = delegate
            delegate.player._py_ref = self # 用于回调时访问 Python 对象
            self._player.prepareToPlay()
            self._is_playing_native = False
            return True
        except Exception as e:
            print(f"[iOS] Failed to load/prepare audio: {e}")
            self._player = None
            return False

    def _play_once(self):
        if self._player:
            self._player.play()
            self._is_playing_native = True
        else:
            print("[iOS] AVAudioPlayer not loaded.")

    def _pause_playback(self):
        if self._player and self._player.isPlaying():
            self._player.pause()

    def _resume_playback(self):
        if self._player:
            self._player.play()

    def _stop_playback(self):
        if self._player:
            try:
                self._player.stop()
            except Exception as e:
                print(f"[iOS] Stop error: {e}")
            finally:
                # 在 iOS 中，通常不 release 而是让 ARC 管理
                self._player = None
                self._is_playing_native = False

    def _is_playing_audio(self) -> bool:
        if self._player:
            # 最佳实践是依赖原生 delegate 回调来设置 _is_playing_native
            return self._player.isPlaying() or self._is_playing_native
        return False
    
    def cleanup(self):
        self.stop()
        super().cleanup()