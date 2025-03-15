@echo off
setlocal enabledelayedexpansion

:: Check Python installation
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH
    exit /b 1
)

:: Check Python version
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"
if %ERRORLEVEL% neq 0 (
    echo Python 3.8 or higher is required
    exit /b 1
)

:: Check virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo Failed to create virtual environment
        exit /b 1
    )
)

:: Activate virtual environment
call venv\Scripts\activate
if %ERRORLEVEL% neq 0 (
    echo Failed to activate virtual environment
    exit /b 1
)

:: Parse arguments
set DEBUG=0
set CONSOLE=0
set CLEAN=0
set TEST=0
set LINT=0
set DOC=0

:parse_args
if "%~1"=="" goto end_parse
if /i "%~1"=="--debug" set DEBUG=1
if /i "%~1"=="--console" set CONSOLE=1
if /i "%~1"=="--clean" set CLEAN=1
if /i "%~1"=="--test" set TEST=1
if /i "%~1"=="--lint" set LINT=1
if /i "%~1"=="--doc" set DOC=1
shift
goto parse_args
:end_parse

:: Clean build
if %CLEAN%==1 (
    echo Cleaning previous builds...
    if exist "build" rd /s /q "build"
    if exist "dist" rd /s /q "dist"
    if exist "*.spec" del /q "*.spec"
    if exist "__pycache__" rd /s /q "__pycache__"
)

:: Install/upgrade pip
python -m pip install --upgrade pip
if %ERRORLEVEL% neq 0 (
    echo Failed to upgrade pip
    exit /b 1
)

:: Install requirements
echo Installing requirements...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo Failed to install requirements
    exit /b 1
)

:: Run tests if requested
if %TEST%==1 (
    echo Running tests...
    python -m pytest tests --cov=src --cov-report=html
    if %ERRORLEVEL% neq 0 (
        echo Tests failed
        exit /b 1
    )
)

:: Run linting if requested
if %LINT%==1 (
    echo Running linting...
    python -m pylint src
    if %ERRORLEVEL% neq 0 (
        echo Linting found issues
        exit /b 1
    )
    
    echo Running code formatting check...
    python -m black --check src
    if %ERRORLEVEL% neq 0 (
        echo Code formatting issues found
        exit /b 1
    )
)

:: Build documentation if requested
if %DOC%==1 (
    echo Building documentation...
    cd docs
    call make html
    if %ERRORLEVEL% neq 0 (
        echo Documentation build failed
        cd ..
        exit /b 1
    )
    cd ..
)

:: Download UPX if not present
if not exist "upx" (
    echo Downloading UPX...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/upx/upx/releases/download/v4.0.2/upx-4.0.2-win64.zip' -OutFile 'upx.zip'}"
    powershell -Command "& {Expand-Archive -Path 'upx.zip' -DestinationPath 'upx' -Force}"
    del /q "upx.zip"
)

:: Build executable
echo Building executable...
set BUILD_ARGS=
if %DEBUG%==1 set BUILD_ARGS=!BUILD_ARGS! --debug
if %CONSOLE%==1 set BUILD_ARGS=!BUILD_ARGS! --console

python build_standalone.py !BUILD_ARGS!
if %ERRORLEVEL% neq 0 (
    echo Build failed
    exit /b 1
)

:: Create installer if not debug build
if %DEBUG%==0 (
    echo Creating installer...
    iscc atomic_macro.iss
    if %ERRORLEVEL% neq 0 (
        echo Installer creation failed
        exit /b 1
    )
)

:: Success message
echo.
echo Build completed successfully!
if %DEBUG%==1 (
    echo Debug build is in dist\atomic_macro\
) else (
    echo Release build is in dist\atomic_macro\
    echo Portable version is in dist\atomic_macro_portable\
    echo Installer is in Output\AtomicMacroSetup.exe
)

:: Deactivate virtual environment
deactivate

endlocal
exit /b 0
