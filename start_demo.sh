#!/bin/bash

echo "🚀 启动浏览器 MCP 服务器演示"
echo "================================"

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3"
    exit 1
fi

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  警告: 建议在虚拟环境中运行"
    echo "正在使用系统 Python..."
fi

# 检查必要的依赖
echo "📦 检查依赖..."
python3 -c "import aiohttp" 2>/dev/null || {
    echo "安装 aiohttp..."
    pip3 install aiohttp aiohttp-cors
}

# 启动服务器
echo ""
echo "🌐 服务器信息:"
echo "   HTTP 接口: http://localhost:8081"
echo "   WebSocket: ws://localhost:8081/ws"
echo "   演示页面: http://localhost:8081/"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "================================"
echo ""

python3 browser_mcp_server.py