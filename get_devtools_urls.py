import asyncio
import aiohttp
import json

async def get_devtools_urls():
    """获取 DevTools 调试 URL"""
    try:
        # 使用之前获取的端点
        devtools_url = "http://127.0.0.1:42872/proxy/9222/json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(devtools_url) as response:
                data = await response.text()
                print("DevTools 页面列表:")
                print(data)
                
                pages = json.loads(data)
                if pages:
                    print("\n可用的 WebSocket Debugger URLs:")
                    for page in pages:
                        ws_url = page.get("webSocketDebuggerUrl")
                        if ws_url:
                            print(f"  {ws_url}")
                            print(f"  标题: {page.get('title', 'N/A')}")
                            print(f"  URL: {page.get('url', 'N/A')}")
                            print()
                            return ws_url
                else:
                    print("未找到可用页面")
                    return None
    except Exception as e:
        print(f"获取 DevTools URLs 时出错: {e}")
        return None

if __name__ == "__main__":
    ws_url = asyncio.run(get_devtools_urls())
    if ws_url:
        print(f"\n将此 URL 复制到 screencast_viewer.html 中:")
        print(ws_url)