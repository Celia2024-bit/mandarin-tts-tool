# -*- mode: python ; coding: utf-8 -*-

import certifi
import os
import sys

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
    "platformdirs",
]

# 只在 Windows 平台添加 baidu_aip
if sys.platform == "win32":
    hiddenimports.append("baidu_aip")

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

# ---- Windows 用 EXE ----
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MandarinTTS',
    console=False,
)

# ---- macOS 用 BUNDLE(生成 .app)----
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name='MandarinTTS.app',
        icon=None,
        bundle_identifier=None,
    )

# ---- COLLECT ----
if sys.platform == "darwin":
    # macOS: 收集到 app 内部
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        name='MandarinTTS',
    )
else:
    # Windows: 正常收集
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        name='MandarinTTS',
    )