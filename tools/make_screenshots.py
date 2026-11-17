"""Скриншоты работающего приложения для отчётов (лабы 1, 2, 3, 6, 7, 8).

Требует: локальное приложение на :8000 и стек лабы 8 (nginx на :443).
Запуск: .venv\\Scripts\\python tools\\make_screenshots.py
"""
import json
import sqlite3
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "screenshots.db"
BASE = "http://127.0.0.1:8000"
BASES = "https://localhost"


def seed_posts():
    sys.path.insert(0, str(ROOT))
    from app.db import connect  # создаёт схему при подключении

    conn = connect(str(DB))
    if conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]:
        return
    uid = conn.execute(
        "INSERT INTO users (name, email, age, password_hash) VALUES (?, ?, ?, ?)",
        ("John Doe", "john@example.com", 30, "pbkdf2$ZGV2$ZGV2"),
    ).lastrowid
    conn.executemany(
        "INSERT INTO posts (author_id, title, body) VALUES (?, ?, ?)",
        [(uid, f"Пост {i}", f"Содержимое поста номер {i}") for i in range(1, 6)],
    )
    conn.commit()
    conn.close()


def shot(page, url: str, path: Path, full_page: bool = False):
    page.goto(url, wait_until="networkidle")
    path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(path), full_page=full_page)
    print(f"  {path.relative_to(ROOT)}")


HTML_WRAP = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>body{{background:#1e1e1e;color:#d4d4d4;font:14px/1.5 Consolas,monospace;
padding:24px;margin:0}}pre{{white-space:pre-wrap}}</style></head>
<body><pre>{body}</pre></body></html>"""


def shot_json(page, method: str, url: str, path: Path, payload=None, headers=None, status=""):
    import urllib.request

    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req) as resp:
            body, code = json.dumps(json.loads(resp.read()), indent=2, ensure_ascii=False), resp.status
    except urllib.error.HTTPError as e:
        body, code = json.dumps(json.loads(e.read()), indent=2, ensure_ascii=False), e.code
    title = f"HTTP {code} {method} {url}\n\n"
    page.set_content(HTML_WRAP.format(body=title + body))
    path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(path))
    print(f"  {path.relative_to(ROOT)}")


def main():
    seed_posts()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(ignore_https_errors=True)  # самоподписанный сертификат
        page = ctx.new_page()
        page.set_viewport_size({"width": 1280, "height": 900})

        print("lab1:")
        shot(page, f"{BASE}/docs", ROOT / "lab1/screenshots/swagger-ui.png")
        shot(page, f"{BASE}/echo?foo=bar", ROOT / "lab1/screenshots/echo.png")

        print("lab2:")
        shot(page, f"{BASE}/docs", ROOT / "lab2/screenshots/swagger-users.png")

        print("lab3:")
        shot_json(page, "POST", f"{BASE}/users",
                  ROOT / "lab3/screenshots/validation-422.png",
                  payload={"name": "J", "email": "invalid-email", "age": 15, "password": "123"})
        shot(page, f"{BASE}/debug/boom", ROOT / "lab3/screenshots/error-500.png")

        print("lab6:")
        shot_json(page, "POST", f"{BASE}/auth/login",
                  ROOT / "lab6/screenshots/login-tokens.png",
                  payload={"email": "john@example.com", "password": "pass12345"})

        print("lab7:")
        shot(page, f"{BASE}/users/1/posts", ROOT / "lab7/screenshots/posts-join.png")

        print("lab8:")
        shot(page, f"{BASES}/static/index.html", ROOT / "lab8/screenshots/https-static.png")
        shot(page, f"{BASES}/docs", ROOT / "lab8/screenshots/https-docs-proxy.png")

        browser.close()


if __name__ == "__main__":
    sys.exit(main())
