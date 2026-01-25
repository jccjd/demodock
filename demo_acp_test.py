#!/usr/bin/env python3
"""
ACP 服务测试 Demo
用于验证 iFlow ACP 服务是否能正常启动和连接
"""

import asyncio
import os
from datetime import timedelta

from opensandbox import Sandbox
from opensandbox.config import ConnectionConfig
from opensandbox.models.execd import RunCommandOpts

async def test_acp_service():
    """测试 ACP 服务的基本功能"""
    domain = os.getenv("SANDBOX_DOMAIN", "localhost:8080")
    api_key = os.getenv("SANDBOX_API_KEY")
    iflow_api_key = os.getenv("IFLOW_API_KEY", "sk-5674661b611f3ef28ab5d53b594c3cb6")
    image = "opensandbox/desktop-iflow:latest"
    vnc_password = "opensandbox"

    config = ConnectionConfig(
        domain=domain,
        api_key=api_key,
        request_timeout=timedelta(seconds=120),
    )

    print(f"🚀 创建 Sandbox 容器 (使用 {image})...")
    sandbox = await Sandbox.create(
        image,
        connection_config=config,
        env={"IFLOW_apiKey": iflow_api_key}
    )

    async with sandbox:
        print("🖥️  启动桌面环境...")
        
        # 启动 Xvfb 和桌面环境
        await sandbox.commands.run("Xvfb :0 -screen 0 1280x800x24", opts=RunCommandOpts(background=True))
        await sandbox.commands.run("DISPLAY=:0 dbus-launch startxfce4", opts=RunCommandOpts(background=True))

        # 启动 VNC 服务
        await sandbox.commands.run(f"x11vnc -display :0 -passwd {vnc_password} -forever -shared -rfbport 5900", opts=RunCommandOpts(background=True))
        await sandbox.commands.run("/usr/bin/websockify --web=/usr/share/novnc 6080 localhost:5900", opts=RunCommandOpts(background=True))

        # 启动 iFlow ACP 服务
        print("📡 启动 iFlow ACP 服务...")
        acp_port = 50051
        acp_cmd = (
            f"export DISPLAY=:0 && "
            f"export CHROME_FLAGS='--no-sandbox --disable-dev-shm-usage' && "
            f"iflow --experimental-acp --port {acp_port} --host 0.0.0.0"
        )
        acp_process = await sandbox.commands.run(acp_cmd, opts=RunCommandOpts(background=True))

        # 等待服务启动
        print("⏳ 等待 ACP 服务就绪...")
        await asyncio.sleep(25)

        # 检查 ACP 进程状态
        print("🔍 检查 ACP 进程状态...")
        ps_result = await sandbox.commands.run("ps aux | grep 'iflow.*--experimental-acp'")
        # 查看可用属性并输出日志
        for msg in ps_result.logs.stdout:
            print(f"ACP 进程状态: {msg.text}")

        # 检查端口监听
        print("🔍 检查端口监听...")
        netstat_result = await sandbox.commands.run("netstat -tuln | grep 50051")
        for msg in netstat_result.logs.stdout:
            print(f"端口监听状态: {msg.text}")

        # 检查 MCP 服务
        print("🔍 检查 MCP 服务配置...")
        mcp_check = await sandbox.commands.run("iflow mcp list", opts=RunCommandOpts(user="desktop"))
        for msg in mcp_check.logs.stdout:
            print(f"MCP 服务列表: {msg.text}")

        # 获取 endpoint
        endpoint_acp = await sandbox.get_endpoint(acp_port)
        print(f"✅ ACP 服务地址: ws://{endpoint_acp.endpoint}/acp")

        print("\n✅ ACP 服务测试完成 - 服务已启动并运行")
        print("💡 提示：如果 WebSocket 连接失败，可能是路由或防火墙问题")
        
        # 保持沙箱运行一段时间以便测试
        print("\n⏰ 保持沙箱运行 2 分钟...")
        await asyncio.sleep(120)

if __name__ == "__main__":
    asyncio.run(test_acp_service())