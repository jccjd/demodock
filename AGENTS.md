# iFlow DemoDock 项目

## 项目概述

**iFlow DemoDock** 是一个基于 iFlow SDK + MCP 的浏览器自动化演示项目。

### 核心功能

- **流式浏览器自动化**: 通过 iFlow SDK 连接到 MCP 浏览器服务
- **WebSocket 实时通信**: 前端通过 WebSocket 进行实时交互
- **SSE 流式响应**: Server-Sent Events 流式任务执行

### 技术栈

- **后端**: Python 3.14+, FastAPI, uvicorn, websockets
- **前端**: HTML5, CSS3, JavaScript, Tailwind CSS
- **核心依赖**: iflow-cli-sdk, pydantic

## 项目结构

```
demodock/
├── src/
│   └── server.py          # FastAPI 后端服务
├── frontend/
│   └── index.html         # 前端界面 (VIBE Studio)
├── .iflow/                # iFlow 配置
├── pyproject.toml         # 项目配置
├── uv.lock                # 依赖锁定
└── AGENTS.md              # 本文档
```

## 启动服务

### 环境要求

- Python 3.14+
- uv 包管理器

### 安装依赖

```bash
uv sync
```

### 启动步骤

**终端 1 - 启动 iFlow ACP 服务器**
```bash
iflow --experimental-acp --port 8090
```

**终端 2 - 启动 Browser Server**
```bash
uv run python src/server.py
```

服务启动后：
- 后端 API: http://localhost:8082
- 前端界面: 打开 `frontend/index.html`
- API 文档: http://localhost:8082/docs

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务信息 |
| `/health` | GET | 健康检查 |
| `/docs` | GET | API 文档 |
| `/ws` | WebSocket | 实时通信 |
| `/browser/stream-task` | POST | 流式执行任务 (SSE) |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `IFLOW_URL` | `ws://localhost:8090/acp` | iFlow ACP 地址 |
| `MCP_HTTP_URL` | `http://localhost:8080/mcp` | MCP 服务地址 |
| `PORT` | `8082` | 服务端口 |
| `TIMEOUT` | `300.0` | 超时时间(秒) |

## 故障排查

### 连接失败

如果前端显示"服务器离线"，请检查：

1. iFlow ACP 服务是否运行
   ```bash
   iflow --experimental-acp --port 8090
   ```

2. Browser Server 是否运行
   ```bash
   uv run python src/server.py
   ```

3. 端口是否被占用
   ```bash
   lsof -i :8082
   lsof -i :8090
   ```

## 依赖版本

| 包 | 版本 |
|----|------|
| fastapi | >=0.129.0 |
| uvicorn | >=0.40.0 |
| websockets | >=16.0 |
| pydantic | >=2.12.5 |
| iflow-cli-sdk | ==0.1.11 |