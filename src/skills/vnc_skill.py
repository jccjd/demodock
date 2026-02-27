# -*- coding: utf-8 -*-
"""
VNC 基础操作 Skill

提供 VNC 连接、屏幕捕获、键盘鼠标模拟等基础操作
"""

import asyncio
import base64
import logging
import time
from io import BytesIO
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
from functools import partial

logger = logging.getLogger(__name__)

# 检查依赖
try:
    from vncdotool import api
    from PIL import Image
    VNC_AVAILABLE = True
except ImportError:
    VNC_AVAILABLE = False
    logger.warning("vncdotool 或 PIL 未安装，VNC 功能将不可用")


@dataclass
class VNCConfig:
    """VNC 连接配置"""
    host: str = "127.0.0.1"
    port: int = 5901
    password: str = ""
    username: str = ""
    timeout: float = 30.0


@dataclass
class VNCClient:
    """VNC 客户端管理器"""
    config: VNCConfig
    client: Any = None
    connected: bool = False
    screen_size: Tuple[int, int] = (1024, 768)
    last_screenshot: Optional[Any] = None
    executor: ThreadPoolExecutor = field(default_factory=lambda: ThreadPoolExecutor(max_workers=2))
    
    def connect(self) -> bool:
        """连接到 VNC 服务器"""
        if not VNC_AVAILABLE:
            raise RuntimeError("vncdotool 或 PIL 未安装")
        
        try:
            logger.info(f"正在连接 VNC: {self.config.host}:{self.config.port}")
            self.client = api.connect(
                f"{self.config.host}:{self.config.port}",
                password=self.config.password
            )
            self.connected = True
            logger.info(f"VNC 连接成功: {self.config.host}:{self.config.port}")
            return True
        except Exception as e:
            logger.error(f"VNC 连接失败: {e}")
            self.connected = False
            raise
    
    def disconnect(self):
        """断开 VNC 连接"""
        if self.client:
            try:
                self.client = None
                self.connected = False
                logger.info("VNC 连接已断开")
            except Exception as e:
                logger.error(f"断开 VNC 连接失败: {e}")
    
    def capture_screen(self, resize: Optional[int] = None):
        """捕获屏幕"""
        if not self.connected or not self.client:
            raise RuntimeError("VNC 未连接")
        
        try:
            screen = self.client.captureScreen()
            img = Image.frombytes('RGB', screen.size, screen.data)
            self.screen_size = img.size
            self.last_screenshot = img
            
            if resize and img.width > resize:
                ratio = resize / img.width
                new_height = int(img.height * ratio)
                img = img.resize((resize, new_height), Image.Resampling.LANCZOS)
            
            return img
        except Exception as e:
            logger.error(f"屏幕捕获失败: {e}")
            raise
    
    def screenshot_base64(self, resize: Optional[int] = 800, quality: int = 85) -> str:
        """获取屏幕截图的 base64 编码"""
        img = self.capture_screen(resize=resize)
        buffered = BytesIO()
        img.save(buffered, format='JPEG', quality=quality)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    def key_press(self, key: str, count: int = 1):
        """发送按键"""
        if not self.connected or not self.client:
            raise RuntimeError("VNC 未连接")
        
        key = key.lower().strip()
        
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
        
        mapped_key = key_map.get(key, key)
        
        try:
            for _ in range(count):
                self.client.keyPress(mapped_key)
                time.sleep(0.05)
            logger.info(f"发送按键: {key} x {count}")
        except Exception as e:
            logger.error(f"发送按键失败: {e}")
            raise
    
    def type_text(self, text: str, interval: float = 0.05):
        """输入文本"""
        if not self.connected or not self.client:
            raise RuntimeError("VNC 未连接")
        
        try:
            for char in text:
                self.client.keyPress(char)
                time.sleep(interval)
            preview = text[:50] + "..." if len(text) > 50 else text
            logger.info(f"输入文本: {preview}")
        except Exception as e:
            logger.error(f"输入文本失败: {e}")
            raise
    
    def mouse_click(self, x: int, y: int, button: int = 1, double: bool = False):
        """鼠标点击"""
        if not self.connected or not self.client:
            raise RuntimeError("VNC 未连接")
        
        try:
            self.client.mouseMove(x, y)
            time.sleep(0.05)
            
            if double:
                self.client.mouseDoubleClick(button)
            else:
                self.client.mousePress(button)
            
            logger.info(f"鼠标点击: ({x}, {y}) button={button} double={double}")
        except Exception as e:
            logger.error(f"鼠标点击失败: {e}")
            raise
    
    def mouse_move(self, x: int, y: int):
        """移动鼠标"""
        if not self.connected or not self.client:
            raise RuntimeError("VNC 未连接")
        
        try:
            self.client.mouseMove(x, y)
            logger.info(f"鼠标移动: ({x}, {y})")
        except Exception as e:
            logger.error(f"鼠标移动失败: {e}")
            raise
    
    def mouse_drag(self, start_x: int, start_y: int, end_x: int, end_y: int):
        """鼠标拖拽"""
        if not self.connected or not self.client:
            raise RuntimeError("VNC 未连接")
        
        try:
            self.client.mouseMove(start_x, start_y)
            time.sleep(0.05)
            self.client.mouseDown(1)
            time.sleep(0.05)
            self.client.mouseMove(end_x, end_y)
            time.sleep(0.05)
            self.client.mouseUp(1)
            logger.info(f"鼠标拖拽: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
        except Exception as e:
            logger.error(f"鼠标拖拽失败: {e}")
            raise


# 全局 VNC 客户端实例管理
_vnc_clients: Dict[str, VNCClient] = {}
_default_client: Optional[VNCClient] = None


def get_vnc_client(name: str = "default") -> Optional[VNCClient]:
    """获取 VNC 客户端实例"""
    return _vnc_clients.get(name)


def set_vnc_client(client: VNCClient, name: str = "default"):
    """设置 VNC 客户端实例"""
    global _default_client
    _vnc_clients[name] = client
    if name == "default":
        _default_client = client


# MCP Tool 函数

async def vnc_connect(
    host: str = "127.0.0.1",
    port: int = 5901,
    password: str = "",
    name: str = "default"
) -> Dict[str, Any]:
    """连接到 VNC 服务器"""
    config = VNCConfig(host=host, port=port, password=password)
    client = VNCClient(config=config)
    
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(client.executor, client.connect)
        set_vnc_client(client, name)
        
        return {
            "success": True,
            "message": f"已连接到 VNC 服务器 {host}:{port}",
            "host": host,
            "port": port,
            "client_name": name
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"连接失败: {e}"
        }


async def vnc_disconnect(name: str = "default") -> Dict[str, Any]:
    """断开 VNC 连接"""
    client = get_vnc_client(name)
    if not client:
        return {
            "success": False,
            "error": f"客户端 '{name}' 不存在"
        }
    
    try:
        client.disconnect()
        if name in _vnc_clients:
            del _vnc_clients[name]
        
        return {
            "success": True,
            "message": f"已断开 VNC 连接 '{name}'"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def vnc_screenshot(
    name: str = "default",
    resize: Optional[int] = 800,
    quality: int = 85,
    return_base64: bool = True
) -> Dict[str, Any]:
    """获取 VNC 屏幕截图"""
    client = get_vnc_client(name)
    if not client:
        return {
            "success": False,
            "error": f"客户端 '{name}' 不存在，请先连接 VNC"
        }
    
    if not client.connected:
        return {
            "success": False,
            "error": "VNC 未连接"
        }
    
    loop = asyncio.get_event_loop()
    try:
        if return_base64:
            base64_img = await loop.run_in_executor(
                client.executor,
                lambda: client.screenshot_base64(resize=resize, quality=quality)
            )
            return {
                "success": True,
                "image_base64": base64_img,
                "width": client.screen_size[0],
                "height": client.screen_size[1],
                "format": "jpeg"
            }
        else:
            img = await loop.run_in_executor(
                client.executor,
                lambda: client.capture_screen(resize=resize)
            )
            return {
                "success": True,
                "width": img.width,
                "height": img.height,
                "message": "截图成功"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def vnc_key_press(
    key: str,
    count: int = 1,
    name: str = "default"
) -> Dict[str, Any]:
    """发送按键到 VNC 会话"""
    client = get_vnc_client(name)
    if not client:
        return {
            "success": False,
            "error": f"客户端 '{name}' 不存在，请先连接 VNC"
        }
    
    if not client.connected:
        return {
            "success": False,
            "error": "VNC 未连接"
        }
    
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            client.executor,
            lambda: client.key_press(key, count)
        )
        return {
            "success": True,
            "message": f"已发送按键 '{key}' x {count}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def vnc_type_text(
    text: str,
    interval: float = 0.05,
    name: str = "default"
) -> Dict[str, Any]:
    """在 VNC 会话中输入文本"""
    client = get_vnc_client(name)
    if not client:
        return {
            "success": False,
            "error": f"客户端 '{name}' 不存在，请先连接 VNC"
        }
    
    if not client.connected:
        return {
            "success": False,
            "error": "VNC 未连接"
        }
    
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            client.executor,
            lambda: client.type_text(text, interval)
        )
        return {
            "success": True,
            "message": f"已输入文本（{len(text)} 字符）"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def vnc_mouse_click(
    x: int,
    y: int,
    button: int = 1,
    double: bool = False,
    name: str = "default"
) -> Dict[str, Any]:
    """在 VNC 会话中点击鼠标"""
    client = get_vnc_client(name)
    if not client:
        return {
            "success": False,
            "error": f"客户端 '{name}' 不存在，请先连接 VNC"
        }
    
    if not client.connected:
        return {
            "success": False,
            "error": "VNC 未连接"
        }
    
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            client.executor,
            lambda: client.mouse_click(x, y, button, double)
        )
        return {
            "success": True,
            "message": f"已点击 ({x}, {y})",
            "button": button,
            "double": double
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def vnc_mouse_move(
    x: int,
    y: int,
    name: str = "default"
) -> Dict[str, Any]:
    """在 VNC 会话中移动鼠标"""
    client = get_vnc_client(name)
    if not client:
        return {
            "success": False,
            "error": f"客户端 '{name}' 不存在，请先连接 VNC"
        }
    
    if not client.connected:
        return {
            "success": False,
            "error": "VNC 未连接"
        }
    
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            client.executor,
            lambda: client.mouse_move(x, y)
        )
        return {
            "success": True,
            "message": f"已移动到 ({x}, {y})"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def vnc_mouse_drag(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    name: str = "default"
) -> Dict[str, Any]:
    """在 VNC 会话中拖拽鼠标"""
    client = get_vnc_client(name)
    if not client:
        return {
            "success": False,
            "error": f"客户端 '{name}' 不存在，请先连接 VNC"
        }
    
    if not client.connected:
        return {
            "success": False,
            "error": "VNC 未连接"
        }
    
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            client.executor,
            lambda: client.mouse_drag(start_x, start_y, end_x, end_y)
        )
        return {
            "success": True,
            "message": f"已拖拽 ({start_x}, {start_y}) -> ({end_x}, {end_y})"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


class VNCSkill:
    """VNC 操作技能封装"""
    
    def __init__(self, config: Optional[VNCConfig] = None):
        self.config = config or VNCConfig()
        self.client: Optional[VNCClient] = None
    
    async def connect(self, host: str = None, port: int = None, password: str = None) -> Dict[str, Any]:
        """连接 VNC"""
        result = await vnc_connect(
            host=host or self.config.host,
            port=port or self.config.port,
            password=password or self.config.password
        )
        if result.get("success"):
            self.client = get_vnc_client()
        return result
    
    async def disconnect(self) -> Dict[str, Any]:
        """断开连接"""
        return await vnc_disconnect()
    
    async def screenshot(self, **kwargs) -> Dict[str, Any]:
        """获取截图"""
        return await vnc_screenshot(**kwargs)
    
    async def press(self, key: str, count: int = 1) -> Dict[str, Any]:
        """发送按键"""
        return await vnc_key_press(key, count)
    
    async def type(self, text: str, interval: float = 0.05) -> Dict[str, Any]:
        """输入文本"""
        return await vnc_type_text(text, interval)
    
    async def click(self, x: int, y: int, button: int = 1, double: bool = False) -> Dict[str, Any]:
        """鼠标点击"""
        return await vnc_mouse_click(x, y, button, double)
    
    async def move(self, x: int, y: int) -> Dict[str, Any]:
        """移动鼠标"""
        return await vnc_mouse_move(x, y)
    
    async def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> Dict[str, Any]:
        """拖拽"""
        return await vnc_mouse_drag(start_x, start_y, end_x, end_y)


# 模块可用性标志
VNC_SKILL_AVAILABLE = VNC_AVAILABLE