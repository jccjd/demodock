import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # 替换为你图片中的 IP
    browser = p.chromium.connect_over_cdp("ws://10.8.135.251:3000")
    page = browser.new_page()
    page.goto("https://www.baidu.com")
    print("页面已打开，请刷新 /sessions 页面查看")
    
    # 保持运行 60 秒，不要关闭，否则会话会消失
    time.sleep(60) 
    browser.close()