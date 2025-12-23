# -*- coding: utf-8 -*-
"""
TkinterUI: 继承 ui_base.UIBase，仅负责界面构建与事件绑定。
- 自动从 AppController.get_voice_names() 读取语音列表
- 默认选中为 controller.selected_voice_ui
"""

import tkinter as tk
import os
from tkinter import ttk, scrolledtext, filedialog
from typing import List
import sys
from core.app_controller import AppController
from interface.ui_base import UIBase




class TkinterUI(UIBase):
    def __init__(self):
        # ========== 仅新增这3行：Mac兼容（不改动你的其他代码） ==========
        if sys.platform == "darwin":  # 仅对Mac生效
            tk.Tk().tk.call("tk", "scaling", 2.0)  # 修复Mac Retina屏模糊/字体小
        
        # ========== 你原来的Windows适配代码（保留不动） ==========
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
                root_temp = tk.Tk()
                root_temp.tk.call('tk', 'scaling', 1.2)
                root_temp.destroy()
            except Exception as e:
                print(f"DPI适配警告: {e}")
        
        # ========== 你原来的窗口初始化（保留不动） ==========
        self.root = tk.Tk()
        if self.is_ci_environment():
            # CI无头环境：极简配置，仅保证进程不退出
            self.root.geometry("800x600")  # 固定最小窗口
            self.root.resizable(False, False)
            self.root.withdraw()  # 隐藏窗口（CI无显示器，无需渲染）
            self.root.after(30000, self.root.quit)  # 30秒后自动退出（避免CI进程挂起）
        else:
            self.root.title("Mandarin TTS Tool")
            
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            adapt_width = int(screen_width * 0.8)
            adapt_height = int(screen_height * 0.8) if screen_height * 0.9 > 750 else 750
            self.root.geometry(f"{adapt_width}x{adapt_height}")
            self.root.minsize(1200, 750)
            x = (screen_width - adapt_width) // 2
            y = (screen_height - adapt_height) // 2
            self.root.geometry(f"{adapt_width}x{adapt_height}+{x}+{y}")

            # ========== 以下所有代码：完全保留你觉得“能看”的版本（一行未改） ==========
            cfg = ttk.Frame(self.root)
            cfg.pack(fill=tk.X, padx=10, pady=8)

            ttk.Label(cfg, text="Voice:").pack(side=tk.LEFT)

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

            self.play_btn = ttk.Button(cfg, text="▶ Play", command=self.on_click_play, state=tk.DISABLED)
            self.pause_btn = ttk.Button(cfg, text="⏸ Pause", command=self.on_click_pause, state=tk.DISABLED)
            self.stop_btn  = ttk.Button(cfg, text="■ Stop", command=self.on_click_stop,  state=tk.DISABLED)
            self.play_btn.pack(side=tk.LEFT, padx=4)
            self.pause_btn.pack(side=tk.LEFT, padx=4)
            self.stop_btn.pack(side=tk.LEFT,  padx=4)

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
            self.repeat_entry.bind("<FocusOut>", lambda e: self._apply_repeat_config())
            self.repeat_entry.bind("<Return>", lambda e: (self._apply_repeat_config(), self.repeat_entry.master.focus()))
            ttk.Checkbutton(cfg, text="Loop", variable=self.infinite_var,
                            command=lambda: self._apply_repeat_config()).pack(side=tk.LEFT, padx=4)
            ttk.Label(cfg, text="Interval (ms):").pack(side=tk.LEFT, padx=(16, 4))
            self.interval_entry = ttk.Entry(cfg, width=6)
            self.interval_entry.insert(0, '500')
            self.interval_entry.pack(side=tk.LEFT)
            self.interval_entry.bind("<FocusOut>", lambda e: self._apply_repeat_config())
            self.interval_entry.bind("<Return>", lambda e: (self._apply_repeat_config(), self.interval_entry.master.focus()))

            self.status_label = ttk.Label(
                self.root,
                text="Status: Ready\nNo Audio Generated",
                justify=tk.LEFT
            )
            self.status_label.pack(fill=tk.X, padx=10)

            main = ttk.Frame(self.root)
            main.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
            main.columnconfigure(0, weight=6)
            main.columnconfigure(1, weight=4)
            main.rowconfigure(0, weight=1)

            right = ttk.Frame(main)
            right.grid(row=0, column=1, sticky="nsew", padx=(10,0))
            
            ttk.Label(right, text="Sentence List (Double-click to play)").pack(anchor=tk.W)
            font_size = int(adapt_width / 100) if int(adapt_width / 100) >= 12 else 12
            self.sentence_list = tk.Listbox(right, height=28, width=70, font=("Segoe UI", font_size))
            self.sentence_list.pack(fill=tk.BOTH, expand=True)
            self.sentence_list.bind("<Double-Button-1>", lambda e: self._on_double_click_list())

            controller = AppController(
                on_status=self.cb_update_status,
                on_sentences_ready=self.cb_fill_sentences,
                on_buttons_update=self.cb_set_buttons,
                on_mode_change=self.cb_mode_changed,
                on_ocr_result=self.cb_fill_ocr_text
            )

            super().__init__(controller)
            
            left = ttk.Frame(main)
            left.grid(row=0, column=0, sticky="nsew")
            left.rowconfigure(1, weight=1)
            left.columnconfigure(0, weight=1)

            ttk.Label(left, text="Input Chinese Text").grid(row=0, column=0, sticky="w", padx=5, pady=5)
            self.text_input = scrolledtext.ScrolledText(left, height=25, width=70, font=("Segoe UI", font_size))
            self.text_input.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

            btn_frame = ttk.Frame(left)
            btn_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
            
            ttk.Button(btn_frame, text="Process Text & Generate Audio", style="Accent.TButton",
                       command=self.on_click_process).pack(fill=tk.X, pady=3)

            if self.controller.is_ocr_supported():
                ttk.Button(btn_frame, text="Select Image for OCR", command=self.on_click_ocr).pack(fill=tk.X, pady=3)

            try:
                voice_names = self.controller.get_voice_names()
                if voice_names:
                    self.voice_combo['values'] = voice_names
                self.voice_var.set(self.controller.selected_voice_ui)
            except Exception:
                pass
                
            try:
                default_text = self.controller.get_default_text()
                self.text_input.delete("1.0", tk.END)
                self.text_input.insert("1.0", default_text)
            except Exception:
                pass

    def is_ci_environment(self):
        """判断是否在CI环境（GitHub Actions）中运行"""
        return "CI" in os.environ or "RUNNER" in os.environ or "GITHUB_ACTIONS" in os.environ
    def run(self) -> None:
        if not self.is_ci_environment():
            self.root.deiconify() 
        self.root.mainloop()

    def cb_update_status(self, text: str) -> None:
        self.root.after(0, lambda: self.status_label.config(text=text))
        
    def cb_fill_ocr_text(self, text: str) -> None:
        def update():
            self.text_input.delete("1.0", tk.END)
            self.text_input.insert(tk.END, text)
        self.root.after(0, update)

    def cb_fill_sentences(self, sentences: List[str]) -> None:
        self.root.after(0, lambda: [self.sentence_list.delete(0, tk.END), [self.sentence_list.insert(tk.END, s) for s in sentences]])

    def cb_set_buttons(self, play_enabled: bool, pause_enabled: bool, stop_enabled: bool) -> None:
        self.root.after(0, lambda: [
            self.play_btn.config(state=(tk.NORMAL if play_enabled else tk.DISABLED)),
            self.pause_btn.config(state=(tk.NORMAL if pause_enabled else tk.DISABLED)),
            self.stop_btn.config(state=(tk.NORMAL if stop_enabled else tk.DISABLED))
        ])

    def cb_mode_changed(self, mode: str) -> None:
        self.root.after(0, lambda: self.mode_var.set(mode))

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


if __name__ == '__main__':
    ui = TkinterUI()
    ui.run()