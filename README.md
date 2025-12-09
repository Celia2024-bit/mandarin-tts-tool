# Mandarin TTS Tool — Cross‑Platform Architecture

This document explains the folder structure, responsibilities, and run targets for the desktop and mobile builds. The goal is to **cleanly separate interfaces (abstract bases), core logic, platform implementations**, and a minimal factory for audio playback.

## Folder Layout

```
your_repo/
├─ interface/
│  ├─ audio_player_base.py   # Abstract audio player contract
│  ├─ ui_base.py             # Abstract UI contract (default controller forwards)
│  └─ __init__.py
│
├─ core/
│  ├─ app_controller.py      # Business/state, orchestrates TTS and player
│  ├─ tts_engine.py          # TTS + cache naming (edge-tts/Azure SDK interchangeable)
│  └─ __init__.py
│
├─ platforms/
│  ├─ desktop/
│  │  ├─ tkinter_ui.py       # UIBase implementation (Tkinter)
│  │  ├─ audio_player_desktop.py  # pygame implementation
│  │  └─ __init__.py
│  └─ mobiles/
│     ├─ audio_player_android.py  # Android stub/MediaPlayer impl
│     ├─ audio_player_ios.py      # iOS stub/AVAudioPlayer impl
│     └─ __init__.py
│
├─ platform_factory/
│  ├─ audio_player_impl.py   # create_audio_player() — lazy import & platform detect
│  └─ __init__.py
│
├─ main_desktop.py           # Desktop entrypoint (Tkinter)
├─ main_mobile.py            # Mobile entrypoint (Kivy/BeeWare placeholder)
└─ README.md                 # This file
```

> Put **empty `__init__.py`** into every package folder above. You may optionally re-export common classes from `__init__.py` to simplify imports.

## Imports (after the refactor)

- **Factory & controller**
  
  ```python
  # core/app_controller.py
  from platform_factory.audio_player_impl import create_audio_player
  from interface.audio_player_base import AudioPlayerBase
  ```
- **Desktop UI**
  
  ```python
  # platforms/desktop/tkinter_ui.py
  from core.app_controller import AppController
  from interface.ui_base import UIBase
  ```
- **Platform players**
  
  ```python
  from interface.audio_player_base import AudioPlayerBase
  ```

## How the layers talk

- `TkinterUI` / `MobileUI` inherit **`UIBase`** and bind user events to default controller‑forwarding methods (e.g. `on_click_process`, `on_change_voice`).
- `AppController` exposes four callbacks to UI: `on_status`, `on_sentences_ready`, `on_buttons_update`, `on_mode_change`.
- `AppController` composes `TTSEngine` for **split + synth** and the **AudioPlayer** created by `create_audio_player()`.
- `create_audio_player()` determines platform at runtime and **lazy imports** `PygameAudioPlayer` / `AndroidAudioPlayer` / `IOSAudioPlayer`.

## Run targets

### Desktop (Tkinter)

```bash
python main_desktop.py
# or
python -m main_desktop
```

### Mobile (Android/iOS)

Use `main_mobile.py` as your starter. Replace `YourMobileUI` with a real Kivy/BeeWare UI class and hook it to `UIBase` methods. The audio factory returns the right player implementation.

## Caching & files

- `tts_engine.py` produces `audio_cache/full_*.mp3|.wav` and `audio_cache/single_*.mp3|.wav`.
- Always treat cache hit as **exists AND size >= threshold** to avoid false positives when an upstream service returns empty bytes.
- If `pygame.mixer.music.load()` rejects MP3 (tags/stream), consider a **WAV fallback** (via ffmpeg) or synthesize **WAV directly**.

## Switching TTS backends

- Current engine uses `edge-tts`; you can swap to **Azure Speech SDK** for higher stability and direct MP3/WAV output formats. SDK lets you set output format with `SpeechSynthesisOutputFormat` and synthesize via SSML.
- Pricing & free tier notes are on Azure’s official pages; plan your usage with the pricing calculator and free quotas.

## Design principles

- **Interface segregation**: `interface/` holds contracts; `core/` depends only on contracts.
- **Lazy imports & platform detection**: in factory to avoid importing desktop libs on mobile.
- **No cyclic imports**: UI files never imported by controller; controller only receives UI callbacks.
- **Single source of truth**: `AppController` owns state (voice, repeat, speed, playing flags) and updates UI via callbacks.

## Next steps

- Implement real Android/iOS players (MediaPlayer / AVAudioPlayer) in `platforms/mobiles`.
- Replace `YourMobileUI` with Kivy/BeeWare screens and wire controls to `UIBase`.
- Add tests for `TTSEngine` cache naming + `AppController` state transitions.

---

### Mermaid diagram

See **`app_logic_all_plateform.mmd`** for a visual overview of the architecture.
