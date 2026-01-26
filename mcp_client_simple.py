#!/usr/bin/env python3
"""
浏览器 MCP 客户端 - 简化版
直接连接到 http://localhost:8080 的真实 MCP 服务器
"""

import asyncio
import httpx
import json
from typing import Dict, Any

class MCPClient:
    """MCP 客户端"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.request_id = 0
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """调用 MCP 工具"""
        self.request_id += 1
        
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            },
            "id": self.request_id
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

async def main():
    """主函数 - 演示浏览器自动化"""
    
    print("🚀 浏览器 MCP 客户端演示")
    print("=" * 50)
    print()
    
    # 连接到真实的 MCP 服务器
    mcp_client = MCPClient("http://localhost:8080/mcp")
    
    try:
        # 1. 导航到页面
        print("📍 步骤 1: 导航到 https://example.com")
        result = await mcp_client.call_tool("browser_navigate", {
            "url": "https://example.com"
        })
        
        if "result" in result and "content" in result["result"]:
            text = result["result"]["content"][0]["text"]
            print(f"✅ {text}")
        print()
        
        await asyncio.sleep(2)
        
        # 2. 截图
        print("📸 步骤 2: 获取页面截图")
        result = await mcp_client.call_tool("browser_screenshot")
        
        if "result" in result and "content" in result["result"]:
            text = result["result"]["content"][0]["text"]
            print(f"✅ {text}")
            
            # 如果有图片数据
            if len(result["result"]["content"]) > 1:
                image_data = result["result"]["content"][1]
                print(f"   图片尺寸: {image_data.get('data', 'N/A')[:50]}...")
        print()
        
        await asyncio.sleep(1)
        
        # 3. 获取页面文本
        print("📄 步骤 3: 获取页面文本")
        result = await mcp_client.call_tool("browser_get_text")
        
        if "result" in result and "content" in result["result"]:
            text = result["result"]["content"][0]["text"]
            print(f"✅ 页面内容:")
            print(f"   {text[:200]}...")
        print()
        
        await asyncio.sleep(1)
        
        # 4. 获取可点击元素
        print("🔍 步骤 4: 获取可点击元素")
        result = await mcp_client.call_tool("browser_get_clickable_elements")
        
        if "result" in result and "content" in result["result"]:
            text = result["result"]["content"][0]["text"]
            print(f"✅ {text[:200]}...")
        print()
        
        print("🎉 演示完成！")
        print()
        print("💡 提示: 你可以打开 VNC 查看器实时查看浏览器操作:")
        print("   http://localhost:8080/vnc/index.html?autoconnect=true")
        
    except httpx.HTTPError as e:
        print(f"❌ HTTP 错误: {e}")
        print("💡 请确保 AIO Sandbox MCP 服务器正在运行")
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())