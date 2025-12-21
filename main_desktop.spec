# -*- mode: python ; coding: utf-8 -*-

import certifi
import os
import sys

block_cipher = None

# ---- 1. 基础数据收集 ----
datas = [
    (certifi.where(), "certifi"),
]

project_dirs = [
    ("core", "core"),
    ("interface", "interface"),
    ("platform_factory", "platform_factory"),
    ("platforms", "platforms"),
]

for src, dest in project_dirs:
    if os.path.isdir(src):
        datas.append((src, dest))

# ---- 2. 隐藏导入 (修正了列表逗号) ----
hiddenimports = [
    "edge_tts", 
    "aiohttp", 
    "asyncio", 
    "pygame", 
    "certifi", 
    "chardet",
    "pkg_resources",
    "jaraco",
    "jaraco.functools",
    "jaraco.text",
    "jaraco.context",
    "jaraco.collections",
    "jaraco.classes",
    "appdirs",
    "platformdirs"
]

if sys.platform == "win32":
    hiddenimports.append("baidu_aip")
elif sys.platform == "darwin":
    hiddenimports.extend(["tkinter", "_tkinter"])

# ---- 3. 执行分析 ----
a = Analysis(
    ['main_desktop.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ---- 4. 平台特定逻辑：Windows 做该做的事情，Mac 做该做的事情 ----

if sys.platform == "darwin":
    # --- macOS 流程 ---
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='MandarinTTS',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=True,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='MandarinTTS',
    )

    app = BUNDLE(
        coll,
        name='MandarinTTS.app',
        icon=None,
        bundle_identifier='com.mandarintts.app',
        version='1.0.0',
        info_plist={
            'CFBundleName': 'MandarinTTS',
            'CFBundleDisplayName': 'Mandarin TTS',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'LSMinimumSystemVersion': '10.13.0',
        },
    )

else:
    # --- Windows 流程 ---
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='MandarinTTS',
        console=False,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        name='MandarinTTS',
    )