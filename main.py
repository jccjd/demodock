#!/usr/bin/env python3
"""
FastAPI服务 - 作为用户浏览器和OpenSandbox之间的中间层
"""

import os
import logging
from datetime import timedelta
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
from contextlib import asynccontextmanager
import traceback

# 加载 .env 文件
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入OpenSandbox相关模块
try:
    from opensandbox import Sandbox
    from opensandbox.config import ConnectionConfig
    from opensandbox.models.sandboxes import SandboxImageSpec
except ImportError:
    logger.error("OpenSandbox SDK未安装，请运行: pip install opensandbox")
    raise

# 全局沙箱实例（用于演示目的，实际生产中可能需要连接池）
sandbox_instance = None
connection_config = ConnectionConfig(
    domain=os.getenv("SANDBOX_DOMAIN", "localhost:8081"),
    api_key=os.getenv("SANDBOX_API_KEY"),
    request_timeout=timedelta(seconds=120),
)

async def initialize_sandbox():
    """初始化沙箱实例"""
    global sandbox_instance
    try:
        if sandbox_instance is None:
            logger.info("正在创建沙箱环境...")
            sandbox_instance = await Sandbox.create(
                os.getenv(
                    "SANDBOX_IMAGE",
                    "sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:latest",
                ),
                connection_config=connection_config,
                env={
                    "IFLOW_apiKey": os.getenv("IFLOW_API_KEY"),
                    "IFLOW_baseUrl": os.getenv("IFLOW_BASE_URL", "https://apis.iflow.cn/v1"),
                    "IFLOW_modelName": os.getenv("IFLOW_MODEL_NAME", "qwen3-coder-plus"),
                },
            )
            logger.info("沙箱环境已创建！")
            
            # 安装iFlow CLI
            logger.info("正在安装 iFlow CLI...")
            install_exec = await sandbox_instance.commands.run(
                "npm install -g @iflow-ai/iflow-cli@latest"
            )
            
            # 检查安装日志
            if install_exec.logs.stdout:
                for msg in install_exec.logs.stdout:
                    logger.info(f"安装输出: {msg.text}")
            if install_exec.logs.stderr:
                for msg in install_exec.logs.stderr:
                    logger.error(f"安装错误: {msg.text}")
            if install_exec.error:
                error_msg = f"iFlow CLI 安装失败: {install_exec.error.name}: {install_exec.error.value}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            logger.info("iFlow CLI 安装成功！")
    except Exception as e:
        logger.error(f"初始化沙箱时出错: {e}")
        logger.error(traceback.format_exc())
        raise


async def ensure_sandbox_ready():
    """确保沙箱已准备好"""
    global sandbox_instance
    try:
        if sandbox_instance is None:
            await initialize_sandbox()
        else:
            # 简单检查沙箱是否仍然可用
            # 在实际应用中，这可能包括更详细的健康检查
            pass
    except Exception as e:
        logger.error(f"沙箱不可用，尝试重新初始化: {e}")
        sandbox_instance = None
        await initialize_sandbox()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时的初始化
    try:
        await initialize_sandbox()
        logger.info("应用启动完成")
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise
    yield
    # 关闭时的清理
    global sandbox_instance
    if sandbox_instance:
        try:
            await sandbox_instance.kill()
            logger.info("沙箱环境已清理")
        except Exception as e:
            logger.error(f"清理沙箱时出错: {e}")
        finally:
            sandbox_instance = None
    logger.info("应用已关闭")


