# 🛠️ service-manager 服务管理

> 用于管理 Termux 中的后台服务，如 pi-web、SSH、code-server 等

## 常用命令

```bash
service-skill status               # 查看所有服务状态
service-skill start 服务名          # 启动服务
service-skill stop 服务名           # 停止服务
service-skill log 服务名 [行数]     # 查看日志
service-skill ports                # 查看端口清单
service-skill add 名称 "命令" 端口   # 添加新服务
service-skill remove 服务名         # 删除服务
service-skill enable 服务名         # 启用服务
service-skill disable 服务名        # 禁用服务
```

## 本机已注册服务

| 服务 | 端口 | 状态 |
|------|:---:|:---:|
| code-server | 8080 | 启用 |
| pi-web | 30141 | 启用 |
| sshd | 8022 | 禁用 |
| clash | 7892 | 禁用 |
| adb | 5037 | 禁用 |

## 配置文件

```text
~/.pi/agent/skills/service-manager/config/services.conf
```

格式：`服务名|启动命令|端口|日志文件|PID文件|启用状态`
