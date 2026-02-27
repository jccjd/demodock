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


```
D:\apps\qemu\qemu-system-x86_64.exe -m 2G -smp 2 -cdrom D:\TinyCore-current.iso -boot menu=on,strict=on
  -vnc 127.0.0.1:1 -net nic -net user -accel whpx -display none
  
键盘有反应了
 D:\apps\qemu\qemu-system-x86_64.exe -m 2G -smp 2 -cdrom D:\TinyCore-current.iso -net nic -net user -
   display sdl
D:\apps\qemu\qemu-system-x86_64.exe -m 2G -smp 2 -cdrom D:\TinyCore-current.iso -net nic -net user -display sdl -vnc 127.0.0.1:1

   D:\apps\qemu\qemu-system-x86_64.exe -m 2G -smp 2 -drive if=pflash,format=raw,readonly=on,file
   =D:\apps\qemu\share\edk2-x86_64-code.fd -cdrom D:\TinyCore-current.iso -net nic -net user -display sdl
   -vnc 127.0.0.1:1
```

✦ 是的！安装后会安装到我们创建的虚拟磁盘 uefi_disk.qcow2 中，并且可以通过 UEFI 启动。
  安装位置：
   - 虚拟磁盘：D:\apps\qemu\uefi_disk.qcow2（20GB）
   - Ubuntu 会自动安装 UEFI 启动引导程序到虚拟磁盘

  安装完成后如何通过 UEFI 启动：

  安装完成后，Ubuntu 会在 UEFI 启动管理器中注册启动项。下次启动时：

   1. 重启虚拟机
   2. 在 UEFI 启动菜单中，您会看到：
      - ubuntu - 新安装的 Ubuntu 系统（从硬盘启动）
      - EFI Internal Shell - UEFI Shell
      - EFI DVD/CDROM - CD-ROM（如果还在）

   3. 选择 `ubuntu` 并按 Enter，就会从虚拟磁盘启动 Ubuntu

  当前配置说明：
   -drive file=uefi_disk.qcow2,format=qcow2,if=ide,index=0    # 虚拟硬盘（index=0，第一硬盘）
   -drive file=D:\ubuntu-22.04-live-server-amd64.iso,media=cdrom,if=ide,index=1  #
   安装光盘（index=1，第二光驱）

  安装完成后，Ubuntu 会配置 UEFI 启动，您可以从硬盘启动了。
