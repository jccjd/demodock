@echo off
REM Websockify VNC Proxy for QEMU
REM This script starts websockify to proxy VNC connections to web

echo Starting Websockify VNC Proxy...
echo WebSocket Server: http://localhost:6080
echo VNC Target: 127.0.0.1:5901

REM Start websockify
REM Port 6080 - WebSocket port for browser connections
REM 127.0.0.1:5901 - VNC server address (QEMU -vnc 127.0.0.1:1 means port 5901)
uv run websockify 6080 127.0.0.1:5901

pause