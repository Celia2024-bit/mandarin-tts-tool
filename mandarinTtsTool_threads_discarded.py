import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import re
import shutil
import asyncio
import threading
import pygame
import datetime
from tts_engine import TTSEngine  # Import external TTS engine
from ocr_engine import OCREngine  # Import external OCR engine

# Speaker dictionary (consistent with tts_engine)
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

        # ====================== Core Style Configuration ======================
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Accent button (Process) style
        self.style.configure(
            "Accent.TButton",
            font=("Segoe UI", 10, "bold"),
            foreground="#FFFFFF",
            background="#2563EB",
            padding=(12, 6),
            borderwidth=0,
            relief="flat",
            borderradius=4
        )
        self.style.map(
            "Accent.TButton",
            background=[("active", "#1D4ED8"), ("pressed", "#1E40AF")],
            relief=[("active", "flat"), ("pressed", "flat")]
        )

        # Regular button (Play/Pause/Stop) style
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

        # Label style
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

        # Input box/dropdown style
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

        # Frame style (input area/list area)
        self.style.configure(
            "Content.TFrame",
            background="#FFFFFF",
            borderwidth=1,
            relief="solid",
            bordercolor="#E5E7EB",
            borderradius=6
        )

        # Status box style
        self.style.configure(
            "Status.TFrame",
            background="#F9FAFB",
            borderwidth=1,
            relief="solid",
            bordercolor="#E5E7EB"
        )

        # ====================== Core Variable Definition ======================
        self.full_audio_path = None
        self.single_audio_path = None
        self.selected_single_text = ""
        self.selected_single_idx = -1
        self.selected_voice = "Mandarin Female (Xiaoyi)"
        self.is_playing = False
        self.is_paused = False
        self.is_processing = False
        self.is_batch_processing = False  # Batch processing status flag
        self.infinite_var = tk.BooleanVar(value=False)
        self.is_batch_processing = False 
        
        # Initialize engines
        self.tts_engine = TTSEngine()
        self.ocr_engine = OCREngine()  # Initialize OCR engine

        # Initialize player
        pygame.mixer.init()

        # ====================== Configuration Area (beautified, layout unchanged) ======================
        self.config_frame = ttk.Frame(root, padding=(5, 8))
        self.config_frame.pack(fill=tk.X, padx=10, pady=5)

        # Speaker
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
        
        # Speed control
        self.speed_label = ttk.Label(self.config_frame, text="Speed:", font=("Segoe UI", 10))
        self.speed_label.pack(side=tk.LEFT, padx=(20, 3))
        self.speed_var = tk.StringVar(value="0")  # Default normal speed
        self.speed_slider = ttk.Scale(
            self.config_frame,
            from_=-50,  # 50% slower
            to=100,     # 100% faster
            orient=tk.HORIZONTAL,
            length=120,
            variable=self.speed_var,
            command=self.on_speed_change
        )
        self.speed_slider.pack(side=tk.LEFT, padx=3)
        self.speed_value_label = ttk.Label(self.config_frame, text="0%", font=("Segoe UI", 9), width=5)
        self.speed_value_label.pack(side=tk.LEFT, padx=3)

        # Playback buttons
        self.play_btn = ttk.Button(self.config_frame, text="▶ Play", command=self.play_audio, state=tk.DISABLED)
        self.play_btn.pack(side=tk.LEFT, padx=3)
        self.pause_btn = ttk.Button(self.config_frame, text="⏸ Pause", command=self.pause_audio, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=3)
        self.stop_btn = ttk.Button(self.config_frame, text="■ Stop", command=self.stop_audio, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=3)

        # Playback mode
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

        # Repeat and interval
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

        # ====================== Status Area (beautified, layout unchanged) ======================
        self.status_frame = ttk.Frame(root, style="Status.TFrame", padding=(5, 3))
        self.status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # OCR button (newly added)
        self.ocr_btn = ttk.Button(
            self.status_frame,
            text="Select Image for OCR",
            command=self.select_image_for_ocr
        )
        self.ocr_btn.pack(side=tk.RIGHT, padx=(40, 5))
        
        self.main_status = ttk.Label(
            self.status_frame,
            text="Status: Ready | No Audio Generated | OCR: Ready",
            padding=(5, 2),
            font=("Segoe UI", 9)
        )
        self.main_status.pack(side=tk.LEFT)

        # ====================== Main Content Area (maintain stable layout, only beautify) ======================
        self.main_content = ttk.Frame(root)
        self.main_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left input area (beautified, layout unchanged)
        self.left_frame = ttk.Frame(self.main_content, style="Content.TFrame", padding=(10, 10))
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.text_label = ttk.Label(self.left_frame, text="Input Chinese Text", style="Title.TLabel")
        self.text_label.pack(anchor=tk.W, pady=(0, 5))
        # Input box beautification
        self.text_input = scrolledtext.ScrolledText(
            self.left_frame,
            height=25,
            width=60,
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#1F2937",
            bd=1,  # Border width
            relief="solid",  # Solid border
            highlightthickness=0,
            selectbackground="#DBEAFE",  # Selected background color
            selectforeground="#1F2937"
        )
        self.text_input.pack(fill=tk.BOTH, expand=True, pady=5)
        default_text = """这是一个高质量的普通话TTS工具，支持全文朗读和单句播放功能。
用户可以输入任意中文文本，点击处理按钮即可完成断句和音频生成。
切换不同的发音人后，需要重新生成音频才能生效。
支持重复播放、无限循环和自定义播放间隔，操作简单易用。
新增OCR功能：可以从图片中提取文字并转换为语音。"""
        self.text_input.insert(tk.END, default_text)

        # Process button (accent style)
        self.submit_btn = ttk.Button(
            self.left_frame,
            text="Process Text & Generate Audio",
            command=self.process_text,
            style="Accent.TButton"
        )
        self.submit_btn.pack(pady=5, fill=tk.X)

        # Right list area (beautified, layout unchanged)
        self.right_frame = ttk.Frame(self.main_content, style="Content.TFrame", padding=(10, 10))
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.list_label = ttk.Label(self.right_frame, text="Sentence List (Double-click to play)", style="Title.TLabel")
        self.list_label.pack(anchor=tk.W, pady=(0, 5))
        # List box beautification
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

        # ====================== Waiting Popup ======================
        self.wait_popup = tk.Toplevel(root)
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

        # ====================== Status Color Configuration ======================
        self.status_colors = {
            "ready": "#166534",    # Ready: dark green
            "playing": "#1E40AF",  # Playing: dark blue
            "paused": "#C2410C",   # Paused: dark orange
            "processing": "#4338CA",  # Processing: dark purple
            "error": "#991B1B"     # Error: dark red
        }   
        
    # ====================== Basic Function Methods ======================
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
        ocr_status = "Ready"
        self.update_status(f"Status: Ready | Play Type: {current_mode} | Audio Status: {audio_status} | OCR: {ocr_status}")
        
    def on_speed_change(self, value):
        """Update speed display when slider moves and auto-regenerate if needed"""
        speed_val = int(float(value))
        self.speed_var.set(str(speed_val))
        self.speed_value_label.config(text=f"{speed_val:+d}%")
        
        # Stop playback if audio is currently playing
        if self.is_playing or self.is_paused:
            self.stop_audio()
        
        # If there was audio before, auto-regenerate with new speed
        had_full_audio = self.full_audio_path is not None
        had_single_audio = self.single_audio_path is not None
        
        # Invalidate old audio
        self.full_audio_path = None
        self.single_audio_path = None
        self.update_buttons()
        
        mode_text = "Full Text" if self.repeat_mode_var.get() == "full" else "Single Sentence"
        ocr_status = "Ready"
        
        # Auto-regenerate if user had generated audio before
        if had_full_audio and self.text_input.get("1.0", tk.END).strip():
            self.update_status(f"Status: Processing | Speed: {speed_val:+d}% | Auto-regenerating full audio... | OCR: {ocr_status}")
            self.root.after(1000, self.process_text)  # Trigger regeneration after UI updates
        elif had_single_audio and self.selected_single_text:
            self.update_status(f"Status: Ready | Speed: {speed_val:+d}% | Double-click sentence to regenerate | OCR: {ocr_status}")
        else:
            self.update_status(f"Status: Ready | Play Type: {mode_text} | Speed: {speed_val:+d}% | Click 'Process' to generate audio | OCR: {ocr_status}")
        
    def check_audio_available(self):
        """Check if corresponding audio exists for current mode and voice"""
        current_mode = self.repeat_mode_var.get()
        if current_mode == "full":
            return self.full_audio_path and os.path.exists(self.full_audio_path)
        else:
            return self.single_audio_path and os.path.exists(self.single_audio_path)

    def on_voice_change(self, event):
        """When switching speakers, completely reset all states + unbind/re-bind double-click event"""
        new_voice = self.voice_var.get()
        
        # 1. If selecting the same speaker, do nothing
        if new_voice == self.selected_voice:
            return

        # 2. Temporarily unbind double-click event from sentence list
        self.sentence_list.unbind("<Double-Button-1>")

        # 3. Stop all playback
        if self.is_playing or self.is_paused:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False

        # 4. Completely reset all variables related to audio/selection status
        self.full_audio_path = None          
        self.single_audio_path = None        
        self.selected_single_text = ""       
        self.selected_single_idx = -1        
        self.speed_var.set("0")
        self.speed_value_label.config(text="0%")
        self.speed_slider.set(0)

        # 5. Update current speaker
        self.selected_voice = new_voice

        # 6. Clear sentence list
        self.sentence_list.delete(0, tk.END)
        self.sentence_list.selection_clear(0, tk.END)

        # 7. Rebind double-click event for sentence list
        self.sentence_list.bind("<Double-Button-1>", self.play_single_sentence)

        # 8. Update button status and status bar
        self.update_buttons()
        current_mode = "Single Sentence" if self.repeat_mode_var.get() == "single" else "Full Text"
        ocr_status = "Ready"
        self.update_status(f"Status: Ready | Play Type: {current_mode} | Voice: {new_voice} | All data reset (re-generate required) | OCR: {ocr_status}")

        # 9. Pop up prompt
        messagebox.showinfo(
            "Voice Changed Successfully",
            f"Switched to voice: {new_voice}\n\nImportant Notes:\n1. All previous audio files and sentence data are reset.\n2. Please click 'Process' to split text and generate full audio.\n3. Double-click a sentence in the list to generate single sentence audio."
        )
        
        self.speed_var.set("0")
        self.speed_value_label.config(text="0%")
        self.speed_slider.set(0)

    # ====================== OCR Functionality (fully updated) ======================
    def select_image_for_ocr(self):
        """Select image and call OCREngine for text recognition"""
        # Disable key buttons
        self.ocr_btn.config(state=tk.DISABLED, text="⏳ Processing...")
        self.submit_btn.config(state=tk.DISABLED)  # Disable Process button
        self.play_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        
        if not file_path:
            # Restore button states
            self.ocr_btn.config(state=tk.NORMAL, text="Select Image for OCR")
            self.submit_btn.config(state=tk.NORMAL)
            return
            
        self.update_status("Status: Processing | Recognizing text from image... | OCR: Processing")
        self.root.update()
        
        # Define OCR processing thread
        def ocr_thread_func():
            try:
                # Call external OCR engine
                result_text = self.ocr_engine.ocr_image(file_path)
                
                # Process recognition result
                if result_text.startswith(("Error:", "Warning:")):
                    self.root.after(0, lambda: self.update_status(f"Status: Error | {result_text} | OCR: Failed"))
                    self.root.after(0, lambda: messagebox.showwarning("Recognition Result", result_text))
                else:
                    # Clear existing text and insert recognition result
                    self.root.after(0, lambda: self.text_input.delete("1.0", tk.END))
                    self.root.after(0, lambda: self.text_input.insert(tk.END, result_text))
                    # Count valid lines
                    filtered_lines = [line.strip() for line in result_text.split('\n') if line.strip()]
                    self.root.after(0, lambda: self.update_status(
                        f"Status: Ready | Recognition completed, total {len(filtered_lines)} lines | OCR: Success"
                    ))
                    
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"Status: Error | OCR failed: {str(e)} | OCR: Error"))
                self.root.after(0, lambda: messagebox.showerror("Recognition Error", f"Text recognition failed: {str(e)}"))
            
            finally:
                # Restore all button states
                self.root.after(0, lambda: self.ocr_btn.config(state=tk.NORMAL, text="Select Image for OCR"))
                self.root.after(0, lambda: self.submit_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.update_buttons())

        # Start OCR thread
        ocr_thread = threading.Thread(target=ocr_thread_func, daemon=True)
        ocr_thread.start()

    # ====================== Text Processing Logic (fully updated) ======================
    def process_text(self):
        output_dir = "./audio_cache"
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir, ignore_errors=True)
        os.makedirs(output_dir, exist_ok=True)
        self.update_status(f"Cleared all files in {output_dir} (force delete)")
        
        if self.is_processing:
            messagebox.showinfo("Info", "Processing is already in progress! Please wait.")
            return

        input_text = self.text_input.get("1.0", tk.END).strip()
        if not input_text:
            messagebox.showwarning("Warning", "Please enter text first before processing!")
            return

        # Reset state and disable buttons
        if self.is_playing or self.is_paused:
            self.stop_audio()
        self.full_audio_path = None
        self.single_audio_path = None
        self.update_buttons()
        
        # Disable related buttons
        self.submit_btn.config(state=tk.DISABLED, text="⏳ Processing...")
        self.play_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        self.ocr_btn.config(state=tk.DISABLED)
        self.voice_combobox.config(state=tk.DISABLED)
        self.speed_slider.config(state=tk.DISABLED)
        self.single_radio.config(state=tk.DISABLED)
        self.full_radio.config(state=tk.DISABLED)
        self.infinite_check.config(state=tk.DISABLED)
        self.repeat_entry.config(state=tk.DISABLED)
        self.interval_entry.config(state=tk.DISABLED)
        self.text_input.config(state=tk.DISABLED)

        self.is_processing = True
        self.update_status(f"Status: Processing | Play Type: Full Text | Voice: {self.selected_voice} | Splitting text...")
        self.root.update()

        # Initialize TTS engine
        tts_engine = TTSEngine()
        current_voice = VOICE_DICT[self.selected_voice]
        current_speed = int(float(self.speed_var.get()))
        
        # After successful generation, set sentence list state to "processing"
        self.is_batch_processing = True
        self.update_sentence_list_state(disabled=True)   # Disable list clicks and change color

        # Define second thread: batch generate single sentence audio
        def batch_process_thread():
            try:
                # Wait for first thread to complete (ensure sentence_list is populated)
                while not hasattr(self, 'sentence_list_data'):
                    time.sleep(0.1)
                
                # Call tts-engine's batch generation method
                asyncio.run(tts_engine.process_all_sentences(
                    self.sentence_list_data,  # Sentence list obtained from first thread
                    current_voice,
                    current_speed
                ))
                print("Batch processing of all sentences completed")
            except Exception as e:
                print(f"Batch processing error: {str(e)}")
            finally:
                self.is_batch_processing = False
                self.root.after(0, lambda: self.update_sentence_list_state(disabled=False))
                # Restore button states and auto-play
                self.root.after(0, lambda: self.submit_btn.config(state=tk.NORMAL, text="✅ Process (Split Text + Generate Audio)"))
                self.root.after(0, lambda: self.update_buttons())
                self.root.after(0, lambda: self.play_audio(skip_warning=True))
                pass

        # Define first thread: generate full text audio
        def main_process_thread():
            try:
                # Call tts-engine's full text generation method
                audio_path, sentences = tts_engine.generate_full_audio(
                    input_text,
                    current_voice,
                    current_speed
                )

                if audio_path.startswith("Error"):
                    raise Exception(audio_path)

                # Save sentence list for later use
                self.sentence_list_data = sentences
                self.sentence_list.delete(0, tk.END)
                for sentence in sentences:
                    self.sentence_list.insert(tk.END, sentence)

                # Save full text audio path
                self.full_audio_path = audio_path

                # Enable playback control buttons after first thread completes
                self.root.after(0, lambda: self.update_buttons())
                self.root.after(0, lambda: self.play_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.pause_btn.config(state=tk.NORMAL))  # Additional enable pause button
                self.root.after(0, lambda: self.stop_btn.config(state=tk.NORMAL))

                # Start second thread: batch generate single sentence audio (run in background)
                batch_thread = threading.Thread(target=batch_process_thread)
                batch_thread.daemon = True
                batch_thread.start()

                # Update status
                self.root.after(0, lambda: self.repeat_mode_var.set("full"))
                self.root.after(0, self.on_mode_change)
                repeat_info = "Infinite Loop" if self.infinite_var.get() else f"Repeat {self.repeat_count_var.get()} times"
                interval_info = f"Interval {self.get_interval()}ms"
                self.root.after(0, lambda: self.update_status(
                    f"Status: Ready | Play Type: Full Text | Voice: {self.selected_voice} | Audio Generated Successfully | {repeat_info} | {interval_info}"))
                
                # Core modification: Auto-play after first thread completes (skip warning)
                #self.root.after(0, lambda: self.play_audio(skip_warning=True))

            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self.update_status(
                    f"Status: Error | Play Type: Full Text | Voice: {self.selected_voice} | Error: {error_msg}"))
                self.root.after(0, lambda: messagebox.showerror("Processing Failed", f"Failed to process text:\n\n{error_msg}"))
            
            finally:
                # Restore button states
                self.is_processing = False
                self.root.after(0, lambda: self.submit_btn.config(state=tk.NORMAL, text="✅ Process (Split Text + Generate Audio)"))
                self.root.after(0, lambda: self.ocr_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.voice_combobox.config(state="readonly"))
                self.root.after(0, lambda: self.speed_slider.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.single_radio.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.full_radio.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.infinite_check.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.repeat_entry.config(state=tk.NORMAL if not self.infinite_var.get() else tk.DISABLED))
                self.root.after(0, lambda: self.interval_entry.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.text_input.config(state=tk.NORMAL))

        # Start main processing thread
        main_thread = threading.Thread(target=main_process_thread)
        main_thread.daemon = True
        main_thread.start()
    

    # ====================== Sentence List State Management ======================
    def update_sentence_list_state(self, disabled):
        """Update sentence list clickable state and display style"""
        if disabled:
            # Disabled state: gray text + cannot select
            for i in range(self.sentence_list.size()):
                self.sentence_list.itemconfig(i, fg="#9CA3AF")  # Gray text
            self.sentence_list.unbind("<Double-Button-1>")  # Unbind double-click event
            self.update_status(f"Status: Processing | Pre-generating all sentences (please wait)... | OCR: Ready")
        else:
            # Enabled state: black text + restore click
            for i in range(self.sentence_list.size()):
                self.sentence_list.itemconfig(i, fg="#1F2937")  # Normal text
            self.sentence_list.bind("<Double-Button-1>", self.play_single_sentence)  # Rebind event
            current_mode = "Single Sentence" if self.repeat_mode_var.get() == "single" else "Full Text"
            self.update_status(f"Status: Ready | Play Type: {current_mode} | All sentences ready for playback | OCR: Ready")

    # ====================== Single Sentence Playback Logic (fully updated) ======================
    def play_single_sentence(self, event):
        # Check 1: Batch processing in progress, disable clicks
        if self.is_batch_processing:
            messagebox.showinfo("Processing", "Please wait for all sentences to be pre-generated!")
            return

        # Check 2: If processing in progress/state not initialized, return directly
        if self.is_processing or self.selected_voice == "":
            return

        # Check 3: Sentence list is empty, return directly and prompt
        if self.sentence_list.size() == 0:
            messagebox.showinfo("No Sentences", "No sentences available! Please click 'Process' first to split text.")
            return

        # Check 4: No selected item, return directly
        selected_idx = self.sentence_list.curselection()
        if not selected_idx:
            return
        
        selected_idx = selected_idx[0]
            
        if self.is_processing:
            messagebox.showinfo("Info", "Processing in progress, please wait!")
            return
            
        if self.is_playing:
            self.stop_audio()

        # Cancel previous selection highlight
        if self.selected_single_idx != -1:
            self.sentence_list.itemconfig(self.selected_single_idx, bg="white", fg="#1F2937")
        
        # Set current selection highlight
        self.selected_single_idx = selected_idx
        self.sentence_list.itemconfig(selected_idx, bg="#DBEAFE", fg="#1E40AF")  # Blue highlight
        
        self.selected_single_text = self.sentence_list.get(selected_idx)
        if not self.selected_single_text:
            messagebox.showwarning("Warning", "Selected sentence is invalid!")
            return

        # Disable playback control buttons
        self.play_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)

        # Switch to single sentence mode
        self.repeat_mode_var.set("single")
        ocr_status = "Ready"
        self.update_status(f"Status: Processing | Play Type: Single Sentence | Generating audio... (Voice: {self.selected_voice}) | OCR: {ocr_status}")
        self.root.update()

        # Define single sentence audio generation thread
        def single_tts_thread_func():
            try:
                # Get current configuration
                current_voice = VOICE_DICT[self.selected_voice]
                current_speed = int(float(self.speed_var.get()))
                
                # Call external TTS engine to generate single sentence audio
                audio_path = self.tts_engine.generate_single_sentence_audio(
                    self.selected_single_text,
                    current_voice,
                    current_speed
                )

                if audio_path.startswith("Error"):
                    raise Exception(audio_path)

                if os.path.getsize(audio_path) > 10 * 1024:
                    self.single_audio_path = audio_path
                    repeat_info = "Infinite Loop" if self.infinite_var.get() else f"Repeat {self.repeat_count_var.get()} times"
                    interval_info = f"Interval {self.get_interval()}ms"
                    self.root.after(0, lambda: self.update_status(
                        f"Status: Ready | Play Type: Single Sentence | Audio Generated (Voice: {self.selected_voice}) | {repeat_info} | {interval_info} | OCR: {ocr_status}"
                    ))
                    # Enable playback control buttons and auto-play
                    self.root.after(0, self.update_buttons)
                    self.root.after(0, lambda: self.play_audio(skip_warning=True))
                else:
                    os.remove(audio_path)
                    self.root.after(0, lambda: self.update_status(
                        f"Status: Error | Play Type: Single Sentence | Failed to generate audio (Voice: {self.selected_voice}) | OCR: {ocr_status}"
                    ))
                    self.root.after(0, lambda: messagebox.showerror(
                        "Error", 
                        f"Failed to generate audio for selected sentence (Voice: {self.selected_voice})!"
                    ))
            except Exception as e:
                self.root.after(0, lambda: self.update_status(
                    f"Status: Error | Play Type: Single Sentence | {str(e)} (Voice: {self.selected_voice}) | OCR: {ocr_status}"
                ))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to generate audio: {str(e)}"))
            finally:
                # Ensure button states are restored
                self.root.after(0, self.update_buttons)

        # Start single sentence audio generation thread
        single_tts_thread = threading.Thread(target=single_tts_thread_func, daemon=True)
        single_tts_thread.start()

    # ====================== Playback Control Core ======================
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
        """Automatically match colors based on status text and update the status bar"""
        # Clear previous styles
        self.main_status.config(foreground="#333333")

        # Match colors based on status keywords
        if "Error" in status_text or "Failed" in status_text:
            # Error status: red
            self.main_status.config(foreground=self.status_colors["error"])
        elif "Playing" in status_text:
            # Playing status: blue
            self.main_status.config(foreground=self.status_colors["playing"])
        elif "Paused" in status_text:
            # Paused status: orange
            self.main_status.config(foreground=self.status_colors["paused"])
        elif "Processing" in status_text:
            # Processing status: indigo
            self.main_status.config(foreground=self.status_colors["processing"])
        elif "Ready" in status_text:
            # Ready status: dark green
            self.main_status.config(foreground=self.status_colors["ready"])

        # Update status text
        self.main_status.config(text=status_text)

    def play_audio(self, skip_warning=False):
        """Play corresponding audio according to current mode and voice"""
        current_mode = self.repeat_mode_var.get()
        current_voice = self.selected_voice

        # Check if audio exists
        if current_mode == "full":
            audio_path = self.full_audio_path
            # Validation logic
            if not skip_warning and (not audio_path or not os.path.exists(audio_path)):
                messagebox.showwarning("Audio Not Found", f"Full text audio for {current_voice} not found!\nPlease click 'Process' to generate first.")
                return
        else:
            audio_path = self.single_audio_path
            if not skip_warning and (not audio_path or not os.path.exists(audio_path)):
                messagebox.showwarning("Audio Not Found", f"Single sentence audio for {current_voice} not found!\nPlease double-click a sentence to generate first.")
                return

        # Verify audio path
        if not audio_path or not os.path.exists(audio_path):
            return

        # Resume playback
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.is_playing = True
            self.update_buttons()
            repeat_info = "Infinite Loop" if self.infinite_var.get() else f"Repeat {self.repeat_count_var.get()} times"
            interval_info = f"Interval {self.get_interval()}ms"
            ocr_status = "Ready"
            self.update_status(f"Status: Playing | Play Type: {current_mode} | Voice: {current_voice} | {repeat_info} | {interval_info} | OCR: {ocr_status}")
            return

        # Start new playback (asynchronous thread)
        play_thread = threading.Thread(target=self.background_play, args=(audio_path, current_mode, current_voice))
        play_thread.daemon = True
        play_thread.start()

    def background_play(self, audio_path, play_mode, voice):
        """Background playback logic"""
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
            ocr_status = "Ready"
            self.update_status(f"Status: Playing | Play Type: {mode_text} | Voice: {voice} | {repeat_info} | {interval_info} | OCR: {ocr_status}")

            # Play audio
            play_count = 0
            while self.is_playing and (infinite or play_count < repeat_times):
                if not self.is_paused:
                    pygame.mixer.music.play()
                    # Wait for playback completion
                    while pygame.mixer.music.get_busy() and self.is_playing and not self.is_paused:
                        pygame.time.Clock().tick(10)
                    
                    play_count += 1
                    # Add interval between repeats
                    if self.is_playing and not self.is_paused and (infinite or play_count < repeat_times):
                        pygame.time.wait(interval)
                else:
                    pygame.time.Clock().tick(10)

            # Playback completed
            if not self.is_paused:
                self.stop_audio()
                complete_info = "Infinite Loop Stopped" if infinite else f"Completed {repeat_times} repeats"
                self.update_status(f"Status: Completed | Play Type: {mode_text} | Voice: {voice} | {complete_info} | OCR: {ocr_status}")
        except Exception as e:
            messagebox.showerror("Error", f"Playback failed (Voice: {voice}): {str(e)}")
            self.stop_audio()
            self.update_status(f"Status: Error | Play Type: {mode_text} | Voice: {voice} | Playback failed: {str(e)} | OCR: {ocr_status}")

    def pause_audio(self):
        """Pause playback"""
        if not self.is_playing or self.is_paused:
            return

        pygame.mixer.music.pause()
        self.is_paused = True
        self.update_buttons()
        mode_text = "Full Text" if self.repeat_mode_var.get() == "full" else "Single Sentence"
        ocr_status = "Ready"
        self.update_status(f"Status: Paused | Play Type: {mode_text} | Voice: {self.selected_voice} | Click 'Resume' to continue | OCR: {ocr_status}")

    def stop_audio(self):
        """Stop playback"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.update_buttons()
        mode_text = "Full Text" if self.repeat_mode_var.get() == "full" else "Single Sentence"
        ocr_status = "Ready"
        self.update_status(f"Status: Ready | Play Type: {mode_text} | Voice: {self.selected_voice} | Playback Stopped | OCR: {ocr_status}")

if __name__ == "__main__":
    # Automatically install required packages
    required_packages = ["pygame", "edge-tts", "requests"]
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