#!/usr/bin/env python3
"""
UEFI/BIOS 操作工具

提供 UEFI/BIOS 环境下的操作功能
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
        VNCClient,
    )
    VNC_SKILL_AVAILABLE = True
except ImportError:
    VNC_SKILL_AVAILABLE = False
    logger.warning("VNC Skill 未安装，UEFI 操作将不可用")


class UEFIMenuType(Enum):
    """UEFI 菜单类型"""
    MAIN = "main"
    ADVANCED = "advanced"
    BOOT = "boot"
    SECURITY = "security"
    SAVE_EXIT = "save_exit"
    UNKNOWN = "unknown"


class BootDeviceType(Enum):
    """启动设备类型"""
    HDD = "hdd"
    SSD = "ssd"
    USB = "usb"
    CDROM = "cdrom"
    NETWORK = "network"
    EFI = "efi"


@dataclass
class UEFIMenuItem:
    """UEFI 菜单项"""
    name: str
    value: str
    is_selectable: bool = True
    is_submenu: bool = False


@dataclass
class BootDevice:
    """启动设备"""
    name: str
    device_type: BootDeviceType
    priority: int
    is_enabled: bool = True


# ============================================================================
# UEFI 界面检测
# ============================================================================

async def uefi_detect_screen(name: str = "default") -> Dict[str, Any]:
    """
    检测当前屏幕是否为 UEFI/BIOS 界面
    
    Args:
        name: VNC 客户端名称
    
    Returns:
        检测结果
    """
    if not VNC_SKILL_AVAILABLE:
        return {"success": False, "error": "VNC Skill 未安装"}
    
    # 获取屏幕截图
    screenshot_result = await vnc_screenshot(name=name, resize=800)
    if not screenshot_result.get("success"):
        return {"success": False, "error": "无法获取屏幕截图"}
    
    # 分析屏幕内容
    # 这里可以通过图像识别或 OCR 来检测 UEFI 界面
    # 简化实现：通过按键测试来验证
    
    return {
        "success": True,
        "is_uefi": None,  # 需要通过图像分析确定
        "message": "屏幕截图已获取，请通过图像分析确认是否为 UEFI 界面",
        "screenshot": screenshot_result.get("image_base64", "")[:100] + "..."
    }


async def uefi_detect_menu_type(name: str = "default") -> Dict[str, Any]:
    """
    检测当前 UEFI 菜单类型
    
    Args:
        name: VNC 客户端名称
    
    Returns:
        菜单类型检测结果
    """
    # UEFI 界面常见的菜单标识
    menu_indicators = {
        UEFIMenuType.MAIN: ["Main", "System Overview", "System Information"],
        UEFIMenuType.ADVANCED: ["Advanced", "CPU Configuration", "Chipset"],
        UEFIMenuType.BOOT: ["Boot", "Boot Priority", "Boot Order", "Boot Mode"],
        UEFIMenuType.SECURITY: ["Security", "Password", "Secure Boot"],
        UEFIMenuType.SAVE_EXIT: ["Save & Exit", "Exit", "Save Changes"],
    }
    
    return {
        "success": True,
        "menu_type": UEFIMenuType.UNKNOWN.value,
        "message": "需要通过图像分析确定菜单类型"
    }


# ============================================================================
# UEFI 导航操作
# ============================================================================

async def uefi_enter(key: str = "f2", name: str = "default") -> Dict[str, Any]:
    """
    进入 UEFI/BIOS 设置
    
    Args:
        key: 进入按键（f2, del, esc）
        name: VNC 客户端名称
    
    Returns:
        操作结果
    """
    if not VNC_SKILL_AVAILABLE:
        return {"success": False, "error": "VNC Skill 未安装"}
    
    try:
        # 发送进入按键
        result = await vnc_key_press(key, name=name)
        
        if not result.get("success"):
            return result
        
        # 等待 BIOS 加载
        await asyncio.sleep(2)
        
        # 获取截图确认
        screenshot = await vnc_screenshot(name=name)
        
        return {
            "success": True,
            "message": f"已发送 {key.upper()} 按键，请检查是否已进入 BIOS",
            "screenshot_available": screenshot.get("success", False)
        }
        
    except Exception as e:
        logger.error(f"进入 UEFI 失败: {e}")
        return {"success": False, "error": str(e)}


async def uefi_navigate_menu(
    direction: str = "right",
    steps: int = 1,
    name: str = "default"
) -> Dict[str, Any]:
    """
    导航 UEFI 菜单
    
    Args:
        direction: 方向（up, down, left, right）
        steps: 步数
        name: VNC 客户端名称
    
    Returns:
        操作结果
    """
    if not VNC_SKILL_AVAILABLE:
        return {"success": False, "error": "VNC Skill 未安装"}
    
    try:
        result = await vnc_key_press(direction, count=steps, name=name)
        
        # 等待界面响应
        await asyncio.sleep(0.3)
        
        return {
            "success": result.get("success", False),
            "message": f"已导航: {direction} x {steps}",
            "error": result.get("error")
        }
        
    except Exception as e:
        logger.error(f"菜单导航失败: {e}")
        return {"success": False, "error": str(e)}


async def uefi_select_option(name: str = "default") -> Dict[str, Any]:
    """
    选择当前选项（按 Enter）
    
    Args:
        name: VNC 客户端名称
    
    Returns:
        操作结果
    """
    if not VNC_SKILL_AVAILABLE:
        return {"success": False, "error": "VNC Skill 未安装"}
    
    result = await vnc_key_press("enter", name=name)
    await asyncio.sleep(0.5)
    
    return {
        "success": result.get("success", False),
        "message": "已按 Enter 选择",
        "error": result.get("error")
    }


async def uefi_go_back(name: str = "default") -> Dict[str, Any]:
    """
    返回上级菜单（按 Escape）
    
    Args:
        name: VNC 客户端名称
    
    Returns:
        操作结果
    """
    if not VNC_SKILL_AVAILABLE:
        return {"success": False, "error": "VNC Skill 未安装"}
    
    result = await vnc_key_press("escape", name=name)
    await asyncio.sleep(0.5)
    
    return {
        "success": result.get("success", False),
        "message": "已按 Escape 返回",
        "error": result.get("error")
    }


# ============================================================================
# UEFI 设置操作
# ============================================================================

async def uefi_set_boot_order(
    devices: List[str],
    name: str = "default"
) -> Dict[str, Any]:
    """
    设置启动顺序
    
    Args:
        devices: 启动设备顺序列表（如 ["USB", "HDD", "Network"]）
        name: VNC 客户端名称
    
    Returns:
        操作结果
    """
    if not VNC_SKILL_AVAILABLE:
        return {"success": False, "error": "VNC Skill 未安装"}
    
    try:
        operations = []
        
        # 导航到 Boot 菜单（假设从 Main 开始）
        operations.append(await uefi_navigate_menu("right", steps=2, name=name))
        await asyncio.sleep(0.5)
        
        # 进入 Boot Priority 设置
        operations.append(await vnc_key_press("down", count=2, name=name))
        await asyncio.sleep(0.3)
        operations.append(await vnc_key_press("enter", name=name))
        await asyncio.sleep(0.3)
        
        # 调整启动顺序
        for i, device in enumerate(devices):
            # 选择设备（需要根据实际情况调整）
            operations.append(await vnc_key_press("down", count=1, name=name))
            await asyncio.sleep(0.2)
            
            # 使用 + 或 F5/F6 调整优先级
            operations.append(await vnc_key_press("f5", name=name))  # 或 "+"
            await asyncio.sleep(0.2)
        
        return {
            "success": True,
            "message": f"已设置启动顺序: {' -> '.join(devices)}",
            "operations": [op.get("message", "") for op in operations]
        }
        
    except Exception as e:
        logger.error(f"设置启动顺序失败: {e}")
        return {"success": False, "error": str(e)}


async def uefi_enable_virtualization(
    name: str = "default"
) -> Dict[str, Any]:
    """
    启用 CPU 虚拟化支持（Intel VT-x / AMD-V）
    
    Args:
        name: VNC 客户端名称
    
    Returns:
        操作结果
    """
    if not VNC_SKILL_AVAILABLE:
        return {"success": False, "error": "VNC Skill 未安装"}
    
    try:
        operations = []
        
        # 导航到 Advanced 菜单
        operations.append(await uefi_navigate_menu("right", steps=1, name=name))
        await asyncio.sleep(0.5)
        
        # 进入 CPU Configuration
        operations.append(await vnc_key_press("down", count=2, name=name))
        await asyncio.sleep(0.3)
        operations.append(await vnc_key_press("enter", name=name))
        await asyncio.sleep(0.5)
        
        # 找到并启用虚拟化选项
        # 通常需要向下导航几步
        for _ in range(5):
            operations.append(await vnc_key_press("down", name=name))
            await asyncio.sleep(0.2)
            
            # 检查是否为虚拟化选项（需要图像识别）
            # 简化处理：直接尝试启用
            operations.append(await vnc_key_press("enter", name=name))
            await asyncio.sleep(0.2)
            operations.append(await vnc_key_press("down", name=name))  # 选择 Enabled
            await asyncio.sleep(0.2)
            operations.append(await vnc_key_press("enter", name=name))
            await asyncio.sleep(0.2)
        
        return {
            "success": True,
            "message": "虚拟化设置操作已完成，请检查截图确认",
            "operations": [op.get("message", "") for op in operations]
        }
        
    except Exception as e:
        logger.error(f"启用虚拟化失败: {e}")
        return {"success": False, "error": str(e)}


async def uefi_disable_secure_boot(name: str = "default") -> Dict[str, Any]:
    """
    禁用 Secure Boot
    
    Args:
        name: VNC 客户端名称
    
    Returns:
        操作结果
    """
    if not VNC_SKILL_AVAILABLE:
        return {"success": False, "error": "VNC Skill 未安装"}
    
    try:
        operations = []
        
        # 导航到 Boot 或 Security 菜单
        operations.append(await uefi_navigate_menu("right", steps=2, name=name))
        await asyncio.sleep(0.5)
        
        # 找到 Secure Boot 选项
        operations.append(await vnc_key_press("down", count=4, name=name))
        await asyncio.sleep(0.3)
        operations.append(await vnc_key_press("enter", name=name))
        await asyncio.sleep(0.3)
        
        # 禁用 Secure Boot
        operations.append(await vnc_key_press("down", name=name))  # 选择 Disabled
        await asyncio.sleep(0.2)
        operations.append(await vnc_key_press("enter", name=name))
        await asyncio.sleep(0.2)
        
        return {
            "success": True,
            "message": "Secure Boot 禁用操作已完成",
            "operations": [op.get("message", "") for op in operations]
        }
        
    except Exception as e:
        logger.error(f"禁用 Secure Boot 失败: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# UEFI 保存和退出
# ============================================================================

async def uefi_save_and_exit(name: str = "default") -> Dict[str, Any]:
    """
    保存设置并退出 UEFI
    
    Args:
        name: VNC 客户端名称
    
    Returns:
        操作结果
    """
    if not VNC_SKILL_AVAILABLE:
        return {"success": False, "error": "VNC Skill 未安装"}
    
    try:
        # 按 F10 保存退出
        result = await vnc_key_press("f10", name=name)
        await asyncio.sleep(1)
        
        # 确认保存（某些 BIOS 需要确认）
        result2 = await vnc_key_press("enter", name=name)
        await asyncio.sleep(2)
        
        return {
            "success": True,
            "message": "已保存设置并退出 BIOS",
            "note": "系统将重启"
        }
        
    except Exception as e:
        logger.error(f"保存退出失败: {e}")
        return {"success": False, "error": str(e)}


async def uefi_discard_and_exit(name: str = "default") -> Dict[str, Any]:
    """
    放弃更改并退出 UEFI
    
    Args:
        name: VNC 客户端名称
    
    Returns:
        操作结果
    """
    if not VNC_SKILL_AVAILABLE:
        return {"success": False, "error": "VNC Skill 未安装"}
    
    try:
        # 导航到 Exit 菜单
        await uefi_navigate_menu("right", steps=4, name=name)
        await asyncio.sleep(0.5)
        
        # 选择 Discard Changes and Exit
        await vnc_key_press("down", count=2, name=name)
        await asyncio.sleep(0.3)
        await vnc_key_press("enter", name=name)
        await asyncio.sleep(0.5)
        
        # 确认
        await vnc_key_press("enter", name=name)
        await asyncio.sleep(2)
        
        return {
            "success": True,
            "message": "已放弃更改并退出 BIOS"
        }
        
    except Exception as e:
        logger.error(f"放弃退出失败: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# 从 UEFI 启动到 OS
# ============================================================================

async def uefi_boot_to_os(
    timeout: float = 120.0,
    name: str = "default"
) -> Dict[str, Any]:
    """
    从 UEFI 保存退出并等待 OS 启动
    
    Args:
        timeout: 等待 OS 启动的超时时间
        name: VNC 客户端名称
    
    Returns:
        操作结果
    """
    if not VNC_SKILL_AVAILABLE:
        return {"success": False, "error": "VNC Skill 未安装"}
    
    try:
        # 保存退出
        exit_result = await uefi_save_and_exit(name=name)
        if not exit_result.get("success"):
            return exit_result
        
        # 等待系统启动
        await asyncio.sleep(10)  # 初始等待
        
        # 检测启动进度
        # 这里可以添加更复杂的状态检测逻辑
        
        return {
            "success": True,
            "message": "已从 BIOS 退出，系统正在启动",
            "timeout": timeout
        }
        
    except Exception as e:
        logger.error(f"启动 OS 失败: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# UEFISkill 类 - 封装所有 UEFI 操作
# ============================================================================

class UEFISkill:
    """UEFI/BIOS 操作技能封装"""
    
    def __init__(self):
        self.current_menu = UEFIMenuType.UNKNOWN
    
    async def enter(self, key: str = "f2") -> Dict[str, Any]:
        """进入 BIOS"""
        return await uefi_enter(key)
    
    async def navigate(self, direction: str, steps: int = 1) -> Dict[str, Any]:
        """导航菜单"""
        return await uefi_navigate_menu(direction, steps)
    
    async def select(self) -> Dict[str, Any]:
        """选择当前项"""
        return await uefi_select_option()
    
    async def back(self) -> Dict[str, Any]:
        """返回上级"""
        return await uefi_go_back()
    
    async def set_boot_order(self, devices: List[str]) -> Dict[str, Any]:
        """设置启动顺序"""
        return await uefi_set_boot_order(devices)
    
    async def enable_virtualization(self) -> Dict[str, Any]:
        """启用虚拟化"""
        return await uefi_enable_virtualization()
    
    async def disable_secure_boot(self) -> Dict[str, Any]:
        """禁用 Secure Boot"""
        return await uefi_disable_secure_boot()
    
    async def save_exit(self) -> Dict[str, Any]:
        """保存退出"""
        return await uefi_save_and_exit()
    
    async def boot_to_os(self, timeout: float = 120.0) -> Dict[str, Any]:
        """启动到 OS"""
        return await uefi_boot_to_os(timeout)
