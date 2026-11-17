"""Пересъёмка скриншота Swagger UI через Nginx-прокси (lab8)."""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(ignore_https_errors=True)
    page = ctx.new_page()
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto("https://localhost/docs", wait_until="networkidle")
    page.wait_for_selector("text=Web Labs API", timeout=15000)
    page.wait_for_timeout(1000)
    page.screenshot(path=str(ROOT / "lab8/screenshots/https-docs-proxy.png"))
    browser.close()
print("переснят: lab8/screenshots/https-docs-proxy.png")
