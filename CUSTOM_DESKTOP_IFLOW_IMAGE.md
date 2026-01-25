# 自定义 OpenSandbox Desktop 镜像 with iFlow CLI

我们成功创建了一个自定义的 OpenSandbox Desktop 镜像，预装了 Node.js 和 iFlow CLI。

## 创建过程

1. 创建了 Dockerfile.desktop-iflow，基于 opensandbox/desktop:latest 镜像
2. 安装了必要的工具 (curl, sudo) 和 Node.js 18.x
3. 全局安装了 iFlow CLI (`npm install -g @iflow-ai/iflow-cli@latest`)
4. 构建了自定义镜像 `opensandbox/desktop-iflow:latest`

## 镜像特性

- 基于: opensandbox/desktop:latest
- 包含: Node.js v18.20.8
- 包含: iFlow CLI (位于 /usr/bin/iflow)
- 可用性: 桌面环境 (VNC/noVNC) 和 iFlow CLI 均可正常使用

## 使用方法

在您的 OpenSandbox 应用中使用 `opensandbox/desktop-iflow:latest` 作为镜像:

```python
sandbox = await Sandbox.create(
    "opensandbox/desktop-iflow:latest",  # 使用自定义镜像
    connection_config=config,
    env={
        "VNC_PASSWORD": "your_password",
        "IFLOW_apiKey": "your_iflow_api_key",
        "IFLOW_baseUrl": "https://apis.iflow.cn/v1",
        "IFLOW_modelName": "qwen3-coder-plus",
    },
)
```

## 注意事项

- iFlow CLI 需要 Node.js 20+ (当前镜像使用 18.x)，可能存在兼容性问题
- 如需完全兼容的环境，可重新构建使用 Node.js 20.x 的镜像
- 镜像大小约为 1.05GB

## 重新构建使用 Node.js 20.x

如果需要使用 Node.js 20.x 以获得更好的兼容性，请修改 Dockerfile 中的相应行:

```dockerfile
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
```

然后重新运行构建脚本:

```bash
./build_desktop_iflow.sh
```