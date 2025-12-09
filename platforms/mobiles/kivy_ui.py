# -*- coding:utf-8 -*-
"""
Kivy UI Adapter - connects the platform-agnostic controller to Kivy UI.
This template shows how to build the same app for mobile (Android/iOS).

Installation for mobile:
- Android: buildozer + python-for-android
- iOS: kivy-ios + Xcode

Note: This is a template showing the architecture - you'll need to:
1. Install Kivy: pip install kivy
2. Adapt the layout to your needs
3. Test on actual devices using buildozer (Android) or kivy-ios
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.clock import Clock, mainthread
from kivy.core.window import Window

import threading
from pathlib import Path

# Import core business logic (same as desktop!)
# from core.app_controller import AppController, PlayMode, PlayState
# from core.tts_engine import TTSEngine
# from core.ocr_engine import OCREngine
# from core.audio_player import create_audio_player


class SentenceListItem(BoxLayout):
    """Custom widget for each sentence in the list"""
    
    def __init__(self, text, index, on_tap_callback, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 60
        self.padding = [10, 5]
        
        self.index = index
        self.on_tap = on_tap_callback
        
        # Index label
        index_label = Label(
            text=f"[{index + 1}]",
            size_hint_x=0.15,
            font_size='14sp'
        )
        self.add_widget(index_label)
        
        # Sentence text button (tappable)
        self.text_btn = Button(
            text=text,
            size_hint_x=0.85,
            font_size='15sp',
            halign='left',
            valign='middle',
            text_size=(None, None),
            background_normal='',
            background_color=(0.2, 0.6, 0.9, 1)
        )
        self.text_btn.bind(on_press=self._on_press)
        self.add_widget(self.text_btn)
    
    def _on_press(self, instance):
        if self.on_tap:
            self.on_tap(self.index)


class KivyUI(BoxLayout):
    """
    Main UI layout for Kivy mobile app.
    Architecture mirrors the tkinter adapter but uses Kivy widgets.
    """
    
    def __init__(self, controller, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        
        # Register controller callbacks
        self._register_controller_callbacks()
        
        # Build UI sections
        self._build_header()
        self._build_controls()
        self._build_text_input()
        self._build_sentence_list()
        self._build_status_bar()
        
        # Loading popup (created but not shown)
        self.loading_popup = None
        
        # Initial state update
        self._on_state_changed(self.controller.state)
    
    def _register_controller_callbacks(self):
        """Register callbacks with controller"""
        self.controller.register_callback('on_state_changed', self._on_state_changed_safe)
        self.controller.register_callback('on_sentences_updated', self._on_sentences_updated_safe)
        self.controller.register_callback('on_status_update', self._on_status_update_safe)
        self.controller.register_callback('on_error', self._on_error_safe)
        self.controller.register_callback('on_processing_start', self._on_processing_start_safe)
        self.controller.register_callback('on_processing_end', self._on_processing_end_safe)
    
    # Thread-safe callback wrappers (Kivy requires UI updates on main thread)
    @mainthread
    def _on_state_changed_safe(self, state):
        self._on_state_changed(state)
    
    @mainthread
    def _on_sentences_updated_safe(self, sentences):
        self._on_sentences_updated(sentences)
    
    @mainthread
    def _on_status_update_safe(self, message):
        self._on_status_update(message)
    
    @mainthread
    def _on_error_safe(self, error):
        self._on_error(error)
    
    @mainthread
    def _on_processing_start_safe(self):
        self._on_processing_start()
    
    @mainthread
    def _on_processing_end_safe(self, success):
        self._on_processing_end(success)
    
    # ==================== UI Construction ====================
    
    def _build_header(self):
        """Build app header"""
        header = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=10)
        
        title = Label(
            text='Mandarin TTS Tool',
            font_size='24sp',
            bold=True,
            size_hint_x=0.7
        )
        header.add_widget(title)
        
        # OCR button
        self.ocr_btn = Button(
            text='📷 OCR',
            size_hint_x=0.3,
            font_size='16sp',
            background_color=(0.3, 0.7, 0.3, 1)
        )
        self.ocr_btn.bind(on_press=lambda x: self._on_ocr_clicked())
        header.add_widget(self.ocr_btn)
        
        self.add_widget(header)
    
    def _build_controls(self):
        """Build control panel with voice, speed, playback controls"""
        controls = GridLayout(cols=2, size_hint_y=0.25, spacing=5, padding=5)
        
        # Row 1: Voice selection
        controls.add_widget(Label(text='Voice:', size_hint_x=0.3))
        self.voice_spinner = Spinner(
            text=self.controller.state.config.voice,
            values=self.controller.get_available_voices(),
            size_hint_x=0.7
        )
        self.voice_spinner.bind(text=self._on_voice_changed)
        controls.add_widget(self.voice_spinner)
        
        # Row 2: Speed control
        controls.add_widget(Label(text='Speed:', size_hint_x=0.3))
        speed_box = BoxLayout(orientation='horizontal', size_hint_x=0.7)
        self.speed_slider = Slider(min=-50, max=100, value=0, step=5)
        self.speed_slider.bind(value=self._on_speed_changed)
        self.speed_label = Label(text='0%', size_hint_x=0.3)
        speed_box.add_widget(self.speed_slider)
        speed_box.add_widget(self.speed_label)
        controls.add_widget(speed_box)
        
        # Row 3: Playback controls
        controls.add_widget(Label(text='Controls:', size_hint_x=0.3))
        playback_box = BoxLayout(orientation='horizontal', size_hint_x=0.7, spacing=5)
        
        self.play_btn = Button(text='▶', font_size='20sp')
        self.play_btn.bind(on_press=lambda x: self.controller.play_audio())
        playback_box.add_widget(self.play_btn)
        
        self.pause_btn = Button(text='⏸', font_size='20sp')
        self.pause_btn.bind(on_press=lambda x: self.controller.pause_audio())
        playback_box.add_widget(self.pause_btn)
        
        self.stop_btn = Button(text='⏹', font_size='20sp')
        self.stop_btn.bind(on_press=lambda x: self.controller.stop_audio())
        playback_box.add_widget(self.stop_btn)
        
        controls.add_widget(playback_box)
        
        # Row 4: Repeat settings
        controls.add_widget(Label(text='Repeat:', size_hint_x=0.3))
        repeat_box = BoxLayout(orientation='horizontal', size_hint_x=0.7, spacing=5)
        
        self.repeat_input = TextInput(
            text='1',
            input_filter='int',
            multiline=False,
            size_hint_x=0.3
        )
        repeat_box.add_widget(self.repeat_input)
        
        self.infinite_check = CheckBox(size_hint_x=0.2)
        self.infinite_check.bind(active=self._on_repeat_config_changed)
        repeat_box.add_widget(self.infinite_check)
        repeat_box.add_widget(Label(text='Loop', size_hint_x=0.3))
        
        self.interval_input = TextInput(
            text='500',
            input_filter='int',
            multiline=False,
            size_hint_x=0.2
        )
        repeat_box.add_widget(self.interval_input)
        
        controls.add_widget(repeat_box)
        
        self.add_widget(controls)
    
    def _build_text_input(self):
        """Build text input area with process button"""
        text_section = BoxLayout(orientation='vertical', size_hint_y=0.35, spacing=5)
        
        text_section.add_widget(Label(
            text='Input Chinese Text:',
            size_hint_y=0.1,
            font_size='16sp',
            bold=True,
            halign='left'
        ))
        
        # Text input
        self.text_input = TextInput(
            text='这是一个高质量的普通话TTS工具。\n支持全文朗读和单句播放功能。',
            multiline=True,
            font_size='16sp',
            size_hint_y=0.7
        )
        text_section.add_widget(self.text_input)
        
        # Process button
        self.process_btn = Button(
            text='Process Text & Generate Audio',
            size_hint_y=0.2,
            font_size='18sp',
            background_color=(0.2, 0.6, 0.9, 1),
            bold=True
        )
        self.process_btn.bind(on_press=lambda x: self._on_process_clicked())
        text_section.add_widget(self.process_btn)
        
        self.add_widget(text_section)
    
    def _build_sentence_list(self):
        """Build scrollable sentence list"""
        list_section = BoxLayout(orientation='vertical', size_hint_y=0.27, spacing=5)
        
        list_section.add_widget(Label(
            text='Sentences (Tap to play):',
            size_hint_y=0.15,
            font_size='16sp',
            bold=True,
            halign='left'
        ))
        
        # Scrollable list container
        scroll = ScrollView(size_hint_y=0.85)
        self.sentence_list_layout = GridLayout(
            cols=1,
            spacing=5,
            size_hint_y=None
        )
        self.sentence_list_layout.bind(minimum_height=self.sentence_list_layout.setter('height'))
        
        scroll.add_widget(self.sentence_list_layout)
        list_section.add_widget(scroll)
        
        self.add_widget(list_section)
    
    def _build_status_bar(self):
        """Build status bar"""
        self.status_label = Label(
            text='Status: Ready',
            size_hint_y=0.05,
            font_size='14sp',
            color=(0.7, 0.7, 0.7, 1),
            halign='left'
        )
        self.add_widget(self.status_label)
    
    # ==================== Event Handlers ====================
    
    def _on_voice_changed(self, spinner, text):
        """Handle voice change"""
        changed = self.controller.set_voice(text)
        if changed:
            self._show_info("Voice Changed", f"Switched to {text}. Please re-process text.")
    
    def _on_speed_changed(self, slider, value):
        """Handle speed slider"""
        speed = int(value)
        self.speed_label.text = f"{speed:+d}%"
        self.controller.set_speed(speed)
    
    def _on_repeat_config_changed(self, checkbox, value):
        """Handle repeat configuration change"""
        try:
            repeat = int(self.repeat_input.text) if not self.infinite_check.active else 1
            interval = int(self.interval_input.text)
            self.controller.set_repeat_config(
                repeat_count=repeat,
                infinite=self.infinite_check.active,
                interval_ms=interval
            )
            
            # Disable repeat input when infinite is checked
            self.repeat_input.disabled = self.infinite_check.active
        except ValueError:
            pass
    
    def _on_ocr_clicked(self):
        """Handle OCR button - would open file picker on mobile"""
        # On Android: use plyer or android APIs to pick image
        # On iOS: use similar native picker
        # For now, show placeholder
        self._show_info("OCR", "OCR feature requires platform-specific file picker integration.\nUse plyer library or native APIs.")
    
    def _on_process_clicked(self):
        """Handle process button"""
        text = self.text_input.text.strip()
        
        def process_task():
            self.controller.process_text(text)
        
        threading.Thread(target=process_task, daemon=True).start()
    
    def _on_sentence_tapped(self, index):
        """Handle sentence tap"""
        def select_task():
            success = self.controller.select_sentence(index)
            if success:
                # Auto-play after generation
                Clock.schedule_once(lambda dt: self.controller.play_audio(), 0.1)
        
        threading.Thread(target=select_task, daemon=True).start()
    
    # ==================== Controller Callbacks ====================
    
    def _on_state_changed(self, state):
        """Update UI based on controller state"""
        can_play = self.controller.can_play()
        
        from core.app_controller import PlayState
        
        # Update button states
        if state.play_state == PlayState.PLAYING:
            self.play_btn.disabled = True
            self.pause_btn.disabled = False
            self.stop_btn.disabled = False
        elif state.play_state == PlayState.PAUSED:
            self.play_btn.disabled = False
            self.play_btn.text = '▶ Resume'
            self.pause_btn.disabled = True
            self.stop_btn.disabled = False
        else:
            self.play_btn.disabled = not can_play
            self.play_btn.text = '▶'
            self.pause_btn.disabled = True
            self.stop_btn.disabled = True
        
        self.process_btn.disabled = (state.play_state == PlayState.PROCESSING)
    
    def _on_sentences_updated(self, sentences):
        """Update sentence list"""
        self.sentence_list_layout.clear_widgets()
        
        for i, sentence in enumerate(sentences):
            item = SentenceListItem(
                text=sentence,
                index=i,
                on_tap_callback=self._on_sentence_tapped
            )
            self.sentence_list_layout.add_widget(item)
    
    def _on_status_update(self, message):
        """Update status label"""
        self.status_label.text = f"Status: {message}"
    
    def _on_error(self, error):
        """Show error popup"""
        self._show_error("Error", error)
    
    def _on_processing_start(self):
        """Show loading popup"""
        if not self.loading_popup:
            content = BoxLayout(orientation='vertical', padding=20, spacing=20)
            content.add_widget(Label(text='⏳ Generating audio...', font_size='18sp'))
            content.add_widget(Label(text='Please wait', font_size='14sp'))
            
            self.loading_popup = Popup(
                title='Processing',
                content=content,
                size_hint=(0.8, 0.3),
                auto_dismiss=False
            )
        
        self.loading_popup.open()
    
    def _on_processing_end(self, success):
        """Hide loading popup"""
        if self.loading_popup:
            self.loading_popup.dismiss()
        
        if success:
            # Auto-play after successful processing
            Clock.schedule_once(lambda dt: self.controller.play_audio(), 0.1)
    
    # ==================== Helper Methods ====================
    
    def _show_info(self, title, message):
        """Show info popup"""
        content = BoxLayout(orientation='vertical', padding=20, spacing=20)
        content.add_widget(Label(text=message, font_size='16sp'))
        close_btn = Button(text='OK', size_hint_y=0.3)
        content.add_widget(close_btn)
        
        popup = Popup(title=title, content=content, size_hint=(0.9, 0.4))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def _show_error(self, title, message):
        """Show error popup"""
        self._show_info(title, message)


class MandarinTTSApp(App):
    """
    Main Kivy application class.
    This is the entry point for mobile platforms.
    """
    
    def build(self):
        """Build and return the root widget"""
        # Import core components
        from core.app_controller import AppController
        from core.tts_engine import TTSEngine
        from core.ocr_engine import OCREngine
        from core.audio_player import create_audio_player
        
        # Initialize engines
        tts_engine = TTSEngine()
        ocr_engine = OCREngine()
        audio_player = create_audio_player()
        
        # Create controller
        self.controller = AppController(tts_engine, ocr_engine, audio_player)
        
        # Create and return UI
        return KivyUI(controller=self.controller)
    
    def on_stop(self):
        """Cleanup when app closes"""
        self.controller.cleanup()
        return True


# ==================== Entry Point ====================

if __name__ == '__main__':
    MandarinTTSApp().run()


# ==================== Buildozer Spec Notes ====================
"""
For Android deployment, create a buildozer.spec file:

[app]
title = Mandarin TTS Tool
package.name = mandarintts
package.domain = com.yourdomain
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 1.0
requirements = python3,kivy,edge-tts,pygame,baidu-aip
permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
orientation = portrait
android.api = 31
android.minapi = 21

[buildozer]
log_level = 2
warn_on_root = 1

Then run: buildozer android debug
"""