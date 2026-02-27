---
name: uefi-control
description: UEFI/BIOS 专用操作技能，提供详细的 UEFI 界面导航、设置修改、启动配置等能力。适用于虚拟机 BIOS 配置、系统安装引导、硬件设置等场景。
version: 1.0.0
category: System
tags:
  - uefi
  - bios
  - boot
  - firmware
  - virtual-machine
triggers:
  - "进入 BIOS"
  - "UEFI 设置"
  - "BIOS 配置"
  - "修改启动顺序"
  - "设置 BIOS"
---

# UEFI/BIOS 操作技能

## 概述

本技能专门用于 UEFI/BIOS 环境的操作，通过 **vnc-control MCP 服务器** 提供的工具实现：
- 进入 BIOS 的各种方法
- UEFI 界面导航
- 常见 BIOS 设置任务
- 启动配置

## MCP 工具

| 工具 | 说明 | 参数 |
|------|------|------|
| `uefi_enter` | 进入 BIOS | key (f2/del/esc), name |
| `uefi_navigate` | 导航菜单 | direction, steps, name |
| `uefi_select` | 选择选项 (Enter) | name |
| `uefi_save_exit` | 保存退出 (F10) | name |
| `uefi_set_boot_order` | 设置启动顺序 | devices[], name |

---

## 进入 BIOS 的方法

### 常见进入按键

| 厂商/平台 | 按键 |
|-----------|------|
| 大多数主板/虚拟机 | F2 |
| 传统主板 (ASUS, MSI) | Del |
| HP 部分机型 | Esc |
| 启动菜单选择 | F12 |

**调用示例：**
```
uefi_enter(key="f2")
```

### 通过 OS 重启进入

Windows 命令：
```
shutdown /r /fw /t 0
```

Linux 命令：
```
systemctl reboot --firmware-setup
```

---

## UEFI 界面导航

### 键盘导航

| 按键 | 功能 |
|------|------|
| ↑/↓ | 上下选择菜单项 |
| ←/→ | 切换标签页/菜单页 |
| Enter | 确认/进入子菜单 |
| Escape | 返回/退出 |
| F1 | 帮助 |
| F9 | 恢复默认设置 |
| F10 | 保存并退出 |
| +/-/F5/F6 | 调整值/顺序 |

**导航示例：**
```
# 向右切换 2 个标签页
uefi_navigate(direction="right", steps=2)

# 向下选择 3 个选项
uefi_navigate(direction="down", steps=3)

# 确认选择
uefi_select()
```

---

## 常见配置任务

### 设置启动顺序

```
# 设置 USB 为第一启动项
uefi_set_boot_order(devices=["USB", "HDD", "Network"])
uefi_save_exit()
```

### 启用虚拟化

```
# 导航到 Advanced -> CPU Configuration
uefi_navigate(direction="right", steps=1)  # Advanced
uefi_navigate(direction="down", steps=2)   # CPU Configuration
uefi_select()
uefi_navigate(direction="down", steps=3)   # 找到 VT-x
uefi_select()
uefi_navigate(direction="down")            # 选择 Enabled
uefi_select()
uefi_save_exit()
```

### 禁用 Secure Boot

```
# 导航到 Boot -> Secure Boot
uefi_navigate(direction="right", steps=2)  # Boot
uefi_navigate(direction="down", steps=4)   # Secure Boot
uefi_select()
uefi_navigate(direction="down")            # Disabled
uefi_select()
uefi_save_exit()
```

---

## UEFI 菜单结构

大多数 UEFI 界面的菜单结构：

```
Main (主菜单)
├── System Overview
├── Processor
└── Memory

Advanced (高级)
├── CPU Configuration
│   ├── Virtualization Technology
│   └── Hyper-Threading
├── SATA Configuration
└── USB Configuration

Boot (启动)
├── Boot Priority
├── Boot Mode (UEFI/Legacy)
├── Secure Boot
└── Boot Override

Security (安全)
├── Administrator Password
└── Secure Boot Settings

Save & Exit (保存退出)
├── Save Changes
├── Discard Changes
└── Load Defaults
```

---

## 虚拟机 BIOS 注意事项

### KVM/QEMU
- 默认 F2 进入 BIOS
- UEFI 需要配置 OVMF 固件

### VMware
- F2 进入 BIOS Setup
- Esc 显示启动菜单

### VirtualBox
- F12 显示启动菜单
- 可设置启动延迟

---

## 完整示例：配置虚拟机从 USB 启动

```
步骤 1: 连接 VNC
vnc_connect(host="10.8.136.182", port=5900, password="admin")

步骤 2: 查看当前状态
vnc_screenshot()

步骤 3: 进入 BIOS
uefi_enter(key="f2")
# 等待 2-3 秒

步骤 4: 导航到 Boot 菜单
uefi_navigate(direction="right", steps=2)

步骤 5: 设置启动顺序
uefi_set_boot_order(devices=["USB", "HDD"])

步骤 6: 保存退出
uefi_save_exit()

步骤 7: 验证重启
vnc_screenshot()
```

---

## 故障排除

### 无法进入 BIOS
1. 尝试不同按键 (F2/Del/Esc)
2. 增加虚拟机启动延迟
3. 检查是否已进入 BIOS（界面可能不同）

### 设置不生效
1. 确保使用 F10 保存退出
2. 检查是否需要管理员密码
3. 确认硬件支持该功能

### 启动设备不显示
1. 检查设备是否正确连接
2. 检查 UEFI/Legacy 模式兼容性
3. 确认设备有有效引导记录
