#!/usr/bin/env python3
"""
iFlow 浏览器自动化服务

使用 iFlow SDK + MCP 实现浏览器自动化，支持：
- WebSocket 实时通信
- SSE 流式响应
- 实时返回 AI 思考和操作过程
"""

import os
import sys
import json
import asyncio
import logging
import base64
from typing import AsyncGenerator, Optional, List
from datetime import datetime
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

# VNC 相关导入
try:
    from vncdotool import api
    from PIL import Image
    VNC_AVAILABLE = True
except ImportError:
    VNC_AVAILABLE = False
    print("⚠️  警告: vncdotool 或 PIL 未安装，VNC 功能将不可用")

# SSH 相关导入
try:
    import paramiko
    SSH_AVAILABLE = True
except ImportError:
    SSH_AVAILABLE = False
    print("⚠️  警告: paramiko 未安装，虚拟机控制功能将不可用")

# 导入 iFlow SDK
try:
    from iflow_sdk import IFlowClient, IFlowOptions, ApprovalMode
    IFLOW_SDK_AVAILABLE = True
except ImportError:
    IFLOW_SDK_AVAILABLE = False
    print("❌ 错误: 缺少 iflow-cli-sdk")
    print("   请运行: pip install iflow-cli-sdk")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 环境变量
IFLOW_URL = os.getenv("IFLOW_URL", "ws://127.0.0.1:8090/acp")
MCP_HTTP_URL = os.getenv("MCP_HTTP_URL", "http://127.0.0.1:8080/mcp")
PORT = int(os.getenv("PORT", "8082"))
TIMEOUT = float(os.getenv("TIMEOUT", "300.0"))

