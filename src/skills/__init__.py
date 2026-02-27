"""
VNC 操作 Skills 模块

提供 VNC 远程控制相关的功能，支持：
- VNC 连接和屏幕操作
- UEFI/BIOS 操作
- 系统操作
- 从 UEFI 进入 OS 的自动化流程
"""

from .vnc_skill import (
    VNCConfig,
    VNCClient,
    vnc_connect,
    vnc_disconnect,
    vnc_screenshot,
    vnc_key_press,
    vnc_type_text,
    vnc_mouse_click,
    vnc_mouse_move,
    vnc_mouse_drag,
    get_vnc_client,
    set_vnc_client,
    VNC_SKILL_AVAILABLE,
)

from .uefi_skill import (
    UEFIMenuType,
    BootDeviceType,
    uefi_detect_screen,
    uefi_detect_menu_type,
    uefi_enter,
    uefi_navigate_menu,
    uefi_select_option,
    uefi_go_back,
    uefi_set_boot_order,
    uefi_enable_virtualization,
    uefi_disable_secure_boot,
    uefi_save_and_exit,
    uefi_discard_and_exit,
    uefi_boot_to_os,
    UEFISkill,
)

from .system_skill import (
    SystemState,
    OSType,
    SystemInfo,
    system_detect_state,
    system_detect_os,
    system_wait_for_state,
    system_wait_for_login,
    system_wait_for_desktop,
    system_wait_for_prompt,
    system_login,
    system_execute_command,
    system_open_terminal,
    system_send_shortcut,
    SystemSkill,
)

__all__ = [
    # VNC 配置和客户端
    'VNCConfig',
    'VNCClient',
    'get_vnc_client',
    'set_vnc_client',
    'VNC_SKILL_AVAILABLE',
    
    # VNC 基础操作
    'vnc_connect',
    'vnc_disconnect',
    'vnc_screenshot',
    'vnc_key_press',
    'vnc_type_text',
    'vnc_mouse_click',
    'vnc_mouse_move',
    'vnc_mouse_drag',
    
    # UEFI 枚举
    'UEFIMenuType',
    'BootDeviceType',
    
    # UEFI 操作
    'uefi_detect_screen',
    'uefi_detect_menu_type',
    'uefi_enter',
    'uefi_navigate_menu',
    'uefi_select_option',
    'uefi_go_back',
    'uefi_set_boot_order',
    'uefi_enable_virtualization',
    'uefi_disable_secure_boot',
    'uefi_save_and_exit',
    'uefi_discard_and_exit',
    'uefi_boot_to_os',
    'UEFISkill',
    
    # 系统枚举
    'SystemState',
    'OSType',
    'SystemInfo',
    
    # 系统操作
    'system_detect_state',
    'system_detect_os',
    'system_wait_for_state',
    'system_wait_for_login',
    'system_wait_for_desktop',
    'system_wait_for_prompt',
    'system_login',
    'system_execute_command',
    'system_open_terminal',
    'system_send_shortcut',
    'SystemSkill',
]

# 版本信息
__version__ = '1.0.0'
__author__ = 'iFlow DemoDock'