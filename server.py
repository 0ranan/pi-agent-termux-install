#!/data/data/com.termux/files/usr/bin/python3
"""
局域网文件共享服务器 + 报错收集 API
- 静态文件服务（下载 APK、HTML 页面）
- POST /api/report — 接收报错信息，保存到本地文件
"""

import os
import json
import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

# 报错信息保存目录
REPORT_DIR = os.path.expanduser("~/error-reports")
os.makedirs(REPORT_DIR, exist_ok=True)

class CustomHandler(SimpleHTTPRequestHandler):
    """自定义 HTTP 请求处理器"""

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
    httpd = HTTPServer(server_addr, CustomHandler)

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
