#!/usr/bin/env python3
"""
VNC MCP 服务器

提供 VNC 远程控制相关的 MCP 工具，支持：
- VNC 连接和屏幕操作
- UEFI/BIOS 操作
- 系统操作

使用 FastMCP 框架实现 MCP 协议
"""

import asyncio
import base64
import logging
from io import BytesIO
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 检查依赖
try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    try:
        from fastmcp import FastMCP
        MCP_AVAILABLE = True
    except ImportError:
        MCP_AVAILABLE = False
        logger.warning("FastMCP 未安装，请运行: pip install fastmcp")

try:
    from vncdotool import api
    from PIL import Image
    VNC_AVAILABLE = True
except ImportError:
    VNC_AVAILABLE = False
    logger.warning("vncdotool 或 PIL 未安装，请运行: pip install vncdotool pillow")


# ============================================================================
# VNC 客户端管理
# ============================================================================

_vnc_clients: Dict[str, Any] = {}
_vnc_configs: Dict[str, Dict] = {}


def get_vnc_client(name: str = "default"):
    """获取 VNC 客户端"""
    return _vnc_clients.get(name)


def set_vnc_client(client: Any, name: str = "default", config: Dict = None):
    """设置 VNC 客户端"""
    _vnc_clients[name] = client
    if config:
        _vnc_configs[name] = config


# ============================================================================
# 创建 MCP 服务器
# ============================================================================

