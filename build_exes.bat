@echo off
setlocal

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
pushd "%ROOT%" >nul

set "PYTHON_EXE=C:\Users\ZBook\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if exist "%PYTHON_EXE%" goto :python_ok

set "PYTHON_EXE=python"
where %PYTHON_EXE% >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found. Install Python or edit PYTHON_EXE in this script.
    if "%PAUSE_ON_EXIT%"=="1" (
        echo.
        echo Press any key to close this window...
        pause >nul
    )
    popd >nul
    exit /b 1
)

:python_ok
echo [INFO] Using Python: %PYTHON_EXE%

echo [1/4] Installing/Updating build dependencies...
"%PYTHON_EXE%" -m pip install --disable-pip-version-check pyinstaller keyboard
if errorlevel 1 goto :fail

echo [2/4] Cleaning old build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "gui.spec" del /f /q "gui.spec"
if exist "cli.spec" del /f /q "cli.spec"

echo [3/4] Building GUI executable...
"%PYTHON_EXE%" -m PyInstaller --noconfirm --clean --onefile --windowed --name os-scheduler-gui --paths "%ROOT%" --paths "%ROOT%\schedulers_simulator" --hidden-import Process --hidden-import gantt_chart "%ROOT%\gui\scheduler_gui.py"
if errorlevel 1 goto :fail

echo [4/4] Building CLI executable...
"%PYTHON_EXE%" -m PyInstaller --noconfirm --clean --onefile --console --name os-scheduler-cli --paths "%ROOT%" --paths "%ROOT%\schedulers_simulator" --hidden-import Process --hidden-import gantt_chart --hidden-import keyboard "%ROOT%\schedulers_simulator\main.py"
if errorlevel 1 goto :fail

echo.
echo [SUCCESS] Build completed.
echo [INFO] Generated files:
dir /b "dist"

if "%PAUSE_ON_EXIT%"=="1" (
    echo.
    echo Build finished. Press any key to close this window...
    pause >nul
)

popd >nul
exit /b 0

:fail
set "BUILD_EXIT=%ERRORLEVEL%"
echo.
echo [ERROR] Build failed with exit code %BUILD_EXIT%.
if "%PAUSE_ON_EXIT%"=="1" (
    echo.
    echo Build failed. Press any key to close this window...
    pause >nul
)
popd >nul
exit /b %BUILD_EXIT%
