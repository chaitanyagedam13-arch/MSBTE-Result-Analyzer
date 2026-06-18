from __future__ import annotations

import cgi
import html
import os
import shutil
import tempfile
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from msbte_result_analyzer import analyze_pdfs


HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "8000"))
OUTPUT_DIR = Path("output")


class UploadHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.respond_html(render_home())
            return
        if parsed.path == "/download":
            query = parse_qs(parsed.query)
            file_name = query.get("file", [""])[0]
            file_path = (OUTPUT_DIR / file_name).resolve()
            if OUTPUT_DIR.resolve() not in file_path.parents or not file_path.exists():
                self.send_error(404, "File not found")
                return
            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            self.send_header("Content-Disposition", f'attachment; filename="{file_path.name}"')
            self.end_headers()
            with file_path.open("rb") as source:
                shutil.copyfileobj(source, self.wfile)
            return
        self.send_error(404, "Not found")

    def do_POST(self) -> None:
        if self.path != "/analyze":
            self.send_error(404, "Not found")
            return
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            self.send_error(400, "Please upload PDFs using the form.")
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type},
        )
        files = form["pdfs"] if "pdfs" in form else []
        if not isinstance(files, list):
            files = [files]

        with tempfile.TemporaryDirectory(prefix="msbte_upload_") as tmp:
            upload_dir = Path(tmp)
            pdf_paths: list[Path] = []
            for item in files:
                if not item.filename:
                    continue
                safe_name = Path(item.filename).name
                if not safe_name.lower().endswith(".pdf"):
                    continue
                target = upload_dir / safe_name
                with target.open("wb") as output:
                    shutil.copyfileobj(item.file, output)
                pdf_paths.append(target)

            if not pdf_paths:
                self.respond_html(render_home("Please upload at least one PDF file."))
                return

            output_name = f"msbte_result_analysis_{uuid.uuid4().hex[:8]}.xlsx"
            output_path = OUTPUT_DIR / output_name
            result = analyze_pdfs(pdf_paths, output_path)
            self.respond_html(render_result(output_name, len(result.students), result.warnings))

    def respond_html(self, body: str, status: int = 200) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def render_home(message: str = "") -> str:
    notice = f'<p class="notice">{html.escape(message)}</p>' if message else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MSBTE Result Analyzer</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f5f7fb; color: #172033; }}
    main {{ max-width: 820px; margin: 48px auto; padding: 0 24px; }}
    section {{ background: #fff; border: 1px solid #d9e0ec; border-radius: 8px; padding: 28px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; }}
    p {{ line-height: 1.5; }}
    input[type=file] {{ display: block; margin: 22px 0; }}
    button {{ background: #1f4e78; color: #fff; border: 0; border-radius: 6px; padding: 11px 18px; cursor: pointer; }}
    .notice {{ background: #fff4d6; border: 1px solid #e7c76f; padding: 12px; border-radius: 6px; }}
  </style>
</head>
<body>
  <main>
    <section>
      <h1>MSBTE Result Analyzer</h1>
      <p>Upload result PDFs from the same class and download the Excel analysis workbook.</p>
      {notice}
      <form method="post" action="/analyze" enctype="multipart/form-data">
        <input type="file" name="pdfs" accept="application/pdf,.pdf" multiple required>
        <button type="submit">Analyze PDFs</button>
      </form>
    </section>
  </main>
</body>
</html>"""


def render_result(file_name: str, student_count: int, warnings: list[str]) -> str:
    warning_items = "".join(f"<li>{html.escape(warning)}</li>" for warning in warnings)
    warnings_html = f"<h2>Warnings</h2><ul>{warning_items}</ul>" if warnings else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Analysis Complete</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f5f7fb; color: #172033; }}
    main {{ max-width: 820px; margin: 48px auto; padding: 0 24px; }}
    section {{ background: #fff; border: 1px solid #d9e0ec; border-radius: 8px; padding: 28px; }}
    a.button {{ display: inline-block; background: #1f4e78; color: #fff; border-radius: 6px; padding: 11px 18px; text-decoration: none; }}
    li {{ margin-bottom: 6px; }}
  </style>
</head>
<body>
  <main>
    <section>
      <h1>Analysis Complete</h1>
      <p>Processed {student_count} student result PDF(s).</p>
      <p><a class="button" href="/download?file={html.escape(file_name)}">Download Excel Workbook</a></p>
      {warnings_html}
      <p><a href="/">Analyze another batch</a></p>
    </section>
  </main>
</body>
</html>"""


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), UploadHandler)
    print(f"MSBTE Result Analyzer running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