app = FastAPI(
    title="OpenSandbox + iFlow CLI Gateway",
    description="一个安全的AI CLI网关服务，集成OpenSandbox沙箱环境",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录（如果存在）
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
else:
    # 如果没有static目录，我们直接提供index.html
    @app.get("/")
    async def read_root(request: Request):
        """提供前端界面"""
        try:
            return FileResponse("index.html")
        except FileNotFoundError:
            return {
                "message": "OpenSandbox + iFlow CLI Gateway",
                "status": "running",
                "config": {
                    "sandbox_domain": os.getenv("SANDBOX_DOMAIN", "localhost:8081"),
                    "sandbox_image": os.getenv(
                        "SANDBOX_IMAGE",
                        "sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:latest",
                    ),
                    "iflow_model": os.getenv("IFLOW_MODEL_NAME", "qwen3-coder-plus")
                }
            }

# 配置参数
DOMAIN = os.getenv("SANDBOX_DOMAIN", "localhost:8081")
API_KEY = os.getenv("SANDBOX_API_KEY")
IFLOW_API_KEY = os.getenv("IFLOW_API_KEY")
IFLOW_BASE_URL = os.getenv("IFLOW_BASE_URL", "https://apis.iflow.cn/v1")
IFLOW_MODEL_NAME = os.getenv("IFLOW_MODEL_NAME", "qwen3-coder-plus")
SANDBOX_IMAGE = os.getenv(
    "SANDBOX_IMAGE",
    "sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:latest",
)

class QueryRequest(BaseModel):
    """用户查询请求模型"""
    query: str
    timeout: Optional[int] = 120  # 超时时间（秒）


class QueryResponse(BaseModel):
    """查询响应模型"""
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    execution_logs: Optional[dict] = None


async def _print_execution_logs(execution) -> dict:
    """获取执行日志"""
    logs = {"stdout": [], "stderr": [], "error": None}
    
    if execution.logs.stdout:
        for msg in execution.logs.stdout:
            logs["stdout"].append(msg.text)
    if execution.logs.stderr:
        for msg in execution.logs.stderr:
            logs["stderr"].append(msg.text)
    if execution.error:
        logs["error"] = f"{execution.error.name}: {execution.error.value}"
    
    return logs


async def execute_query_in_sandbox(query: str) -> QueryResponse:
    """在沙箱中执行查询"""
    global sandbox_instance
    
    try:
        # 确保沙箱已准备好
        await ensure_sandbox_ready()
        
        logger.info(f"执行查询: {query[:100]}...")  # 只记录查询的前100个字符
        
        # 执行用户查询
        exec_result = await sandbox_instance.commands.run(f'iflow "{query}"')
        
        # 获取执行日志
        execution_logs = await _print_execution_logs(exec_result)
        
        if exec_result.error:
            error_msg = execution_logs["error"] or f"执行失败，错误代码: {exec_result.error.name}"
            logger.error(f"查询执行失败: {error_msg}")
            return QueryResponse(
                success=False,
                error=error_msg,
                execution_logs=execution_logs
            )
        
        # 合并stdout输出
        result = "\n".join(execution_logs["stdout"]) if execution_logs["stdout"] else "无输出"
        logger.info(f"查询执行成功，输出长度: {len(result)} 字符")
        
        return QueryResponse(
            success=True,
            result=result,
            execution_logs=execution_logs
        )
    
    except asyncio.TimeoutError:
        logger.error("查询执行超时")
        return QueryResponse(
            success=False,
            error="查询执行超时"
        )
    except Exception as e:
        logger.error(f"执行查询时出现错误: {e}")
        logger.error(traceback.format_exc())
        return QueryResponse(
            success=False,
            error=f"执行查询时出现错误: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"message": "服务器内部错误", "error": str(exc)}
    )


@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("FastAPI服务启动")
    logger.info(f"配置信息:")
    logger.info(f"  - 沙箱地址: {DOMAIN}")
    logger.info(f"  - 沙箱镜像: {SANDBOX_IMAGE}")
    logger.info(f"  - iFlow模型: {IFLOW_MODEL_NAME}")
    logger.info(f"  - iFlow地址: {IFLOW_BASE_URL}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    logger.info("FastAPI服务关闭")


@app.get("/api/status")
async def root():
    """API根路径，返回服务状态"""
    return {
        "message": "OpenSandbox + iFlow CLI Gateway",
        "status": "running",
        "config": {
            "sandbox_domain": DOMAIN,
            "sandbox_image": SANDBOX_IMAGE,
            "iflow_model": IFLOW_MODEL_NAME
        }
    }


@app.post("/query", response_model=QueryResponse)
async def query_ai(request: QueryRequest):
    """
    向AI发送查询请求
    """
    logger.info(f"收到查询请求: {request.query[:50]}...")
    
    try:
        response = await execute_query_in_sandbox(request.query)
        return response
    except Exception as e:
        logger.error(f"处理查询请求时出错: {e}")
        logger.error(traceback.format_exc())
        return QueryResponse(
            success=False,
            error=f"处理请求时出错: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        # 检查沙箱是否可用
        global sandbox_instance
        if sandbox_instance:
            # 尝试执行一个简单的命令来检查沙箱状态
            exec_result = await sandbox_instance.commands.run("echo 'health check'")
            if exec_result.error:
                return {"status": "unhealthy", "service": "opensandbox-iflow-gateway", "error": "沙箱不可用"}
        
        return {"status": "healthy", "service": "opensandbox-iflow-gateway"}
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {"status": "unhealthy", "service": "opensandbox-iflow-gateway", "error": str(e)}


@app.get("/status")
async def status():
    """详细状态信息"""
    return {
        "status": "running",
        "sandbox_ready": sandbox_instance is not None,
        "config": {
            "sandbox_domain": DOMAIN,
            "sandbox_image": SANDBOX_IMAGE,
            "iflow_model": IFLOW_MODEL_NAME
        }
    }


# 为index.html提供服务
@app.get("/index.html")
async def read_index():
    return FileResponse("index.html")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))  # Changed from 8000 to 8001 to avoid conflict
    logger.info(f"启动服务器，端口: {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)