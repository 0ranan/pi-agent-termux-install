# 🤖 Termux 原生安装 pi-agent（AI 编码助手）

> 记录于 2026-08-07，环境：Termux 0.118.3 (F-Droid) / Android 12 / aarch64 (ARM64)
> 本机版本：pi-coding-agent 0.82.1

## 简介

pi-agent（npm 包名 `@earendil-works/pi-coding-agent`）是一个终端 AI 编码助手，
支持 `read`、`bash`、`edit`、`write` 等工具操作。

GitHub: https://github.com/earendil-works/pi

## 安装前提

Termux 原生环境已安装 Node.js 与 npm：

```bash
node --version   # v24.14.1
npm --version    # 11.13.0
```

若未安装：

```bash
pkg install -y nodejs
```

## 安装步骤

### 第 1 步：全局安装 pi-coding-agent

```bash
npm install -g @earendil-works/pi-coding-agent@latest
```

### 第 2 步：验证安装

```bash
pi --version   # 本机: 0.82.1
```

### 第 3 步：初始化项目

在项目目录中执行：

```bash
pi init
```

### 第 4 步：启动对话

```bash
pi
```

## 日常使用

| 操作 | 命令 |
|------|------|
| 启动对话 | `pi` |
| 查看版本 | `pi --version` |
| 初始化项目 | `pi init` |
| 查看帮助 | `pi --help` |

## 注意事项

1. **npm 国内镜像**：若安装缓慢，可临时指定镜像源：
   ```bash
   npm install -g @earendil-works/pi-coding-agent@latest --registry=https://registry.npmmirror.com
   ```
2. **pi 是纯 Node.js 包**：在 Termux 原生环境可直接运行，无需容器或额外运行时。
3. **升级**：
   ```bash
   npm update -g @earendil-works/pi-coding-agent
   ```
