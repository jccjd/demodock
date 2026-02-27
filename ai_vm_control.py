#!/usr/bin/env python3
"""
AI 操作 KVM VNC 系统示例

这个脚本展示了如何通过 iFlow SDK 让 AI 操作 KVM 虚拟机
AI 可以直接连接 VNC 服务器并操作虚拟机
"""

import asyncio
import sys
from iflow_sdk import IFlowClient, IFlowOptions, ApprovalMode

# 配置
IFLOW_URL = "ws://10.8.135.251:8090/acp"
MCP_HTTP_URL = "http://10.8.135.251:8080/mcp"
TIMEOUT = 300.0

# VNC 服务器配置（直接 VNC 连接）
VNC_HOST = "10.8.136.182"
VNC_PORT = 5900
VNC_PASSWORD = "admin"


async def ai_operate_vm():
    """
    让 AI 操作虚拟机

    示例任务：
    1. 连接到 VNC 服务器
    2. 观察 BIOS/OS 状态
    3. 执行键盘和鼠标操作
    4. 验证操作结果
    """

    print("🤖 启动 AI 虚拟机操作助手...")
    print(f"📍 VNC 服务器: {VNC_HOST}:{VNC_PORT}")

    # 创建 iFlow 客户端
    options = IFlowOptions(
        url=IFLOW_URL,
        auto_start_process=True,
        timeout=TIMEOUT,
        log_level="INFO",

        # 文件系统访问
        file_access=False,
        cwd=".",

        # MCP 服务器配置
        mcp_servers=[
            {
                "name": "aio-sandbox",
                "httpUrl": MCP_HTTP_URL,
                "headers": {
                    "Accept": "application/json, text/event-stream"
                }
            }
        ],

        # 工具执行权限
        approval_mode=ApprovalMode.YOLO
    )

    client = IFlowClient(options)

    try:
        await client.__aenter__()

        # 示例任务 1: 连接 VNC 并观察界面
        print("\n📋 任务 1: 连接 VNC 并观察界面")
        task1 = f"""
        请帮我执行以下操作：

        1. 连接到 VNC 服务器: {VNC_HOST}:{VNC_PORT}
        2. 使用密码: {VNC_PASSWORD}
        3. 等待连接建立
        4. 截取当前屏幕并描述你看到的内容
        5. 告诉我当前显示的是什么界面（BIOS、UEFI、还是 OS）

        请详细描述你看到的界面元素和状态。
        """

        print(f"发送任务: {task1[:100]}...")
        await client.send_message(task1)

        async for message in client.receive_messages():
            if hasattr(message, 'type'):
                if message.type == 'assistant':
                    if hasattr(message, 'chunk') and message.chunk:
                        print(message.chunk.text or "", end="", flush=True)
                elif message.type == 'task_finish':
                    print("\n✅ 任务 1 完成")
                    break

        # 示例任务 2: 模拟键盘操作
        print("\n📋 任务 2: 模拟键盘操作")
        task2 = """
        现在请你通过 VNC 连接模拟键盘操作：

        1. 如果看到 BIOS 界面，按下 F2 键进入 BIOS 设置
        2. 如果看到登录界面，输入用户名 "root" 和密码
        3. 如果看到命令行，执行 'ls -la' 命令

        请告诉我你执行了什么操作，以及屏幕上有什么变化。
        """

        print(f"发送任务: {task2[:100]}...")
        await client.send_message(task2)

        async for message in client.receive_messages():
            if hasattr(message, 'type'):
                if message.type == 'assistant':
                    if hasattr(message, 'chunk') and message.chunk:
                        print(message.chunk.text or "", end="", flush=True)
                elif message.type == 'task_finish':
                    print("\n✅ 任务 2 完成")
                    break

        # 示例任务 3: 模拟鼠标操作
        print("\n📋 任务 3: 模拟鼠标操作")
        task3 = """
        现在请你通过 VNC 连接模拟鼠标操作：

        1. 截取当前 VNC 屏幕
        2. 识别屏幕上的可点击元素（按钮、菜单等）
        3. 点击某个你感兴趣的元素
        4. 再次截取屏幕，告诉我有什么变化

        请详细描述你的操作过程和结果。
        """

        print(f"发送任务: {task3[:100]}...")
        await client.send_message(task3)

        async for message in client.receive_messages():
            if hasattr(message, 'type'):
                if message.type == 'assistant':
                    if hasattr(message, 'chunk') and message.chunk:
                        print(message.chunk.text or "", end="", flush=True)
                elif message.type == 'task_finish':
                    print("\n✅ 任务 3 完成")
                    break

        print("\n🎉 所有任务完成！")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.__aexit__(None, None, None)


