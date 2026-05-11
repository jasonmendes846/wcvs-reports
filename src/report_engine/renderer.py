"""
Report renderer: builds markdown and HTML from WCVS data.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape


class ReportRenderer:
    """Renders WCVS reports to Markdown and HTML."""

    def __init__(self, templates_dir: Path):
        self.templates_dir = Path(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(),
        )

    def render_markdown(self, context: Dict[str, Any]) -> str:
        template = self.env.get_template("report.md.j2")
        return template.render(**context)

    def markdown_to_html(self, md_text: str, css_path: Path = None, title: str = "WCVS Report") -> str:
        """Convert markdown to standalone HTML with WCVS styling."""
        import markdown as md_lib
        # Convert markdown to HTML body
        body_html = md_lib.markdown(md_text, extensions=["tables", "fenced_code"])
        # Post-process: inject CSS classes based on content patterns
        body_html = self._postprocess_body(body_html)
        # Build full HTML
        css = ""
        if css_path and css_path.exists():
            css = f"<style>{css_path.read_text(encoding='utf-8')}</style>"
        else:
            # Inline compact CSS fallback
            css = self._default_css()
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
{css}
</head>
<body>
{body_html}
<div class="footer">
WCVS Report | Generated {datetime.now().strftime('%Y-%m-%d')} | Not financial advice
</div>
</body>
</html>"""
        return html

    def _postprocess_body(self, body: str) -> str:
        """Inject WCVS CSS classes into generated HTML."""
        # Hero score box
        body = re.sub(
            r'<p><strong>WCVS Composite Score:.*?</strong></p>',
            self._replace_hero,
            body,
            flags=re.DOTALL,
        )
        # Category headers
        for i, label in [(1, "Extreme"), (2, "Unfavorable"), (3, "Neutral"), (4, "Favorable"), (5, "Attractive")]:
            body = re.sub(
                rf'<h2>(\d+\. .*? \(Score: {i}\.\d+ — {label}\))</h2>',
                rf'<div class="category cat-{self._cat_class(i)}"><h2 class="category-title">\1</h2>',
                body,
            )
        # Close category divs before next h2 or h1
        body = re.sub(r'</div>\s*(?=<h2>|<h1>)', '</div>', body)
        # Wrap key risks
        body = re.sub(
            r'(<h2>Key Risks.*?</h2>.*?)(?=<h2>|$)',
            r'<div class="warning-box"><div class="warning-title">⚠ Key Risks & Divergences</div>\1</div>',
            body,
            flags=re.DOTALL,
        )
        # Wrap key drivers
        body = re.sub(
            r'(<h2>Key Drivers.*?</h2>.*?)(?=<h2>|$)',
            r'<div class="key-box"><h3 class="key-title">Key Drivers This Week</h3>\1</div>',
            body,
            flags=re.DOTALL,
        )
        # Style tables
        body = body.replace("<table>", '<table class="data-table">', 1)  # first table (hero)
        # Add numeric class to score columns
        body = re.sub(r'<td>(\d+\.\d+ / 5\.0)</td>', r'<td class="score">\1</td>', body)
        body = re.sub(r'<td>(Significantly Overvalued|Overvalued|Fairly Valued|Undervalued)</td>', r'<td class="score">\1</td>', body)
        return body

    def _replace_hero(self, match) -> str:
        # Extract score if present in the match text
        text = match.group(0)
        score_match = re.search(r'(\d+\.\d+)', text)
        score = score_match.group(1) if score_match else "2.5"
        try:
            score_f = float(score)
        except ValueError:
            score_f = 2.5
        if score_f <= 1.9:
            rating, rclass = "SEVERELY OVERVALUED", "rating-red"
        elif score_f <= 3.0:
            rating, rclass = "OVERVALUED", "rating-orange"
        elif score_f <= 4.0:
            rating, rclass = "FAIRLY VALUED", "rating-green"
        else:
            rating, rclass = "UNDERVALUED", "rating-green"
        return f'''<div class="hero">
<div class="hero-label">Weighted Composite Valuation Score</div>
<div class="hero-score">{score}</div>
<div class="hero-rating {rclass}">{rating}</div>
</div>'''

    @staticmethod
    def _cat_class(score: int) -> str:
        mapping = {1: "extreme", 2: "expensive", 3: "fair", 4: "fair", 5: "cheap"}
        return mapping.get(score, "fair")

    def _default_css(self) -> str:
        css_path = self.templates_dir / "compact.css"
        if css_path.exists():
            return f"<style>{css_path.read_text(encoding='utf-8')}</style>"
        return "<style>body{font-family:sans-serif;}</style>"
