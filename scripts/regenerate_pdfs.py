"""
Batch regenerate all WCVS PDFs with unified design matching 2026-05-10 reference.
Usage:
    python scripts/regenerate_pdfs.py
"""

import asyncio
import re
import shutil
import sys
from pathlib import Path

import markdown

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

CSS_PATH = PROJECT_ROOT / "src" / "report_engine" / "templates" / "report.css"
FONTS_DIR = PROJECT_ROOT / "src" / "report_engine" / "templates" / "fonts"
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"
DATES = [f"2026-05-{d:02d}" for d in range(3, 12)]

FONT_FACE_CSS = """
@font-face {
  font-family: 'Liberation Sans';
  src: url('./fonts/LiberationSans-Regular.ttf') format('truetype');
  font-weight: 400;
  font-style: normal;
}
@font-face {
  font-family: 'Liberation Sans';
  src: url('./fonts/LiberationSans-Bold.ttf') format('truetype');
  font-weight: 700;
  font-style: normal;
}
@font-face {
  font-family: 'Liberation Sans';
  src: url('./fonts/LiberationSans-Italic.ttf') format('truetype');
  font-weight: 400;
  font-style: italic;
}
@font-face {
  font-family: 'Liberation Sans';
  src: url('./fonts/LiberationSans-BoldItalic.ttf') format('truetype');
  font-weight: 700;
  font-style: italic;
}
"""


def find_markdown(report_dir: Path) -> Path | None:
    """Find the best markdown file in a report directory."""
    md_files = list(report_dir.glob("*.md"))
    if not md_files:
        return None

    # Prefer "full" markdowns
    full_mds = [f for f in md_files if "full" in f.name.lower()]
    if full_mds:
        return full_mds[0]

    # Prefer the standard-named report
    date = report_dir.name
    standard = report_dir / f"wcvs-report-{date}.md"
    if standard.exists():
        return standard

    # Fall back to longest markdown
    return max(md_files, key=lambda p: len(p.read_text(encoding="utf-8")))


def md_to_html(md_text: str, css: str, date: str, report_dir: Path) -> str:
    """Convert markdown to standalone HTML with institutional styling."""
    body_html = markdown.markdown(md_text, extensions=["tables", "fenced_code"])

    # Clean up stray HTML id attributes that markdown may leak
    body_html = re.sub(r'<a id="[^"]*"></a>', '', body_html)
    body_html = re.sub(r'ID="[^"]*">', '', body_html)

    # Extract title from first h1 if present
    title = f"WCVS Report — {date}"
    h1_match = re.search(r"<h1>(.*?)</h1>", body_html)
    if h1_match:
        title = re.sub(r"<[^>]+>", "", h1_match.group(1)).strip()

    # Copy fonts to report directory
    fonts_dst = report_dir / "fonts"
    if fonts_dst.exists():
        shutil.rmtree(fonts_dst)
    shutil.copytree(FONTS_DIR, fonts_dst)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>{FONT_FACE_CSS}{css}</style>
</head>
<body>
{body_html}
<div class="footer">
WCVS Report | Generated {date} | OpenClaw Multi-Agent System | Not financial advice
</div>
</body>
</html>"""
    return html


async def generate_pdf(html_path: Path, pdf_path: Path) -> Path:
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(f"file:///{html_path.resolve().as_posix()}", wait_until="networkidle")
        await page.pdf(
            path=str(pdf_path),
            format="A4",
            margin={"top": "0.5cm", "right": "0.7cm", "bottom": "0.5cm", "left": "0.7cm"},
            print_background=True,
        )
        await browser.close()
    return pdf_path


def clean_old_pdfs(report_dir: Path, keep: Path) -> None:
    """Remove all PDFs except the specified one."""
    for pdf in report_dir.glob("*.pdf"):
        if pdf.resolve() != keep.resolve():
            pdf.unlink()
            print(f"  Removed old PDF: {pdf.name}")


def main() -> None:
    css = CSS_PATH.read_text(encoding="utf-8")
    total = 0

    for date in DATES:
        report_dir = REPORTS_DIR / date
        if not report_dir.exists():
            print(f"[SKIP] Directory not found: {report_dir}")
            continue

        md_file = find_markdown(report_dir)
        if not md_file:
            print(f"[SKIP] No markdown found for {date}")
            continue

        print(f"[PROCESS] {date} — {md_file.name}")
        md_text = md_file.read_text(encoding="utf-8")

        # Generate HTML
        html_text = md_to_html(md_text, css, date, report_dir)
        html_path = report_dir / f"wcvs-report-{date}.html"
        html_path.write_text(html_text, encoding="utf-8")
        print(f"  HTML: {html_path.name}")

        # Generate PDF
        pdf_path = report_dir / f"wcvs-report-{date}.pdf"
        try:
            asyncio.run(generate_pdf(html_path, pdf_path))
            print(f"  PDF: {pdf_path.name}")
            clean_old_pdfs(report_dir, pdf_path)
            total += 1
        except Exception as e:
            print(f"  [ERROR] PDF generation failed: {e}")

    print(f"\n[DONE] Regenerated {total} reports.")


if __name__ == "__main__":
    main()
