#!/bin/bash

echo "🚀 启动浏览器 MCP 演示 Web 界面"
echo "================================"

# 查找可用端口
PORT=3000
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; do
    echo "⚠️  端口 $PORT 已被占用"
    PORT=$((PORT + 1))
done

echo "📡 启动 HTTP 服务器在端口 $PORT..."
echo ""
echo "🌐 访问地址: http://localhost:$PORT/browser_mcp_demo.html"
echo "🖥️ VNC 视图: http://localhost:8080/vnc/index.html?autoconnect=true"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "================================"
echo ""

python3 -m http.server $PORT