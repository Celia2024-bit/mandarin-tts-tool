
# -*- coding: utf-8 -*-
"""
audio_player_base.py
平台无关的音频播放器抽象接口（不包含任何具体实现）。
"""

import threading
import time
from abc import ABC, abstractmethod
from typing import Optional, Callable


class AudioPlayerBase(ABC):
    """
    抽象播放器基类。
    平台/框架的具体实现（pygame、Android、iOS 等）应继承本类并实现抽象方法。
    """

    def __init__(self):
        self.is_playing = False
        self.is_paused = False
        self._on_complete_callback: Optional[Callable] = None

    # ------- 需由具体实现覆盖的“私有”方法 -------
    @abstractmethod
    def _load_audio(self, audio_path: str) -> bool:
        """加载音频文件。成功返回 True。"""
        raise NotImplementedError

    @abstractmethod
    def _play_once(self):
        """播放已加载音频一次（阻塞直至该次播放开始）。"""
        raise NotImplementedError

    @abstractmethod
    def _pause_playback(self):
        """暂停当前播放。"""
        raise NotImplementedError

    @abstractmethod
    def _resume_playback(self):
        """恢复暂停播放。"""
        raise NotImplementedError

    @abstractmethod
    def _stop_playback(self):
        """完全停止播放。"""
        raise NotImplementedError

    @abstractmethod
    def _is_playing_audio(self) -> bool:
        """查询底层是否仍在播放（busy）。"""
        raise NotImplementedError

    # ------- 公共控制接口（已实现通用逻辑） -------
    def play(
        self,
        audio_path: str,
        repeat_count: int = 1,
        interval_ms: int = 500,
        on_complete: Optional[Callable] = None,
    ) -> bool:
        """
        按配置播放音频（支持重复与间隔），播放线程在后台进行。

        Args:
            audio_path: 音频文件路径
            repeat_count: 播放次数（-1 表示无限循环）
            interval_ms: 每次播放间隔（毫秒）
            on_complete: 自然播放完成时的回调

        Returns:
            True 表示已开始播放线程；False 表示加载失败
        """
        if not self._load_audio(audio_path):
            return False

        self._on_complete_callback = on_complete
        self.is_playing = True
        self.is_paused = False

        # 后台线程跑循环播放
        play_thread = threading.Thread(
            target=self._playback_loop, args=(repeat_count, interval_ms), daemon=True
        )
        play_thread.start()
        return True

    def _playback_loop(self, repeat_count: int, interval_ms: int):
        """后台播放循环（通用逻辑）。"""
        infinite = (repeat_count == -1)
        play_counter = 0

        while self.is_playing and (infinite or play_counter < repeat_count):
            if not self.is_paused:
                try:
                    self._play_once()
                    # 等待底层播放状态结束
                    while self._is_playing_audio() and self.is_playing and not self.is_paused:
                        time.sleep(0.1)
                    play_counter += 1
                    # 间隔（最后一次不等待）
                    if self.is_playing and not self.is_paused and (infinite or play_counter < repeat_count):
                        time.sleep(interval_ms / 1000.0)
                except Exception as e:
                    print(f"Playback error: {e}")
                    break
            else:
                time.sleep(0.1)

        # 自然完成
        if self.is_playing and not self.is_paused:
            self.is_playing = False
            if self._on_complete_callback:
                try:
                    self._on_complete_callback()
                except Exception as e:
                    print(f"on_complete callback error: {e}")

    def pause(self):
        """暂停播放。"""
        if self.is_playing and not self.is_paused:
            self._pause_playback()
            self.is_paused = True

    def resume(self):
        """恢复播放。"""
        if self.is_paused:
            self._resume_playback()
            self.is_paused = False

    def stop(self):
        """停止播放。"""
        self.is_playing = False
        self.is_paused = False
        try:
            self._stop_playback()
        except Exception:
            pass

    def cleanup(self):
        """清理资源（如果需要）。"""
        self.stop()
