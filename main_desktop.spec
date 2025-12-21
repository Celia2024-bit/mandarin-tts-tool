# -*- mode: python ; coding: utf-8 -*-

import certifi
import os
import sys
import tkinter
from pathlib import Path
import logging

# ======================== 基础配置 ========================
# 启用打包日志（便于调试）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="pyinstaller_main.log"
)
logger = logging.getLogger(__name__)
block_cipher = None
app_name = "MandarinTTS"
entry_file = "main_desktop.py"  # 仅保留主程序入口
current_dir = os.path.dirname(os.path.abspath(SPECPATH))

# ---- 1. 基础数据收集 ----
# 1. 保留Windows默认路径：certifi/cacert.pem（保证Windows能找到）
datas = [(certifi.where(), "certifi")]
# 2. 追加macOS适配：根目录的cacert.pem（匹配macOS环境变量）
datas.append((certifi.where(), "cacert.pem"))

# 2. 打包项目核心目录（按需打包，不存在则跳过）
project_dirs = ["core", "interface", "platform_factory", "platforms"]
for dir_name in project_dirs:
    src_path = os.path.join(current_dir, dir_name)
    if os.path.isdir(src_path):
        datas.append((src_path, dir_name))
        logger.info(f"已添加打包目录：{dir_name}")
# 3. macOS：打包tk/tcl库（解决tkinter缺失）
if sys.platform == "darwin":
    def get_tk_tcl_paths():
        tk_root = Path(tkinter.__file__).parent
        # 适配macOS多版本Python的tk/tcl路径
        possible_paths = [
            (tk_root / "tk" / "tk8.6", "tk"),
            (tk_root / "tcl" / "tcl8.6", "tcl"),
            (Path("/opt/homebrew/lib/tk8.6"), "tk"),
            (Path("/opt/homebrew/lib/tcl8.6"), "tcl"),
            (Path("/usr/lib/tk8.6"), "tk"),
            (Path("/usr/lib/tcl8.6"), "tcl"),
        ]
        valid_paths = []
        for src, dest in possible_paths:
            if src.exists() and len(valid_paths) < 2:
                valid_paths.append((str(src), dest))
        return valid_paths

    tk_tcl_paths = get_tk_tcl_paths()
    for src, dest in tk_tcl_paths:
        datas.append((src, dest))
        logger.info(f"已添加tk/tcl库：{src} -> {dest}")

# ======================== 隐藏导入（跨平台兼容）========================
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
    hiddenimports.extend([
        "tkinter", "_tkinter", "tkinter.filedialog", "tkinter.ttk",
        "tkinter.font", "tkinter.messagebox", "Carbon", "AppKit",
        "aiohttp.client", "aiohttp.connector", "ssl", "cryptography"
    ])

# ---- 3. 执行分析 ----
a = Analysis(
    ['main_desktop.py'],
    pathex=[current_dir],
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

# ---- 4. 平台特定逻辑：Windows 做该做的事情，Mac 做该做的事情 ----

if sys.platform == "darwin":
    # --- macOS 流程 ---
    exe_kwargs = {
    "pyz": pyz,
    "scripts": a.scripts,
    "exclude_binaries": True,
    "name": app_name,
    "debug": False,
    "bootloader_ignore_signals": False,
    "strip": False if sys.platform == "darwin" else True,
    "upx": False if sys.platform == "darwin" else True,  # macOS禁用UPX
    "disable_windowed_traceback": True,
    "target_arch": None,
    "codesign_identity": None,
    "entitlements_file": None,
    "console": False,  # GUI应用隐藏控制台
    "argv_emulation": True if sys.platform == "darwin" else False  # macOS argv模拟
    }
    exe = EXE(**exe_kwargs)

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False if sys.platform == "darwin" else True,
        upx=False if sys.platform == "darwin" else True,
        upx_exclude=["libtk8.6.dylib", "libtcl8.6.dylib", "libssl.dylib", "libcrypto.dylib"],
        name='MandarinTTS',
    )

    app = BUNDLE(
        coll,
        name=f"{app_name}.app",
        icon=None,  # 替换为你的图标路径：'assets/icon.icns'
        bundle_identifier='com.mandarintts.app',
        version='1.0.0',
        info_plist={
            'CFBundleName': app_name,
            'CFBundleDisplayName': 'Mandarin TTS',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'NSRequiresAquaSystemAppearance': 'True',
            'LSEnvironment': {
                'TK_LIBRARY': '@executable_path/../Resources/tk',
                'TCL_LIBRARY': '@executable_path/../Resources/tcl',
                'SSL_CERT_FILE': '@executable_path/../Resources/cacert.pem',
                'REQUESTS_CA_BUNDLE': '@executable_path/../Resources/cacert.pem'
            },
            # 权限声明（按需删减）
            'NSDesktopFolderUsageDescription': 'MandarinTTS需要访问桌面以保存音频文件',
            'NSDownloadsFolderUsageDescription': 'MandarinTTS需要访问下载文件夹以保存音频文件',
            'APP_SANDBOX_ENABLED': 'NO'
        }
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