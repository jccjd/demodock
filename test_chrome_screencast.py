# main.py
from opensandbox import SandboxClient
import requests
import time
from opensandbox import SandboxClient
def start_chrome_and_get_ws():
    client = SandboxClient(endpoint="http://127.0.0.1:48379") # 你的 OpenSandbox 地址
    
    # 1. 创建并启动 Chrome 容器
    # 确保镜像已经 pull 好了
    sandbox = client.create_sandbox(
        image="opensandbox/chrome:latest",
        ports=[9222, 5901]
    )
    print(f"Sandbox created: {sandbox.id}")
    
    # 等待 Chrome 启动
    time.sleep(3)

    # 2. 获取 DevTools 的代理地址
    # OpenSandbox 会把 9222 端口映射到宿主机的某个代理端口
    proxy_url = f"http://127.0.0.1:48379/proxy/{sandbox.id}/9222"
    
    # 3. 通过 /json 接口获取具体的 WebSocket 调试地址
    try:
        resp = requests.get(f"{proxy_url}/json")
        tabs = resp.json()
        # 找到类型为 'page' 的 tab
        page_tab = next(tab for tab in tabs if tab['type'] == 'page')
        
        # 这里的 URL 可能是内网 IP，需要把 IP/Port 替换为 OpenSandbox 的代理地址
        raw_ws_url = page_tab['webSocketDebuggerUrl']
        # 修正 URL 格式，确保前端能通过代理访问
        # 格式通常为 ws://127.0.0.1:48379/proxy/{id}/9222/devtools/page/{uuid}
        final_ws_url = raw_ws_url.replace("localhost:9222", f"127.0.0.1:48379/proxy/{sandbox.id}/9222")
        
        print(f"\n[成功] 复制以下 WebSocket 地址到前端 HTML 中:")
        print(final_ws_url)
        return final_ws_url
    except Exception as e:
        print(f"获取调试地址失败: {e}")

if __name__ == "__main__":
    start_chrome_and_get_ws()