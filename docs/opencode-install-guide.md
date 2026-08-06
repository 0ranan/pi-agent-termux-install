# 🚀 Termux 安装 OpenCode 完整指南

> 记录于 2026-08-07，环境：Termux 0.118.3 (F-Droid) / Android 12 / aarch64 (ARM64)

## 背景

OpenCode 是一个 AI 编码助手（类似 Claude Code），官方支持 Linux / macOS / Windows，
**不支持 Android / Termux**。本文记录在 Termux 上成功安装并运行 OpenCode 1.18.14 的完整过程，
包括踩过的所有坑和最终解决方案。

---

## 一、为什么不能直接安装？

### 1. npm 安装失败（平台限制）

```bash
npm install -g opencode-ai --registry=https://registry.npmmirror.com
```

报错：

```
npm error code EBADPLATFORM
npm error notsup Unsupported platform for opencode-ai@1.18.14:
wanted {"os":"darwin,linux,win32","cpu":"arm64,x64"}
(current: {"os":"android","cpu":"arm64"})
```

原因：Termux 中 Node 的 `process.platform` 返回 `'android'`，而 opencode-ai 包声明只支持
darwin / linux / win32。

### 2. 直接下载官方二进制失败（动态链接器缺失）

从 GitHub Releases 下载 `opencode-linux-arm64.tar.gz`（glibc 版）后直接运行报错：

```
sh: 1: /path/opencode: not found
```

原因：二进制需要动态链接器 `/lib/ld-linux-aarch64.so.1`（glibc），
但 Termux 使用 **Android bionic libc**（链接器在 `/system/bin/linker64`），没有 glibc 链接器。

musl 版（`opencode-linux-arm64-musl.tar.gz`）同样失败，需要 `/lib/ld-musl-aarch64.so.1`。

### 3. Termux glibc 环境修补失败（兼容性 bug）

安装 Termux glibc 用户仓库 + patchelf 修补链接器路径：

```bash
pkg install -y glibc-repo patchelf
pkg install -y glibc
patchelf --set-interpreter "$PREFIX/glibc/lib/ld-linux-aarch64.so.1" \
         --set-rpath "$PREFIX/glibc/lib" opencode
```

库能成功加载，但程序启动即段错误（SIGSEGV）。用 gdb 定位：

```
Program received signal SIGSEGV, Segmentation fault.
0x... in _dl_check_map_versions () from ld-linux-aarch64.so.1
```

根因：**OpenCode 是 Bun 编译的二进制**（包含 Bun 运行时 + JavaScriptCore），
其 ELF 版本信息结构在 Termux glibc 2.43 的动态链接器中解析异常，
指针计算得到无效地址（`x1=0x5a7ac0ae`），触发段错误。
这是 Termux glibc 与 Bun 编译二进制格式的兼容性问题，无法通过配置修复。

---

## 二、最终方案：proot-distro + Ubuntu 容器 ✅

原理：在 Termux 中用 proot-distro 安装 Ubuntu 24.04 容器，容器内提供**官方 glibc 2.39 环境**
（与 OpenCode 编译环境一致），OpenCode 在其中原生运行。

### 第 1 步：安装 proot-distro

```bash
pkg install -y proot-distro
```

> ⚠️ 注意：proot-distro 5.5.0 的 shebang 指向 `python3.13`，若系统 Python 已升级到 3.14，
> 直接运行 `proot-distro` 会报 `not found`。可用以下方式绕过：
> ```bash
> python3.14 "$PREFIX/bin/proot-distro" <命令>
> ```

### 第 2 步：安装 Ubuntu 24.04 容器

```bash
python3.14 "$PREFIX/bin/proot-distro" install ubuntu:24.04
```

（新版 proot-distro 从 Docker Hub 拉取 OCI 镜像，rootfs 约 27.5 MiB，速度较快）

### 第 3 步：在容器内下载并安装 OpenCode

```bash
python3.14 "$PREFIX/bin/proot-distro" login ubuntu -- bash -c "
    cd /root && \
    curl -sL -o opencode.tar.gz \
      https://github.com/anomalyco/opencode/releases/download/v1.18.14/opencode-linux-arm64.tar.gz && \
    tar -xzf opencode.tar.gz && \
    mv opencode /usr/local/bin/opencode && \
    chmod +x /usr/local/bin/opencode && \
    rm -f opencode.tar.gz
"
```

> 版本号按需替换，最新版资产名可在官方安装脚本中查看：
> `curl -sL https://opencode.ai/install | less`

验证：

```bash
python3.14 "$PREFIX/bin/proot-distro" login ubuntu -- opencode --version
# 输出: 1.18.14
```

### 第 4 步：宿主机创建便捷入口

创建 `/data/data/com.termux/files/usr/bin/opencode` 脚本：

```bash
#!/data/data/com.termux/files/usr/bin/bash
# 通过 proot-distro Ubuntu 容器运行 opencode
# 自动将宿主机当前目录作为容器内工作目录
CWD="$PWD"
exec python3.14 "$PREFIX/bin/proot-distro" login ubuntu -- bash -c "cd '$CWD' && exec opencode \"\$@\"" _ "$@"
```

```bash
chmod +x "$PREFIX/bin/opencode"
```

之后在 Termux 任意目录直接输入 `opencode` 即可启动，并自动切换到当前目录。

---

## 三、日常使用

| 操作 | 命令 |
|------|------|
| 启动 OpenCode | `opencode` |
| 查看版本 | `opencode --version` |
| 手动进入容器 | `python3.14 $PREFIX/bin/proot-distro login ubuntu` |
| 列出容器 | `python3.14 $PREFIX/bin/proot-distro list` |

---

## 四、注意事项

1. **proot 性能损耗**：容器内运行比原生略慢，但对 OpenCode 这种交互式工具影响不大。
2. **文件访问**：proot 默认不隔离宿主机文件系统，容器内可直接访问
   `/data/data/com.termux/files/home/` 等宿主机路径。
3. **后台保活**：Android 可能杀掉 Termux 进程，建议将 Termux 加入电池优化白名单。
4. **版本更新**：下载新版本时只需在容器内替换 `/usr/local/bin/opencode`。
5. **备用方案**：若 OpenCode 官方未来发布 Android 原生版本，可放弃容器方案直接安装。

---

## 五、相关资源

- OpenCode 仓库：https://github.com/anomalyco/opencode
- 官方安装脚本：https://opencode.ai/install
- proot-distro：`pkg install proot-distro`
- Termux glibc 仓库（备选方案，遇到 Bun 二进制兼容性问题）：`pkg install glibc-repo`
