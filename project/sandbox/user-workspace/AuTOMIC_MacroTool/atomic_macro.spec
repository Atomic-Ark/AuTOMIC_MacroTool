# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

# Get project root
project_root = os.path.abspath(SPECPATH)

# Add project root to path
sys.path.insert(0, project_root)

# Get data files
def get_data_files():
    data_files = []
    
    # Language files
    langs_dir = os.path.join(project_root, 'src', 'resources', 'langs')
    for lang_file in Path(langs_dir).glob('*.json'):
        data_files.append((str(lang_file), os.path.join('resources', 'langs')))
    
    # Icons
    icons_dir = os.path.join(project_root, 'src', 'resources', 'icons')
    if os.path.exists(icons_dir):
        for icon_file in Path(icons_dir).glob('*.*'):
            data_files.append((str(icon_file), os.path.join('resources', 'icons')))
    
    # Themes
    themes_dir = os.path.join(project_root, 'src', 'resources', 'themes')
    if os.path.exists(themes_dir):
        for theme_file in Path(themes_dir).glob('*.*'):
            data_files.append((str(theme_file), os.path.join('resources', 'themes')))
    
    return data_files

# Hidden imports
hidden_imports = [
    'win32api',
    'win32con',
    'win32gui',
    'win32process',
    'win32ui',
    'pynput.keyboard._win32',
    'pynput.mouse._win32',
    'cv2',
    'numpy',
    'darkdetect',
    'keyboard',
    'mouse',
    'psutil',
    'requests',
]

# Binary dependencies
binaries = []

# Get data files
datas = get_data_files()

# Add documentation and license
datas.extend([
    (os.path.join(project_root, 'README.md'), '.'),
    (os.path.join(project_root, 'LICENSE'), '.'),
])

a = Analysis(
    [os.path.join(project_root, 'src', 'main.py')],
    pathex=[project_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
    module_collection_mode={'cv2': 'pyz+py'},
)

# Exclude unnecessary files
def exclude_from_analysis(analysis):
    excludes = {
        'mkl_',  # MKL libraries
        'libopenblas',  # OpenBLAS
        'libtbb',  # Intel TBB
        'cudart',  # CUDA Runtime
        'cublas',  # CUDA BLAS
        'cusolver',  # CUDA Solver
    }
    
    return [
        (b, n, t)
        for b, n, t in analysis.binaries
        if not any(e in n.lower() for e in excludes)
    ]

a.binaries = exclude_from_analysis(a)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='atomic_macro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=not DEBUG,
    upx=not DEBUG,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=DEBUG,
    disable_windowed_traceback=not DEBUG,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'src', 'resources', 'icons', 'app.ico'),
    version='file_version_info.txt',
    uac_admin=True,
)

# Create collection
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=not DEBUG,
    upx=not DEBUG,
    upx_exclude=[],
    name='atomic_macro',
)

# Create portable version if not debug
if not DEBUG:
    portable_dir = os.path.join('dist', 'atomic_macro_portable')
    if not os.path.exists(portable_dir):
        import shutil
        shutil.copytree(
            os.path.join('dist', 'atomic_macro'),
            portable_dir
        )
        # Create portable marker
        with open(os.path.join(portable_dir, 'portable.txt'), 'w') as f:
            f.write('This is a portable version of AuTOMIC MacroTool')

# Create Windows installer if not debug
if not DEBUG and os.path.exists('atomic_macro.iss'):
    import subprocess
    subprocess.run(['iscc', 'atomic_macro.iss'], check=True)
