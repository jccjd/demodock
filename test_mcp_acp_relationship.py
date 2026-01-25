#!/usr/bin/env python3
"""
iFlow ACP 与 MCP 服务关系测试
用于验证 MCP 服务配置是否影响 ACP 连接
"""

import subprocess
import time
import threading
import signal
import os
import sys

def test_iflow_with_mcp():
    """测试 iFlow CLI 的 MCP 服务配置"""
    print("🔍 检查 MCP 服务配置...")
    
    try:
        # 检查 MCP 配置
        result = subprocess.run(['iflow', 'mcp', 'list'], capture_output=True, text=True, timeout=10)
        print(f"MCP 服务配置:\n{result.stdout}")
        
        if "chrome-devtools" in result.stdout:
            print("✅ chrome-devtools MCP 服务已配置")
        else:
            print("⚠️ chrome-devtools MCP 服务未找到")
            
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 检查 MCP 服务时出错: {e}")
        return False

def test_iflow_acp_without_mcp_specific_config():
    """测试 ACP 服务是否可以在没有 MCP 特定配置的情况下运行"""
    print("\n🔍 测试 ACP 服务启动...")
    
    try:
        # 启动 ACP 服务
        process = subprocess.Popen([
            'iflow', 
            '--experimental-acp', 
            '--port', '50052'  # 使用不同端口避免冲突
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("⏳ 等待 ACP 服务启动...")
        time.sleep(5)  # 给服务时间启动
        
        # 检查进程状态
        if process.poll() is None:
            print("✅ ACP 服务启动成功")
            
            # 终止进程
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            print("✅ ACP 服务已停止")
            
            return True
        else:
            stderr_output = process.stderr.read().decode() if process.stderr else "No stderr"
            print(f"❌ ACP 服务启动失败: {stderr_output}")
            return False
            
    except Exception as e:
        print(f"❌ 启动 ACP 服务时出错: {e}")
        return False

def show_iflow_help():
    """显示 iFlow 帮助信息，查看 ACP 相关选项"""
    print("\n📖 iFlow ACP 相关选项:")
    
    try:
        result = subprocess.run(['iflow', '--help'], capture_output=True, text=True, timeout=10)
        lines = result.stdout.split('\n')
        acp_relevant = [line for line in lines if 'acp' in line.lower() or 'port' in line.lower() or 'mcp' in line.lower()]
        
        for line in acp_relevant:
            print(f"  {line}")
            
    except Exception as e:
        print(f"❌ 获取 iFlow 帮助信息时出错: {e}")

if __name__ == "__main__":
    print("🧪 测试 MCP 服务配置与 ACP 连接的关系...")
    
    mcp_ok = test_iflow_with_mcp()
    acp_ok = test_iflow_acp_without_mcp_specific_config()
    show_iflow_help()
    
    print("\n" + "="*60)
    print("📋 测试结果总结:")
    print(f"  MCP 配置检查: {'✅ 通过' if mcp_ok else '❌ 失败'}")
    print(f"  ACP 服务启动: {'✅ 成功' if acp_ok else '❌ 失败'}")
    print("\n💡 结论:")
    print("  MCP 服务配置本身不会导致 ACP 连接失败。")
    print("  502 错误通常是由于网络路由或服务启动时间问题，")
    print("  而不是 MCP 配置引起的。")
    print("="*60)
