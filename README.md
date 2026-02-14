# iFlow DemoDock

基于 iFlow SDK + MCP 的浏览器自动化演示项目。

## 功能特性

- 🤖 流式浏览器自动化 - 通过自然语言控制浏览器
- 🔄 实时 WebSocket 通信 - 低延迟交互体验
- 📡 SSE 流式响应 - 支持流式任务执行
- 🎯 ACP 连接管理 - 智能连接复用和重连

## 快速开始

### 环境要求

- Python 3.14+
- uv (包管理器)

### 安装

```bash
# 安装 uv (如果尚未安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 初始化项目并安装依赖
uv add fastapi uvicorn websockets pydantic iflow-cli-sdk
```

### 运行

需要启动两个服务：

**终端 1 - 启动 iFlow ACP 服务器**

```bash
iflow --experimental-acp --port 8090
```

**终端 2 - 启动 FastAPI 服务器**

```bash
export PATH="$HOME/.local/bin:$PATH"
uv run python iflow_browser_server.py
```

FastAPI 服务器将在 `http://localhost:8082` 启动，iFlow ACP 运行在 `ws://localhost:8090/acp`。

### 使用界面

1. 打开 `ai_browser_chat.html` - AI 浏览器助手界面
2. 打开 `demo.html` - 集成演示环境 (IDE 风格)

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务信息 |
| `/health` | GET | 健康检查 |
| `/docs` | GET | API 文档 (Swagger UI) |
| `/browser/stream-task` | POST | 流式执行浏览器任务 |
| `/ws` | WebSocket | 实时通信 |

## 环境变量

```bash
IFLOW_URL=ws://localhost:8090/acp      # iFlow ACP 地址
MCP_HTTP_URL=http://localhost:8080/mcp # MCP 服务地址
PORT=8082                              # 服务端口
TIMEOUT=300.0                          # 超时时间(秒)
```

## 示例指令

- "打开百度搜索人工智能"
- "访问淘宝搜索手机"
- "打开知乎查看热门话题"
- "打开 GitHub 搜索 iFlow"

## 项目结构

```
demodock/
├── iflow_browser_server.py    # 主服务器
├── ai_browser_chat.html       # 浏览器助手前端
├── demo.html                  # 集成演示界面
├── pyproject.toml             # 项目配置
└── .venv/                     # 虚拟环境
```

## 技术栈

- **后端**: Python, FastAPI, uvicorn, websockets
- **前端**: HTML5, CSS3, JavaScript
- **核心**: iFlow-cli-sdk, MCP Protocol

## 许可证

MIT