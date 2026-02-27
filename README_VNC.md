# QEMU VNC Web 代理设置指南

## 概述

本指南介绍如何使用 websockify 将 QEMU VNC 连接代理到 Web 浏览器。

## 快速开始

### 1. 启动 QEMU 虚拟机

确保 QEMU 使用以下 VNC 参数启动：

```cmd
D:\apps\qemu\qemu-system-x86_64.exe -m 2G -smp 2 ^
-drive if=pflash,format=raw,readonly=on,file=D:\apps\qemu\share\edk2-x86_64-code.fd ^
-cdrom D:\TinyCore-current.iso ^
-net nic -net user ^
-display sdl ^
-vnc 127.0.0.1:1
```

**重要**: `-vnc 127.0.0.1:1` 表示 VNC 服务器运行在 `127.0.0.1:5901`（端口 = 5900 + 显示编号）

### 2. 启动 websockify 代理

双击运行 `start_vnc_proxy.bat` 或在命令行中执行：

```cmd
start_vnc_proxy.bat
```

这将启动 websockify 服务，监听 `localhost:6080` 并代理到 `127.0.0.1:5901`

### 3. 访问 Web VNC 客户端

在浏览器中打开 `frontend/vnc.html` 文件，或使用本地服务器：

```cmd
python -m http.server 8080 --directory frontend
```

然后访问: `http://localhost:8080/vnc.html`

## 端口映射

| 服务 | 地址 | 说明 |
|------|------|------|
| QEMU VNC | `127.0.0.1:5901` | QEMU VNC 服务器 (`-vnc 127.0.0.1:1`) |
| WebSocket | `localhost:6080` | websockify WebSocket 代理端口 |
| Web 客户端 | `http://localhost:8080` | VNC Web 界面 |

## 技术栈

- **websockify**: WebSocket 到 TCP 的代理/桥接器
- **noVNC**: 基于 HTML5 的 VNC 客户端
- **QEMU**: 虚拟机模拟器

## 故障排查

### 无法连接到 VNC

1. 确认 QEMU 正在运行且使用了 `-vnc` 参数
2. 检查 websockify 是否正在运行（应该看到 "WebSocket server settings" 输出）
3. 验证端口没有被占用：

```cmd
netstat -ano | findstr "6080"
netstat -ano | findstr "5901"
```

### WebSocket 连接失败

1. 检查浏览器控制台是否有错误信息
2. 确认 websockify 正在监听正确的端口
3. 尝试使用不同的浏览器（推荐 Chrome 或 Firefox）

### VNC 显示黑屏

1. 确认 QEMU 虚拟机已经正常启动
2. 检查 VNC 显示编号是否正确（`:1` = `5901`, `:0` = `5900`）
3. 验证 QEMU 是否支持 SDL 显示

## 高级配置

### 修改 WebSocket 端口

编辑 `start_vnc_proxy.bat`:

```bat
uv run websockify <新端口> 127.0.0.1:5901
```

同时需要在 `vnc.html` 中更新端口输入框的默认值。

### 修改 VNC 目标

编辑 `start_vnc_proxy.bat`:

```bat
uv run websockify 6080 <VNC主机>:<VNC端口>
```

例如连接到远程 VNC:

```bat
uv run websockify 6080 192.168.1.100:5901
```

### 添加 VNC 密码

如果 VNC 服务器设置了密码，可以在 `vnc.html` 中输入密码连接。

## 参考资源

- [websockify GitHub](https://github.com/novnc/websockify)
- [noVNC GitHub](https://github.com/novnc/noVNC)
- [QEMU 文档](https://www.qemu.org/docs/master/system/invocation.html)

## 许可证

本项目遵循与 websockify 和 noVNC 相同的开源许可证。