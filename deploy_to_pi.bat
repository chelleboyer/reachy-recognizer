@echo off
REM Simple deployment script for Windows using SCP
REM Usage: deploy_to_pi.bat <pi-ip-address>

if "%1"=="" (
    echo Usage: deploy_to_pi.bat ^<pi-ip-address^>
    echo Example: deploy_to_pi.bat 192.168.1.100
    exit /b 1
)

set PI_HOST=%1
set PI_USER=pi
set TARGET_DIR=/home/pi/reachy-mini-dev

echo ========================================
echo   Deploying to Pi: %PI_HOST%
echo ========================================
echo.

echo [1/5] Testing connection...
ping -n 1 %PI_HOST% >nul 2>&1
if errorlevel 1 (
    echo X Cannot reach %PI_HOST%
    exit /b 1
)
echo + Connection OK
echo.

echo [2/5] Creating target directory...
ssh %PI_USER%@%PI_HOST% "mkdir -p %TARGET_DIR%"
if errorlevel 1 (
    echo X Failed to create directory
    exit /b 1
)
echo + Directory created
echo.

echo [3/5] Transferring files...
echo    - conversation_demo.py
scp conversation_demo.py %PI_USER%@%PI_HOST%:%TARGET_DIR%/
echo    - requirements.txt
scp requirements.txt %PI_USER%@%PI_HOST%:%TARGET_DIR%/
echo    - .env
scp .env %PI_USER%@%PI_HOST%:%TARGET_DIR%/
echo    - setup script
scp setup_conversation_demo_pi.sh %PI_USER%@%PI_HOST%:%TARGET_DIR%/
echo    - src/ directory (this may take a moment...)
scp -r src %PI_USER%@%PI_HOST%:%TARGET_DIR%/
if errorlevel 1 (
    echo X File transfer failed
    exit /b 1
)
echo + Files transferred
echo.

echo [4/5] Transferring Vosk model (40MB, may take 1-2 minutes)...
ssh %PI_USER%@%PI_HOST% "mkdir -p %TARGET_DIR%/models"
scp -r models\vosk-model-small-en-us-0.15 %PI_USER%@%PI_HOST%:%TARGET_DIR%/models/
if errorlevel 1 (
    echo X Model transfer failed
    exit /b 1
)
echo + Vosk model transferred
echo.

echo [5/5] Making setup script executable...
ssh %PI_USER%@%PI_HOST% "chmod +x %TARGET_DIR%/setup_conversation_demo_pi.sh"
echo + Setup script ready
echo.

echo ========================================
echo   Deployment Complete!
echo ========================================
echo.
echo Next steps:
echo   1. SSH to your Pi: ssh %PI_USER%@%PI_HOST%
echo   2. Run setup: cd %TARGET_DIR% ^&^& ./setup_conversation_demo_pi.sh
echo   3. Start demo: python3 conversation_demo.py --reachy --headless
echo.
echo Open SSH session now? (Press Ctrl+C to skip)
pause
ssh %PI_USER%@%PI_HOST%
