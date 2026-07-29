#!/data/data/com.termux/files/usr/bin/python3
"""
📦 Termux 初始化工具 — 自动下载最新 APK + 环境检查

功能：
  1. 检测设备架构，从 GitHub 获取最新 Termux release
  2. 下载对应架构的 APK（支持断点续传 + 多镜像重试）
  3. 校验文件完整性
  4. 检查基础依赖（curl、git、python 等）
  5. 可选：启动局域网共享服务器

用法：
  python3 init.py              # 完整运行：检测→下载→校验
  python3 init.py --check      # 仅检查环境，不下载
  python3 init.py --serve      # 下载后启动 HTTP 共享服务器
  python3 init.py --help       # 查看帮助
"""

import os
import sys
import json
import hashlib
import platform
import subprocess
import urllib.request
import urllib.error
import shutil
import time
import argparse
from pathlib import Path

# ─── 配置 ───────────────────────────────────────────────────────
REPO_OWNER = "termux"
REPO_NAME = "termux-app"
API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
MIRROR_URLS = [
    # 官方源
    "https://github.com/{owner}/{repo}/releases/download/{tag}/{filename}",
    # 镜像加速（按需启用）
    # "https://ghproxy.net/https://github.com/{owner}/{repo}/releases/download/{tag}/{filename}",
    # "https://mirror.ghproxy.com/https://github.com/{owner}/{repo}/releases/download/{tag}/{filename}",
]

HOME = os.path.expanduser("~")
SHARE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT = os.path.join(SHARE_DIR, "termux-app.apk")

# ─── 工具函数 ───────────────────────────────────────────────────

def log(msg, emoji="📌"):
    """带表情的统一输出"""
    print(f"  {emoji} {msg}")

def ok(msg):
    print(f"  ✅ {msg}")

def warn(msg):
    print(f"  ⚠️  {msg}")

def fail(msg):
    print(f"  ❌ {msg}")
    return False

def run_cmd(cmd, capture=False):
    """执行 shell 命令"""
    try:
        if capture:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return r.returncode == 0, r.stdout.strip()
        r = subprocess.run(cmd, shell=True, timeout=60)
        return r.returncode == 0, ""
    except subprocess.TimeoutExpired:
        return False, "超时"
    except Exception as e:
        return False, str(e)

# ─── 架构检测 ───────────────────────────────────────────────────

def detect_arch():
    """检测设备架构，返回 APK 文件名中的架构标识"""
    machine = platform.machine().lower()
    log(f"检测到架构: {machine}")

    arch_map = {
        "aarch64":  "arm64-v8a",
        "arm64":    "arm64-v8a",
        "armv7l":   "armeabi-v7a",
        "arm":      "armeabi-v7a",
        "x86_64":   "x86_64",
        "i686":     "x86",
        "i386":     "x86",
    }
    return arch_map.get(machine, "arm64-v8a")

# ─── 获取最新版本 ───────────────────────────────────────────────

