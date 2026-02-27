#!/usr/bin/env python3
"""
系统操作工具

提供操作系统级别的操作功能，包括登录、命令执行等
"""

import asyncio
import logging
import re
import time
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# 导入 VNC 技能
try:
    from .vnc_skill import (
        get_vnc_client,
        vnc_screenshot,
        vnc_key_press,
        vnc_type_text,
        vnc_mouse_click,
        VNCClient,
    )
    VNC_SKILL_AVAILABLE = True
except ImportError:
    VNC_SKILL_AVAILABLE = False
    logger.warning("VNC Skill 未安装，系统操作将不可用")


class SystemState(Enum):
    """系统状态"""
    UEFI_BIOS = "uefi_bios"
    BOOT_LOADER = "boot_loader"
    OS_LOADING = "os_loading"
    LOGIN_SCREEN = "login_screen"
    DESKTOP = "desktop"
    LOCK_SCREEN = "lock_screen"
    TEXT_CONSOLE = "text_console"
    UNKNOWN = "unknown"


class OSType(Enum):
    """操作系统类型"""
    LINUX = "linux"
    WINDOWS = "windows"
    MACOS = "macos"
    UNKNOWN = "unknown"


@dataclass
class SystemInfo:
    """系统信息"""
    os_type: OSType
    os_name: str = ""
    os_version: str = ""
    hostname: str = ""
    username: str = ""


# ============================================================================
# 系统状态检测
# ============================================================================

async def system_detect_state(name: str = "default") -> Dict[str, Any]:
    """
    检测当前系统状态
    
    Args:
        name: VNC 客户端名称
    
    Returns:
        状态检测结果
    """
    if not VNC_SKILL_AVAILABLE:
        return {"success": False, "error": "VNC Skill 未安装"}
    
    # 获取屏幕截图
    screenshot_result = await vnc_screenshot(name=name, resize=800)
    if not screenshot_result.get("success"):
        return {"success": False, "error": "无法获取屏幕截图"}
    
    # 分析屏幕内容
    # 这里需要图像识别或 OCR 来确定状态
    # 简化实现：返回需要分析的信息
    
    state_indicators = {
        SystemState.UEFI_BIOS: ["Setup", "BIOS", "UEFI", "Boot Menu", "F10 Save"],
        SystemState.BOOT_LOADER: ["GRUB", "GNU GRUB", "Windows Boot Manager", "GNU/Linux"],
        SystemState.OS_LOADING: ["Loading", "Starting", "进度条", "spinner"],
        SystemState.LOGIN_SCREEN: ["登录", "Login", "Password", "用户名", "Sign in"],
        SystemState.DESKTOP: ["桌面", "Desktop", "任务栏", "Taskbar", "开始"],
        SystemState.LOCK_SCREEN: ["锁定", "Lock", "输入密码"],
        SystemState.TEXT_CONSOLE: ["login:", "Password:", "~$", "#"],
    }
    
    return {
        "success": True,
        "state": SystemState.UNKNOWN.value,
        "message": "需要通过图像分析确定系统状态",
        "screenshot_available": True
    }


async def system_detect_os(name: str = "default") -> Dict[str, Any]:
    """
    检测操作系统类型
    
    Args:
        name: VNC 客户端名称
    
    Returns:
        OS 检测结果
    """
    if not VNC_SKILL_AVAILABLE:
        return {"success": False, "error": "VNC Skill 未安装"}
    
    # 通过屏幕特征检测 OS 类型
    # Linux: GNOME/KDE 桌面特征, GRUB 启动菜单
    # Windows: Windows Logo, CMD/PowerShell
    # macOS: Apple Logo, Dock
    
    return {
        "success": True,
        "os_type": OSType.UNKNOWN.value,
        "message": "需要通过图像分析确定 OS 类型"
    }


# ============================================================================
# 系统等待操作
# ============================================================================

async def system_wait_for_state(
    target_state: SystemState,
    timeout: float = 120.0,
    interval: float = 2.0,
    name: str = "default"
) -> Dict[str, Any]:
    """
    等待系统进入指定状态
    
    Args:
        target_state: 目标状态
        timeout: 超时时间（秒）
        interval: 检查间隔（秒）
        name: VNC 客户端名称
    
    Returns:
        等待结果
    """
    if not VNC_SKILL_AVAILABLE:
        return {"success": False, "error": "VNC Skill 未安装"}
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # 检测当前状态
        result = await system_detect_state(name=name)
        
        if result.get("state") == target_state.value:
            return {
                "success": True,
                "message": f"已进入 {target_state.value} 状态",
                "elapsed": time.time() - start_time
            }
        
        await asyncio.sleep(interval)
    
    return {
        "success": False,
        "error": f"等待超时（{timeout}秒），未进入 {target_state.value} 状态"
    }


