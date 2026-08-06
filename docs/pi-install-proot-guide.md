# 🐧 通过 proot-distro + Ubuntu 24.04 容器安装 pi-agent

> 记录于 2026-08-07，环境：Termux 0.118.3 (F-Droid) / Android 12 / aarch64 (ARM64)
> 适用于：希望将 pi 运行在隔离的 Linux 容器环境中，与宿主 Termux 环境分离

## 背景

pi-agent 是纯 Node.js 包，在 Termux **原生环境可直接安装运行**（见 `pi-install-guide.md`）。
本方案通过 **proot-distro + Ubuntu 24.04 容器** 提供完整的官方 Linux 环境，
适合需要环境隔离、依赖一致性或与 OpenCode 容器方案统一管理的场景。

## 前提：已安装 proot-distro + Ubuntu 容器

```bash
pkg install -y proot-distro
python3.14 "$PREFIX/bin/proot-distro" install ubuntu:24.04
```

> ⚠️ 若 `proot-distro` 命令提示 not found（shebang 指向 python3.13 而系统为 3.14），
> 使用 `python3.14 "$PREFIX/bin/proot-distro" <命令>` 代替。

## 安装步骤

### 第 1 步：进入 Ubuntu 容器并安装 Node.js

```bash
python3.14 "$PREFIX/bin/proot-distro" login ubuntu -- bash -c "
    apt update && \
    apt install -y nodejs npm
"
```

验证：

```bash
python3.14 "$PREFIX/bin/proot-distro" login ubuntu -- node --version
python3.14 "$PREFIX/bin/proot-distro" login ubuntu -- npm --version
```

> 📌 Ubuntu 24.04 默认 Node.js 为 18.x。若需更新版本，可在容器内使用 nvm 安装：
> ```bash
> curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
> ```

### 第 2 步：容器内全局安装 pi-coding-agent

```bash
python3.14 "$PREFIX/bin/proot-distro" login ubuntu -- bash -c "
    npm install -g @earendil-works/pi-coding-agent@latest
"
```

### 第 3 步：验证安装

```bash
python3.14 "$PREFIX/bin/proot-distro" login ubuntu -- pi --version
```

### 第 4 步：宿主机创建便捷入口

创建 `/data/data/com.termux/files/usr/bin/pi` 脚本：

```bash
#!/data/data/com.termux/files/usr/bin/bash
# 通过 proot-distro Ubuntu 容器运行 pi-agent
# 自动将宿主机当前目录作为容器内工作目录
CWD="$PWD"
exec python3.14 "$PREFIX/bin/proot-distro" login ubuntu -- bash -c "cd '$CWD' && exec pi \"\$@\"" _ "$@"
```

```bash
chmod +x "$PREFIX/bin/pi"
```

之后在 Termux 任意目录直接输入 `pi` 即可启动，并自动切换到当前目录。

## 日常使用

| 操作 | 命令 |
|------|------|
| 启动 pi | `pi` |
| 查看版本 | `pi --version` |
| 初始化项目 | `pi init`（在项目目录中执行） |
| 手动进入容器 | `python3.14 $PREFIX/bin/proot-distro login ubuntu` |

## 注意事项

1. **文件访问**：proot 默认不隔离宿主机文件系统，容器内可直接访问
   `/data/data/com.termux/files/home/` 等宿主机路径。
2. **Node.js 版本**：Ubuntu 24.04 apt 默认提供 Node 18，pi 兼容；如需最新版用 nvm。
3. **proot 性能**：容器内运行比原生略慢，但对交互式工具影响不大。
4. **与原生方案对比**：
   | 对比项 | 原生安装 | proot 容器安装 |
   |--------|:---:|:---:|
   | 安装复杂度 | 简单 | 较复杂 |
   | 环境隔离 | 无 | 有 |
   | 性能 | 快 | 略慢 |
   | 依赖一致性 | 依赖 Termux 环境 | 官方 Linux 环境 |

## 相关文档

- 原生安装：`pi-install-guide.md`
- OpenCode 容器安装：`opencode-install-guide.md`
