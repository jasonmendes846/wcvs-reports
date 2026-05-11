"""
PDF generator using Playwright headless Chromium.
"""

import asyncio
from pathlib import Path
from typing import Optional


class PDFGenerator:
    """Generates PDF from HTML using Playwright."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate(self, html_path: Path, pdf_path: Path, format_size: str = "A4") -> Path:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(f"file:///{html_path.resolve().as_posix()}", wait_until="networkidle")
            await page.pdf(
                path=str(pdf_path),
                format=format_size,
                margin={"top": "0.5cm", "right": "0.7cm", "bottom": "0.5cm", "left": "0.7cm"},
                print_background=True,
            )
            await browser.close()
        return pdf_path

    def generate_sync(self, html_path: Path, pdf_path: Path, format_size: str = "A4") -> Path:
        return asyncio.run(self.generate(html_path, pdf_path, format_size))