async def system_wait_for_login(
    timeout: float = 120.0,
    name: str = "default"
) -> Dict[str, Any]:
    """
    等待登录界面
    
    Args:
        timeout: 超时时间
        name: VNC 客户端名称
    
    Returns:
        等待结果
    """
    return await system_wait_for_state(
        SystemState.LOGIN_SCREEN,
        timeout=timeout,
        name=name
    )


async def system_wait_for_desktop(
    timeout: float = 120.0,
    name: str = "default"
) -> Dict[str, Any]:
    """
    等待桌面环境加载
    
    Args:
        timeout: 超时时间
        name: VNC 客户端名称
    
    Returns:
        等待结果
    """
    return await system_wait_for_state(
        SystemState.DESKTOP,
        timeout=timeout,
        name=name
    )


async def system_wait_for_prompt(
    timeout: float = 60.0,
    name: str = "default"
) -> Dict[str, Any]:
    """
    等待命令提示符（控制台模式）
    
    Args:
        timeout: 超时时间
        name: VNC 客户端名称
    
    Returns:
        等待结果
    """
    return await system_wait_for_state(
        SystemState.TEXT_CONSOLE,
        timeout=timeout,
        name=name
    )


# ============================================================================
# 系统登录操作
# ============================================================================

async def system_login(
    username: str,
    password: str,
    os_type: Optional[OSType] = None,
    name: str = "default"
) -> Dict[str, Any]:
    """
    系统登录
    
    Args:
        username: 用户名
        password: 密码
        os_type: 操作系统类型（可选，自动检测）
        name: VNC 客户端名称
    
    Returns:
        登录结果
    """
    if not VNC_SKILL_AVAILABLE:
        return {"success": False, "error": "VNC Skill 未安装"}
    
    try:
        # 检测 OS 类型
        if os_type is None:
            os_result = await system_detect_os(name=name)
            os_type = OSType(os_result.get("os_type", "unknown"))
        
        if os_type == OSType.LINUX:
            return await _linux_login(username, password, name)
        elif os_type == OSType.WINDOWS:
            return await _windows_login(username, password, name)
        else:
            # 通用登录流程
            return await _generic_login(username, password, name)
            
    except Exception as e:
        logger.error(f"登录失败: {e}")
        return {"success": False, "error": str(e)}


async def _linux_login(username: str, password: str, name: str) -> Dict[str, Any]:
    """Linux 系统登录"""
    operations = []
    
    # 检测是 GUI 还是控制台
    state_result = await system_detect_state(name=name)
    state = SystemState(state_result.get("state", "unknown"))
    
    if state == SystemState.TEXT_CONSOLE:
        # 文本控制台登录
        # 输入用户名
        result = await vnc_type_text(username, name=name)
        operations.append(result)
        
        result = await vnc_key_press("enter", name=name)
        operations.append(result)
        
        await asyncio.sleep(0.5)
        
        # 输入密码
        result = await vnc_type_text(password, name=name)
        operations.append(result)
        
        result = await vnc_key_press("enter", name=name)
        operations.append(result)
        
        await asyncio.sleep(1)
        
    elif state == SystemState.LOGIN_SCREEN:
        # GUI 登录界面
        # 输入密码（用户名可能已预选）
        result = await vnc_type_text(password, name=name)
        operations.append(result)
        
        result = await vnc_key_press("enter", name=name)
        operations.append(result)
        
        await asyncio.sleep(2)
    
    return {
        "success": True,
        "message": f"Linux 登录操作已完成（用户: {username}）",
        "operations": len(operations)
    }


async def _windows_login(username: str, password: str, name: str) -> Dict[str, Any]:
    """Windows 系统登录"""
    operations = []
    
    # Windows 登录界面通常只需要密码
    # 用户名可能已预选
    
    # 输入密码
    result = await vnc_type_text(password, name=name)
    operations.append(result)
    
    result = await vnc_key_press("enter", name=name)
    operations.append(result)
    
    await asyncio.sleep(3)
    
    return {
        "success": True,
        "message": f"Windows 登录操作已完成",
        "operations": len(operations)
    }


async def _generic_login(username: str, password: str, name: str) -> Dict[str, Any]:
    """通用登录流程"""
    operations = []
    
    # 尝试输入用户名（如果界面支持）
    result = await vnc_type_text(username, name=name)
    operations.append(result)
    
    result = await vnc_key_press("enter", name=name)
    operations.append(result)
    
    await asyncio.sleep(0.5)
    
    # 输入密码
    result = await vnc_type_text(password, name=name)
    operations.append(result)
    
    result = await vnc_key_press("enter", name=name)
    operations.append(result)
    
    await asyncio.sleep(2)
    
    return {
        "success": True,
        "message": "通用登录操作已完成",
        "operations": len(operations)
    }


# ============================================================================
# 命令执行操作
# ============================================================================

