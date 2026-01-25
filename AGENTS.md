# 项目概览

本项目是 iFlow CLI 与 OpenSandbox 框架的集成环境，提供了通过 Web 界面与 iFlow AI 模型交互的能力。该项目基于 OpenSandbox 框架构建，支持安全的代码执行环境，并集成了桌面环境（VNC）和 Chrome 浏览器功能，为用户提供了一个功能丰富的 AI 开发环境。


### .python-version
指定 Python 版本（3.10）。


### OpenSandbox/
OpenSandbox 框架的完整源代码，包括服务器、组件、SDK 和示例。


### AGENTS.md
本文件，用于为 iFlow CLI 提供上下文信息，帮助 AI 智能体理解项目结构和用途。


## 架构设计

```
用户浏览器 → FastAPI 服务器 → OpenSandbox API → Docker 容器 → iFlow CLI → iFlow API
     ↑                              ↓
   WebSocket ← → 实时通信 ← → 桌面环境(VNC/Chrome)
```

## OpenSandbox 框架结构

OpenSandbox 框架的主要组件包括：

- **server/**：Python FastAPI 服务，沙箱管理 API
- **components/**：核心组件（execd, ingress, egress 等）
- **sdks/**：多语言 SDK（Python, JavaScript, Kotlin）
- **examples/**：使用示例（包括 iFlow-CLI 集成示例）
- **sandboxes/**：运行时沙箱实现
- **specs/**：OpenAPI 规范和生命周期定义
- **tests/**：跨组件测试

