# iFlow DemoDock

基于 iFlow SDK + MCP 的智能浏览器自动化与虚拟机控制演示平台。

## 功能特性

- 🖥️ **VIBE Studio IDE** - 集成开发环境风格的操作界面
- 🤖 **AI Agent Protocol** - 通过自然语言控制浏览器和虚拟机
- 📺 **VNC 远程桌面** - 支持 OS Console 和 BMC Web 双模式
- 📋 **执行步骤追踪** - 实时显示任务执行步骤和状态
- 🔄 **WebSocket 实时通信** - 低延迟交互体验
- 🛠️ **系统控制技能** - 支持 UEFI/BIOS 操作和虚拟机管理

## 界面预览

```
┌─────────────────────────────────────────────────────────┐
│ VIBE STUDIO  │ Task: iFlow CLI Console    │ Online     │
├──────────────┬──────────────────────────────────────────┤
│ Execution    │  OS Console │ BMC Web                     │
│ Steps        ├──────────────────────────────────────────┤
│              │                                          │
│  ⏳ Step 1   │         VNC 远程桌面区域                 │
│  ✅ Step 2   │                                          │
│  ❌ Step 3   │                                          │
│              ├──────────────────────────────────────────┤
│              │  AI Agent │ System Logs    │   Online    │
│              ├──────────────────────────────────────────┤
│              │  ✓ Agent protocol active...              │
│              │  › 输入指令...                [Send]     │
└──────────────┴──────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+ (可选，用于前端开发)
- uv 包管理器

### 安装依赖

```bash
# 安装 uv (如果尚未安装)
pip install uv

# 同步项目依赖
uv sync
```

### 启动服务

**方式一：分别启动各服务**

```bash
# 终端 1 - 启动 iFlow ACP 服务器
iflow --experimental-acp --port 8090

# 终端 2 - 启动 Browser Server
uv run python src/server.py

# 终端 3 - 启动前端 HTTP 服务 (可选)
cd frontend && python -m http.server 8000
```

**方式二：使用批处理脚本 (Windows)**

```bash
# 一键启动所有服务
start_all.bat
```

### 访问界面

- **前端界面**: 打开 `frontend/index.html` 或访问 `http://localhost:8000`
- **API 文档**: http://localhost:8082/docs
- **VNC 代理**: http://localhost:6080

## 项目结构

```
demodock/
├── frontend/
│   ├── index.html          # VIBE Studio 主界面
│   ├── novnc/              # noVNC 客户端库
│   └── rfb.js              # RFB 协议支持
├── src/
│   ├── server.py           # FastAPI 后端服务
│   ├── mcp_vnc_server.py   # MCP VNC 服务
│   └── skills/             # iFlow 技能模块
│       ├── system_skill.py # 系统控制
│       ├── uefi_skill.py   # UEFI/BIOS 控制
│       └── vnc_skill.py    # VNC 控制
├── .iflow/
│   ├── settings.json       # iFlow 配置
│   └── skills/             # 技能配置
│       ├── system-control/
│       ├── uefi-control/
│       └── vnc-control/
├── pyproject.toml          # Python 项目配置
└── uv.lock                 # 依赖锁定文件
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务信息 |
| `/health` | GET | 健康检查 |
| `/docs` | GET | API 文档 (Swagger UI) |
| `/ws` | WebSocket | AI Agent 实时通信 |
| `/browser/stream-task` | POST | 流式执行任务 (SSE) |
| `/vm/control` | POST | 虚拟机控制 (start/stop/reboot) |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `IFLOW_URL` | `ws://localhost:8090/acp` | iFlow ACP 地址 |
| `MCP_HTTP_URL` | `http://localhost:8080/mcp` | MCP 服务地址 |
| `PORT` | `8082` | 服务端口 |
| `TIMEOUT` | `300.0` | 超时时间(秒) |

## iFlow 技能

项目内置三个系统控制技能：

### 1. system-control
操作系统远程控制，支持 Linux 和 Windows 的远程操作、命令执行、文件管理。

### 2. uefi-control
UEFI/BIOS 专用操作，提供 UEFI 界面导航、设置修改、启动配置等能力。

### 3. vnc-control
VNC 远程控制，支持系统操作、UEFI 操作，以及从 UEFI 进入 OS 的完整自动化流程。

## 示例指令

### 浏览器控制
- "打开百度搜索人工智能"
- "访问 GitHub 搜索 iFlow"

### 系统控制
- "列出当前目录文件"
- "检查系统资源使用情况"
- "分析项目代码结构"

### 虚拟机控制
- "启动虚拟机 test-vm"
- "重启目标机器"
- "进入 UEFI 设置界面"

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | Python 3.12+, FastAPI, uvicorn, websockets |
| **前端** | HTML5, CSS3, JavaScript, Tailwind CSS |
| **核心** | iFlow-cli-sdk, MCP Protocol, noVNC |
| **工具** | uv, marked.js |

## 开发指南

### 前端开发

```bash
cd frontend
# 直接打开 index.html 或使用 HTTP 服务器
python -m http.server 8000
```

### 后端开发

```bash
# 开发模式启动 (带热重载)
uv run uvicorn src.server:app --reload --port 8082
```

### 添加新技能

1. 在 `src/skills/` 创建技能模块
2. 在 `.iflow/skills/` 添加技能配置 (SKILL.md)
3. 在 `server.py` 中注册技能

## 故障排查

### 连接失败

如果前端显示"服务器离线"：

1. 检查 iFlow ACP 服务是否运行
2. 检查 Browser Server 是否运行
3. 检查端口是否被占用

### VNC 无法连接

1. 确认 VNC 代理服务已启动 (`start_vnc_proxy.bat`)
2. 检查防火墙设置
3. 确认目标机器 VNC 服务已开启

## 相关文档

- [AI VNC 控制指南](AI_VNC_GUIDE.md)
- [VNC 使用说明](README_VNC.md)
- [项目上下文](AGENTS.md)

## 许可证

MIT License