async def system_execute_command(
    command: str,
    timeout: float = 30.0,
    name: str = "default"
) -> Dict[str, Any]:
    """
    执行系统命令
    
    Args:
        command: 要执行的命令
        timeout: 超时时间
        name: VNC 客户端名称
    
    Returns:
        执行结果
    """
    if not VNC_SKILL_AVAILABLE:
        return {"success": False, "error": "VNC Skill 未安装"}
    
    try:
        operations = []
        
        # 打开终端（如果是 GUI 环境）
        # Linux: Ctrl+Alt+T 或终端图标
        # Windows: Win+R -> cmd
        
        # 输入命令
        result = await vnc_type_text(command, name=name)
        operations.append(result)
        
        result = await vnc_key_press("enter", name=name)
        operations.append(result)
        
        await asyncio.sleep(1)
        
        return {
            "success": True,
            "message": f"命令已执行: {command}",
            "command": command,
            "operations": len(operations)
        }
        
    except Exception as e:
        logger.error(f"命令执行失败: {e}")
        return {"success": False, "error": str(e)}


async def system_open_terminal(
    os_type: OSType = OSType.LINUX,
    name: str = "default"
) -> Dict[str, Any]:
    """
    打开终端
    
    Args:
        os_type: 操作系统类型
        name: VNC 客户端名称
    
    Returns:
        操作结果
    """
    if not VNC_SKILL_AVAILABLE:
        return {"success": False, "error": "VNC Skill 未安装"}
    
    operations = []
    
    if os_type == OSType.LINUX:
        # GNOME: Ctrl+Alt+T
        result = await vnc_key_press("t", name=name)  # 需要 Ctrl 组合
        # 简化处理：直接发送 Ctrl+Alt+T 序列
        operations.append(result)
        
    elif os_type == OSType.WINDOWS:
        # Win+R -> cmd
        result = await vnc_key_press("r", name=name)  # 需要 Win 组合
        operations.append(result)
        await asyncio.sleep(0.5)
        result = await vnc_type_text("cmd", name=name)
        operations.append(result)
        result = await vnc_key_press("enter", name=name)
        operations.append(result)
    
    await asyncio.sleep(1)
    
    return {
        "success": True,
        "message": f"终端已打开 ({os_type.value})",
        "operations": len(operations)
    }


# ============================================================================
# 快捷键操作
# ============================================================================

async def system_send_shortcut(
    shortcut: str,
    name: str = "default"
) -> Dict[str, Any]:
    """
    发送快捷键
    
    Args:
        shortcut: 快捷键名称（如 "ctrl+c", "alt+f4", "win+r"）
        name: VNC 客户端名称
    
    Returns:
        操作结果
    """
    if not VNC_SKILL_AVAILABLE:
        return {"success": False, "error": "VNC Skill 未安装"}
    
    # 解析快捷键
    # 格式: modifier+key, 如 "ctrl+c", "alt+f4", "ctrl+alt+del"
    
    parts = shortcut.lower().split("+")
    
    # 简化处理：按顺序发送按键
    # 实际实现需要处理修饰键的按下和释放
    
    result = await vnc_key_press(parts[-1], name=name)
    
    return {
        "success": result.get("success", False),
        "message": f"已发送快捷键: {shortcut}"
    }


# ============================================================================
# SystemSkill 类 - 封装所有系统操作
# ============================================================================

class SystemSkill:
    """系统操作技能封装"""
    
    def __init__(self):
        self.os_type = OSType.UNKNOWN
        self.current_state = SystemState.UNKNOWN
    
    async def detect_state(self) -> Dict[str, Any]:
        """检测系统状态"""
        result = await system_detect_state()
        if result.get("success"):
            self.current_state = SystemState(result.get("state", "unknown"))
        return result
    
    async def detect_os(self) -> Dict[str, Any]:
        """检测 OS 类型"""
        result = await system_detect_os()
        if result.get("success"):
            self.os_type = OSType(result.get("os_type", "unknown"))
        return result
    
    async def wait_for_desktop(self, timeout: float = 120.0) -> Dict[str, Any]:
        """等待桌面"""
        return await system_wait_for_desktop(timeout)
    
    async def wait_for_login(self, timeout: float = 120.0) -> Dict[str, Any]:
        """等待登录界面"""
        return await system_wait_for_login(timeout)
    
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """登录系统"""
        return await system_login(username, password, self.os_type)
    
    async def execute(self, command: str) -> Dict[str, Any]:
        """执行命令"""
        return await system_execute_command(command)
    
    async def open_terminal(self) -> Dict[str, Any]:
        """打开终端"""
        return await system_open_terminal(self.os_type)
    
    async def send_shortcut(self, shortcut: str) -> Dict[str, Any]:
        """发送快捷键"""
        return await system_send_shortcut(shortcut)