# FastAPI 应用
app = FastAPI(
    title="🤖 iFlow 浏览器自动化服务",
    description="使用 iFlow SDK + MCP 实现浏览器自动化",
    version="2.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# 数据模型
# ============================================================================

class BrowserTask(BaseModel):
    """浏览器任务请求"""
    task: str
    timeout: Optional[float] = TIMEOUT

class VNCConfig(BaseModel):
    """VNC 连接配置"""
    host: str = "127.0.0.1"
    port: int = 5901
    username: str = ""
    password: str = ""

class VMConfig(BaseModel):
    """虚拟机配置"""
    host: str = "127.0.0.1"
    ssh_port: int = 22
    username: str = "root"
    password: str = ""
    vm_name: str = "test-vm"  # 虚拟机名称

class VMControlRequest(BaseModel):
    """虚拟机控制请求"""
    action: str  # start, stop, reboot, shutdown, status
    vm_name: Optional[str] = None

# ============================================================================
# ACP WebSocket 管理
# ============================================================================

class ACPConnectionManager:
    """ACP WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

# 创建连接管理器实例
manager = ACPConnectionManager()

# 创建线程池用于同步 VNC 操作
vnc_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="vnc_")

# VNC 客户端缓存
vnc_client_cache = None
vnc_client_lock = asyncio.Lock()

# ============================================================================
# 虚拟机控制（通过 SSH + virsh）
# ============================================================================

def _execute_virsh_command_sync(ssh_host: str, ssh_port: int, ssh_user: str, ssh_password: str, vm_name: str, action: str):
    """
    同步函数：通过 SSH 执行 virsh 命令控制虚拟机
    """
    if not SSH_AVAILABLE:
        raise RuntimeError("paramiko 未安装")

    try:
        # 创建 SSH 客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # 连接到服务器
        ssh.connect(
            hostname=ssh_host,
            port=ssh_port,
            username=ssh_user,
            password=ssh_password,
            timeout=10
        )

        # 根据动作执行不同的 virsh 命令
        commands = {
            'start': f'virsh start {vm_name}',
            'stop': f'virsh destroy {vm_name}',
            'reboot': f'virsh reboot {vm_name}',
            'shutdown': f'virsh shutdown {vm_name}',
            'status': f'virsh domstate {vm_name}'
        }

        if action not in commands:
            raise ValueError(f"不支持的操作: {action}")

        command = commands[action]
        logger.info(f"执行 virsh 命令: {command}")

        # 执行命令
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()

        # 关闭连接
        ssh.close()

        if error and action != 'status':
            logger.warning(f"virsh 命令警告: {error}")

        result = {
            'action': action,
            'vm_name': vm_name,
            'output': output,
            'success': True
        }

        # 解析状态
        if action == 'status':
            result['state'] = output
            result['output'] = f"虚拟机 {vm_name} 状态: {output}"
        else:
            result['output'] = f"虚拟机 {vm_name} {action} 成功"

        return result

    except paramiko.AuthenticationException:
        raise Exception("SSH 认证失败，请检查用户名和密码")
    except paramiko.SSHException as e:
        raise Exception(f"SSH 连接失败: {str(e)}")
    except Exception as e:
        logger.error(f"执行 virsh 命令失败: {e}")
        raise

# ============================================================================
# VNC 图像生成器（真实 VNC 图像流）
# ============================================================================

def _capture_vnc_screen_sync(host: str, port: int, username: str, password: str):
    """
    同步函数：捕获 VNC 屏幕

    注意：vncdotool 的 API 是同步的，需要在线程池中运行
    """
    if not VNC_AVAILABLE:
        raise RuntimeError("vncdotool 或 PIL 未安装")

    try:
        # 连接到 VNC 服务器
        client = api.connect(
            f"{host}:{port}",
            password=password
        )

        # 捕获屏幕
        screen = client.captureScreen()

        # 转换为 PIL Image
        img = Image.frombytes('RGB', screen.size, screen.data)

        # 调整图像大小以优化传输（最大宽度 800px）
        if img.width > 800:
            ratio = 800 / img.width
            new_height = int(img.height * ratio)
            img = img.resize((800, new_height), Image.Resampling.LANCZOS)

        # 转换为 JPEG 格式并编码为 base64
        buffered = BytesIO()
        img.save(buffered, format='JPEG', quality=85)
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return img_base64

    except Exception as e:
        logger.error(f"VNC 屏幕捕获失败: {e}")
        raise

async def get_vnc_client(vnc_config: VNCConfig):
    """
    获取或创建 VNC 客户端（使用缓存）
    """
    global vnc_client_cache

    async with vnc_client_lock:
        if vnc_client_cache is None:
            # 在线程池中创建 VNC 客户端
            loop = asyncio.get_event_loop()
            try:
                vnc_client_cache = await loop.run_in_executor(
                    vnc_executor,
                    lambda: api.connect(
                        f"{vnc_config.host}:{vnc_config.port}",
                        password=vnc_config.password
                    )
                )
                logger.info(f"✅ VNC 客户端已创建: {vnc_config.host}:{vnc_config.port}")
            except Exception as e:
                logger.error(f"❌ VNC 客户端创建失败: {e}")
                vnc_client_cache = None
                raise

        return vnc_client_cache

async def generate_vnc_image_stream(vnc_config: VNCConfig) -> AsyncGenerator[dict, None]:
    """
    生成真实的 VNC 图像流

    Args:
        vnc_config: VNC 连接配置

    Yields:
        图像数据字典，包含：
        - image: base64 编码的 JPEG 图像数据
        - timestamp: 时间戳
        - status: 状态信息
        - width: 图像宽度
        - height: 图像高度
    """
    if not VNC_AVAILABLE:
        yield {
            'status': 'error',
            'error': 'vncdotool 或 PIL 未安装，请先安装: pip install vncdotool pillow',
            'timestamp': datetime.now().isoformat()
        }
        return

    try:
        logger.info(f"🖥️  开始 VNC 图像流: {vnc_config.host}:{vnc_config.port}")

        # 在线程池中执行同步的 VNC 操作
        loop = asyncio.get_event_loop()
        retry_count = 0
        max_retries = 3

        while True:
            try:
                # 在线程池中捕获屏幕（设置超时）
                try:
                    img_base64 = await asyncio.wait_for(
                        loop.run_in_executor(
                            vnc_executor,
                            lambda: _capture_vnc_screen_sync(
                                vnc_config.host,
                                vnc_config.port,
                                vnc_config.username,
                                vnc_config.password
                            )
                        ),
                        timeout=10.0  # 10秒超时
                    )

                    # 重置重试计数
                    retry_count = 0

                    # 发送图像数据
                    yield {
                        'image': img_base64,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'connected',
                        'host': vnc_config.host,
                        'port': vnc_config.port
                    }

                except asyncio.TimeoutError:
                    retry_count += 1
                    logger.warning(f"⚠️  VNC 捕获超时 (重试 {retry_count}/{max_retries})")

                    if retry_count >= max_retries:
                        error_msg = f"VNC 连接超时，已重试 {max_retries} 次。请检查："
                        error_msg += f"\n1. VNC 服务器 {vnc_config.host}:{vnc_config.port} 是否运行"
                        error_msg += f"\n2. 网络连接是否正常"
                        error_msg += f"\n3. 防火墙是否允许连接"
                        error_msg += f"\n4. 用户名密码是否正确 ({vnc_config.username}/{vnc_config.password})"

                        yield {
                            'status': 'error',
                            'error': error_msg,
                            'timestamp': datetime.now().isoformat()
                        }
                        # 等待更长时间后继续尝试
                        await asyncio.sleep(5)
                        retry_count = 0
                    else:
                        # 短暂等待后重试
                        await asyncio.sleep(2)

                # 控制帧率（约 10fps，避免过高负载）
                await asyncio.sleep(0.1)

            except ConnectionRefusedError as e:
                logger.error(f"❌ VNC 连接被拒绝: {e}")
                yield {
                    'status': 'error',
                    'error': f'VNC 连接被拒绝。请检查 VNC 服务器 {vnc_config.host}:{vnc_config.port} 是否正在运行。',
                    'timestamp': datetime.now().isoformat()
                }
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"❌ VNC 图像捕获失败: {e}")
                yield {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                # 等待一段时间后重试
                await asyncio.sleep(2)

    except Exception as e:
        logger.error(f"❌ VNC 图像流生成失败: {e}")
        yield {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# ============================================================================
# iFlow 客户端管理
# ============================================================================

async def create_iflow_client() -> IFlowClient:
    """创建 iFlow 客户端实例"""
    options = IFlowOptions(
        # 连接设置
        url=IFLOW_URL,
        auto_start_process=True,
        timeout=TIMEOUT,
        log_level="INFO",

        # 文件系统访问 - 禁用以避免路径问题
        file_access=False,

        # 工作目录 - 使用相对路径避免 Windows 路径问题
        cwd=".",

        # MCP 服务器配置 - HTTP 方式
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

    return IFlowClient(options)

# ============================================================================
# 流式任务执行
# ============================================================================

async def execute_stream_task(task: str) -> AsyncGenerator[dict, None]:
    """
    执行流式任务并返回事件生成器

    Args:
        task: 用户任务描述

    Yields:
        事件字典，包含以下字段：
        - chunk: 文本片段
        - full_response: 完整响应（累积）
        - status: 状态信息
        - error: 错误信息（如果有）
    """
    client = None
    try:
        logger.info(f"🚀 开始任务: {task}")

        # 创建 iFlow 客户端
        client = await create_iflow_client()
        await client.__aenter__()

        # 发送任务
        await client.send_message(task)

        # 接收响应流
        full_response = ""
        async for message in client.receive_messages():
            logger.debug(f"收到消息: {message}")

            # 处理不同类型的消息
            if hasattr(message, 'type'):
                if message.type == 'assistant':
                    # AI 响应消息
                    chunk = ""
                    if hasattr(message, 'chunk') and message.chunk:
                        chunk = message.chunk.text or ""
                        full_response += chunk

                    yield {
                        'chunk': chunk,
                        'full_response': full_response,
                        'status': 'streaming'
                    }

                elif message.type == 'tool_use':
                    # 工具使用消息（浏览器操作）
                    logger.info(f"🔧 工具调用: {message}")

                elif message.type == 'system':
                    # 系统消息
                    logger.info(f"📢 系统消息: {message}")

            # 检查是否完成
            # iFlow SDK 可能在某个时刻表示任务完成
            # 这里简化处理，收到一定数量的消息后认为完成
            if len(full_response) > 0 and "。" in full_response[-10:]:
                # 简单判断：如果响应以句号结尾，可能已完成
                yield {
                    'status': 'completed',
                    'full_response': full_response
                }
                break

        logger.info("✅ 任务完成")

    except Exception as e:
        logger.error(f"❌ 任务执行失败: {e}")
        logger.exception("详细错误:")
        yield {
            'status': 'error',
            'error': str(e)
        }

    finally:
        # 清理资源
        if client:
            try:
                await client.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"清理客户端失败: {e}")

# ============================================================================
# API 端点
# ============================================================================

@app.post("/vm/control")
async def vm_control(request: VMControlRequest):
    """
    虚拟机控制 API

    支持的操作:
    - start: 启动虚拟机
    - stop: 强制停止虚拟机
    - reboot: 重启虚拟机
    - shutdown: 优雅关闭虚拟机
    - status: 查询虚拟机状态

    请求格式:
    {
        "action": "start",
        "vm_name": "test-vm"
    }

    响应格式:
    {
        "action": "start",
        "vm_name": "test-vm",
        "output": "虚拟机 test-vm start 成功",
        "success": true,
        "state": "running"  # 仅 status 操作返回
    }
    """
    try:
        # 从环境变量或使用默认配置
        vm_config = VMConfig(
            host=os.getenv("VM_HOST", "127.0.0.1"),
            ssh_port=int(os.getenv("VM_SSH_PORT", "22")),
            username=os.getenv("VM_SSH_USER", "root"),
            password=os.getenv("VM_SSH_PASSWORD", ""),
            vm_name=request.vm_name or os.getenv("VM_NAME", "test-vm")
        )

        logger.info(f"🎮 虚拟机控制请求: {request.action} - {vm_config.vm_name}")

        # 在线程池中执行同步的 SSH 操作
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(
                vnc_executor,
                lambda: _execute_virsh_command_sync(
                    vm_config.host,
                    vm_config.ssh_port,
                    vm_config.username,
                    vm_config.password,
                    vm_config.vm_name,
                    request.action
                )
            ),
            timeout=30.0
        )

        logger.info(f"✅ 虚拟机控制成功: {result['output']}")
        return result

    except asyncio.TimeoutError:
        logger.error(f"❌ 虚拟机控制超时")
        raise HTTPException(status_code=408, detail="操作超时，请检查网络连接")

    except Exception as e:
        logger.error(f"❌ 虚拟机控制失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vm/status/{vm_name}")
async def get_vm_status(vm_name: str):
    """
    获取虚拟机状态

    响应格式:
    {
        "vm_name": "test-vm",
        "state": "running",
        "success": true
    }
    """
    try:
        vm_config = VMConfig(
            host=os.getenv("VM_HOST", "127.0.0.1"),
            ssh_port=int(os.getenv("VM_SSH_PORT", "22")),
            username=os.getenv("VM_SSH_USER", "root"),
            password=os.getenv("VM_SSH_PASSWORD", ""),
            vm_name=vm_name
        )

        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(
                vnc_executor,
                lambda: _execute_virsh_command_sync(
                    vm_config.host,
                    vm_config.ssh_port,
                    vm_config.username,
                    vm_config.password,
                    vm_config.vm_name,
                    'status'
                )
            ),
            timeout=10.0
        )

        return {
            "vm_name": vm_name,
            "state": result.get('state', 'unknown'),
            "success": True
        }

    except Exception as e:
        logger.error(f"❌ 获取虚拟机状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/vnc")
async def vnc_websocket(websocket: WebSocket):
    """
    VNC 图像流 WebSocket 端点

    连接后持续发送 VNC 图像帧（base64 编码）

    客户端连接示例：
    const ws = new WebSocket('ws://localhost:8082/vnc');
    ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.image) {
            // 显示图像
            const img = document.getElementById('vnc-display');
            img.src = 'data:image/jpeg;base64,' + data.image;
        }
    };
    """
    await websocket.accept()
    vnc_config = VNCConfig()  # 使用默认配置

    try:
        logger.info(f"🖥️  VNC WebSocket 客户端连接: {vnc_config.host}:{vnc_config.port}")

        # 发送连接确认
        await websocket.send_text(json.dumps({
            'type': 'connected',
            'host': vnc_config.host,
            'port': vnc_config.port,
            'message': f'已连接到 VNC 服务器 {vnc_config.host}:{vnc_config.port}'
        }, ensure_ascii=False))

        # 生成并发送图像流
        async for image_data in generate_vnc_image_stream(vnc_config):
            await websocket.send_text(json.dumps(image_data, ensure_ascii=False))

    except WebSocketDisconnect:
        logger.info("VNC WebSocket 连接断开")
    except Exception as e:
        logger.error(f"VNC WebSocket 错误: {e}")
        try:
            await websocket.send_text(json.dumps({
                'type': 'error',
                'error': str(e)
            }, ensure_ascii=False))
        except:
            pass

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点 - 用于前端直接连接，使用 iFlow SDK 处理任务"""
    await manager.connect(websocket)
    client = None
    try:
        while True:
            # 接收前端消息
            data = await websocket.receive_text()
            logger.info(f"收到前端消息: {data}")

            try:
                # 创建 iFlow 客户端
                client = await create_iflow_client()
                await client.__aenter__()

                # 发送任务
                await client.send_message(data)

                # 接收响应流
                full_response = ""
                async for message in client.receive_messages():
                    msg_type = getattr(message, 'type', 'unknown')
                    logger.info(f"📨 收到消息 type={msg_type}: {str(message)[:200]}...")
                    logger.debug(f"完整消息对象: {message}")

                    # 处理不同类型的消息
                    if hasattr(message, 'type'):
                        if message.type == 'assistant':
                            # AI 响应消息 - 可能是文本或思考内容
                            chunk = ""
                            thought = None
                            
                            if hasattr(message, 'chunk') and message.chunk:
                                # 获取文本内容
                                chunk = message.chunk.text or ""
                                # 获取思考内容（通过 agent_thought_chunk 发送时会有值）
                                thought = getattr(message.chunk, 'thought', None)
                                
                                # 调试日志：显示 chunk 的具体内容
                                logger.debug(f"📝 AssistantMessageChunk: text={bool(chunk)}, thought={bool(thought)}")
                                
                                # 只有文本内容才累加到 full_response
                                if chunk:
                                    full_response += chunk
                            
                            # 判断消息类型：是思考内容还是文本内容
                            is_thought_message = thought is not None and not chunk
                            
                            # 构建响应数据
                            response_data = {
                                'type': 'assistant',
                                'chunk': chunk,
                                'full_response': full_response,
                                'status': 'streaming'
                            }
                            
                            # 如果有思考内容，添加到响应中
                            if thought:
                                response_data['thought'] = thought
                                logger.info(f"💭 思考内容: {thought[:100]}...")
                            
                            # 如果是纯思考消息，使用单独的类型标识
                            if is_thought_message:
                                response_data['subtype'] = 'thought'
                                logger.info(f"🧠 发送思考消息: thought长度={len(thought)}")
                            
                            # 发送响应
                            logger.info(f"📤 发送流式响应: chunk='{chunk[:50] if chunk else '(empty)'}...' thought={bool(thought)} full_response长度={len(full_response)}")
                            await websocket.send_text(json.dumps(response_data, ensure_ascii=False))

                        elif message.type == 'tool_call':
                            # 工具调用消息
                            tool_name = message.tool_name if hasattr(message, 'tool_name') else (message.label if hasattr(message, 'label') else 'unknown')
                            tool_status = message.status if hasattr(message, 'status') else 'pending'
                            tool_args = {}
                            
                            # 尝试获取参数
                            if hasattr(message, 'arguments'):
                                tool_args = message.arguments if isinstance(message.arguments, dict) else {}
                            elif hasattr(message, 'args'):
                                tool_args = message.args if isinstance(message.args, dict) else {}
                            elif hasattr(message, 'input'):
                                tool_args = message.input if isinstance(message.input, dict) else {}
                            
                            await websocket.send_text(json.dumps({
                                'type': 'tool_use',
                                'tool': tool_name,
                                'status': tool_status,
                                'args': tool_args
                            }, ensure_ascii=False))
                            
                            logger.info(f"🔧 工具调用: {tool_name}, status: {tool_status}, args: {tool_args}")

                        elif message.type == 'plan':
                            # 计划消息
                            entries = []
                            if hasattr(message, 'entries'):
                                for entry in message.entries:
                                    entries.append({
                                        'content': entry.content,
                                        'priority': entry.priority,
                                        'status': entry.status
                                    })
                            await websocket.send_text(json.dumps({
                                'type': 'plan',
                                'entries': entries
                            }, ensure_ascii=False))

                        elif message.type == 'task_finish':
                            # 任务完成
                            await websocket.send_text(json.dumps({
                                'type': 'task_finish',
                                'stop_reason': message.stop_reason,
                                'full_response': full_response,
                                'status': 'completed'
                            }, ensure_ascii=False))
                            break

            except Exception as e:
                logger.error(f"处理消息失败: {e}")
                await websocket.send_text(json.dumps({"type": "error", "error": str(e)}, ensure_ascii=False))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket 连接断开")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
        manager.disconnect(websocket)
    finally:
        # 清理资源
        if client:
            try:
                await client.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"清理客户端失败: {e}")

