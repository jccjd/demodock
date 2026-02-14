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
from typing import AsyncGenerator, Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

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
IFLOW_URL = os.getenv("IFLOW_URL", "ws://localhost:8090/acp")
MCP_HTTP_URL = os.getenv("MCP_HTTP_URL", "http://localhost:8080/mcp")
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

        # 文件系统访问
        file_access=True,
        file_allowed_dirs=["/Users/zz/Desktop/codes/demodock"],

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
                    logger.debug(f"收到消息: {message}")

                    # 处理不同类型的消息
                    if hasattr(message, 'type'):
                        if message.type == 'assistant':
                            # AI 响应消息
                            chunk = ""
                            if hasattr(message, 'chunk') and message.chunk:
                                chunk = message.chunk.text or ""
                                full_response += chunk
                                # 发送流式响应
                                await websocket.send_text(json.dumps({
                                    'type': 'assistant',
                                    'chunk': chunk,
                                    'full_response': full_response,
                                    'status': 'streaming'
                                }, ensure_ascii=False))

                        elif message.type == 'tool_call':
                            # 工具调用消息
                            await websocket.send_text(json.dumps({
                                'type': 'tool_use',
                                'tool': message.tool_name if hasattr(message, 'tool_name') else message.label,
                                'status': message.status,
                                'args': getattr(message, 'arguments', {})
                            }, ensure_ascii=False))

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
        "endpoints": {
            "GET /": "服务信息",
            "GET /health": "健康检查",
            "POST /browser/stream-task": "流式执行浏览器任务"
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
    ║      版本: 2.1.0                                                    ║
    ║      架构: FastAPI → iFlow SDK → MCP 浏览器                          ║
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
    print("   2. 命令行: curl -X POST http://localhost:8082/browser/stream-task -d '{\"task\":\"打开百度\"}'")
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