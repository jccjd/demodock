#!/usr/bin/env python3
"""
MCP FastAPI 代理服务器
架构: 用户界面 → FastAPI → MCP (AIO Sandbox)
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from typing import Dict, Any
import uvicorn

app = FastAPI(title="MCP Proxy Server", version="1.0.0")

# CORS 配置 - 允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MCP 后端地址
MCP_BACKEND_URL = "http://localhost:8080/mcp"


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "MCP Proxy Server",
        "version": "1.0.0",
        "backend": MCP_BACKEND_URL,
        "status": "running"
    }


@app.get("/health")
async def health():
    """健康检查"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8080/health")
            return {
                "status": "healthy",
                "backend": "connected",
                "backend_status": response.status_code
            }
    except Exception as e:
        return {
            "status": "degraded",
            "backend": "disconnected",
            "error": str(e)
        }


@app.post("/mcp")
async def proxy_mcp(request: Request):
    """
    代理 MCP 请求到 AIO Sandbox
    这是标准的 FastAPI → MCP 架构
    """
    try:
        # 获取请求体
        request_data = await request.json()
        
        # 转发到 MCP 后端
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                MCP_BACKEND_URL,
                json=request_data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )
            
            # 返回 MCP 的响应
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
            
    except httpx.TimeoutException:
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": request_data.get("id") if request_data else None,
                "error": {
                    "code": -32000,
                    "message": "请求超时: MCP 后端响应时间过长"
                }
            },
            status_code=504
        )
    except httpx.ConnectError:
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": request_data.get("id") if request_data else None,
                "error": {
                    "code": -32001,
                    "message": "连接失败: 无法连接到 MCP 后端"
                }
            },
            status_code=503
        )
    except Exception as e:
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": request_data.get("id") if request_data else None,
                "error": {
                    "code": -32603,
                    "message": f"代理错误: {str(e)}"
                }
            },
            status_code=500
        )


@app.get("/status")
async def status():
    """获取代理服务器状态"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # 测试 MCP 后端连接
            response = await client.post(
                MCP_BACKEND_URL,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 1
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )
            
            backend_connected = response.status_code == 200
            
            return {
                "proxy": {
                    "status": "running",
                    "version": "1.0.0",
                    "framework": "FastAPI"
                },
                "backend": {
                    "url": MCP_BACKEND_URL,
                    "connected": backend_connected,
                    "status_code": response.status_code
                }
            }
    except Exception as e:
        return {
            "proxy": {
                "status": "running",
                "version": "1.0.0",
                "framework": "FastAPI"
            },
            "backend": {
                "url": MCP_BACKEND_URL,
                "connected": False,
                "error": str(e)
            }
        }


if __name__ == "__main__":
    print("🚀 MCP FastAPI 代理服务器")
    print("=" * 50)
    print("📋 架构: 用户界面 → FastAPI → MCP (AIO Sandbox)")
    print(f"📡 FastAPI 服务: http://localhost:8082")
    print(f"🔄 MCP 后端:    {MCP_BACKEND_URL}")
    print(f"📊 状态页面:    http://localhost:8082/status")
    print(f"💚 健康检查:    http://localhost:8082/health")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="localhost",
        port=8082,
        log_level="info"
    )