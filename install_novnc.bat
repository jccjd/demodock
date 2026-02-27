@echo off
REM Install noVNC for web-based VNC client

echo Installing noVNC...
echo.

REM Create frontend/novnc directory if it doesn't exist
if not exist "frontend\novnc" mkdir "frontend\novnc"

REM Download noVNC from GitHub
echo Downloading noVNC from GitHub...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/novnc/noVNC/archive/refs/tags/v1.4.0.zip' -OutFile 'novnc.zip'"

REM Extract the archive
echo Extracting noVNC...
powershell -Command "Expand-Archive -Path 'novnc.zip' -DestinationPath 'frontend' -Force"

REM Rename the extracted folder
if exist "frontend\novnc-1.4.0" (
    if exist "frontend\novnc" rmdir /s /q "frontend\novnc"
    move "frontend\novnc-1.4.0" "frontend\novnc"
)

REM Cleanup
echo Cleaning up...
del novnc.zip

echo.
echo ========================================
echo noVNC installation completed!
echo ========================================
echo.
echo To use noVNC:
echo 1. Ensure websockify is running (start_vnc_proxy.bat)
echo 2. Open frontend\novnc\vnc_lite.html in your browser
echo 3. Enter: Host=localhost, Port=6080, Path=websockify
echo.
pause