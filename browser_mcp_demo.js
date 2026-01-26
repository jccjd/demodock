// 浏览器 MCP 演示 - 前端 JavaScript
let isRunning = false;
let operationCount = 0;
let ws = null;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    log('系统初始化完成', 'info');
    updateStatus('connectionStatus', '未连接');
});

// WebSocket 连接
function connectWebSocket() {
    const mcpServer = document.getElementById('mcpServer').value || 'http://localhost:8081';
    const wsUrl = mcpServer.replace('http://', 'ws://').replace('https://', 'wss://');
    
    try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = function() {
            log('WebSocket 连接成功', 'success');
            updateStatus('connectionStatus', '已连接');
        };
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            handleMCPResponse(data);
        };
        
        ws.onerror = function(error) {
            log('WebSocket 错误: ' + error.message, 'error');
            updateStatus('connectionStatus', '连接错误');
        };
        
        ws.onclose = function() {
            log('WebSocket 连接关闭', 'warning');
            updateStatus('connectionStatus', '未连接');
        };
    } catch (error) {
        log('WebSocket 连接失败: ' + error.message, 'error');
    }
}

// 处理 MCP 响应
function handleMCPResponse(data) {
    if (data.type === 'screenshot') {
        document.getElementById('screenshot').src = data.content;
        log('截图更新成功', 'success');
    } else if (data.type === 'log') {
        log(data.message, data.level || 'info');
    } else if (data.type === 'elements') {
        displayElements(data.elements);
    } else if (data.type === 'text') {
        log('页面文本: ' + data.text.substring(0, 100) + '...', 'info');
    }
}

// 发送 MCP 请求
function sendMCPRequest(tool, params = {}) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        log('WebSocket 未连接，正在重连...', 'warning');
        connectWebSocket();
        return;
    }
    
    const request = {
        jsonrpc: '2.0',
        method: 'tools/call',
        params: {
            name: tool,
            arguments: params
        },
        id: Date.now()
    };
    
    ws.send(JSON.stringify(request));
    log(`发送请求: ${tool}`, 'info');
    incrementOperation();
}

// 开始演示
function startDemo() {
    if (isRunning) {
        log('演示已经在运行中', 'warning');
        return;
    }
    
    isRunning = true;
    log('开始浏览器自动化演示', 'success');
    
    connectWebSocket();
    
    // 执行完整流程
    setTimeout(() => {
        runFullWorkflow();
    }, 1000);
}

// 停止演示
function stopDemo() {
    isRunning = false;
    log('停止演示', 'warning');
    
    if (ws) {
        ws.close();
    }
}

// 运行预设操作
function runPreset(preset) {
    if (!isRunning) {
        log('请先点击"开始演示"', 'warning');
        return;
    }
    
    switch(preset) {
        case 'navigate':
            navigateToPage();
            break;
        case 'screenshot':
            takeScreenshot();
            break;
        case 'getText':
            getPageText();
            break;
        case 'getElements':
            getClickableElements();
            break;
        case 'evaluate':
            evaluateJavaScript();
            break;
        case 'fullWorkflow':
            runFullWorkflow();
            break;
    }
}

// 导航到页面
function navigateToPage() {
    const url = document.getElementById('targetUrl').value;
    log(`导航到: ${url}`, 'info');
    sendMCPRequest('browser_navigate', { url: url });
    updateStatus('currentPage', url);
    updateLastUpdate();
}

// 截图
function takeScreenshot() {
    log('正在截图...', 'info');
    sendMCPRequest('browser_screenshot', { path: '/tmp/screenshot.png' });
}

// 获取页面文本
function getPageText() {
    log('获取页面文本...', 'info');
    sendMCPRequest('browser_get_text');
}

// 获取可点击元素
function getClickableElements() {
    log('获取可点击元素...', 'info');
    sendMCPRequest('browser_get_clickable_elements');
}

// 执行 JavaScript
function evaluateJavaScript() {
    const jsCode = `
        (function() {
            return {
                title: document.title,
                url: window.location.href,
                timestamp: new Date().toISOString()
            };
        })();
    `;
    log('执行 JavaScript...', 'info');
    sendMCPRequest('browser_evaluate', { expression: jsCode });
}

// 完整工作流
async function runFullWorkflow() {
    log('开始执行完整工作流...', 'info');
    
    // 1. 导航
    navigateToPage();
    await sleep(2000);
    
    // 2. 截图
    takeScreenshot();
    await sleep(1000);
    
    // 3. 获取文本
    getPageText();
    await sleep(1000);
    
    // 4. 获取元素
    getClickableElements();
    await sleep(1000);
    
    // 5. 执行 JS
    evaluateJavaScript();
    await sleep(1000);
    
    // 6. 再次截图
    takeScreenshot();
    
    log('完整工作流执行完成', 'success');
}

// 显示元素
function displayElements(elements) {
    const container = document.getElementById('elementsContainer');
    
    if (!elements || elements.length === 0) {
        container.innerHTML = '<p class="placeholder">暂无元素信息</p>';
        return;
    }
    
    let html = '';
    elements.slice(0, 20).forEach((el, index) => {
        html += `
            <div class="element-item">
                <span class="element-tag">[${index}]</span>
                <span class="element-tag">${el.tag || 'unknown'}</span>
                <span class="element-text">${el.text || el.id || el.class || '无文本'}</span>
            </div>
        `;
    });
    
    container.innerHTML = html;
    log(`找到 ${elements.length} 个可点击元素`, 'info');
}

// 日志
function log(message, level = 'info') {
    const container = document.getElementById('logContainer');
    const time = new Date().toLocaleTimeString();
    
    const entry = document.createElement('div');
    entry.className = `log-entry log-${level}`;
    entry.innerHTML = `
        <span class="log-time">${time}</span>
        <span class="log-message">${message}</span>
    `;
    
    container.appendChild(entry);
    container.scrollTop = container.scrollHeight;
}

// 清空日志
function clearLogs() {
    const container = document.getElementById('logContainer');
    container.innerHTML = '';
    log('日志已清空', 'info');
}

// 更新状态
function updateStatus(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

// 更新最后更新时间
function updateLastUpdate() {
    const now = new Date().toLocaleTimeString();
    updateStatus('lastUpdate', now);
}

// 增加操作计数
function incrementOperation() {
    operationCount++;
    updateStatus('operationCount', operationCount.toString());
}

// 辅助函数
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 定时更新截图
setInterval(() => {
    if (isRunning && ws && ws.readyState === WebSocket.OPEN) {
        takeScreenshot();
    }
}, 5000);