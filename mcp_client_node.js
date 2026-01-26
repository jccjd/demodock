#!/usr/bin/env node

/**
 * 浏览器 MCP 客户端 - Node.js 版本
 * 使用官方 @modelcontextprotocol/sdk
 */

const { McpClient } = require('@modelcontextprotocol/sdk');

async function browserAutomation() {
    console.log('🚀 浏览器 MCP 客户端演示 (Node.js)');
    console.log('='.repeat(50));
    console.log();

    const client = new McpClient("http://localhost:8080/mcp");

    try {
        console.log('📡 正在连接到 MCP 服务器...');
        await client.connect();
        console.log('✅ 连接成功');
        console.log();

        // 1. 导航到页面
        console.log('📍 步骤 1: 导航到 https://example.com');
        const navigateResult = await client.callTool("browser_navigate", {
            url: "https://example.com"
        });
        console.log('✅ 导航完成');
        if (navigateResult.content && navigateResult.content[0]) {
            console.log(`   ${navigateResult.content[0].text.substring(0, 100)}...`);
        }
        console.log();

        // 等待页面加载
        await new Promise(resolve => setTimeout(resolve, 2000));

        // 2. 获取截图
        console.log('📸 步骤 2: 获取页面截图');
        const screenshotResult = await client.callTool("browser_screenshot");
        console.log('✅ 截图完成');
        if (screenshotResult.content && screenshotResult.content[0]) {
            console.log(`   ${screenshotResult.content[0].text}`);
        }
        console.log();

        // 等待一下
        await new Promise(resolve => setTimeout(resolve, 1000));

        // 3. 获取页面文本
        console.log('📄 步骤 3: 获取页面文本内容');
        const textResult = await client.callTool("browser_get_text");
        console.log('✅ 获取文本完成');
        if (textResult.content && textResult.content[0]) {
            console.log(`   ${textResult.content[0].text.substring(0, 200)}...`);
        }
        console.log();

        // 等待一下
        await new Promise(resolve => setTimeout(resolve, 1000));

        // 4. 获取可点击元素
        console.log('🔍 步骤 4: 获取可点击元素');
        const elementsResult = await client.callTool("browser_get_clickable_elements");
        console.log('✅ 获取元素完成');
        if (elementsResult.content && elementsResult.content[0]) {
            console.log(`   ${elementsResult.content[0].text.substring(0, 200)}...`);
        }
        console.log();

        console.log('🎉 演示完成！');
        console.log();
        console.log('💡 提示: 你可以打开 VNC 查看器实时查看浏览器操作:');
        console.log('   http://localhost:8080/vnc/index.html?autoconnect=true');

    } catch (error) {
        console.error('❌ 错误:', error.message);
        console.error('💡 请确保:');
        console.log('   1. AIO Sandbox MCP 服务器正在运行 (http://localhost:8080)');
        console.log('   2. 已安装 @modelcontextprotocol/sdk: npm install @modelcontextprotocol/sdk');
    } finally {
        await client.disconnect();
        console.log();
        console.log('📡 已断开连接');
    }
}

// 运行演示
browserAutomation().catch(console.error);