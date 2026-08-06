#!/data/data/com.termux/files/usr/bin/python3
"""
局域网文件共享服务器 + 报错收集 API
- 静态文件服务（下载 APK、HTML 页面）
- POST /api/report — 接收报错信息，保存到本地文件
"""

import os
import json
import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

try:
    import markdown  # Markdown → HTML 渲染
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

# 报错信息保存目录
REPORT_DIR = os.path.expanduser("~/error-reports")
os.makedirs(REPORT_DIR, exist_ok=True)

# Markdown 渲染页面模板（带样式）
MARKDOWN_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, system-ui, "Segoe UI", sans-serif;
            max-width: 820px;
            margin: 30px auto;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
            line-height: 1.7;
        }}
        .md-card {{
            background: white;
            border-radius: 12px;
            padding: 35px 45px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .md-card h1 {{
            font-size: 26px;
            border-bottom: 2px solid #e8e8e8;
            padding-bottom: 12px;
            margin-top: 10px;
        }}
        .md-card h2 {{
            font-size: 21px;
            border-bottom: 1px solid #eee;
            padding-bottom: 8px;
            margin-top: 32px;
        }}
        .md-card h3 {{ font-size: 18px; margin-top: 24px; }}
        .md-card h4 {{ font-size: 16px; margin-top: 20px; }}
        .md-card a {{ color: #0366d6; text-decoration: none; }}
        .md-card a:hover {{ text-decoration: underline; }}
        .md-card code {{
            background: #f0f0f0;
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 0.9em;
            font-family: "JetBrains Mono", Consolas, monospace;
        }}
        .md-card pre {{
            background: #1e1e2e;
            color: #e8e8e8;
            border-radius: 8px;
            padding: 16px 20px;
            overflow-x: auto;
            line-height: 1.5;
        }}
        .md-card pre code {{ background: none; padding: 0; color: inherit; }}
        .md-card blockquote {{
            border-left: 4px solid #0366d6;
            margin: 16px 0;
            padding: 8px 16px;
            background: #f0f7ff;
            border-radius: 0 8px 8px 0;
            color: #555;
        }}
        .md-card table {{
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }}
        .md-card th, .md-card td {{
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }}
        .md-card th {{ background: #f8f8f8; font-weight: 600; }}
        .md-card tr:nth-child(even) {{ background: #fafafa; }}
        .md-card img {{ max-width: 100%; border-radius: 8px; }}
        .md-card hr {{ border: none; border-top: 1px solid #e0e0e0; margin: 24px 0; }}
        .md-card ul, .md-card ol {{ padding-left: 24px; }}
        .md-card li {{ margin: 4px 0; }}
        .md-card input[type="checkbox"] {{ margin-right: 6px; }}
        .back-link {{
            display: inline-block;
            margin-bottom: 16px;
            color: #666;
            font-size: 14px;
            text-decoration: none;
        }}
        .back-link:hover {{ color: #0366d6; }}
        @media (max-width: 600px) {{
            .md-card {{ padding: 20px; }}
            body {{ padding: 10px; }}
        }}
    </style>
</head>
<body>
    <a class="back-link" href="/">← 返回首页</a>
    <div class="md-card">
{content}
    </div>
</body>
</html>
"""

class CustomHandler(SimpleHTTPRequestHandler):
    """自定义 HTTP 请求处理器"""

    def do_GET(self):
        """处理 GET 请求：.md 文件渲染为 HTML 页面，其余走静态文件服务"""
        parsed = urlparse(self.path)
        path = parsed.path

        # 判断是否为 .md 文件请求
        if path.endswith(".md"):
            filepath = self.translate_path(path)
            if os.path.isfile(filepath):
                self.render_markdown(filepath)
            else:
                self.send_error(404, "Not Found")
            return

        # 其他请求走默认静态文件服务
        super().do_GET()

    def render_markdown(self, filepath):
        """将 Markdown 文件渲染为 HTML 页面返回"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                md_text = f.read()

            # Markdown → HTML
            if MARKDOWN_AVAILABLE:
                html_body = markdown.markdown(
                    md_text,
                    extensions=["fenced_code", "tables", "toc", "sane_lists", "nl2br"],
                )
            else:
                # 兜底：未安装 markdown 库时，按纯文本展示
                import html as html_mod
                html_body = f"<pre>{html_mod.escape(md_text)}</pre>"

            # 页面标题：取文件名（去 .md 后缀）
            title = os.path.basename(filepath)[:-3]

            # 组装完整 HTML 页面
            page = MARKDOWN_TEMPLATE.format(title=title, content=html_body)

            body = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            # 客户端提前断开连接，无需响应
            return
        except Exception as e:
            self.send_error(500, f"渲染失败: {str(e)}")

    def do_POST(self):
        """处理 POST 请求"""
        parsed = urlparse(self.path)

        if parsed.path == "/api/report":
            self.handle_report()
        else:
            self.send_error(404, "Not Found")

    def handle_report(self):
        """处理报错上报：读取 JSON → 保存到文件"""
        try:
            # 读取请求体
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            # 提取报错内容
            error_text = data.get("text", "").strip()
            source = data.get("source", "unknown")  # 来源标识
            if not error_text:
                self.send_json(400, {"ok": False, "msg": "报错内容不能为空"})
                return

            # 生成文件名：error_20260729_233000_xxx.log
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            filename = f"error_{timestamp}_{os.urandom(4).hex()}.log"
            filepath = os.path.join(REPORT_DIR, filename)

            # 写入文件
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# 报错时间: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 来源: {source}\n")
                f.write(f"# {'='*50}\n\n")
                f.write(error_text)
                f.write("\n")

            # 同时也追加到汇总日志
            summary_log = os.path.join(REPORT_DIR, "all_reports.log")
            with open(summary_log, "a", encoding="utf-8") as f:
                f.write(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 来源:{source} | 文件:{filename}\n")
                f.write(f"{error_text}\n")
                f.write(f"{'─'*60}\n")

            self.send_json(200, {
                "ok": True,
                "msg": "报错已保存",
                "file": filename,
                "path": filepath
            })

        except json.JSONDecodeError:
            self.send_json(400, {"ok": False, "msg": "无效的 JSON 格式"})
        except Exception as e:
            self.send_json(500, {"ok": False, "msg": f"服务器错误: {str(e)}"})

    def send_json(self, status_code, data):
        """发送 JSON 响应"""
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")  # CORS
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # 让目录列表更好看
    def list_directory(self, path):
        try:
            return SimpleHTTPRequestHandler.list_directory(self, path)
        except:
            self.send_error(404, "No permission to list directory")
            return None


def main():
    PORT = 8000
    server_addr = ("0.0.0.0", PORT)
    httpd = ThreadingHTTPServer(server_addr, CustomHandler)

    print(f"🚀 服务器已启动: http://0.0.0.0:{PORT}")
    print(f"📁 共享目录: {os.path.abspath('.')}")
    print(f"📝 报错保存: {REPORT_DIR}")
    print(f"    POST /api/report  — 提交报错信息")
    print(f"    GET  /            — 静态文件服务")
    print(f"{'─'*50}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已关闭")
        httpd.server_close()


if __name__ == "__main__":
    main()
