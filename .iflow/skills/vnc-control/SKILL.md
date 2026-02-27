---
name: vnc-control
description: VNC 远程控制技能，支持系统操作、UEFI/BIOS 操作，以及从 UEFI 进入 OS 的完整自动化流程。适用于虚拟机远程管理、系统安装、BIOS 配置等场景。
version: 1.0.0
category: System
tags:
  - vnc
  - remote-control
  - uefi
  - bios
  - virtual-machine
  - automation
triggers:
  - "操作 VNC"
  - "远程控制虚拟机"
  - "进入 BIOS"
  - "UEFI 设置"
  - "从 BIOS 启动系统"
  - "安装系统"
  - "虚拟机操作"
---

# VNC 远程控制技能

## 概述

本技能提供完整的 VNC 远程控制能力，通过 **vnc-control MCP 服务器** 提供的工具实现：
- **基础 VNC 操作**：连接、截图、键盘输入、鼠标操作
- **UEFI/BIOS 操作**：进入 BIOS、导航菜单、修改设置、保存退出
- **系统操作**：登录系统、执行命令
- **自动化流程**：从 UEFI 进入 OS 的完整流程

## MCP 工具列表

本技能依赖 `vnc-control` MCP 服务器提供的以下工具：

### VNC 连接工具

| 工具名 | 说明 | 参数 |
|--------|------|------|
| `vnc_connect` | 连接到 VNC 服务器 | host, port, password, name |
| `vnc_disconnect` | 断开 VNC 连接 | name |
| `vnc_screenshot` | 获取屏幕截图 | name, resize, quality |
| `vnc_status` | 获取连接状态 | - |

### VNC 输入工具

| 工具名 | 说明 | 参数 |
|--------|------|------|
| `vnc_key_press` | 发送按键 | key, count, name |
| `vnc_type_text` | 输入文本 | text, interval, name |
| `vnc_mouse_click` | 鼠标点击 | x, y, button, double, name |
| `vnc_mouse_move` | 移动鼠标 | x, y, name |

### UEFI/BIOS 工具

| 工具名 | 说明 | 参数 |
|--------|------|------|
| `uefi_enter` | 进入 UEFI/BIOS | key, name |
| `uefi_navigate` | 导航菜单 | direction, steps, name |
| `uefi_select` | 选择选项 (Enter) | name |
| `uefi_save_exit` | 保存并退出 (F10) | name |
| `uefi_set_boot_order` | 设置启动顺序 | devices[], name |

### 系统操作工具

| 工具名 | 说明 | 参数 |
|--------|------|------|
| `system_login` | 系统登录 | username, password, name |
| `system_execute_command` | 执行命令 | command, name |
| `system_send_shortcut` | 发送快捷键 | shortcut, name |

### 复合工具

| 工具名 | 说明 | 参数 |
|--------|------|------|
| `vnc_boot_to_os` | 完整启动流程 | host, port, password, username, user_password, timeout |

---

## 使用指南

### 1. 连接 VNC 服务器

**调用 MCP 工具：**
```
vnc_connect(
    host="10.8.136.182",
    port=5900,
    password="admin",
    name="default"
)
```

**返回示例：**
```
✅ 已连接到 VNC 服务器 10.8.136.182:5900 (名称: default)
```

### 2. 获取屏幕截图

```
vnc_screenshot(name="default", resize=800, quality=85)
```

返回 base64 编码的 JPEG 图像数据。

### 3. 发送按键

**常用按键名称：**
- 功能键：f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11, f12
- 方向键：up, down, left, right
- 编辑键：enter, escape, tab, backspace, delete, insert, home, end

```
vnc_key_press(key="f2", count=1, name="default")
```

### 4. 输入文本

```
vnc_type_text(text="root", interval=0.05, name="default")
```

### 5. 鼠标操作

```
vnc_mouse_click(x=400, y=300, button=1, double=False, name="default")
```

---

## UEFI/BIOS 操作流程

### 进入 BIOS

```
1. vnc_connect(host="10.8.136.182", port=5900, password="admin")
2. vnc_screenshot() # 查看当前状态
3. uefi_enter(key="f2") # 发送 F2 进入 BIOS
4. 等待 2-3 秒
5. vnc_screenshot() # 确认已进入
```

### 导航和设置

```
# 导航到 Boot 菜单
uefi_navigate(direction="right", steps=2)

# 选择选项
uefi_select()

# 设置启动顺序
uefi_set_boot_order(devices=["USB", "HDD", "Network"])

# 保存退出
uefi_save_exit()
```

---

## 完整示例：从 BIOS 启动到 Linux 系统

```
步骤 1: 连接 VNC
vnc_connect(host="10.8.136.182", port=5900, password="admin")

步骤 2: 获取屏幕状态
vnc_screenshot()

步骤 3: 如果在 BIOS，保存退出
uefi_save_exit()

步骤 4: 等待系统启动（约 30-60 秒）
# 可以多次截图查看进度

步骤 5: 登录系统
system_login(username="root", password="password")

步骤 6: 验证系统
system_execute_command(command="uname -a")

步骤 7: 断开连接
vnc_disconnect()
```

---

## 最佳实践

### 操作间隔
- 按键之间: 50-100ms
- 菜单导航后等待: 200-500ms
- 等待系统启动: 30-120秒

### 错误处理
1. 每次关键操作后截图验证
2. 如果操作未生效，重试最多 3 次
3. 超时后检查 VNC 连接状态

### 安全注意
1. 不要在日志中记录敏感密码
2. 操作完成后断开连接
3. 使用 name 参数管理多个连接

---

## 故障排除

### 无法连接 VNC
- 检查 VNC 服务器是否运行
- 检查网络连通性
- 确认端口和密码正确

### 无法进入 BIOS
- 尝试不同的进入键（F2/Del/Esc）
- 检查虚拟机是否支持 BIOS/UEFI
- 可能需要增加启动延迟

### 键盘输入无效
- 确认 VNC 连接正常
- 检查当前界面是否支持输入
- 尝试先点击界面获取焦点
