# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata


project_root = Path(SPECPATH).parent
entry_script = project_root / "packaging" / "pyinstaller_gui.py"

datas = collect_data_files("aisrt", includes=["assets/*.svg"])
for package_name in (
    "aisrt",
    "qwen-asr",
    "PyQt6",
    "torch",
    "torchaudio",
    "transformers",
    "accelerate",
    "huggingface_hub",
    "safetensors",
    "tokenizers",
):
    try:
        datas += copy_metadata(package_name, recursive=True)
    except Exception:
        pass

hiddenimports = collect_submodules("aisrt")
try:
    hiddenimports += collect_submodules("qwen_asr")
except Exception:
    hiddenimports.append("qwen_asr")

a = Analysis(
    [str(entry_script)],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "tests"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AiSRT",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AiSRT",
)
