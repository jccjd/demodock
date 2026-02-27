---
name: system-control
description: 操作系统远程控制技能，支持 Linux 和 Windows 系统的远程操作、命令执行、文件管理等。适用于系统管理、自动化运维、远程故障排除等场景。
version: 1.0.0
category: System
tags:
  - linux
  - windows
  - remote-control
  - system-administration
  - automation
triggers:
  - "操作 Linux"
  - "远程执行命令"
  - "系统管理"
  - "系统登录"
  - "远程运维"
---

# 系统远程控制技能

## 概述

本技能通过 **vnc-control MCP 服务器** 提供操作系统远程控制能力：
- **系统登录**：自动登录 Linux/Windows 系统
- **命令执行**：执行系统命令
- **快捷键**：发送系统快捷键

## MCP 工具

| 工具 | 说明 | 参数 |
|------|------|------|
| `system_login` | 系统登录 | username, password, name |
| `system_execute_command` | 执行命令 | command, name |
| `system_send_shortcut` | 发送快捷键 | shortcut, name |

### 依赖工具

需要先使用 VNC 工具连接：
- `vnc_connect` - 连接到目标系统
- `vnc_screenshot` - 查看当前状态
- `vnc_type_text` - 输入文本
- `vnc_key_press` - 发送按键

---

## 系统登录

### Linux 系统登录

```
# 文本控制台登录
vnc_type_text(text="root")
vnc_key_press(key="enter")
# 等待密码提示
vnc_type_text(text="password")
vnc_key_press(key="enter")

# GUI 登录界面
vnc_type_text(text="password")  # 用户名通常已预选
vnc_key_press(key="enter")

# 或使用封装工具
system_login(username="root", password="password")
```

### Windows 系统登录

```
# Windows 登录界面通常只需密码
vnc_type_text(text="Password123!")
vnc_key_press(key="enter")

# 或使用封装工具
system_login(username="user", password="Password123!")
```

---

## 命令执行

### Linux 常用命令

```
# 系统信息
system_execute_command(command="uname -a")
system_execute_command(command="cat /etc/os-release")

# 网络管理
system_execute_command(command="ip addr")
system_execute_command(command="ping -c 4 8.8.8.8")

# 磁盘管理
system_execute_command(command="lsblk")
system_execute_command(command="df -h")

# 进程管理
system_execute_command(command="ps aux")
system_execute_command(command="systemctl status nginx")

# 软件管理 (Debian/Ubuntu)
system_execute_command(command="apt update")
system_execute_command(command="apt install nginx")
```

### Windows 常用命令

```
# 系统信息
system_execute_command(command="systeminfo")
system_execute_command(command="hostname")

# 网络管理
system_execute_command(command="ipconfig /all")
system_execute_command(command="ping 8.8.8.8")

# 进程管理
system_execute_command(command="tasklist")
system_execute_command(command="taskkill /PID 1234")

# 服务管理
system_execute_command(command="sc query")
system_execute_command(command="net start")
```

---

## 快捷键

### Linux (GNOME)

| 快捷键 | 功能 |
|--------|------|
| Ctrl+Alt+T | 打开终端 |
| Super | 打开活动概览 |
| Ctrl+Q | 关闭窗口 |
| Alt+F4 | 关闭窗口 |

### Windows

| 快捷键 | 功能 |
|--------|------|
| Win+R | 运行对话框 |
| Win+E | 打开资源管理器 |
| Win+I | 打开设置 |
| Ctrl+Shift+Esc | 任务管理器 |

**调用示例：**
```
system_send_shortcut(shortcut="ctrl+alt+t")  # 打开终端
```

---

## 完整示例

### 示例 1: 从 BIOS 进入 Linux 系统并执行命令

```
步骤 1: 连接 VNC
vnc_connect(host="10.8.136.182", port=5900, password="admin")

步骤 2: 查看当前状态
vnc_screenshot()

步骤 3: 如果在 BIOS，保存退出
uefi_save_exit()

步骤 4: 等待系统启动 (30-60秒)
# 多次截图查看进度

步骤 5: 登录系统
system_login(username="root", password="password")

步骤 6: 执行命令
system_execute_command(command="uname -a")
system_execute_command(command="ip addr")

步骤 7: 断开连接
vnc_disconnect()
```

### 示例 2: Windows 系统操作

```
步骤 1: 连接 VNC
vnc_connect(host="10.8.136.183", port=5900, password="admin")

步骤 2: 登录 Windows
system_login(username="Administrator", password="Password123!")

步骤 3: 打开 PowerShell
vnc_key_press(key="r")  # 需要 Win 组合
vnc_type_text(text="powershell")
vnc_key_press(key="enter")

步骤 4: 执行命令
system_execute_command(command="Get-Process")
system_execute_command(command="Get-Service")

步骤 5: 断开连接
vnc_disconnect()
```

---

## 最佳实践

### 操作间隔
- 按键之间: 50-100ms
- 等待界面加载: 1-3秒
- 等待系统启动: 30-120秒

### 安全注意
1. 不要在日志中记录密码
2. 操作完成后断开连接
3. 限制并发连接数

### 错误处理
1. 每次关键操作后截图验证
2. 如果输入无效，检查键盘布局
3. 命令执行超时后检查系统状态
