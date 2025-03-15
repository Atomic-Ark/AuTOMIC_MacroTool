@echo off
setlocal enabledelayedexpansion

:: AuTOMIC MacroTool Build Script
:: Copyright (c) 2025 AtomicArk

echo AuTOMIC MacroTool Build Script
echo =============================
echo.

:: Check Python installation
python --version > nul 2>&1
if errorlevel 1 (
    echo Error: Python not found in PATH
    echo Please install Python 3.8 or later
    pause
    exit /b 1
)

:: Check pip installation
pip --version > nul 2>&1
if errorlevel 1 (
    echo Error: pip not found
    echo Please install pip
    pause
    exit /b 1
)

:: Check virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

:: Activate virtual environment
call venv\Scripts\activate
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

:: Update pip
echo Updating pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo Warning: Failed to update pip
)

:: Install requirements
echo Installing requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install requirements
    pause
    exit /b 1
)

:: Install development requirements
echo Installing development requirements...
pip install -e .[dev]
if errorlevel 1 (
    echo Warning: Failed to install development requirements
)

:: Run tests
echo Running tests...
pytest tests
if errorlevel 1 (
    echo Warning: Some tests failed
    choice /C YN /M "Continue with build?"
    if errorlevel 2 exit /b 1
)

:: Check code style
echo Checking code style...
black --check src
if errorlevel 1 (
    echo Warning: Code style issues found
    choice /C YN /M "Format code automatically?"
    if errorlevel 1 (
        black src
    )
)

:: Run static type checking
echo Running type checking...
mypy src
if errorlevel 1 (
    echo Warning: Type checking issues found
    choice /C YN /M "Continue with build?"
    if errorlevel 2 exit /b 1
)

:: Check Inno Setup installation
echo Checking Inno Setup installation...
if not exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    echo Warning: Inno Setup not found
    echo Please install Inno Setup 6 from https://jrsoftware.org/isdl.php
    choice /C YN /M "Continue without installer?"
    if errorlevel 2 exit /b 1
)

:: Clean previous builds
echo Cleaning previous builds...
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"
if exist "atomic_macro.spec" del /f /q "atomic_macro.spec"

:: Build documentation
echo Building documentation...
cd docs
if errorlevel 1 (
    echo Warning: Documentation build failed
) else (
    make html
    cd ..
)

:: Create version file
echo Creating version file...
echo __version__ = "1.0.0" > src\version.py

:: Build executable
echo Building executable...
python build_standalone.py
if errorlevel 1 (
    echo Error: Build failed
    pause
    exit /b 1
)

:: Create ZIP archive
echo Creating ZIP archive...
cd dist\standalone
powershell Compress-Archive -Path * -DestinationPath ..\AuTOMIC_MacroTool.zip -Force
cd ..\..

:: Success message
echo.
echo Build completed successfully!
echo.
echo Files created:
echo - Standalone executable: dist\standalone\AuTOMIC_MacroTool.exe
echo - Installer: dist\installer\AuTOMIC_MacroTool_Setup.exe
echo - ZIP archive: dist\AuTOMIC_MacroTool.zip
echo.

:: Deactivate virtual environment
deactivate

:: Optional: Clean up
choice /C YN /M "Clean up build files?"
if errorlevel 1 (
    if exist "build" rd /s /q "build"
    if exist "atomic_macro.spec" del /f /q "atomic_macro.spec"
)

echo.
echo Thank you for using AuTOMIC MacroTool Build Script
pause
exit /b 0
