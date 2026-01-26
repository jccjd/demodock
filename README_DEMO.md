# 浏览器 MCP 服务器 - 高级自动化演示

这是一个使用浏览器 MCP 服务器进行高级自动化的演示界面，支持实时显示操作过程。

## 📋 功能特性

- ✅ 实时浏览器操作监控
- ✅ 动态截图显示
- ✅ 操作日志记录
- ✅ 元素信息展示
- ✅ WebSocket 实时通信
- ✅ 多种预设操作
- ✅ 完整工作流演示

## 🚀 快速开始

### 1. 安装依赖

```bash
pip3 install aiohttp aiohttp-cors
```

### 2. 启动服务器

```bash
./start_demo.sh
```

或者直接运行：

```bash
python3 browser_mcp_server.py
```

### 3. 访问演示页面

在浏览器中打开：

```
http://localhost:8080/
```

## 📖 使用说明

### 控制面板

- **MCP 服务器地址**: 设置浏览器 MCP 服务器的地址
- **目标 URL**: 设置要访问的网页地址

### 按钮功能

- **开始演示**: 启动浏览器自动化演示
- **停止**: 停止当前演示
- **清空日志**: 清除操作日志

### 预设操作

1. **导航**: 导航到指定的 URL
2. **截图**: 获取当前页面的截图
3. **获取文本**: 提取页面的文本内容
4. **获取元素**: 获取页面上可点击的元素
5. **执行JS**: 在页面中执行 JavaScript 代码
6. **完整流程**: 执行完整的自动化工作流

### 实时显示区域

- **实时截图**: 显示浏览器当前页面的截图
- **操作日志**: 记录所有操作和系统消息
- **状态信息**: 显示连接状态、当前页面、操作次数等
- **元素信息**: 显示页面上可点击的元素列表

## 🔧 MCP 工具 API

服务器支持以下 MCP 工具：

### 导航和基本操作

- `browser_navigate` - 导航到 URL
- `browser_close` - 关闭浏览器

### 内容检索

- `browser_screenshot` - 截图
- `browser_get_text` - 获取页面文本内容
- `browser_get_clickable_elements` - 获取可点击元素

### 高级功能

- `browser_evaluate` - 执行 JavaScript

## 📡 API 接口

### HTTP 接口

```
POST http://localhost:8080/mcp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "browser_navigate",
    "arguments": {
      "url": "https://example.com"
    }
  },
  "id": 1
}
```

### WebSocket 接口

```
ws://localhost:8080/ws
```

连接后发送 JSON-RPC 请求，接收实时响应。

### 状态接口

```
GET http://localhost:8080/status
```

返回服务器当前状态。

## 🎯 完整工作流示例

完整工作流包括以下步骤：

1. 导航到目标页面
2. 获取页面截图
3. 提取页面文本内容
4. 获取可点击元素
5. 执行 JavaScript 代码
6. 再次截图确认结果

## 📝 示例代码

### Python 客户端

```python
import asyncio
import aiohttp

async def browser_automation():
    async with aiohttp.ClientSession() as session:
        # 导航到页面
        async with session.post('http://localhost:8080/mcp', json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "browser_navigate",
                "arguments": {"url": "https://example.com"}
            },
            "id": 1
        }) as response:
            result = await response.json()
            print(result)

asyncio.run(browser_automation())
```

### JavaScript 客户端

```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onopen = function() {
    ws.send(JSON.stringify({
        jsonrpc: '2.0',
        method: 'tools/call',
        params: {
            name: 'browser_navigate',
            arguments: { url: 'https://example.com' }
        },
        id: 1
    }));
};

ws.onmessage = function(event) {
    const response = JSON.parse(event.data);
    console.log(response);
};
```

## 🛠️ 技术栈

- **后端**: Python 3 + aiohttp
- **前端**: HTML5 + CSS3 + JavaScript
- **通信**: WebSocket + HTTP
- **协议**: JSON-RPC 2.0

## 📂 文件结构

```
demodock/
├── browser_mcp_demo.html      # HTML 主界面
├── browser_mcp_demo.css       # CSS 样式文件
├── browser_mcp_demo.js        # JavaScript 前端逻辑
├── browser_mcp_server.py      # Python 后端服务器
├── start_demo.sh              # 启动脚本
└── README_DEMO.md             # 说明文档
```

## 🎨 界面预览

演示界面包含：

- 左侧控制面板：配置和操作按钮
- 右侧显示区域：截图、日志、状态、元素信息

界面采用现代化设计，支持响应式布局。

## 🔍 调试技巧

1. **查看日志**: 所有操作都会记录在操作日志中
2. **检查状态**: 状态信息区域显示当前连接和页面状态
3. **实时截图**: 每 5 秒自动更新截图（演示运行时）

## 📌 注意事项

- 这是一个演示系统，使用模拟的浏览器状态
- 实际使用时需要连接到真实的浏览器 MCP 服务器
- WebSocket 连接需要保持活跃状态
- 建议在虚拟环境中运行

## 🚧 未来扩展

可以扩展以下功能：

- 支持更多浏览器操作（点击、输入、滚动等）
- 集成真实的浏览器（如 Playwright、Selenium）
- 添加更多预设操作和模板
- 支持多标签页管理
- 添加性能监控和报告

## 📞 支持

如有问题或建议，请查看相关文档或联系开发团队。

---

**享受浏览器自动化的乐趣！** 🎉