@app.post("/acp/task")
async def acp_task(request: BrowserTask):
    """
    通过 iFlow SDK 执行任务（流式响应）

    请求格式:
    {
        "task": "你好",
        "timeout": 300.0
    }

    响应格式（SSE）:
    data: {"chunk": "...", "full_response": "...", "status": "streaming"}
    """
    async def event_generator():
        client = None
        try:
            yield f"data: {json.dumps({'status': 'started', 'task': request.task}, ensure_ascii=False)}\n\n"

            # 创建 iFlow 客户端
            client = await create_iflow_client()
            await client.__aenter__()

            # 发送任务
            await client.send_message(request.task)

            # 接收响应流
            full_response = ""
            async for message in client.receive_messages():
                logger.debug(f"收到消息: {message}")

                # 处理不同类型的消息
                if hasattr(message, 'type'):
                    if message.type == 'assistant':
                        # AI 响应消息
                        chunk = ""
                        if hasattr(message, 'chunk') and message.chunk:
                            chunk = message.chunk.text or ""
                            full_response += chunk
                            yield f"data: {json.dumps({'chunk': chunk, 'full_response': full_response, 'status': 'streaming'}, ensure_ascii=False)}\n\n"

                    elif message.type == 'task_finish':
                        # 任务完成
                        yield f"data: {json.dumps({'status': 'completed', 'full_response': full_response}, ensure_ascii=False)}\n\n"
                        break

            yield f"data: {json.dumps({'status': 'completed', 'full_response': full_response}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"任务执行错误: {e}")
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            # 清理资源
            if client:
                try:
                    await client.__aexit__(None, None, None)
                except Exception as e:
                    logger.error(f"清理客户端失败: {e}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/")
