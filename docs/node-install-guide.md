# ⚡ Termux 安装 Node.js & npm

> 环境：Termux 0.118.3 (F-Droid) / 实测版本：node v24.18.0 / npm 11.18.0

## 安装

在 Termux 中直接用包管理器安装，一步到位，自带 npm：

```bash
pkg install nodejs-lts -y
```

## 验证

```bash
node -v   # v24.18.0
npm -v    # 11.18.0
```

## 网络问题处理

- 如果遇到网络问题，先执行 `pkg update` 更新源后再安装
- 如果 GitHub 直连不稳定，可通过本机代理 `http://192.168.43.1:7892` 加速（需先启动 Clash）
