# main_desktop.py
# === Global SSL monkey patch for edge-tts + aiohttp ===
import ssl
import certifi

def patched_create_default_context(*args, **kwargs):
    """
    强制所有 HTTPS 请求使用 certifi 的 CA 证书。
    这是 edge-tts 在 PyInstaller 打包后仍然能正常验证 SSL 的关键。
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations(certifi.where())
    return ctx

# 覆盖默认 SSL context（aiohttp / edge-tts 会自动用它）
ssl.create_default_context = patched_create_default_context


"""
Desktop entry point for Mandarin TTS Tool.
Loads Tkinter UI from platforms/desktop and starts the event loop.
"""

from platforms.desktop.tkinter_ui import TkinterUI

if __name__ == "__main__":
    ui = TkinterUI()
    ui.run()
