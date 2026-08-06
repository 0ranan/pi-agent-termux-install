# 🖥️ 通过 proot-distro + Ubuntu 24.04 容器安装 code-server

> 记录于 2026-08-07，环境：Termux 0.118.3 (F-Droid) / Android 12 / aarch64 (ARM64)
> 版本：code-server 4.112.0（官方 Linux arm64 二进制，自带 Node 运行时）

## 背景

code-server 是 VS Code 的 Web 版本，可在浏览器中运行完整的 VS Code。
本方案通过 **proot-distro + Ubuntu 24.04 容器** 安装官方 Linux 二进制，
与宿主机 Termux 环境隔离，数据（配置、扩展）存储在容器内。

## 前提：已安装 proot-distro + Ubuntu 容器

```bash
pkg install -y proot-distro
python3.14 "$PREFIX/bin/proot-distro" install ubuntu:24.04
```

## 安装步骤

### 第 1 步：容器内下载并解压官方二进制

```bash
python3.14 "$PREFIX/bin/proot-distro" login ubuntu -- bash -c "
    cd /root && \
    curl -sL -o code-server.tar.gz \
      https://github.com/coder/code-server/releases/download/v4.112.0/code-server-4.112.0-linux-arm64.tar.gz && \
    mkdir -p /usr/local/lib/code-server && \
    tar -xzf code-server.tar.gz -C /usr/local/lib/code-server --strip-components=1 && \
    ln -sf /usr/local/lib/code-server/bin/code-server /usr/local/bin/code-server && \
    rm -f code-server.tar.gz
"
```

> 版本号按需替换，最新版见 https://github.com/coder/code-server/releases

### 第 2 步：验证容器内安装

```bash
python3.14 "$PREFIX/bin/proot-distro" login ubuntu -- code-server --version
# 输出: 4.112.0 ... with Code 1.112.0
```

### 第 3 步：宿主机创建便捷入口

将原生的 `$PREFIX/bin/code-server` 备份为 `code-server-native`，
然后创建 wrapper（通过容器运行）：

```bash
mv "$PREFIX/bin/code-server" "$PREFIX/bin/code-server-native"
```

创建 `/data/data/com.termux/files/usr/bin/code-server` 脚本：

```bash
#!/data/data/com.termux/files/usr/bin/bash
# 通过 proot-distro Ubuntu 容器运行 code-server
# 自动将宿主机当前目录作为容器内工作目录
CWD="$PWD"
exec python3.14 "$PREFIX/bin/proot-distro" login ubuntu -- bash -c "cd '$CWD' && exec code-server \"\$@\"" _ "$@"
```

```bash
chmod +x "$PREFIX/bin/code-server"
```

### 第 4 步：配置后台服务（service-manager）

service-manager 中 code-server 服务命令保持不变（wrapper 自动转发到容器）：

```text
code-server|code-server --auth none --bind-addr 0.0.0.0:8080|8080|code-server.log|code-server.pid|1
```

```bash
service-skill start code-server
service-skill status code-server
```

访问：浏览器打开 `http://localhost:8080`

## 日常使用

| 操作 | 命令 |
|------|------|
| 启动服务 | `service-skill start code-server` |
| 停止服务 | `service-skill stop code-server` |
| 查看日志 | `service-skill log code-server` |
| 手动运行（前台） | `code-server --auth none --bind-addr 0.0.0.0:8080` |

## 注意事项

1. **数据隔离**：容器版 code-server 的配置和扩展存储在容器内
   `/root/.config/code-server/` 与 `/root/.local/share/code-server/`，与宿主机隔离。
2. **网络共享**：proot 不隔离网络，容器内监听 8080 即宿主机 8080。
3. **原生版保留**：备份为 `code-server-native`，如需回退可直接使用。
4. **proot 性能**：容器内运行比原生略慢，对 Web IDE 影响不大。

## 相关文档

- Termux 环境安装：`termux-install-guide.md`
- OpenCode 容器安装：`opencode-install-guide.md`
- 服务管理：`service-manager-guide.md`