async def root():
    """服务信息"""
    return {
        "service": "🤖 iFlow 浏览器自动化服务",
        "version": "2.0.0",
        "architecture": "FastAPI → iFlow SDK → MCP 浏览器",
        "status": "running",
        "iflow": {
            "url": IFLOW_URL,
            "connected": True
        },
        "mcp": {
            "url": MCP_HTTP_URL,
            "type": "http"
        },
        "vnc": {
            "default_host": "127.0.0.1",
            "default_port": 5901,
            "default_user": "admin"
        },
        "endpoints": {
            "GET /": "服务信息",
            "GET /health": "健康检查",
            "POST /browser/stream-task": "流式执行浏览器任务",
            "WS /vnc": "VNC 图像流 WebSocket"
        }
    }

@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "iflow_url": IFLOW_URL,
        "mcp_url": MCP_HTTP_URL
    }

@app.post("/browser/stream-task")
async def browser_stream_task(request: BrowserTask):
    """
    流式执行浏览器任务（SSE）

    使用 Server-Sent Events 流式返回任务执行进度

    请求格式:
    {
        "task": "打开百度搜索人工智能",
        "timeout": 300.0  // 可选，默认 300 秒
    }

    响应格式（SSE）:
    data: {"chunk": "片段", "full_response": "完整响应", "status": "streaming"}

    """
    async def event_generator():
        try:
            # 发送开始事件
            yield f"data: {json.dumps({'status': 'started', 'task': request.task}, ensure_ascii=False)}\n\n"

            # 执行流式任务
            async for event in execute_stream_task(request.task):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            # 发送完成事件
            yield f"data: {json.dumps({'status': 'finished'}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"流式任务错误: {e}")
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 nginx 缓冲
        }
    )

