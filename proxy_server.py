#!/usr/bin/env python3
"""
MCP 代理服务器 - 解决 CORS 问题
将浏览器的请求转发到 AIO Sandbox (8080)
"""

from aiohttp import web, ClientSession
import aiohttp_cors

async def proxy_handler(request: web.Request) -> web.Response:
    """代理 MCP 请求到 AIO Sandbox"""
    try:
        # 获取请求数据
        data = await request.json()
        
        # 转发到 AIO Sandbox
        async with ClientSession() as session:
            async with session.post(
                'http://localhost:8080/mcp',
                json=data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json, text/event-stream'
                }
            ) as response:
                # 获取响应数据
                result_data = await response.json()
                
                # 返回响应并添加 CORS 头
                return web.json_response(result_data, status=response.status)
                
    except Exception as e:
        return web.json_response({
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": f"代理错误: {str(e)}"
            }
        }, status=500)

async def create_app():
    app = web.Application()
    
    # CORS 配置 - 允许所有来源
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })
    
    # 添加路由
    resource = cors.add(app.router.add_resource('/mcp'))
    resource.add_route('POST', proxy_handler)
    
    return app

async def main():
    app = await create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, 'localhost', 8082)
    print("🚀 MCP 代理服务器已启动")
    print("📡 代理地址: http://localhost:8082/mcp")
    print("🔄 转发到: http://localhost:8080/mcp (AIO Sandbox)")
    print("\n按 Ctrl+C 停止服务器")
    
    await site.start()
    
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("\n正在停止代理服务器...")
    finally:
        await runner.cleanup()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())