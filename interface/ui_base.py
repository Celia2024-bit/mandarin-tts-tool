
# -*- coding: utf-8 -*-
"""
UIBase: 抽象 UI 层 + 默认实现（把用户操作统一转发到 AppController）。
子类只需关注界面元素的构建与把事件绑定到这些方法即可；如需自定义行为，覆盖相应方法。
"""
from abc import ABC, abstractmethod
from typing import List

class UIBase(ABC):
    def __init__(self, controller):
        # 由具体 UI 在构造时传入 AppController 实例
        self.controller = controller

    # ---------- 生命周期 ----------
    @abstractmethod
    def run(self) -> None:
        pass

    # ---------- 用户操作（默认直接调用 controller） ----------
    def on_click_process(self) -> None:
        text = self._get_input_text()
        self.controller.process_text(text, auto_play=True)

    def on_click_ocr(self) -> None:
        file_path = self._select_ocr_file()
        if file_path:
            self.controller.ocr_image(file_path)

    def on_click_play(self) -> None:
        self.controller.play_audio()

    def on_click_pause(self) -> None:
        self.controller.pause_audio()

    def on_click_stop(self) -> None:
        self.controller.stop_audio()

    def on_change_voice(self, voice_name: str) -> None:
        self.controller.set_voice(voice_name)

    def on_change_speed(self, percent: int) -> None:
        self.controller.set_speed(percent)

    def on_change_repeat(self, mode: str, infinite: bool, count: int, interval_ms: int) -> None:
        self.controller.set_repeat_config(mode=mode, infinite=infinite, count=count, interval_ms=interval_ms)

    def on_double_click_sentence(self, idx: int) -> None:
        sentence = self._get_sentence_text(idx)
        if sentence:
            self.controller.generate_single_sentence(sentence, idx)

    # ---------- 控制器回调（抽象：子类必须实现） ----------
    @abstractmethod
    def cb_update_status(self, text: str) -> None:
        pass

    @abstractmethod
    def cb_fill_sentences(self, sentences: List[str]) -> None:
        pass

    @abstractmethod
    def cb_set_buttons(self, play_enabled: bool, pause_enabled: bool, stop_enabled: bool) -> None:
        pass

    @abstractmethod
    def cb_mode_changed(self, mode: str) -> None:
        pass

    # ---------- 子类需实现的辅助抽象方法 ----------
    @abstractmethod
    def _get_input_text(self) -> str:
        """返回待处理的输入文本。"""
        pass

    @abstractmethod
    def _select_ocr_file(self) -> str:
        """打开文件选择并返回图片路径；若用户取消返回空串/None。"""
        pass

    @abstractmethod
    def _get_sentence_text(self, idx: int) -> str:
        """根据列表索引返回对应句子文本。"""
        pass
