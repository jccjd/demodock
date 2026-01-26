# 浏览器 MCP 服务器演示

使用真实的 AIO Sandbox 浏览器 MCP 服务器进行浏览器自动化演示。

## 🚀 快速开始

### 1. 确保服务器运行

AIO Sandbox MCP 服务器应该已经在 `http://localhost:8080` 运行。

### 2. 访问演示界面

**方法一：使用启动脚本（推荐）**

```bash
./start_web_demo.sh
```

然后在浏览器中打开：`http://localhost:3000/browser_mcp_demo.html`

**方法二：直接打开文件**

在浏览器中打开：

```
file:///home/f/demodock/browser_mcp_demo.html
```

⚠️ 注意：直接打开文件可能会遇到 CORS 跨域问题。如果遇到请求失败，请使用方法一。

**方法三：手动启动 HTTP 服务器**

```bash
python3 -m http.server 3000
```

然后访问：`http://localhost:3000/browser_mcp_demo.html`

### 3. 使用 VNC 查看器

实时查看浏览器操作：

```
http://localhost:8080/vnc/index.html?autoconnect=true
```

## 📋 功能

- ✅ 导航到指定 URL
- ✅ 获取页面截图
- ✅ 提取页面文本
- ✅ 获取可点击元素
- ✅ 完整工作流演示
- ✅ 实时日志显示
- ✅ VNC 实时浏览器视图

## 🐍 Python 客户端

运行简化版 Python 客户端：

```bash
python3 mcp_client_simple.py
```

## 📡 MCP API

### 导航到页面

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "browser_navigate",
      "arguments": {"url": "https://example.com"}
    },
    "id": 1
  }'
```

### 获取截图

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "browser_screenshot"
    },
    "id": 2
  }'
```

### 获取页面文本

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "browser_get_text"
    },
    "id": 3
  }'
```

### 获取可点击元素

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "browser_get_clickable_elements"
    },
    "id": 4
  }'
```

## 📂 文件说明

- `browser_mcp_demo.html` - Web 演示界面
- `mcp_client_simple.py` - Python 客户端示例
- `README.md` - 本文档

## 💡 提示

1. 确保在操作前打开 VNC 查看器，可以实时看到浏览器操作
2. Web 界面和 Python 客户端可以同时使用
3. 所有操作都会记录在日志中

## 🔗 相关链接

- AIO Sandbox: http://localhost:8080
- VNC 查看器: http://localhost:8080/vnc/index.html?autoconnect=true
- MCP API: http://localhost:8080/mcp