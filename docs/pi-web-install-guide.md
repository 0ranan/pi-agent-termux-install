# 🌐 Termux 安装 pi-web（Web 界面）

> 环境：Termux 0.118.3 (F-Droid) / 实测版本：pi-web 0.8.2
> npm 包：`@agegr/pi-web` · 端口：**30141**

## 简介

pi-web 是 pi-agent 的 Web 图形界面，基于 Next.js 构建。

## 安装步骤

```bash
# 全局安装 pi-web
npm install -g @agegr/pi-web@latest

# 验证安装
pi-web --version   # 0.8.2
```

## 启动服务

前台启动：

```bash
pi-web
```

后台启动（推荐，Termux 专用）：

```bash
nohup pi-web > ~/pi-web.log 2>&1 &
```

访问：浏览器打开 `http://localhost:30141`

## 通过 service-manager 管理

pi-web 已注册为系统服务：

```bash
service-skill start pi-web   # 启动
service-skill stop pi-web    # 停止
service-skill log pi-web     # 查看日志
sss                          # 查看所有服务状态
```
