# 🐍 Termux 安装 Python3 & SkillHub

> 环境：Termux 0.118.3 (F-Droid) / 实测版本：python3 3.13.x

## 安装 Python3

SkillHub 技能商店依赖 Python3，安装后即可使用 `skillhub` 搜索安装各种技能：

```bash
pkg install python -y
```

## 验证

```bash
python3 --version   # 3.13.x
```

## 安装 SkillHub（技能商店）

```bash
# 一键安装
curl -fsSL https://skillhub-1388575217.cos.ap-guangzhou.myqcloud.com/install/install.sh | bash

# 添加到 PATH 并验证
export PATH="$HOME/.local/bin:$PATH"
skillhub --version

# 搜索技能
skillhub search github

# 安装技能到本机 skills 目录
skillhub install 技能名 --namespace 作者 --dir ~/.pi/agent/skills/
```

## 说明

- SkillHub 是国内优先的 Skill 商店，提供加速、合规的技能搜索与安装能力
- 本机 skills 目录：`~/.pi/agent/skills/`
- 项目地址：https://skillhub.cn
