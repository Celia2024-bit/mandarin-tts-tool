# -*- coding:utf-8 -*-
"""
Core business logic package.
Platform-agnostic components.
"""

from .app_controller import AppController, AppConfig, AppState, PlayMode, PlayState
from .tts_engine import TTSEngine
from .ocr_engine import OCREngine
from .audio_player import create_audio_player, AudioPlayerBase

__all__ = [
    'AppController',
    'AppConfig', 
    'AppState',
    'PlayMode',
    'PlayState',
    'TTSEngine',
    'OCREngine',
    'create_audio_player',
    'AudioPlayerBase'
]