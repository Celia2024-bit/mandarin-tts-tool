
# -*- coding: utf-8 -*-
"""
AppController: 负责在用户点击按钮后的各类操作逻辑（不含界面）。
依赖：
- audio_player.create_audio_player / AudioPlayerBase
- tts_engine.TTSEngine  （需用户自备实现）
- ocr_engine.OCREngine  （需用户自备实现）
"""
import os
import threading
import asyncio
from typing import List, Optional, Callable

from platform_factory.audio_player_impl import create_audio_player
from interface.audio_player_base import AudioPlayerBase

from .tts_engine import TTSEngine                              # 外部模块
from .ocr_engine import OCREngine                              # 外部模块

VOICE_DICT = {
    "Mandarin Female (Xiaoyi)": "zh-CN-XiaoyiNeural",
    "Mandarin Female (Xiaoxiao)": "zh-CN-XiaoxiaoNeural",
    "Mandarin Female (Yunxi)": "zh-CN-YunxiNeural",
    "Mandarin Male (Yunjian)": "zh-CN-YunjianNeural",
    "Mandarin Female (Lingling)": "zh-CN-LinglingNeural",
    "Northeast Mandarin Female": "zh-CN-Liaoning-XiaobeiNeural",
}

class AppController:
    """
    将界面事件委托到此控制器：
    - 文本处理（拆句、生成整段与单句音频）
    - 音频播放控制（play/pause/resume/stop）
    - OCR 图片识别
    - 维护运行状态，向 UI 回调通知（状态文本、按钮使能、列表内容等）
    """
    def __init__(self,
                 on_status: Callable[[str], None],
                 on_sentences_ready: Callable[[List[str]], None],
                 on_buttons_update: Callable[[bool, bool, bool], None],
                 on_mode_change: Callable[[str], None],
                 on_ocr_result: Callable[[str], None]):
        # 回调到 UI
        self._on_status = on_status
        self._on_sentences_ready = on_sentences_ready
        self._on_buttons_update = on_buttons_update  # (play_enabled, pause_enabled, stop_enabled)
        self._on_mode_change = on_mode_change        # 'full' / 'single'
        self._on_ocr_result = on_ocr_result

        # 引擎
        self.tts_engine = TTSEngine(clear_cache_on_start=True)
        self.ocr_engine = OCREngine()
        self.player: AudioPlayerBase = create_audio_player()

        # 状态变量
        self.selected_voice_ui: str = "Mandarin Female (Xiaoyi)"
        self.speed_percent: int = 0
        self.repeat_mode: str = 'full'         # 'full' 或 'single'
        self.infinite_loop: bool = False
        self.repeat_count: int = 1
        self.interval_ms: int = 500

        self.is_processing: bool = False
        self.is_batch_processing: bool = False
        self.is_playing: bool = False
        self.is_paused: bool = False

        # 数据
        self.sentences: List[str] = []
        self.full_audio_path: Optional[str] = None
        self.single_audio_path: Optional[str] = None
        self.selected_single_text: str = ''
        self.selected_single_idx: int = -1
        
        self._on_ocr_result = on_ocr_result
        
    def get_voice_names(self): return list(VOICE_DICT.keys())

    # ---------------- Configuration -----------------
    def set_voice(self, ui_voice_name: str):
        self.selected_voice_ui = ui_voice_name
        self._on_status(f"Status: Ready Voice changed -> {ui_voice_name} Re-generate required")
        # 切换说话人时清理之前的音频状态
        self.stop_audio()
        self.full_audio_path = None
        self.single_audio_path = None
        self.sentences = []
        self.selected_single_text = ''
        self.selected_single_idx = -1
        self.speed_percent = 0
        self._on_mode_change(self.repeat_mode)
        self._update_buttons()

    def set_speed(self, percent: int):
        self.speed_percent = percent
        # 改速后旧音频失效
        self.full_audio_path = None
        self.single_audio_path = None
        if self.is_playing or self.is_paused:
            self.stop_audio()
        self._on_status(f"Status: Ready Speed: {percent:+d}% Click 'Process' to regenerate")
        self._update_buttons()

    def set_repeat_config(self, mode: str, infinite: bool, count: int, interval_ms: int):
        self.repeat_mode = mode  # 'full'/'single'
        self.infinite_loop = infinite
        self.repeat_count = max(1, int(count)) if not infinite else 1
        self.interval_ms = max(0, int(interval_ms))
        self._on_mode_change(self.repeat_mode)
        self._update_buttons()

    # ---------------- OCR -----------------
    def ocr_image(self, file_path: str):
        """后台线程进行 OCR，完毕后把结果文本交由 UI。"""
        def _work():
            try:
                self._on_status("Status: Processing Recognizing text from image...")
                result = self.ocr_engine.ocr_image(file_path)
                
                if result.startswith(("Error:", "Warning:")):
                    self._on_status(f"Status: Error {result} OCR: Failed")
                else:
                    # 1. 修复 split 错误：改用 splitlines() 或 split('\n')
                    lines = result.splitlines() 
                    filtered = [ln.strip() for ln in lines if ln.strip()]
                    
                    if self._on_ocr_result:
                        self._on_ocr_result(result)
                    
                    self._on_status(f"Status: Ready Recognition completed, total {len(filtered)} lines OCR: Success")
                    
            except Exception as e:
                # 这里的 e 现在会捕捉到正确的错误信息
                self._on_status(f"Status: Error OCR failed: {str(e)}")
            finally:
                self._update_buttons()

        threading.Thread(target=_work, daemon=True).start()
        

    # ---------------- Processing (Split & TTS) -----------------
    def process_text(self, input_text: str, auto_play: bool = False):
        if self.is_processing:
            self._on_status("Status: Processing Already running, please wait...")
            return
        input_text = (input_text or '').strip()
        if not input_text:
            self._on_status("Status: Error Please enter text first")
            return

        self.is_processing = True
        self.stop_audio()
        self.full_audio_path = None
        self.single_audio_path = None
        self._update_buttons()

        current_voice = VOICE_DICT.get(self.selected_voice_ui, VOICE_DICT["Mandarin Female (Xiaoyi)"])
        current_speed = int(self.speed_percent)

        def _batch_thread():
            try:
                # 等待句子列表准备好
                while not self.sentences:
                    import time; time.sleep(0.1)
                asyncio.run(self.tts_engine.process_all_sentences(self.sentences, current_voice, current_speed))
            finally:
                self.is_batch_processing = False
                self._update_buttons()

        def _main_thread():
            try:
                self._on_status(f"Status: Processing Play Type: Full TextVoice: {self.selected_voice_ui} Splitting text...")
                audio_path, sentences = self.tts_engine.generate_full_audio(input_text, current_voice, current_speed)
                if str(audio_path).startswith("Error"):
                    raise Exception(audio_path)
                self.sentences = sentences or []
                self._on_sentences_ready(self.sentences)
                self.full_audio_path = audio_path
                self._on_status(f"Status: Ready Play Type: Full Text Voice: {self.selected_voice_ui} Audio Generated Successfully")
                # 开二线程做单句批量生成
                self.is_batch_processing = True
                threading.Thread(target=_batch_thread, daemon=True).start()
                self._update_buttons()
                if auto_play and self.full_audio_path:
                    self._on_status("Status: Processing | Generation complete, starting playback...")
                    # 稍微延迟一下确保文件句柄释放（可选）
                    self.play_audio()
            except Exception as e:
                self._on_status(f"Status: Error Play Type: Full Text Voice: {self.selected_voice_ui} Error: {e}")
            finally:
                self.is_processing = False
                self._update_buttons()

        threading.Thread(target=_main_thread, daemon=True).start()

    # ---------------- Single sentence -----------------
    def generate_single_sentence(self, sentence: str, idx: int):
        if self.is_batch_processing or self.is_processing:
            self._on_status("Status: Processing Please wait for tasks to finish...")
            return
        if not sentence:
            self._on_status("Status: Error Selected sentence is invalid")
            return
        self.selected_single_text = sentence
        self.selected_single_idx = idx
        self.repeat_mode = 'single'
        self._on_mode_change(self.repeat_mode)
        self._on_status(f"Status: Processing Play Type: Single Sentence Generating audio... (Voice: {self.selected_voice_ui})")

        def _work():
            try:
                current_voice = VOICE_DICT.get(self.selected_voice_ui, VOICE_DICT["Mandarin Female (Xiaoyi)"])
                current_speed = int(self.speed_percent)
                audio_path = self.tts_engine.generate_single_sentence_audio(
                    self.selected_single_text, current_voice, current_speed)
                if str(audio_path).startswith("Error"):
                    raise Exception(audio_path)
                # 简单体积检查由外部决定，这里只保存路径
                self.single_audio_path = audio_path
                self._on_status(f"Status: Ready Play Type: Single Sentence Audio Generated (Voice: {self.selected_voice_ui})")
                self.play_audio(skip_warning=True)
            except Exception as e:
                self._on_status(f"Status: Error Play Type: Single Sentence {e} (Voice: {self.selected_voice_ui})")
            finally:
                self._update_buttons()
        threading.Thread(target=_work, daemon=True).start()

    # ---------------- Playback -----------------
    def play_audio(self, skip_warning: bool=False):
        mode = self.repeat_mode
        audio_path = self.full_audio_path if mode == 'full' else self.single_audio_path
        if not audio_path or not os.path.exists(audio_path):
            if not skip_warning:
                self._on_status(f"Status: Error Audio not found for {mode}")
            return
        
        # 定义完成回调
        def on_playback_complete():
            self.is_playing = False
            self.is_paused = False
            self._on_status(
                f"Status: Completed Play Type: {'Full Text' if mode=='full' else 'Single Sentence'} "
                f"Voice: {self.selected_voice_ui}")
            self._update_buttons()
        
        # 使用抽象播放器进行循环控制
        self.is_paused = False
        self.is_playing = True
        self.player.play(
            audio_path,
            repeat_count=(-1 if self.infinite_loop else self.repeat_count),
            interval_ms=self.interval_ms,
            on_complete=on_playback_complete
        )
        self._on_status(
            f"Status: Playing Play Type: {'Full Text' if mode=='full' else 'Single Sentence'} "
            f"Voice: {self.selected_voice_ui} "
            f"Repeat: {'Infinite' if self.infinite_loop else self.repeat_count} | Interval: {self.interval_ms}ms"
        )
        self._update_buttons()    

    def pause_audio(self):
        if not self.is_playing or self.is_paused:
            return
        self.player.pause()
        self.is_paused = True
        self._on_status(f"Status: Paused Play Type: {'Full Text' if self.repeat_mode=='full' else 'Single Sentence'} Voice: {self.selected_voice_ui}")
        self._update_buttons()

    def resume_audio(self):
        if not self.is_paused:
            return
        self.player.resume()
        self.is_paused = False
        self._on_status(f"Status: Playing Play Type: {'Full Text' if self.repeat_mode=='full' else 'Single Sentence'} Voice: {self.selected_voice_ui}")
        self._update_buttons()

    def stop_audio(self):
        try:
            self.player.stop()
        except Exception:
            pass
        self.is_playing = False
        self.is_paused = False
        self._on_status(f"Status: Ready Play Type: {'Full Text' if self.repeat_mode=='full' else 'Single Sentence'} Voice: {self.selected_voice_ui} Playback Stopped")
        self._update_buttons()

    # ---------------- internal -----------------
    def _update_buttons(self):
        has_audio = False
        if self.repeat_mode == 'full':
            has_audio = bool(self.full_audio_path and os.path.exists(self.full_audio_path))
        else:
            has_audio = bool(self.single_audio_path and os.path.exists(self.single_audio_path))
        play_enabled = has_audio and (not self.is_playing or self.is_paused)
        pause_enabled = self.is_playing and not self.is_paused
        stop_enabled = self.is_playing
        self._on_buttons_update(play_enabled, pause_enabled, stop_enabled)
