import asyncio
import os
from iflow_sdk import IFlowClient, IFlowOptions, AssistantMessage, TaskFinishMessage, ApprovalMode, SessionSettings

async def main():
        options = IFlowOptions(
            auto_start_process=True,
            cwd=os.getcwd(),
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

        async with IFlowClient(options) as client:
            user_msg = "立即启动浏览器打开 google.com" # 换个简单的动作试试
            print(f"💬 指令: {user_msg}")
            
            await client.send_message(user_msg)
            
            async for message in client.receive_messages():
                if isinstance(message, AssistantMessage):
                    # 如果 AI 调用工具，通常这里会有 chunk 输出
                    print(message.chunk.text, end="", flush=True)
                # 关键：观察是否有 ToolCallMessage（虽然你现在的代码可能没打印，但 SDK 会处理）
if __name__ == "__main__":
    asyncio.run(main())