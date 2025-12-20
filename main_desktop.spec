# -*- mode: python ; coding: utf-8 -*-

import certifi
import os

block_cipher = None

# ---- 打包 certifi 证书 ----
datas = [
    (certifi.where(), "certifi"),
]

# ---- 打包你的整个项目结构 ----
project_dirs = [
    ("core", "core"),
    ("interface", "interface"),
    ("platform_factory", "platform_factory"),
    ("platforms", "platforms"),
]

for src, dest in project_dirs:
    if os.path.isdir(src):
        datas.append((src, dest))

# ---- PyInstaller 无法自动收集的依赖 ----
hiddenimports = [
    "edge_tts",
    "aiohttp",
    "asyncio",
    "pygame",
    "baidu_aip",
    "certifi",
    "chardet",

    # setuptools 依赖
    "pkg_resources",
    "jaraco",
    "jaraco.functools",
    "jaraco.text",
    "jaraco.context",
    "jaraco.collections",
    "jaraco.classes",

    # 你要求加入的
    "appdirs",
    "platformdirs",
]

a = Analysis(
    ['main_desktop.py'],   # 你的唯一入口
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    console=False,   # GUI 程序必须关闭 console
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