async def interactive_ai_control():
    """
    交互式 AI 控制

    让用户输入任务，AI 执行操作
    """

    print("🤖 交互式 AI 虚拟机控制")
    print(f"📍 VNC 服务器: {VNC_HOST}:{VNC_PORT}")
    print("输入 'quit' 退出")
    print("-" * 50)

    options = IFlowOptions(
        url=IFLOW_URL,
        auto_start_process=True,
        timeout=TIMEOUT,
        log_level="INFO",
        file_access=False,
        cwd=".",
        mcp_servers=[
            {
                "name": "aio-sandbox",
                "httpUrl": MCP_HTTP_URL,
                "headers": {
                    "Accept": "application/json, text/event-stream"
                }
            }
        ],
        approval_mode=ApprovalMode.YOLO
    )

    client = IFlowClient(options)

    try:
        await client.__aenter__()

        while True:
            print("\n请输入任务描述:")
            user_input = input("> ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 退出")
                break

            if not user_input:
                continue

            print(f"\n🤖 执行任务: {user_input}")
            print("-" * 50)

            try:
                await client.send_message(user_input)

                async for message in client.receive_messages():
                    if hasattr(message, 'type'):
                        if message.type == 'assistant':
                            if hasattr(message, 'chunk') and message.chunk:
                                print(message.chunk.text or "", end="", flush=True)
                        elif message.type == 'task_finish':
                            print("\n" + "-" * 50)
                            print("✅ 任务完成")
                            break
                        elif message.type == 'error':
                            print(f"\n❌ 错误: {message}")
                            break

            except Exception as e:
                print(f"❌ 执行失败: {e}")

    except KeyboardInterrupt:
        print("\n👋 用户中断")
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        await client.__aexit__(None, None, None)


async def specific_tasks():
    """
    特定任务示例
    """

    options = IFlowOptions(
        url=IFLOW_URL,
        auto_start_process=True,
        timeout=TIMEOUT,
        log_level="INFO",
        file_access=False,
        cwd=".",
        mcp_servers=[
            {
                "name": "aio-sandbox",
                "httpUrl": MCP_HTTP_URL,
                "headers": {
                    "Accept": "application/json, text/event-stream"
                }
            }
        ],
        approval_mode=ApprovalMode.YOLO
    )

    client = IFlowClient(options)

    try:
        await client.__aenter__()

        # 任务: 启动虚拟机并进入 BIOS
        task = f"""
        请帮我执行以下操作：

        1. 连接到 VNC 服务器: {VNC_HOST}:{VNC_PORT}
        2. 使用密码: {VNC_PASSWORD}
        3. 观察当前虚拟机状态
        4. 如果虚拟机未启动，通过 API 调用启动虚拟机
           - 调用 POST http://localhost:8082/vm/control
           - 请求体: {{"action": "start", "vm_name": "test-vm"}}
        5. 等待虚拟机启动，观察启动过程
        6. 如果看到 BIOS 界面，按下 F2 键进入 BIOS 设置
        7. 截图并描述 BIOS 设置内容

        请详细报告每一步的操作和观察结果。
        """

        print(f"🤖 执行任务:\n{task}")
        print("-" * 80)

        await client.send_message(task)

        async for message in client.receive_messages():
            if hasattr(message, 'type'):
                if message.type == 'assistant':
                    if hasattr(message, 'chunk') and message.chunk:
                        print(message.chunk.text or "", end="", flush=True)
                elif message.type == 'task_finish':
                    print("\n" + "-" * 80)
                    print("✅ 任务完成")
                    break

    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        await client.__aexit__(None, None, None)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI 操作 KVM VNC 系统")
    parser.add_argument(
        "--mode",
        choices=["demo", "interactive", "specific"],
        default="interactive",
        help="运行模式: demo(演示), interactive(交互式), specific(特定任务)"
    )
    parser.add_argument(
        "--vnc-host",
        default=VNC_HOST,
        help=f"VNC 服务器主机 (默认: {VNC_HOST})"
    )
    parser.add_argument(
        "--vnc-port",
        type=int,
        default=VNC_PORT,
        help=f"VNC 服务器端口 (默认: {VNC_PORT})"
    )
    parser.add_argument(
        "--vnc-password",
        default=VNC_PASSWORD,
        help="VNC 密码 (默认: admin)"
    )

    args = parser.parse_args()

    # 更新全局配置
    VNC_HOST = args.vnc_host
    VNC_PORT = args.vnc_port
    VNC_PASSWORD = args.vnc_password

    if args.mode == "demo":
        asyncio.run(ai_operate_vm())
    elif args.mode == "interactive":
        asyncio.run(interactive_ai_control())
    elif args.mode == "specific":
        asyncio.run(specific_tasks())