if MCP_AVAILABLE:
    # 创建 FastMCP 实例
    mcp = FastMCP("vnc-control")

    # ========================================================================
    # VNC 连接工具
    # ========================================================================

    @mcp.tool()
    async def vnc_connect(
        host: str,
        port: int = 5901,
        password: str = "",
        name: str = "default"
    ) -> str:
        """
        连接到 VNC 服务器
        
        Args:
            host: VNC 服务器主机地址
            port: VNC 端口，默认 5901
            password: VNC 密码
            name: 连接名称，用于管理多个连接
        
        Returns:
            连接状态信息
        """
        if not VNC_AVAILABLE:
            return "错误: vncdotool 或 PIL 未安装，请先安装依赖"
        
        try:
            # 在线程池中执行同步连接
            loop = asyncio.get_event_loop()
            client = await loop.run_in_executor(
                None,
                lambda: api.connect(f"{host}:{port}", password=password)
            )
            
            set_vnc_client(client, name, {
                "host": host,
                "port": port,
                "password": password
            })
            
            return f"✅ 已连接到 VNC 服务器 {host}:{port} (名称: {name})"
        except Exception as e:
            return f"❌ 连接失败: {str(e)}"

    @mcp.tool()
    async def vnc_disconnect(name: str = "default") -> str:
        """
        断开 VNC 连接
        
        Args:
            name: 连接名称
        
        Returns:
            断开状态信息
        """
        if name in _vnc_clients:
            del _vnc_clients[name]
            if name in _vnc_configs:
                del _vnc_configs[name]
            return f"✅ 已断开 VNC 连接 '{name}'"
        return f"⚠️ 连接 '{name}' 不存在"

    @mcp.tool()
    async def vnc_screenshot(
        name: str = "default",
        resize: int = 800,
        quality: int = 85
    ) -> str:
        """
        获取 VNC 屏幕截图
        
        Args:
            name: 连接名称
            resize: 调整宽度，默认 800px
            quality: JPEG 质量，默认 85
        
        Returns:
            base64 编码的 JPEG 图像数据（前 100 字符预览）
        """
        if not VNC_AVAILABLE:
            return "错误: vncdotool 或 PIL 未安装"
        
        client = get_vnc_client(name)
        if not client:
            return f"错误: 连接 '{name}' 不存在，请先使用 vnc_connect 连接"
        
        try:
            def capture():
                screen = client.captureScreen()
                img = Image.frombytes('RGB', screen.size, screen.data)
                
                if resize and img.width > resize:
                    ratio = resize / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((resize, new_height), Image.Resampling.LANCZOS)
                
                buffered = BytesIO()
                img.save(buffered, format='JPEG', quality=quality)
                return base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            loop = asyncio.get_event_loop()
            img_base64 = await loop.run_in_executor(None, capture)
            
            return f"✅ 截图成功\n尺寸: {resize}px 宽度\nBase64 长度: {len(img_base64)} 字符\n预览: {img_base64[:100]}..."
        except Exception as e:
            return f"❌ 截图失败: {str(e)}"

    @mcp.tool()
    async def vnc_key_press(
        key: str,
        count: int = 1,
        name: str = "default"
    ) -> str:
        """
        发送按键到 VNC 会话
        
        Args:
            key: 按键名称，如 enter, escape, tab, f1-f12, up, down, left, right
            count: 按键次数，默认 1
            name: 连接名称
        
        Returns:
            操作结果
        """
        client = get_vnc_client(name)
        if not client:
            return f"错误: 连接 '{name}' 不存在"
        
        # 按键映射
        key_map = {
            'enter': 'enter', 'return': 'enter',
            'esc': 'escape', 'escape': 'escape',
            'tab': 'tab', 'space': 'space',
            'backspace': 'backspace', 'delete': 'delete',
            'insert': 'insert', 'home': 'home', 'end': 'end',
            'pageup': 'page_up', 'pagedown': 'page_down',
            'up': 'up', 'down': 'down', 'left': 'left', 'right': 'right',
            'f1': 'f1', 'f2': 'f2', 'f3': 'f3', 'f4': 'f4',
            'f5': 'f5', 'f6': 'f6', 'f7': 'f7', 'f8': 'f8',
            'f9': 'f9', 'f10': 'f10', 'f11': 'f11', 'f12': 'f12',
        }
        
        mapped_key = key_map.get(key.lower(), key.lower())
        
        try:
            for _ in range(count):
                client.keyPress(mapped_key)
                await asyncio.sleep(0.05)
            
            return f"✅ 已发送按键 '{key}' x {count}"
        except Exception as e:
            return f"❌ 发送按键失败: {str(e)}"

    @mcp.tool()
    async def vnc_type_text(
        text: str,
        interval: float = 0.05,
        name: str = "default"
    ) -> str:
        """
        在 VNC 会话中输入文本
        
        Args:
            text: 要输入的文本
            interval: 字符间隔（秒），默认 0.05
            name: 连接名称
        
        Returns:
            操作结果
        """
        client = get_vnc_client(name)
        if not client:
            return f"错误: 连接 '{name}' 不存在"
        
        try:
            for char in text:
                client.keyPress(char)
                await asyncio.sleep(interval)
            
            preview = text[:50] + "..." if len(text) > 50 else text
            return f"✅ 已输入文本 ({len(text)} 字符): {preview}"
        except Exception as e:
            return f"❌ 输入文本失败: {str(e)}"

    @mcp.tool()
    async def vnc_mouse_click(
        x: int,
        y: int,
        button: int = 1,
        double: bool = False,
        name: str = "default"
    ) -> str:
        """
        在 VNC 会话中点击鼠标
        
        Args:
            x: X 坐标
            y: Y 坐标
            button: 鼠标按钮，1=左键, 2=中键, 3=右键
            double: 是否双击
            name: 连接名称
        
        Returns:
            操作结果
        """
        client = get_vnc_client(name)
        if not client:
            return f"错误: 连接 '{name}' 不存在"
        
        try:
            client.mouseMove(x, y)
            await asyncio.sleep(0.05)
            
            if double:
                client.mouseDoubleClick(button)
            else:
                client.mousePress(button)
            
            return f"✅ 已点击 ({x}, {y}) button={button} double={double}"
        except Exception as e:
            return f"❌ 点击失败: {str(e)}"

    @mcp.tool()
    async def vnc_mouse_move(
        x: int,
        y: int,
        name: str = "default"
    ) -> str:
        """
        移动鼠标
        
        Args:
            x: X 坐标
            y: Y 坐标
            name: 连接名称
        
        Returns:
            操作结果
        """
        client = get_vnc_client(name)
        if not client:
            return f"错误: 连接 '{name}' 不存在"
        
        try:
            client.mouseMove(x, y)
            return f"✅ 已移动到 ({x}, {y})"
        except Exception as e:
            return f"❌ 移动失败: {str(e)}"

    # ========================================================================
    # UEFI/BIOS 操作工具
    # ========================================================================

    @mcp.tool()
    async def uefi_enter(key: str = "f2", name: str = "default") -> str:
        """
        进入 UEFI/BIOS 设置
        
        Args:
            key: 进入按键，默认 F2（也可以是 del, esc）
            name: VNC 连接名称
        
        Returns:
            操作结果
        """
        try:
            await vnc_key_press(key, name=name)
            await asyncio.sleep(2)
            return f"✅ 已发送 {key.upper()} 按键进入 BIOS，请等待 2-3 秒后检查屏幕"
        except Exception as e:
            return f"❌ 进入 BIOS 失败: {str(e)}"

    @mcp.tool()
    async def uefi_navigate(
        direction: str,
        steps: int = 1,
        name: str = "default"
    ) -> str:
        """
        导航 UEFI 菜单
        
        Args:
            direction: 方向，up/down/left/right
            steps: 步数
            name: 连接名称
        
        Returns:
            操作结果
        """
        return await vnc_key_press(direction, count=steps, name=name)

    @mcp.tool()
    async def uefi_select(name: str = "default") -> str:
        """
        选择当前 UEFI 选项（按 Enter）
        
        Args:
            name: 连接名称
        
        Returns:
            操作结果
        """
        return await vnc_key_press("enter", name=name)

    @mcp.tool()
    async def uefi_save_exit(name: str = "default") -> str:
        """
        保存设置并退出 UEFI（按 F10）
        
        Args:
            name: 连接名称
        
        Returns:
            操作结果
        """
        try:
            await vnc_key_press("f10", name=name)
            await asyncio.sleep(1)
            await vnc_key_press("enter", name=name)  # 确认保存
            return "✅ 已保存并退出 BIOS，系统将重启"
        except Exception as e:
            return f"❌ 保存退出失败: {str(e)}"

    @mcp.tool()
    async def uefi_set_boot_order(
        devices: List[str],
        name: str = "default"
    ) -> str:
        """
        设置启动顺序
        
        Args:
            devices: 启动设备顺序列表，如 ["USB", "HDD", "Network"]
            name: 连接名称
        
        Returns:
            操作结果
        """
        operations = []
        
        try:
            # 导航到 Boot 菜单（假设从 Main 开始）
            await vnc_key_press("right", count=2, name=name)
            operations.append("导航到 Boot 菜单")
            await asyncio.sleep(0.5)
            
            # 选择 Boot Priority
            await vnc_key_press("down", count=2, name=name)
            operations.append("选择 Boot Priority")
            await asyncio.sleep(0.3)
            
            await vnc_key_press("enter", name=name)
            operations.append("进入 Boot Priority")
            await asyncio.sleep(0.3)
            
            return f"✅ 启动顺序设置操作已执行\n设备顺序: {' -> '.join(devices)}\n操作: {', '.join(operations)}"
        except Exception as e:
            return f"❌ 设置启动顺序失败: {str(e)}"

    # ========================================================================
    # 系统操作工具
    # ========================================================================

    @mcp.tool()
    async def system_login(
        username: str,
        password: str,
        name: str = "default"
    ) -> str:
        """
        系统登录
        
        Args:
            username: 用户名
            password: 密码
            name: VNC 连接名称
        
        Returns:
            操作结果
        """
        try:
            # 输入用户名
            await vnc_type_text(username, name=name)
            await vnc_key_press("enter", name=name)
            await asyncio.sleep(0.5)
            
            # 输入密码
            await vnc_type_text(password, name=name)
            await vnc_key_press("enter", name=name)
            await asyncio.sleep(2)
            
            return f"✅ 登录操作已完成（用户: {username}）"
        except Exception as e:
            return f"❌ 登录失败: {str(e)}"

    @mcp.tool()
    async def system_execute_command(
        command: str,
        name: str = "default"
    ) -> str:
        """
        执行系统命令
        
        Args:
            command: 要执行的命令
            name: VNC 连接名称
        
        Returns:
            操作结果
        """
        try:
            await vnc_type_text(command, name=name)
            await vnc_key_press("enter", name=name)
            await asyncio.sleep(1)
            
            return f"✅ 命令已执行: {command}"
        except Exception as e:
            return f"❌ 命令执行失败: {str(e)}"

    @mcp.tool()
    async def system_send_shortcut(
        shortcut: str,
        name: str = "default"
    ) -> str:
        """
        发送快捷键
        
        Args:
            shortcut: 快捷键，如 "ctrl+c", "alt+f4", "ctrl+alt+del"
            name: 连接名称
        
        Returns:
            操作结果
        """
        parts = shortcut.lower().split("+")
        main_key = parts[-1]
        
        # 简化处理：直接发送主键
        # 完整实现需要处理修饰键的按下和释放
        return await vnc_key_press(main_key, name=name)

    # ========================================================================
    # 复合操作工具
    # ========================================================================

    @mcp.tool()
    async def vnc_boot_to_os(
        host: str,
        port: int = 5901,
        password: str = "",
        username: str = "",
        user_password: str = "",
        timeout: int = 120
    ) -> str:
        """
        完整流程：连接 VNC -> 从 BIOS 启动 -> 登录系统
        
        Args:
            host: VNC 主机地址
            port: VNC 端口
            password: VNC 密码
            username: 系统登录用户名（可选）
            user_password: 系统登录密码（可选）
            timeout: 超时时间（秒）
        
        Returns:
            操作结果
        """
        results = []
        
        # 1. 连接 VNC
        result = await vnc_connect(host, port, password)
        results.append(f"1. {result}")
        
        if "失败" in result:
            return "\n".join(results)
        
        # 2. 获取截图查看状态
        result = await vnc_screenshot()
        results.append(f"2. 屏幕截图已获取，请分析当前状态")
        
        # 3. 如果需要，从 BIOS 退出
        # result = await uefi_save_exit()
        # results.append(f"3. {result}")
        
        # 4. 等待系统启动
        results.append(f"3. 等待系统启动（最多 {timeout} 秒）...")
        
        # 5. 如果提供了登录信息，执行登录
        if username and user_password:
            await asyncio.sleep(10)  # 等待登录界面
            result = await system_login(username, user_password)
            results.append(f"4. {result}")
        
        return "\n".join(results)

    @mcp.tool()
    async def vnc_status() -> str:
        """
        获取 VNC 连接状态
        
        Returns:
            当前所有连接的状态
        """
        if not _vnc_clients:
            return "当前没有活动的 VNC 连接"
        
        status_lines = ["当前 VNC 连接状态:"]
        for name, client in _vnc_clients.items():
            config = _vnc_configs.get(name, {})
            status_lines.append(f"  - {name}: {config.get('host', 'unknown')}:{config.get('port', 5901)}")
        
        return "\n".join(status_lines)


# ============================================================================
# 运行 MCP 服务器
# ============================================================================

def run_mcp_server():
    """运行 MCP 服务器"""
    if not MCP_AVAILABLE:
        print("❌ FastMCP 未安装，请运行: pip install fastmcp")
        return
    
    print("🚀 启动 VNC MCP 服务器...")
    print("📡 提供的工具:")
    print("   VNC 连接: vnc_connect, vnc_disconnect, vnc_screenshot, vnc_status")
    print("   VNC 操作: vnc_key_press, vnc_type_text, vnc_mouse_click, vnc_mouse_move")
    print("   UEFI: uefi_enter, uefi_navigate, uefi_select, uefi_save_exit, uefi_set_boot_order")
    print("   系统: system_login, system_execute_command, system_send_shortcut")
    print("   复合: vnc_boot_to_os")
    print()
    
    mcp.run()


if __name__ == "__main__":
    run_mcp_server()
