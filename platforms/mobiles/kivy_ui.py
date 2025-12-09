# -*- coding: utf-8 -*-
"""
kivy_ui.py
Mobile UI implementation using Kivy, inheriting UIBase.
Focuses on binding Kivy events to UIBase methods.
"""

from typing import List
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.clock import mainthread
from kivy.metrics import dp

# 假设 core/app_controller.py 和 interface/ui_base.py 路径正确
from core.app_controller import AppController
from interface.ui_base import UIBase


class KivyUI(UIBase, App):
    """
    Kivy App and UIBase implementation combined.
    """
    
    # Kivy App method
    def build(self):
        # ⚠️ 注意: AppController 必须在界面元素创建后初始化
        # 因为它在初始化时会调用 UIBase 的方法 (e.g., cb_mode_changed)
        
        # 1. 创建界面元素
        self.root_widget = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        # --- Top Config ---
        config_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(5))
        
        # Voice Spinner
        self.voice_spinner = Spinner(text='Select Voice', values=[], size_hint_x=0.4)
        self.voice_spinner.bind(text=lambda spinner, text: self.on_change_voice(text))
        config_layout.add_widget(Label(text="Voice:"))
        config_layout.add_widget(self.voice_spinner)
        
        # Speed Slider (Placeholder)
        # Kivy's Slider needs more complex setup than Tkinter, using a simplified input/label here
        self.speed_label = Label(text="Speed: 0%", size_hint_x=0.2)
        config_layout.add_widget(self.speed_label)
        
        self.root_widget.add_widget(config_layout)

        # --- Play Controls ---
        ctrl_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(10))
        self.play_btn = Button(text="▶ Play", disabled=True, on_release=lambda btn: self.on_click_play())
        self.pause_btn = Button(text="⏸ Pause", disabled=True, on_release=lambda btn: self.on_click_pause())
        self.stop_btn = Button(text="■ Stop", disabled=True, on_release=lambda btn: self.on_click_stop())
        ctrl_layout.add_widget(self.play_btn)
        ctrl_layout.add_widget(self.pause_btn)
        ctrl_layout.add_widget(self.stop_btn)
        self.root_widget.add_widget(ctrl_layout)

        # --- Status Label ---
        self.status_label = Label(text="Status: Ready", size_hint_y=None, height=dp(50), halign='left')
        self.root_widget.add_widget(self.status_label)

        # --- Main Content (Input & List) ---
        main_content = BoxLayout(orientation='horizontal', spacing=dp(10))
        
        # Left: Text Input
        left_panel = BoxLayout(orientation='vertical')
        left_panel.add_widget(Label(text="Input Chinese Text", size_hint_y=None, height=dp(20)))
        self.text_input = TextInput(text='', multiline=True)
        left_panel.add_widget(self.text_input)
        left_panel.add_widget(Button(text="Process Text & Generate Audio", size_hint_y=None, height=dp(40),
                                     on_release=lambda btn: self.on_click_process()))
        left_panel.add_widget(Button(text="Select Image for OCR", size_hint_y=None, height=dp(40),
                                     on_release=lambda btn: self.on_click_ocr()))
        main_content.add_widget(left_panel)

        # Right: Sentence List (Using a basic TextInput for simplicity in this example)
        right_panel = BoxLayout(orientation='vertical')
        right_panel.add_widget(Label(text="Sentence List (Not implemented as a clickable list)", size_hint_y=None, height=dp(20)))
        self.sentence_list = TextInput(text='Sentence 1\nSentence 2', multiline=True, readonly=True)
        right_panel.add_widget(self.sentence_list)
        main_content.add_widget(right_panel)

        self.root_widget.add_widget(main_content)
        
        # 2. 初始化 AppController
        controller = AppController(
            on_status=self.cb_update_status,
            on_sentences_ready=self.cb_fill_sentences,
            on_buttons_update=self.cb_set_buttons,
            on_mode_change=self.cb_mode_changed
        )
        # 调用 UIBase 的构造函数，绑定 controller
        UIBase.__init__(self, controller) 

        # 3. 设置初始值
        self._setup_initial_values()
        
        return self.root_widget

    # ---------- 辅助方法 ----------
    def _setup_initial_values(self):
        try:
            voice_names = self.controller.get_voice_names()
            if voice_names:
                self.voice_spinner.values = voice_names
            self.voice_spinner.text = self.controller.selected_voice_ui
        except Exception as e:
            print(f"Failed to set initial voice values: {e}")
            
        # ⚠️ Missing: Implement logic for speed, mode, repeat/interval controls

    # ---------- UIBase 抽象方法实现（取值） ----------
    def _get_input_text(self) -> str:
        return self.text_input.text

    def _select_ocr_file(self) -> str:
        # ⚠️ 实际 Kivy 应用需要使用 plyer.filechooser 或自定义 File Chooser
        print("[Kivy] Simulating file selection...")
        # 模拟返回一个文件路径
        return '' # 用户取消或未实现

    def _get_sentence_text(self, idx: int) -> str:
        # ⚠️ 需要一个实际的 Kivy List/RecycleView 来根据索引获取
        lines = self.sentence_list.text.split('\n')
        if 0 <= idx < len(lines):
            return lines[idx]
        return ''

    # ---------- UIBase 抽象方法实现（Controller 回调） ----------
    @mainthread
    def cb_update_status(self, text: str) -> None:
        """Kivy 需要在主线程更新 UI"""
        self.status_label.text = text

    @mainthread
    def cb_fill_sentences(self, sentences: List[str]) -> None:
        """Kivy 需要在主线程更新 UI"""
        self.sentence_list.text = '\n'.join(sentences)
        
    @mainthread
    def cb_set_buttons(self, play_enabled: bool, pause_enabled: bool, stop_enabled: bool) -> None:
        """Kivy 需要在主线程更新 UI"""
        self.play_btn.disabled = not play_enabled
        self.pause_btn.disabled = not pause_enabled
        self.stop_btn.disabled = not stop_enabled

    @mainthread
    def cb_mode_changed(self, mode: str) -> None:
        """Kivy 需要在主线程更新 UI"""
        # ⚠️ Missing: Update Kivy Radio buttons/Toggle buttons for mode
        print(f"[Kivy] Mode changed to: {mode}")

    # ---------- 生命周期 ----------
    def run(self):
        self.run() # 调用 Kivy App 的 run 方法

if __name__ == '__main__':
    # ⚠️ 必须确保 AppController 和 UIBase 可导入
    KivyUI().run()