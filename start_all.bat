@echo off
chcp 65001 >nul
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║          iFlow DemoDock - 启动所有服务                               ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.
echo 本脚本将启动以下服务：
echo   1. VNC MCP 服务器 (端口: 8083)
echo   2. DemoDock 主服务器 (端口: 8082)
echo.
echo 请确保已启动 iFlow ACP 服务：
echo   iflow --experimental-acp --port 8090
echo.
pause

cd /d %~dp0

echo.
echo [1/2] 启动 VNC MCP 服务器...
start "VNC MCP Server" uv run python -m src.mcp_vnc_server

timeout /t 3 /nobreak >nul

echo.
echo [2/2] 启动 DemoDock 主服务器...
start "DemoDock Server" uv run python src/server.py

echo.
echo ════════════════════════════════════════════════════════════════════
echo   所有服务已启动！
echo.
echo   - VNC MCP 服务器: http://localhost:8083
echo   - DemoDock 主服务器: http://localhost:8082
echo   - API 文档: http://localhost:8082/docs
echo.
echo   前端界面: 打开 frontend/index.html
echo ════════════════════════════════════════════════════════════════════
echo.
pause
