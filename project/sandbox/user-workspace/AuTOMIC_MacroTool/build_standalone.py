import os
import sys
import shutil
import subprocess
import argparse
import json
from pathlib import Path
from typing import List, Dict
import PyInstaller.__main__

def get_version() -> str:
    """Get current version from package."""
    init_path = Path(__file__).parent / 'src' / '__init__.py'
    with open(init_path) as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"\'')
    return '1.0.0'

def get_data_files() -> List[tuple]:
    """Get data files to include."""
    data_files = []
    
    # Language files
    langs_dir = Path('src/resources/langs')
    for lang_file in langs_dir.glob('*.json'):
        data_files.append((str(lang_file), str(langs_dir)))
    
    # Icons and themes
    resource_dirs = ['icons', 'themes']
    for dir_name in resource_dirs:
        res_dir = Path(f'src/resources/{dir_name}')
        if res_dir.exists():
            for file in res_dir.glob('*.*'):
                data_files.append((str(file), str(res_dir)))
    
    return data_files

def create_version_info() -> Dict:
    """Create version info for Windows executable."""
    version = get_version()
    version_parts = version.split('.')
    while len(version_parts) < 4:
        version_parts.append('0')
    
    return {
        'fileversion': tuple(map(int, version_parts)),
        'productversion': tuple(map(int, version_parts)),
        'filedescription': 'AuTOMIC MacroTool',
        'productname': 'AuTOMIC MacroTool',
        'companyname': 'AtomicArk',
        'legalcopyright': '© 2023 AtomicArk. All rights reserved.',
        'originalfilename': 'atomic_macro.exe',
        'internalname': 'atomic_macro',
        'comments': 'Advanced Macro Recording and Automation Tool',
    }

def build_executable(debug: bool = False, console: bool = False):
    """Build standalone executable."""
    try:
        print("Starting build process...")
        
        # Clean previous builds
        for dir_name in ['build', 'dist']:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
        
        # Create version info
        version_info = create_version_info()
        version_file = 'file_version_info.txt'
        with open(version_file, 'w') as f:
            json.dump(version_info, f, indent=2)
        
        # Prepare PyInstaller arguments
        args = [
            'src/main.py',
            '--name=atomic_macro',
            '--windowed' if not console else '--console',
            '--icon=src/resources/icons/app.ico',
            f'--version-file={version_file}',
            '--noconfirm',
            '--clean',
            '--uac-admin',  # Request admin rights for stealth mode
        ]
        
        # Add data files
        for src, dst in get_data_files():
            args.extend(['--add-data', f'{src};{dst}'])
        
        # Add debug options
        if debug:
            args.extend([
                '--debug=all',
                '--log-level=DEBUG',
            ])
        else:
            args.extend([
                '--log-level=INFO',
                '--strip',  # Strip debug symbols
                '--upx-dir=upx',  # Use UPX if available
            ])
        
        # Add hidden imports
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
        ]
        for imp in hidden_imports:
            args.extend(['--hidden-import', imp])
        
        # Run PyInstaller
        print("Running PyInstaller...")
        PyInstaller.__main__.run(args)
        
        # Clean up
        os.remove(version_file)
        
        # Copy additional files
        dist_dir = Path('dist/atomic_macro')
        shutil.copy2('README.md', dist_dir / 'README.md')
        shutil.copy2('LICENSE', dist_dir / 'LICENSE')
        
        # Create portable version
        if not debug:
            print("Creating portable version...")
            portable_dir = Path('dist/atomic_macro_portable')
            shutil.copytree(dist_dir, portable_dir)
            
            # Create portable marker
            with open(portable_dir / 'portable.txt', 'w') as f:
                f.write('This is a portable version of AuTOMIC MacroTool')
        
        print("Build completed successfully!")
        
    except Exception as e:
        print(f"Error during build: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Build AuTOMIC MacroTool executable')
    parser.add_argument('--debug', action='store_true', help='Build with debug options')
    parser.add_argument('--console', action='store_true', help='Show console window')
    args = parser.parse_args()
    
    build_executable(debug=args.debug, console=args.console)

if __name__ == '__main__':
    main()
