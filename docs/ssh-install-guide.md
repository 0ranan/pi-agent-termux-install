# 🔐 Termux 安装 SSH 服务

> 环境：Termux 0.118.3 (F-Droid) / Android 12

## 安装与启动

```bash
# 安装 OpenSSH
pkg install openssh

# 设置登录密码
passwd

# 启动 SSH 服务（默认端口 8022）
sshd
```

## 查看用户名（重要）

在目标设备的 Termux 中执行：

```bash
whoami
# 输出示例: u0_a348
```

## 连接方式

从另一台设备 SSH 过来：

```bash
ssh 用户名@设备IP -p 8022
# 示例: ssh u0_a348@192.168.43.36 -p 8022
```

## 注意事项

- Termux 的 SSH 默认端口为 **8022**（非标准 22 端口）
- 首次连接需输入之前设置的密码
- 若无法连接，确认设备在同一局域网，且 Termux 进程未被系统杀掉
