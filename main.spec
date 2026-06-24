# -*- mode: python ; coding: utf-8 -*-

import glob
import os

block_cipher = None

spec_dir = os.path.dirname(os.path.abspath(SPEC))
png_files = [(f, '.') for f in glob.glob(os.path.join(spec_dir, '*.png'))]
png_files += [(f, '.') for f in glob.glob(os.path.join(spec_dir, '*.PNG'))]
font_files = [(f, '.') for f in glob.glob(os.path.join(spec_dir, '*.ttf'))]
datas = png_files + font_files + [
    (os.path.join(spec_dir, 'images'), 'images'),
]

a = Analysis(
    ['main.py'],
    pathex=[spec_dir],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
