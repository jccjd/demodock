#!/usr/bin/env python3
"""
测试 VNC 连接
"""

import sys
from vncdotool import api
from PIL import Image
import base64
from io import BytesIO

# VNC 配置
VNC_HOST = "10.8.136.182"
VNC_PORT = 5900
VNC_PASSWORD = "admin"

def test_vnc_connection():
    """测试 VNC 连接和图像捕获"""
    try:
        print(f"正在连接到 VNC 服务器: {VNC_HOST}:{VNC_PORT}...")

        # 连接到 VNC 服务器
        client = api.connect(f"{VNC_HOST}:{VNC_PORT}", password=VNC_PASSWORD)
        print("✅ VNC 连接成功！")

        # 捕获屏幕
        print("正在捕获屏幕...")
        screen = client.captureScreen()
        print(f"✅ 屏幕捕获成功！尺寸: {screen.size}")

        # 转换为 PIL Image
        img = Image.frombytes('RGB', screen.size, screen.data)

        # 保存为文件
        output_file = "vnc_test_capture.jpg"
        img.save(output_file, format='JPEG', quality=85)
        print(f"✅ 图像已保存到: {output_file}")

        # 获取 base64
        buffered = BytesIO()
        img.save(buffered, format='JPEG', quality=85)
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        print(f"✅ Base64 编码长度: {len(img_base64)} 字符")

        # 显示前 100 个字符
        print(f"Base64 预览: {img_base64[:100]}...")

        return True

    except Exception as e:
        print(f"❌ VNC 连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_vnc_connection()
    sys.exit(0 if success else 1)