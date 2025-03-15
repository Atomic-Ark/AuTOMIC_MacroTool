# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for AuTOMIC MacroTool.
Copyright (c) 2025 AtomicArk
"""

import os
import sys
from pathlib import Path

block_cipher = None

# Get project root
project_root = Path(SPECPATH)

# Resource files
resource_files = [
    # Language files
    ('src/resources/langs/*.json', 'resources/langs'),
    # Icons
    ('src/resources/icons/*', 'resources/icons'),
    # Themes
    ('src/resources/themes/*', 'resources/themes'),
    # Documentation
    ('LICENSE', '.'),
    ('README.md', '.'),
]

# Collect data files
datas = []
for src_pattern, dst_dir in resource_files:
    src_path = project_root / src_pattern
    for file_path in Path(src_path.parent).glob(src_path.name):
        datas.append((str(file_path), dst_dir))

# Hidden imports
hidden_imports = [
    # Core dependencies
    'win32api',
    'win32con',
    'win32gui',
    'win32process',
    'keyboard',
    'mouse',
    'pynput',
    'interception',
    'psutil',
    'darkdetect',
    'packaging',
    'requests',
    # Qt plugins
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtNetwork',
    'PyQt6.sip',
]

# Binary dependencies
binaries = []

# Qt plugins to include
qt_plugins = [
    'platforms',
    'platformthemes',
    'styles',
    'imageformats',
    'iconengines',
]

# Add Qt plugins to binaries
import PyQt6
qt_path = os.path.dirname(PyQt6.__file__)
for plugin in qt_plugins:
    plugin_path = os.path.join(qt_path, 'Qt6', 'plugins', plugin)
    if os.path.exists(plugin_path):
        binaries.extend([(os.path.join(plugin_path, file), os.path.join('PyQt6', 'Qt6', 'plugins', plugin))
                        for file in os.listdir(plugin_path) if file.endswith('.dll')])

a = Analysis(
    ['src/main.py'],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Exclude unnecessary Qt modules and debug files
def exclude_from_analysis(analysis):
    excludes = [
        'Qt6Pdf',
        'Qt6Quick',
        'Qt6Qml',
        'Qt6WebEngine',
        'Qt6Designer',
        'libGLESv2',
        'libEGL',
        'd3dcompiler',
        'opengl32sw',
    ]
    
    analysis.binaries = [(name, path, type)
                        for name, path, type in analysis.binaries
                        if not any(exclude in name for exclude in excludes)]
    
    return analysis

a = exclude_from_analysis(a)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AuTOMIC_MacroTool',
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
    version='version_info.txt',
    icon='src/resources/icons/app.ico',
    uac_admin=True,
)

# Create additional files for distribution
dist_dir = os.path.join('dist', 'standalone')
os.makedirs(dist_dir, exist_ok=True)

# Copy license and readme
for file in ['LICENSE', 'README.md']:
    if os.path.exists(file):
        import shutil
        shutil.copy2(file, os.path.join(dist_dir, file))

# Create version file
with open(os.path.join(dist_dir, 'version.txt'), 'w') as f:
    f.write('1.0.0')

# Optional: Create portable mode flag
with open(os.path.join(dist_dir, 'portable.txt'), 'w') as f:
    f.write('This file indicates portable mode.\n')
    f.write('Delete this file to use installed mode.')
