"""
Build script for creating standalone executables.
Copyright (c) 2025 AtomicArk
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import PyInstaller.__main__

def clean_build():
    """Clean build directories."""
    print("Cleaning build directories...")
    
    # Remove build directories
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    # Remove spec file
    if os.path.exists('atomic_macro.spec'):
        os.remove('atomic_macro.spec')

def create_version_info():
    """Create version info file."""
    print("Creating version info...")
    
    version_info = '''
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'AtomicArk'),
         StringStruct(u'FileDescription', u'AuTOMIC MacroTool'),
         StringStruct(u'FileVersion', u'1.0.0'),
         StringStruct(u'InternalName', u'atomic_macro'),
         StringStruct(u'LegalCopyright', u'© 2025 AtomicArk. All rights reserved.'),
         StringStruct(u'OriginalFilename', u'AuTOMIC_MacroTool.exe'),
         StringStruct(u'ProductName', u'AuTOMIC MacroTool'),
         StringStruct(u'ProductVersion', u'1.0.0')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    with open('version_info.txt', 'w') as f:
        f.write(version_info)

def build_executable():
    """Build standalone executable."""
    print("Building executable...")
    
    # Create version info
    create_version_info()
    
    # Prepare resource files
    resources = [
        ('src/resources/langs/*.json', 'resources/langs'),
        ('src/resources/icons/*', 'resources/icons'),
        ('src/resources/themes/*', 'resources/themes'),
        ('LICENSE', '.'),
        ('README.md', '.')
    ]
    
    # Prepare hidden imports
    hidden_imports = [
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
        'requests'
    ]
    
    # Build arguments
    args = [
        'src/main.py',
        '--name=AuTOMIC_MacroTool',
        '--onefile',
        '--windowed',
        '--icon=src/resources/icons/app.ico',
        '--version-file=version_info.txt',
        '--uac-admin',  # Request admin privileges
        '--clean',
        '--noconfirm',
        f'--distpath={os.path.join("dist", "standalone")}',
        '--add-data=version_info.txt;.'
    ]
    
    # Add resources
    for src, dst in resources:
        for file in Path().glob(src):
            args.append(f'--add-data={file};{dst}')
    
    # Add hidden imports
    for imp in hidden_imports:
        args.append(f'--hidden-import={imp}')
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)
    
    # Clean up version info
    os.remove('version_info.txt')

def create_installer():
    """Create installer using Inno Setup."""
    print("Creating installer...")
    
    # Check if Inno Setup is installed
    inno_compiler = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if not os.path.exists(inno_compiler):
        print("Inno Setup not found. Please install it first.")
        return False
    
    # Create installer script
    installer_script = '''
#define MyAppName "AuTOMIC MacroTool"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "AtomicArk"
#define MyAppURL "https://github.com/Atomic-Ark/AuTOMIC_MacroTool"
#define MyAppExeName "AuTOMIC_MacroTool.exe"

[Setup]
AppId={{F8A2E6D8-1234-4567-8901-ABCDEF123456}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=dist\\installer
OutputBaseFilename=AuTOMIC_MacroTool_Setup
SetupIconFile=src\\resources\\icons\\app.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "polish"; MessagesFile: "compiler:Languages\\Polish.isl"
Name: "german"; MessagesFile: "compiler:Languages\\German.isl"
Name: "french"; MessagesFile: "compiler:Languages\\French.isl"
Name: "italian"; MessagesFile: "compiler:Languages\\Italian.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "dist\\standalone\\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "src\\resources\\*"; DestDir: "{app}\\resources"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{group}\\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\\Microsoft\\Internet Explorer\\Quick Launch\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\\{#MyAppName}"
'''
    
    with open('installer.iss', 'w') as f:
        f.write(installer_script)
    
    # Create installer directory
    os.makedirs('dist/installer', exist_ok=True)
    
    # Run Inno Setup Compiler
    subprocess.run([inno_compiler, '/Q', 'installer.iss'])
    
    # Clean up installer script
    os.remove('installer.iss')
    
    return True

def main():
    """Main build process."""
    try:
        # Clean previous builds
        clean_build()
        
        # Build executable
        build_executable()
        
        # Create installer
        if create_installer():
            print("Build completed successfully!")
            print("Installer created at: dist/installer/AuTOMIC_MacroTool_Setup.exe")
        else:
            print("Build completed, but installer creation failed.")
            print("Standalone executable available at: dist/standalone/AuTOMIC_MacroTool.exe")
        
    except Exception as e:
        print(f"Build failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