# ============================================================================
# 兼容性别名端点
# ============================================================================

@app.post("/stream-task")
async def stream_task_alias(request: BrowserTask):
    """兼容性别名: /stream-task -> /browser/stream-task"""
    return await browser_stream_task(request)

# ============================================================================
# 启动和关闭事件
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logger.info("="*70)
    logger.info("🤖 iFlow 浏览器自动化服务启动")
    logger.info("="*70)
    logger.info(f"📌 iFlow URL: {IFLOW_URL}")
    logger.info(f"📌 MCP URL: {MCP_HTTP_URL}")
    logger.info(f"📌 监听端口: {PORT}")
    logger.info(f"📌 超时时间: {TIMEOUT}秒")
    logger.info("="*70)

@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    logger.info("🛑 iFlow 浏览器自动化服务关闭...")

# ============================================================================
# 主程序
# ============================================================================

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║      🤖 iFlow 浏览器自动化服务                                        ║
    ║      版本: 2.0.0                                                    ║
    ║      架构: FastAPI → iFlow SDK → MCP 浏览器                         ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)

    print(f"📌 配置:")
    print(f"   - iFlow URL: {IFLOW_URL}")
    print(f"   - MCP URL: {MCP_HTTP_URL}")
    print(f"   - 监听端口: {PORT}")
    print(f"   - 超时时间: {TIMEOUT}秒")
    print()
    print("📚 API 文档: http://localhost:8082/docs")
    print()
    print("🧪 测试方法:")
    print("   1. 前端: 打开 frontend/index.html")
    print("   2. 浏览器: curl -X POST http://localhost:8082/browser/stream-task -d '{\"task\":\"打开百度\"}'")
    print()
    print("⚠️  启动依赖:")
    print("   1. iflow --experimental-acp --port 8090")
    print("   2. uv run python src/server.py")
    print()

    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )