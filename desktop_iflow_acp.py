import asyncio
import os
from datetime import timedelta

from opensandbox import Sandbox
from opensandbox.config import ConnectionConfig
from opensandbox.models.execd import RunCommandOpts

# 导入必要的类
from iflow_sdk import (
    IFlowClient, 
    IFlowOptions, 
    AssistantMessage, 
    TaskFinishMessage, 
    ApprovalMode,
    SessionSettings
)

async def main() -> None:
    # --- 环境配置 ---
    domain = os.getenv("SANDBOX_DOMAIN", "localhost:8080")
    api_key = os.getenv("SANDBOX_API_KEY")
    # 填入你的 iFlow API Key
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
        print("🖥️  启动桌面与 iFlow 服务...")
        
        # 1. 启动 Xvfb 和 Xfce 桌面环境
        await sandbox.commands.run("Xvfb :0 -screen 0 1280x800x24", opts=RunCommandOpts(background=True))
        await sandbox.commands.run("DISPLAY=:0 dbus-launch startxfce4", opts=RunCommandOpts(background=True))

        # 2. 启动 VNC 和 noVNC 预览
        await sandbox.commands.run(f"x11vnc -display :0 -passwd {vnc_password} -forever -shared -rfbport 5900", opts=RunCommandOpts(background=True))
        await sandbox.commands.run("/usr/bin/websockify --web=/usr/share/novnc 6080 localhost:5900", opts=RunCommandOpts(background=True))

        # 3. 获取 Endpoint
        endpoint_novnc = await sandbox.get_endpoint(6080)

        # 4. 拼接 noVNC URL
        novnc_host_port, novnc_path = endpoint_novnc.endpoint.split("/", 1)
        novnc_host, novnc_port = novnc_host_port.split(":")
        novnc_url = (
            f"http://{endpoint_novnc.endpoint}/vnc.html"
            f"?host={novnc_host}&port={novnc_port}&path={novnc_path}"
        )

        print("\n" + "="*60)
        print(f"✅ noVNC 预览: {novnc_url}")
        print("✅ ACP 服务将由 SDK 自动启动")
        print("="*60 + "\n")

        # 7. 使用 IFlowOptions 启动手动模式客户端
        print("🤖 连接到 AI Agent 并激活工具能力...")
        options = IFlowOptions(
            auto_start_process=True,  # 自动启动 ACP 服务
            cwd="/home",  # 使用存在的目录
            approval_mode=ApprovalMode.YOLO,
            mcp_servers=[
                {
                    "name": "chrome-devtools",
                    "command": "npx",
                    "args": ["-y", "@iflow-mcp/chrome-devtools-mcp"]
                }
            ],
            session_settings=SessionSettings(
                system_prompt="你拥有浏览器操作权限。收到指令后，请立即调用 chrome-devtools 开启浏览器并执行，不要废话。",
                allowed_tools=["*"] # 允许所有工具
            )
        )
        
        # 确保 IFLOW_apiKey 仍然在环境变量中，供 SDK 认证使用
        os.environ["IFLOW_apiKey"] = iflow_api_key

        try:
            async with IFlowClient(options) as client:
                user_msg = "打开浏览器访问百度并搜索 OpenSandbox"
                print(f"💬 指令: {user_msg}")
                
                await client.send_message(user_msg)
                
                print("🤖 iFlow 正在操作: ", end="", flush=True)
                async for message in client.receive_messages():
                    if isinstance(message, AssistantMessage):
                        print(message.chunk.text, end="", flush=True)
                    elif isinstance(message, TaskFinishMessage):
                        print("\n[任务完成]")
                        break
        except Exception as e:
            print(f"❌ 连接 iFlow 出错: {e}")

        print("\n程序将保持运行 10 分钟。请通过上方的 noVNC 链接观察 AI 的实时操作。")
        await asyncio.sleep(600)

if __name__ == "__main__":
    asyncio.run(main())