#!/bin/bash

echo "🚀 启动 MCP 演示环境 (FastAPI 架构)"
echo "===================================="
echo ""

# 关闭可能存在的旧进程
echo "🧹 清理旧进程..."
pkill -f "proxy_server.py" 2>/dev/null
pkill -f "proxy_server_fastapi.py" 2>/dev/null
pkill -f "python3 -m http.server 3000" 2>/dev/null
sleep 1

# 启动 FastAPI 代理服务器
echo "📡 启动 FastAPI 代理服务器 (端口 8082)..."
python3 proxy_server_fastapi.py &
PROXY_PID=$!
sleep 3

# 启动 HTTP 服务器
echo "🌐 启动本地 HTTP 服务器 (端口 3000)..."
python3 -m http.server 3000 &
HTTP_PID=$!
sleep 1

echo ""
echo "✅ 所有服务已启动!"
echo ""
echo "📋 架构: 用户界面 → FastAPI → MCP (AIO Sandbox)"
echo ""
echo "🌐 服务地址:"
echo "   - FastAPI 代理: http://localhost:8082"
echo "   - 演示页面:     http://localhost:3000/browser_mcp_demo.html"
echo "   - 状态检查:     http://localhost:8082/status"
echo "   - 健康检查:     http://localhost:8082/health"
echo ""
echo "🔗 后端服务:"
echo "   - AIO Sandbox:  http://localhost:8080 (正式 MCP 服务)"
echo "   - VNC 查看:     http://localhost:8080/vnc/index.html?autoconnect=true"
echo ""
echo "💡 提示: 在浏览器中打开 http://localhost:3000/browser_mcp_demo.html"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "echo ''; echo '🛑 正在停止服务...'; kill $PROXY_PID $HTTP_PID 2>/dev/null; echo '✅ 服务已停止'; exit 0" INT TERM

wait