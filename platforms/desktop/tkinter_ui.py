
# -*- coding: utf-8 -*-
"""
TkinterUI: 继承 ui_base.UIBase，仅负责界面构建与事件绑定。
- 自动从 AppController.get_voice_names() 读取语音列表
- 默认选中为 controller.selected_voice_ui
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
from typing import List


from core.app_controller import AppController
from interface.ui_base import UIBase


class TkinterUI(UIBase):
    def __init__(self):
        # 先创建界面，再构建控制器并把回调接入（避免 UIBase 调用未就绪控件）
        self.root = tk.Tk()
        self.root.title("Mandarin TTS Tool (UIBase forwarding)")
        self.root.geometry("1100x700")

        # 顶部配置区
        cfg = ttk.Frame(self.root)
        cfg.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(cfg, text="Voice:").pack(side=tk.LEFT)

        # 占位默认值；真正的列表与默认选中在控制器创建后填充
        self.voice_var = tk.StringVar(value="Mandarin Female (Xiaoyi)")
        self.voice_combo = ttk.Combobox(
            cfg, textvariable=self.voice_var, values=[], state='readonly', width=28
        )
        self.voice_combo.pack(side=tk.LEFT, padx=6)
        self.voice_combo.bind("<<ComboboxSelected>>",
                              lambda e: self.on_change_voice(self.voice_var.get()))

        ttk.Label(cfg, text="Speed:").pack(side=tk.LEFT, padx=(16, 4))
        self.speed_label = ttk.Label(cfg, text="0%", width=6)
        self.speed_label.pack(side=tk.LEFT, padx=(0, 4))
        self.speed_slider = ttk.Scale(
            cfg, from_=-50, to=100, orient=tk.HORIZONTAL, length=140,
            command=lambda v: (
                self.speed_label.config(text=f"{int(float(v)):+d}%"),
                self.on_change_speed(int(float(v)))
            )
        )
        self.speed_slider.pack(side=tk.LEFT)

        # 播放按钮
        self.play_btn = ttk.Button(cfg, text="▶ Play", command=self.on_click_play, state=tk.DISABLED)
        self.pause_btn = ttk.Button(cfg, text="⏸ Pause", command=self.on_click_pause, state=tk.DISABLED)
        self.stop_btn  = ttk.Button(cfg, text="■ Stop", command=self.on_click_stop,  state=tk.DISABLED)
        self.play_btn.pack(side=tk.LEFT, padx=4)
        self.pause_btn.pack(side=tk.LEFT, padx=4)
        self.stop_btn.pack(side=tk.LEFT,  padx=4)

        # 模式与循环
        ttk.Label(cfg, text="Mode:").pack(side=tk.LEFT, padx=(16, 4))
        self.mode_var = tk.StringVar(value='full')
        ttk.Radiobutton(cfg, text="Single", variable=self.mode_var, value='single',
                        command=lambda: self._apply_repeat_config()).pack(side=tk.LEFT)
        ttk.Radiobutton(cfg, text="Full",   variable=self.mode_var, value='full',
                        command=lambda: self._apply_repeat_config()).pack(side=tk.LEFT)
        ttk.Label(cfg, text="Repeat:").pack(side=tk.LEFT, padx=(16, 4))
        self.infinite_var = tk.BooleanVar(value=False)
        self.repeat_entry = ttk.Entry(cfg, width=4)
        self.repeat_entry.insert(0, '1')
        self.repeat_entry.pack(side=tk.LEFT)
        # ✅ 新增这两行
        self.repeat_entry.bind("<FocusOut>", lambda e: self._apply_repeat_config())
        self.repeat_entry.bind("<Return>", lambda e: (self._apply_repeat_config(), self.repeat_entry.master.focus()))
        ttk.Checkbutton(cfg, text="Loop", variable=self.infinite_var,
                        command=lambda: self._apply_repeat_config()).pack(side=tk.LEFT, padx=4)
        ttk.Label(cfg, text="Interval (ms):").pack(side=tk.LEFT, padx=(16, 4))
        self.interval_entry = ttk.Entry(cfg, width=6)
        self.interval_entry.insert(0, '500')
        self.interval_entry.pack(side=tk.LEFT)
        # ✅ 新增这两行
        self.interval_entry.bind("<FocusOut>", lambda e: self._apply_repeat_config())
        self.interval_entry.bind("<Return>", lambda e: (self._apply_repeat_config(), self.interval_entry.master.focus()))

        # 状态栏
        self.status_label = ttk.Label(
            self.root,
            text="Status: Ready\nNo Audio Generated",
            justify=tk.LEFT
        )
        self.status_label.pack(fill=tk.X, padx=10)

        # 主内容
        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        # 右：句子列表
        right = ttk.Frame(main)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        ttk.Label(right, text="Sentence List (Double-click to play)").pack(anchor=tk.W)
        self.sentence_list = tk.Listbox(right, height=28, width=60)
        self.sentence_list.pack(fill=tk.BOTH, expand=True)
        self.sentence_list.bind("<Double-Button-1>", lambda e: self._on_double_click_list())

        # 创建控制器并接入回调（最后创建，避免 UI 访问未就绪的控件）
        controller = AppController(
            on_status=self.cb_update_status,
            on_sentences_ready=self.cb_fill_sentences,
            on_buttons_update=self.cb_set_buttons,
            on_mode_change=self.cb_mode_changed,
            on_ocr_result=self.cb_fill_ocr_text
        )

        super().__init__(controller)
        
        # 左：文本输入
        left = ttk.Frame(main)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(left, text="Input Chinese Text").pack(anchor=tk.W)
        self.text_input = scrolledtext.ScrolledText(left, height=25, width=60, font=("Segoe UI", 10))
        self.text_input.pack(fill=tk.BOTH, expand=True)
        ttk.Button(left, text="Process Text & Generate Audio", style="Accent.TButton",
                   command=self.on_click_process).pack(pady=6, fill=tk.X)

        # ✅ 只在支持 OCR 的平台显示按钮
        if self.controller.is_ocr_supported():
            ttk.Button(left, text="Select Image for OCR", command=self.on_click_ocr).pack(pady=4, fill=tk.X)

        # ✅ 从控制器读取 voice 列表并设置默认选中
        try:
            voice_names = self.controller.get_voice_names()
            if voice_names:
                self.voice_combo['values'] = voice_names
            # 默认值设为控制器当前选中项
            self.voice_var.set(self.controller.selected_voice_ui)
        except Exception:
            # 如果出现异常，保持已有占位值
            pass
            
         # ✅ 新增：设置默认文本到输入框
        try:
            default_text = self.controller.get_default_text()
            self.text_input.delete("1.0", tk.END)
            self.text_input.insert("1.0", default_text)
        except Exception:
            # 如果获取默认文本失败，保持空白
            pass

    # ---------- 事件循环 ----------
    def run(self) -> None:
        """启动 Tkinter 主循环"""
        self.root.mainloop()

    # ---------- 控制器回调 ----------
    def cb_update_status(self, text: str) -> None:
        self.status_label.config(text=text)
    def cb_fill_ocr_text(self, text: str) -> None:
        """确保在主线程更新 UI"""
        def update():
            self.text_input.delete("1.0", tk.END)
            self.text_input.insert(tk.END, text)
        self.root.after(0, update)

    def cb_fill_sentences(self, sentences: List[str]) -> None:
        self.sentence_list.delete(0, tk.END)
        for s in sentences:
            self.sentence_list.insert(tk.END, s)

    def cb_set_buttons(self, play_enabled: bool, pause_enabled: bool, stop_enabled: bool) -> None:
        self.play_btn.config(state=(tk.NORMAL if play_enabled else tk.DISABLED))
        self.pause_btn.config(state=(tk.NORMAL if pause_enabled else tk.DISABLED))
        self.stop_btn.config(state=(tk.NORMAL if stop_enabled else tk.DISABLED))

    def cb_mode_changed(self, mode: str) -> None:
        self.mode_var.set(mode)

    # ---------- 取值方法（UIBase 要求） ----------
    def _get_input_text(self) -> str:
        return self.text_input.get("1.0", tk.END)

    def _select_ocr_file(self) -> str:
        return filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )

    def _get_sentence_text(self, idx: int) -> str:
        try:
            return self.sentence_list.get(idx)
        except Exception:
            return ''

    # ---------- 本类内部事件 ----------
    def _apply_repeat_config(self):
        try:
            count = int(self.repeat_entry.get() or '1')
        except Exception:
            count = 1
            self.repeat_entry.delete(0, tk.END)
            self.repeat_entry.insert(0, '1')
        try:
            interval_ms = int(self.interval_entry.get() or '500')
        except Exception:
            interval_ms = 500
            self.interval_entry.delete(0, tk.END)
            self.interval_entry.insert(0, '500')
        self.on_change_repeat(mode=self.mode_var.get(), infinite=self.infinite_var.get(),
                              count=count, interval_ms=interval_ms)

    def _on_double_click_list(self):
        idxs = self.sentence_list.curselection()
        if idxs:
            self.on_double_click_sentence(idxs[0])


# 直接运行
if __name__ == '__main__':
    ui = TkinterUI()
    ui.run()
