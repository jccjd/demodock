# OpenSandbox + iFlow CLI Demo

这是一个演示如何使用 OpenSandbox 框架创建安全的沙箱环境，并在其中运行 iFlow AI CLI 的示例程序。

## 功能演示

这个 demo 包含以下演示场景：

1. **基础数学计算** - 让 AI 计算简单的数学问题
2. **Python 代码生成** - 让 AI 生成 Python 代码
3. **文本分析** - 让 AI 分析文本情感
4. **文件操作** - 在沙箱中创建文件并让 AI 读取分析
5. **连续提问** - 演示多轮对话能力

## 前置要求

- Python 3.10+
- Docker（用于运行 OpenSandbox 服务器）
- OpenSandbox Python SDK

## 快速开始

### 1. 安装依赖

```bash
pip install opensandbox
```

### 2. 设置环境变量

```bash
# OpenSandbox 配置
export SANDBOX_DOMAIN=localhost:8080
export SANDBOX_API_KEY=your_api_key_if_needed

# iFlow 配置（必需）
export IFLOW_API_KEY=your_iflow_api_key
export IFLOW_BASE_URL=https://apis.iflow.cn/v1
export IFLOW_MODEL_NAME=qwen3-coder-plus
```

### 3. 运行 demo

```bash
python demo.py
```

## 环境变量说明

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `SANDBOX_DOMAIN` | 否 | `localhost:8080` | OpenSandbox 服务器地址 |
| `SANDBOX_API_KEY` | 否 | 无 | OpenSandbox API 密钥（本地开发可选） |
| `SANDBOX_IMAGE` | 否 | `sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:latest` | 沙箱镜像 |
| `IFLOW_API_KEY` | **是** | 无 | iFlow API 密钥 |
| `IFLOW_BASE_URL` | 否 | `https://apis.iflow.cn/v1` | iFlow API 地址 |
| `IFLOW_MODEL_NAME` | 否 | `qwen3-coder-plus` | 使用的模型名称 |

## 运行 OpenSandbox 服务器（本地）

如果你想在本地运行 OpenSandbox 服务器：

```bash
# 拉取镜像
docker pull sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:latest

# 克隆 OpenSandbox 仓库
git clone https://github.com/alibaba/OpenSandbox.git
cd OpenSandbox/server

# 配置
cp example.config.toml ~/.sandbox.toml

# 安装依赖并启动
uv sync
uv run python -m src.main
```

## 输出示例

```
============================================================
OpenSandbox + iFlow CLI 演示程序
============================================================

配置信息:
  - 沙箱地址: localhost:8080
  - 沙箱镜像: sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:latest
  - iFlow模型: qwen3-coder-plus
  - iFlow地址: https://apis.iflow.cn/v1

正在创建沙箱环境...
沙箱创建成功！

正在安装 iFlow CLI...
=== 标准输出 ===
...
iFlow CLI 安装成功！

==================================================
演示 1: 基础数学计算
==================================================
=== 标准输出 ===
123 + 456 = 579
...
```

## 相关链接

- [OpenSandbox](https://github.com/alibaba/OpenSandbox) - OpenSandbox 框架
- [iFlow CLI](https://cli.iflow.cn/) - iFlow 官方 CLI
- [OpenSandbox Examples](https://github.com/alibaba/OpenSandbox/tree/main/examples) - 更多示例