def get_latest_release():
    """从 GitHub API 获取最新 release 信息"""
    log("获取最新 Termux 版本...", "🌐")
    req = urllib.request.Request(API_URL, headers={
        "User-Agent": "Termux-Init/1.0",
        "Accept": "application/vnd.github+json",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            tag = data["tag_name"]        # 如 "v0.118.3"
            version = tag.lstrip("v")
            assets = data.get("assets", [])

            # 查找所有 APK 文件
            apks = []
            for asset in assets:
                name = asset["name"]
                if name.endswith(".apk"):
                    apks.append({
                        "name": name,
                        "size": asset["size"],
                        "url": asset["browser_download_url"],
                    })

            return version, tag, apks
    except urllib.error.HTTPError as e:
        fail(f"GitHub API 请求失败 (HTTP {e.code})")
        # 备用：从本地获取版本号
        return None, None, None
    except Exception as e:
        fail(f"获取版本信息失败: {e}")
        return None, None, None

# ─── 下载文件 ───────────────────────────────────────────────────

def download_file(url, dest, expected_size=None):
    """下载文件，带进度显示，支持断点续传"""
    resume_size = 0
    mode = "wb"

    # 检查是否有部分下载
    if os.path.exists(dest):
        resume_size = os.path.getsize(dest)
        if expected_size and resume_size >= expected_size:
            ok(f"文件已存在: {dest}")
            return True
        if resume_size > 0:
            log(f"发现部分下载 ({resume_size / 1024 / 1024:.1f}MB)，尝试续传...", "🔄")
            mode = "ab"

    req = urllib.request.Request(url, headers={
        "User-Agent": "Termux-Init/1.0",
        "Range": f"bytes={resume_size}-" if resume_size > 0 else "",
    })

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            total = expected_size or resp.headers.get("Content-Length")
            if total:
                total = int(total) + resume_size if not expected_size else total

            downloaded = resume_size
            chunk_size = 64 * 1024  # 64KB
            last_log = 0

            with open(dest, mode) as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    # 每 2MB 或完成时打印进度
                    if total and (downloaded - last_log > 2 * 1024 * 1024 or downloaded >= total):
                        pct = downloaded * 100 // total
                        print(f"\r   📥 下载中: {pct}% ({downloaded // 1024 // 1024}MB / {total // 1024 // 1024}MB)", end="")
                        last_log = downloaded

            if total:
                print(f"\r   📥 下载完成: {downloaded // 1024 // 1024}MB / {total // 1024 // 1024}MB    ")
            else:
                print(f"\r   📥 下载完成: {downloaded // 1024 // 1024}MB    ")
            return True

    except urllib.error.HTTPError as e:
        if e.code == 416:  # Range 错误，文件已完整
            ok("文件已完整下载")
            return True
        fail(f"HTTP {e.code}")
        return False
    except Exception as e:
        fail(f"下载失败: {e}")
        return False

# ─── SHA256 校验 ────────────────────────────────────────────────

def sha256_file(path):
    """计算文件的 SHA256"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(64 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def verify_checksum(filepath):
    """计算并显示文件的 SHA256"""
    if not os.path.exists(filepath):
        return False
    log("计算文件校验值...", "🔐")
    checksum = sha256_file(filepath)
    size = os.path.getsize(filepath)
    ok(f"SHA256: {checksum}")
    ok(f"大小: {size / 1024 / 1024:.1f}MB")
    return checksum

# ─── 环境检查 ───────────────────────────────────────────────────

def check_environment():
    """检查基础依赖是否齐全"""
    log("检查运行环境...", "🔍")
    all_ok = True
    checks = []

    # Python 版本
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    checks.append(("Python3", py_ver, True))

    # 基础工具
    for tool in ["curl", "git", "pkg"]:
        ok_flag, ver = run_cmd(f"command -v {tool} && ({tool} --version 2>&1 || {tool} --help 2>&1) | head -1 || echo MISSING")
        ver_str = ver if ok_flag else "未安装"
        checks.append((tool, ver_str, ok_flag))
        if not ok_flag:
            all_ok = False

    # 架构
    arch = detect_arch()
    checks.append(("架构", arch, True))

    # 打印表格
    print()
    print(f"  {'工具':<12} {'状态':<40}")
    print(f"  {'─'*52}")
    for name, ver, ok_flag in checks:
        status = f"✅ {ver}" if ok_flag else f"❌ {ver}"
        print(f"  {name:<12} {status}")
    print()

    return all_ok

# ─── 局域网共享 ─────────────────────────────────────────────────

def start_http_server(port=8000):
    """启动 HTTP 共享服务器"""
    server_script = os.path.join(SHARE_DIR, "server.py")
    if os.path.exists(server_script):
        log(f"启动 HTTP 服务器 (端口 {port})...", "🌐")
        os.chdir(SHARE_DIR)
        cmd = f"nohup python3 server.py > server.log 2>&1 &"
        ok_flag, _ = run_cmd(cmd)
        if ok_flag:
            ok(f"服务器已启动: http://0.0.0.0:{port}")
            return True
        else:
            fail("服务器启动失败")
            return False
    else:
        warn("server.py 不存在，使用内置 http.server")
        os.chdir(SHARE_DIR)
        cmd = f"nohup python3 -m http.server {port} > server.log 2>&1 &"
        run_cmd(cmd)
        ok(f"服务器已启动: http://0.0.0.0:{port}")
        return True

# ─── 主流程 ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="📦 Termux 初始化工具 — 自动下载最新 APK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 init.py                 下载最新 APK 到当前目录
  python3 init.py --check         仅检查环境
  python3 init.py --serve         下载后启动 HTTP 共享
  python3 init.py --output ./x.apk  指定输出路径
  python3 init.py --mirror ghproxy  使用镜像加速
        """
    )
    parser.add_argument("--check", action="store_true", help="仅检查环境，不下载")
    parser.add_argument("--serve", action="store_true", help="下载后启动 HTTP 共享服务器")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="APK 保存路径 (默认: ./termux-app.apk)")
    parser.add_argument("--mirror", choices=["ghproxy", "ghproxy.net"], help="使用镜像加速下载")
    args = parser.parse_args()

    print()
    print("  ╔═══════════════════════════════════════════╗")
    print("  ║    📦 Termux 初始化工具 v1.0              ║")
    print("  ╚═══════════════════════════════════════════╝")
    print()

    # ── 仅检查 ──
    if args.check:
        check_environment()
        return

    # ── 环境检查 ──
    check_environment()

    # ── 获取最新版本 ──
    version, tag, apks = get_latest_release()
    if not version:
        warn("无法获取最新版本，使用本地备用信息")
        version = "0.118.3"
        tag = f"v{version}"

    print(f"  📋 最新版本: {tag}")
    print()

    # ── 选择对应架构的 APK ──
    arch = detect_arch()
    target_apk = None

    if apks:
        for apk in apks:
            if arch in apk["name"]:
                target_apk = apk
                break
        if not target_apk:
            warn(f"未找到 {arch} 架构的 APK，使用第一个")
            target_apk = apks[0]

        log(f"目标文件: {target_apk['name']}", "🎯")
        log(f"文件大小: {target_apk['size'] / 1024 / 1024:.1f}MB", "📏")

        # ── 下载 ──
        dest = args.output
        log(f"下载到: {dest}", "💾")
        print()

        # 构造下载 URL
        download_url = target_apk["url"]
        if args.mirror == "ghproxy":
            download_url = f"https://mirror.ghproxy.com/{download_url}"
        elif args.mirror == "ghproxy.net":
            download_url = f"https://ghproxy.net/{download_url}"

        success = download_file(download_url, dest, expected_size=target_apk["size"])

        if not success:
            # 尝试备用镜像
            warn("主源下载失败，尝试备用镜像...")
            mirror_url = f"https://mirror.ghproxy.com/{target_apk['url']}"
            success = download_file(mirror_url, dest, expected_size=target_apk["size"])

        print()

        if success and os.path.exists(dest):
            checksum = verify_checksum(dest)
            print()
            ok(f"下载完成: {dest}")
            if checksum:
                print(f"  🔐 SHA256: {checksum}")
        else:
            fail("下载失败，请检查网络后重试")
            sys.exit(1)

    else:
        # API 获取失败时的备用方案
        warn("无法从 GitHub API 获取版本信息")
        arch = detect_arch()
        fallback_url = (
            f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/download/"
            f"{tag}/termux-app_{version}+github-debug_{arch}.apk"
        )
        log(f"尝试直接下载: {fallback_url}", "🌐")
        success = download_file(fallback_url, args.output)
        if success:
            verify_checksum(args.output)
        else:
            fail("下载失败")
            sys.exit(1)

    # ── 启动服务器 ──
    if args.serve:
        print()
        start_http_server()

    print()
    print("  ✨ 完成！")
    print()


if __name__ == "__main__":
    main()
