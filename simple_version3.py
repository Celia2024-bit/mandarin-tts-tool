# -*- coding:utf-8 -*-
import edge_tts
import asyncio
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
from datetime import datetime
import pygame
import re
import threading
import shutil

# 定义发音人列表（英文标识）
VOICE_DICT = {
    "Mandarin Female (Xiaoyi)": "zh-CN-XiaoyiNeural",
    "Mandarin Female (Xiaoxiao)": "zh-CN-XiaoxiaoNeural",
    "Mandarin Female (Yunxi)": "zh-CN-YunxiNeural",
    "Mandarin Male (Yunjian)": "zh-CN-YunjianNeural",
    "Mandarin Female (Lingling)": "zh-CN-LinglingNeural",
    "Northeast Mandarin Female": "zh-CN-Liaoning-XiaobeiNeural"
}

class EdgeTTS_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mandarin TTS Tool (Beautiful & Stable)")
        self.root.geometry("1200x700")
        self.root.resizable(True, True)

        # ====================== 核心美化配置（不改动布局） ======================
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # 强调按钮（Process）样式
        self.style.configure(
            "Accent.TButton",
            font=("Segoe UI", 10, "bold"),
            foreground="#FFFFFF",
            background="#2563EB",  # 深蓝色
            padding=(12, 6),
            borderwidth=0,
            relief="flat",
            borderradius=4  # 圆角
        )
        self.style.map(
            "Accent.TButton",
            background=[("active", "#1D4ED8"), ("pressed", "#1E40AF")],
            relief=[("active", "flat"), ("pressed", "flat")]
        )

        # 普通按钮（Play/Pause/Stop）样式
        self.style.configure(
            "TButton",
            font=("Segoe UI", 9),
            foreground="#1F2937",
            background="#F3F4F6",
            padding=(8, 4),
            borderwidth=1,
            relief="solid",
            bordercolor="#D1D5DB",
            borderradius=3
        )
        self.style.map(
            "TButton",
            background=[("active", "#E5E7EB")],
            bordercolor=[("active", "#9CA3AF")]
        )

        # 标签样式
        self.style.configure(
            "TLabel",
            font=("Segoe UI", 10),
            foreground="#1F2937"
        )
        self.style.configure(
            "Title.TLabel",
            font=("Segoe UI", 11, "bold"),
            foreground="#1F2937"
        )

        # 输入框/下拉框样式
        self.style.configure(
            "TEntry",
            font=("Segoe UI", 10),
            foreground="#1F2937",
            background="#FFFFFF",
            padding=(6, 3),
            borderwidth=1,
            relief="solid",
            bordercolor="#D1D5DB",
            borderradius=3
        )
        self.style.map(
            "TEntry",
            bordercolor=[("focus", "#2563EB")]
        )

        self.style.configure(
            "TCombobox",
            font=("Segoe UI", 10),
            foreground="#1F2937",
            background="#FFFFFF",
            padding=(6, 3),
            borderwidth=1,
            relief="solid",
            bordercolor="#D1D5DB",
            borderradius=3
        )
        self.style.map(
            "TCombobox",
            bordercolor=[("focus", "#2563EB")]
        )

        # 框架样式（输入区/列表区）
        self.style.configure(
            "Content.TFrame",
            background="#FFFFFF",
            borderwidth=1,
            relief="solid",
            bordercolor="#E5E7EB",
            borderradius=6
        )

        # 状态框样式
        self.style.configure(
            "Status.TFrame",
            background="#F9FAFB",
            borderwidth=1,
            relief="solid",
            bordercolor="#E5E7EB"
        )

        # ====================== 核心变量定义 ======================
        self.full_audio_path = None
        self.single_audio_path = None
        self.selected_single_text = ""
        self.selected_single_idx = -1
        self.selected_voice = "Mandarin Female (Xiaoyi)"
        self.is_playing = False
        self.is_paused = False
        self.is_processing = False
        self.infinite_var = tk.BooleanVar(value=False)

        # 初始化播放器
        pygame.mixer.init()

        # ====================== 配置区（美化，布局不变） ======================
        self.config_frame = ttk.Frame(root, padding=(5, 8))
        self.config_frame.pack(fill=tk.X, padx=10, pady=5)

        # 发音人
        self.voice_label = ttk.Label(self.config_frame, text="Voice:", font=("Segoe UI", 10))
        self.voice_label.pack(side=tk.LEFT, padx=(5, 3))
        self.voice_var = tk.StringVar(value=self.selected_voice)
        self.voice_combobox = ttk.Combobox(
            self.config_frame,
            textvariable=self.voice_var,
            values=list(VOICE_DICT.keys()),
            state="readonly",
            width=22
        )
        self.voice_combobox.pack(side=tk.LEFT, padx=5)
        self.voice_combobox.bind("<<ComboboxSelected>>", self.on_voice_change)

        # 播放按钮
        self.play_btn = ttk.Button(self.config_frame, text="▶ Play", command=self.play_audio, state=tk.DISABLED)
        self.play_btn.pack(side=tk.LEFT, padx=3)
        self.pause_btn = ttk.Button(self.config_frame, text="⏸ Pause", command=self.pause_audio, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=3)
        self.stop_btn = ttk.Button(self.config_frame, text="■ Stop", command=self.stop_audio, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=3)

        # 播放模式（去掉 font 参数）
        self.mode_label = ttk.Label(self.config_frame, text="Mode:", font=("Segoe UI", 10))
        self.mode_label.pack(side=tk.LEFT, padx=(20, 3))
        self.repeat_mode_var = tk.StringVar(value="full")
        self.single_radio = ttk.Radiobutton(
            self.config_frame,
            text="Single",
            variable=self.repeat_mode_var,
            value="single",
            command=self.on_mode_change
        )
        self.single_radio.pack(side=tk.LEFT, padx=3)
        self.full_radio = ttk.Radiobutton(
            self.config_frame,
            text="Full",
            variable=self.repeat_mode_var,
            value="full",
            command=self.on_mode_change
        )
        self.full_radio.pack(side=tk.LEFT, padx=3)

        # 重复和间隔（去掉 font 参数）
        self.repeat_label = ttk.Label(self.config_frame, text="Repeat:", font=("Segoe UI", 10))
        self.repeat_label.pack(side=tk.LEFT, padx=(20, 3))
        self.repeat_count_var = tk.StringVar(value="1")
        self.repeat_entry = ttk.Entry(self.config_frame, textvariable=self.repeat_count_var, width=3)
        self.repeat_entry.pack(side=tk.LEFT, padx=3)
        self.infinite_check = ttk.Checkbutton(
            self.config_frame,
            text="Loop",
            variable=self.infinite_var,
            command=self.toggle_repeat_entry
        )
        self.infinite_check.pack(side=tk.LEFT, padx=3)

        self.interval_label = ttk.Label(self.config_frame, text="Interval:", font=("Segoe UI", 10))
        self.interval_label.pack(side=tk.LEFT, padx=(20, 3))
        self.interval_var = tk.StringVar(value="500")
        self.interval_entry = ttk.Entry(self.config_frame, textvariable=self.interval_var, width=5)
        self.interval_entry.pack(side=tk.LEFT, padx=3)
        self.interval_unit = ttk.Label(self.config_frame, text="ms", font=("Segoe UI", 9))
        self.interval_unit.pack(side=tk.LEFT)

        # ====================== 状态区（美化，布局不变） ======================
        self.status_frame = ttk.Frame(root, style="Status.TFrame", padding=(5, 3))
        self.status_frame.pack(fill=tk.X, padx=10, pady=5)
        self.main_status = ttk.Label(
            self.status_frame,
            text="Status: Ready | No Audio Generated",
            padding=(5, 2),
            font=("Segoe UI", 9)
        )
        self.main_status.pack(side=tk.LEFT)

        # ====================== 主内容区（保持原有稳定布局，只美化） ======================
        self.main_content = ttk.Frame(root)
        self.main_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 左侧输入区（美化，布局不变）
        self.left_frame = ttk.Frame(self.main_content, style="Content.TFrame", padding=(10, 10))
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.text_label = ttk.Label(self.left_frame, text="Input Chinese Text", style="Title.TLabel")
        self.text_label.pack(anchor=tk.W, pady=(0, 5))
        # 输入框美化（去掉 bordercolor，用 bd+relief 控制边框）
        self.text_input = scrolledtext.ScrolledText(
            self.left_frame,
            height=25,
            width=60,
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#1F2937",
            bd=1,  # 边框宽度
            relief="solid",  # 实线边框
            highlightthickness=0,
            selectbackground="#DBEAFE",  # 选中背景色
            selectforeground="#1F2937"
        )
        self.text_input.pack(fill=tk.BOTH, expand=True, pady=5)
        default_text = """这是一个高质量的普通话TTS工具，支持全文朗读和单句播放功能。
    用户可以输入任意中文文本，点击处理按钮即可完成断句和音频生成。
    切换不同的发音人后，需要重新生成音频才能生效。
    支持重复播放、无限循环和自定义播放间隔，操作简单易用。"""
        self.text_input.insert(tk.END, default_text)

        # 处理按钮（强调样式）
        self.submit_btn = ttk.Button(
            self.left_frame,
            text="Process Text & Generate Audio",
            command=self.process_text,
            style="Accent.TButton"
        )
        self.submit_btn.pack(pady=5, fill=tk.X)

        # 右侧列表区（美化，布局不变）
        self.right_frame = ttk.Frame(self.main_content, style="Content.TFrame", padding=(10, 10))
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.list_label = ttk.Label(self.right_frame, text="Sentence List (Double-click to play)", style="Title.TLabel")
        self.list_label.pack(anchor=tk.W, pady=(0, 5))
        # 列表框美化（去掉 bordercolor）
        self.sentence_list = tk.Listbox(
            self.right_frame,
            height=28,
            width=60,
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#1F2937",
            bd=1,
            relief="solid",
            selectbackground="#DBEAFE",
            selectforeground="#1F2937",
            activestyle="none",
            highlightthickness=0
        )
        self.sentence_list.pack(fill=tk.BOTH, expand=True, pady=5)
        self.sentence_list.bind("<Double-Button-1>", self.play_single_sentence)

        # ====================== 等待弹窗（修复 ttk.Toplevel 错误，改用 tk.Toplevel） ======================
        self.wait_popup = tk.Toplevel(root)  # 关键修复：ttk 没有 Toplevel，用 tk.Toplevel
        self.wait_popup.title("Processing")
        self.wait_popup.geometry("320x110")
        self.wait_popup.attributes("-topmost", True)
        self.wait_popup.attributes("-toolwindow", True)
        self.wait_popup.withdraw()

        self.wait_frame = ttk.Frame(self.wait_popup, style="Content.TFrame", padding=(20, 20))
        self.wait_frame.pack(fill=tk.BOTH, expand=True)
        self.wait_label = ttk.Label(
            self.wait_frame,
            text="⏳ Generating audio...\nPlease wait a moment.",
            font=("Segoe UI", 10),
            justify=tk.CENTER
        )
        self.wait_label.pack(anchor=tk.CENTER)

        # ====================== 状态颜色配置 ======================
        self.status_colors = {
            "ready": "#166534",    # 就绪：深绿
            "playing": "#1E40AF",  # 播放：深蓝
            "paused": "#C2410C",   # 暂停：深橙
            "processing": "#4338CA",  # 处理：深紫
            "error": "#991B1B"     # 错误：深红
        }   
    def toggle_repeat_entry(self):
        """Enable/disable repeat times entry when infinite loop is checked"""
        if self.infinite_var.get():
            self.repeat_entry.config(state=tk.DISABLED)
        else:
            self.repeat_entry.config(state=tk.NORMAL)

    def get_interval(self):
        """Get repeat interval (default 500ms, auto-correct invalid input)"""
        try:
            interval = int(self.interval_var.get())
            return max(interval, 0)
        except:
            self.interval_var.set("500")
            return 500

    def on_mode_change(self):
        """Update button status and status display when play mode changes"""
        self.update_buttons()
        current_mode = "Single Sentence" if self.repeat_mode_var.get() == "single" else "Full Text"
        audio_status = "Available" if self.check_audio_available() else "Not Available"
        self.update_status(f"Status: Ready | Play Type: {current_mode} | Audio Status: {audio_status}")

    def check_audio_available(self):
        """Check if corresponding audio exists for current mode and voice"""
        current_mode = self.repeat_mode_var.get()
        if current_mode == "full":
            # 全文音频与当前发言人绑定，需重新生成
            return self.full_audio_path and os.path.exists(self.full_audio_path)
        else:
            # 单句音频与当前发言人+句子绑定，需重新生成
            return self.single_audio_path and os.path.exists(self.single_audio_path)

    # ====================== 核心修复：发言人切换逻辑 ======================
    def on_voice_change(self, event):
        """切换发言人时，彻底重置所有状态+解绑/重新绑定双击事件（解决单句播放残留问题）"""
        new_voice = self.voice_var.get()
        
        # 1. 选择相同发言人，不做任何操作（避免无效重置）
        if new_voice == self.selected_voice:
            return

        # 2. 临时解除断句列表的双击事件绑定（关键！避免残留事件触发play_single_sentence）
        self.sentence_list.unbind("<Double-Button-1>")

        # 3. 停止所有播放（包括暂停状态），避免旧音频继续播放
        if self.is_playing or self.is_paused:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False

        # 4. 彻底重置所有与音频/选中状态相关的变量（无遗漏）
        self.full_audio_path = None          # 重置全文音频路径
        self.single_audio_path = None        # 重置单句音频路径
        self.selected_single_text = ""       # 重置选中的单句文本
        self.selected_single_idx = -1        # 重置选中的单句索引（彻底清除选中状态）

        # 5. 更新当前发言人
        self.selected_voice = new_voice

        # 6. 清空断句列表（避免旧断句数据残留）
        self.sentence_list.delete(0, tk.END)
        # 清除列表选中状态（视觉上同步重置）
        self.sentence_list.selection_clear(0, tk.END)

        # 7. 重新绑定断句列表的双击事件（此时列表为空，误触会被后续校验拦截）
        self.sentence_list.bind("<Double-Button-1>", self.play_single_sentence)

        # 8. 更新按钮状态和状态栏（告知用户需重新生成音频）
        self.update_buttons()
        current_mode = "Single Sentence" if self.repeat_mode_var.get() == "single" else "Full Text"
        self.update_status(f"Status: Ready | Play Type: {current_mode} | Voice: {new_voice} | All data reset (re-generate required)")

        # 9. 弹出清晰提示，引导用户操作
        messagebox.showinfo(
            "Voice Changed Successfully",
            f"Switched to voice: {new_voice}\n\nImportant Notes:\n1. All previous audio files and sentence data are reset.\n2. Please click 'Process' to split text and generate full audio.\n3. Double-click a sentence in the list to generate single sentence audio."
        )

    # ====================== 文本处理逻辑 ======================
    def process_text(self):
    
        output_dir = "./tts_output"
        # 核心命令：先删除整个文件夹（含所有内容），再重建空文件夹（等价 rm -rf + mkdir）
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir, ignore_errors=True)  # ignore_errors=True → 强制删除，忽略所有错误（文件占用、不存在等）
        os.makedirs(output_dir, exist_ok=True)  # 重建空文件夹（exist_ok=True → 文件夹已存在也不报错）
        self.update_status(f"Cleared all files in {output_dir} (force delete)")
        
    # ====================================================================
        if self.is_processing:
            messagebox.showinfo("Info", "Processing is already in progress! Please wait.")
            return

        input_text = self.text_input.get("1.0", tk.END).strip()
        if not input_text:
            messagebox.showwarning("Warning", "Please enter text first before processing!")
            return

        # 重置相关状态
        if self.is_playing or self.is_paused:
            self.stop_audio()
        self.full_audio_path = None
        self.single_audio_path = None
        self.update_buttons()

        # 显示加载弹窗
        self.wait_popup.deiconify()
        self.root.update()

        self.is_processing = True
        self.submit_btn.config(state=tk.DISABLED, text="⏳ Processing...")
        self.update_status(f"Status: Processing | Play Type: Full Text | Voice: {self.selected_voice} | Splitting text...")
        self.root.update()

        try:
            # 1. 断句处理
            self.split_sentences(input_text)

            # 2. 生成全文音频（当前发言人）
            self.update_status(f"Status: Processing | Play Type: Full Text | Voice: {self.selected_voice} | Generating audio...")
            self.root.update()

            generate_success = asyncio.run(self.generate_full_audio(input_text))
            if not generate_success:
                raise Exception("Failed to generate valid audio file (file too small or corrupted)")

            # 3. 生成成功，自动切换回Full Text模式并播放（传入skip_warning=True跳过警告）
            self.repeat_mode_var.set("full")
            self.on_mode_change()
            repeat_info = "Infinite Loop" if self.infinite_var.get() else f"Repeat {self.repeat_count_var.get()} times"
            interval_info = f"Interval {self.get_interval()}ms"
            self.update_status(f"Status: Ready | Play Type: Full Text | Voice: {self.selected_voice} | Audio Generated Successfully | {repeat_info} | {interval_info}")
            self.submit_btn.config(state=tk.NORMAL, text="✅ Process (Split Text + Generate Audio)")
            self.update_buttons()
            self.play_audio(skip_warning=True)  # 关键修改：跳过警告框，直接播放
        except Exception as e:
            error_msg = str(e)
            self.update_status(f"Status: Error | Play Type: Full Text | Voice: {self.selected_voice} | Error: {error_msg}")
            self.submit_btn.config(state=tk.NORMAL, text="✅ Process (Split Text + Generate Audio)")
            messagebox.showerror("Processing Failed", f"Failed to process text:\n\n{error_msg}")
        finally:
            self.wait_popup.withdraw()
            self.is_processing = False

    def split_sentences(self, text):
        """Split Chinese text into sentences (without sequence numbers)"""
        self.sentence_list.delete(0, tk.END)
        # Split by Chinese sentence punctuation
        pattern = r'([^。！？；～]+[。！？；～])'
        sentences = re.findall(pattern, text.replace("\n", "").replace(" ", ""))
        # Add remaining text if any
        if not sentences or not text.strip().endswith(tuple("。！？；～")):
            remaining = re.sub(pattern, "", text.replace("\n", "").replace(" ", ""))
            if remaining:
                sentences.append(remaining)
        # Insert sentences into listbox
        for sentence in sentences:
            self.sentence_list.insert(tk.END, sentence)

    async def generate_full_audio(self, text):
        """Generate full text audio file for current voice"""
        try:
            output_dir = "./tts_output"
            os.makedirs(output_dir, exist_ok=True)
            # 文件名包含发言人标识，避免不同发言人音频混淆
            voice_tag = self.selected_voice.replace(" ", "_").replace("(", "").replace(")", "").replace(",", "")
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
            audio_path = f"{output_dir}/full_text_{voice_tag}_{timestamp}.mp3"

            # Generate TTS audio with current voice
            communicate = edge_tts.Communicate(
                text=text,
                voice=VOICE_DICT[self.selected_voice],
                rate="+0%",
                pitch="+0Hz",
                volume="+5%"
            )
            await communicate.save(audio_path)

            if os.path.getsize(audio_path) > 10 * 1024:
                self.full_audio_path = audio_path
                return True
            else:
                os.remove(audio_path)
                return False
        except Exception as e:
            print(f"Full audio generation error (Voice: {self.selected_voice}): {e}")
            return False

    # ====================== 单句播放逻辑（修复发言人绑定） ======================
    def play_single_sentence(self, event):
        # 校验1：如果正在处理中/状态未初始化，直接返回
        if self.is_processing or self.selected_voice == "":
            return

        # 校验2：断句列表为空（切换发言人后已清空），直接返回并提示
        if self.sentence_list.size() == 0:
            messagebox.showinfo("No Sentences", "No sentences available! Please click 'Process' first to split text.")
            return

        # 校验3：没有选中项，直接返回
        selected_idx = self.sentence_list.curselection()
        if not selected_idx:
            return
        """Play selected single sentence (for current voice) - 修复：重新生成对应发言人的单句音频"""
        if self.is_processing:
            messagebox.showinfo("Info", "Processing in progress, please wait!")
            return
        if self.is_playing:
            self.stop_audio()

        selected_idx = self.sentence_list.curselection()
        if not selected_idx:
            return
        self.selected_single_text = self.sentence_list.get(selected_idx)
        if not self.selected_single_text:
            messagebox.showwarning("Warning", "Selected sentence is invalid!")
            return

        # Switch to single sentence mode
        self.repeat_mode_var.set("single")
        self.update_status(f"Status: Processing | Play Type: Single Sentence | Generating audio... (Voice: {self.selected_voice})")
        self.root.update()

        async def generate_and_play():
            try:
                output_dir = "./tts_output/sentences"
                os.makedirs(output_dir, exist_ok=True)
                # 文件名包含发言人+句子标识，确保与当前发言人绑定
                voice_tag = self.selected_voice.replace(" ", "_").replace("(", "").replace(")", "").replace(",", "")
                sentence_tag = self.selected_single_text[:20].replace(" ", "_").replace("。", "").replace("！", "").replace("？", "")
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
                audio_path = f"{output_dir}/sentence_{voice_tag}_{sentence_tag}_{timestamp}.mp3"

                # Generate single sentence audio with current voice
                communicate = edge_tts.Communicate(
                    text=self.selected_single_text,
                    voice=VOICE_DICT[self.selected_voice],
                    rate="+0%",
                    pitch="+0Hz",
                    volume="+5%"
                )
                await communicate.save(audio_path)

                if os.path.getsize(audio_path) > 10 * 1024:
                    self.single_audio_path = audio_path
                    repeat_info = "Infinite Loop" if self.infinite_var.get() else f"Repeat {self.repeat_count_var.get()} times"
                    interval_info = f"Interval {self.get_interval()}ms"
                    self.update_status(f"Status: Ready | Play Type: Single Sentence | Audio Generated (Voice: {self.selected_voice}) | {repeat_info} | {interval_info}")
                    self.update_buttons()
                    self.play_audio()
                else:
                    os.remove(audio_path)
                    self.update_status(f"Status: Error | Play Type: Single Sentence | Failed to generate audio (Voice: {self.selected_voice})")
                    messagebox.showerror("Error", f"Failed to generate audio for selected sentence (Voice: {self.selected_voice})!")
            except Exception as e:
                self.update_status(f"Status: Error | Play Type: Single Sentence | {str(e)} (Voice: {self.selected_voice})")
                messagebox.showerror("Error", f"Failed to generate audio: {str(e)}")

        asyncio.run(generate_and_play())

    # ====================== 播放控制核心 ======================
    def update_buttons(self):
        """Update button status based on current mode, voice and audio availability"""
        has_audio = self.check_audio_available()

        if self.is_playing and not self.is_paused:
            self.play_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.NORMAL)
        elif self.is_paused:
            self.play_btn.config(state=tk.NORMAL if has_audio else tk.DISABLED, text="▶ Resume")
            self.pause_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
        else:
            self.play_btn.config(state=tk.NORMAL if has_audio else tk.DISABLED, text="▶ Play")
            self.pause_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)

    def update_status(self, status_text):
        """根据状态文本自动匹配颜色，更新状态栏"""
        # 清空之前的样式
        self.main_status.config(foreground="#333333")

        # 根据状态关键词匹配颜色
        if "Error" in status_text or "Failed" in status_text:
            # 错误状态：红色
            self.main_status.config(foreground=self.status_colors["error"])
        elif "Playing" in status_text:
            # 播放中：蓝色
            self.main_status.config(foreground=self.status_colors["playing"])
        elif "Paused" in status_text:
            # 暂停状态：橙色
            self.main_status.config(foreground=self.status_colors["paused"])
        elif "Processing" in status_text:
            # 处理中：靛蓝色
            self.main_status.config(foreground=self.status_colors["processing"])
        elif "Ready" in status_text:
            # 就绪状态：深绿色
            self.main_status.config(foreground=self.status_colors["ready"])

        # 更新状态文本
        self.main_status.config(text=status_text)

    def play_audio(self, skip_warning=False):  # 新增参数：是否跳过警告框
        """根据当前模式和发言人，播放对应的音频（支持跳过警告）"""
        current_mode = self.repeat_mode_var.get()
        current_voice = self.selected_voice

        # 检查音频是否存在
        if current_mode == "full":
            audio_path = self.full_audio_path
            # 校验逻辑：跳过警告时，直接使用已生成的路径；否则弹出警告
            if not skip_warning and (not audio_path or not os.path.exists(audio_path)):
                messagebox.showwarning("Audio Not Found", f"Full text audio for {current_voice} not found!\nPlease click 'Process' to generate first.")
                return
        else:
            audio_path = self.single_audio_path
            if not skip_warning and (not audio_path or not os.path.exists(audio_path)):
                messagebox.showwarning("Audio Not Found", f"Single sentence audio for {current_voice} not found!\nPlease double-click a sentence to generate first.")
                return

        # 验证音频路径（跳过警告时仍需确保路径有效，避免报错）
        if not audio_path or not os.path.exists(audio_path):
            return

        # 恢复播放
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.is_playing = True
            self.update_buttons()
            repeat_info = "Infinite Loop" if self.infinite_var.get() else f"Repeat {self.repeat_count_var.get()} times"
            interval_info = f"Interval {self.get_interval()}ms"
            self.update_status(f"Status: Playing | Play Type: {current_mode} | Voice: {current_voice} | {repeat_info} | {interval_info}")
            return

        # 开始新播放（异步线程）
        play_thread = threading.Thread(target=self.background_play, args=(audio_path, current_mode, current_voice))
        play_thread.daemon = True
        play_thread.start()

    def background_play(self, audio_path, play_mode, voice):
        """Background playback logic (bind to current voice)"""
        try:
            pygame.mixer.music.load(audio_path)
            self.is_playing = True
            self.is_paused = False
            self.update_buttons()

            # Get playback configuration
            infinite = self.infinite_var.get()
            repeat_times = int(self.repeat_count_var.get()) if not infinite else 1
            repeat_times = max(repeat_times, 1)
            interval = self.get_interval()

            # Update status
            mode_text = "Full Text" if play_mode == "full" else "Single Sentence"
            repeat_info = "Infinite Loop" if infinite else f"Repeat {repeat_times} times"
            interval_info = f"Interval {interval}ms"
            self.update_status(f"Status: Playing | Play Type: {mode_text} | Voice: {voice} | {repeat_info} | {interval_info}")

            # Play audio
            play_count = 0
            while self.is_playing and (infinite or play_count < repeat_times):
                if not self.is_paused:
                    pygame.mixer.music.play()
                    # Wait for playback completion
                    while pygame.mixer.music.get_busy() and self.is_playing and not self.is_paused:
                        pygame.time.Clock().tick(10)
                    
                    play_count += 1
                    # Add interval between repeats (not for last repeat)
                    if self.is_playing and not self.is_paused and (infinite or play_count < repeat_times):
                        pygame.time.wait(interval)
                else:
                    pygame.time.Clock().tick(10)

            # Playback completed
            if not self.is_paused:
                self.stop_audio()
                complete_info = "Infinite Loop Stopped" if infinite else f"Completed {repeat_times} repeats"
                self.update_status(f"Status: Completed | Play Type: {mode_text} | Voice: {voice} | {complete_info}")
        except Exception as e:
            messagebox.showerror("Error", f"Playback failed (Voice: {voice}): {str(e)}")
            self.stop_audio()
            self.update_status(f"Status: Error | Play Type: {mode_text} | Voice: {voice} | Playback failed: {str(e)}")

    def pause_audio(self):
        """Pause playback"""
        if not self.is_playing or self.is_paused:
            return

        pygame.mixer.music.pause()
        self.is_paused = True
        self.update_buttons()
        mode_text = "Full Text" if self.repeat_mode_var.get() == "full" else "Single Sentence"
        self.update_status(f"Status: Paused | Play Type: {mode_text} | Voice: {self.selected_voice} | Click 'Resume' to continue")

    def stop_audio(self):
        """Stop playback"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.update_buttons()
        mode_text = "Full Text" if self.repeat_mode_var.get() == "full" else "Single Sentence"
        self.update_status(f"Status: Ready | Play Type: {mode_text} | Voice: {self.selected_voice} | Playback Stopped")

if __name__ == "__main__":
    # Auto-install required packages
    required_packages = ["pygame", "edge-tts"]
    for pkg in required_packages:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            import subprocess
            import sys
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", pkg,
                "-i", "https://mirrors.aliyun.com/pypi/simple/"
            ])

    root = tk.Tk()
    app = EdgeTTS_GUI(root)
    root.mainloop()