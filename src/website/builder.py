"""
WCVS Static Website Builder
Generates index, archive, and per-report pages from historical report corpus.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape


class WebsiteBuilder:
    """Builds the WCVS static website."""

    def __init__(self, reports_dir: Path, output_dir: Path, templates_dir: Path, base_path: str = ""):
        self.reports_dir = Path(reports_dir)
        self.output_dir = Path(output_dir)
        self.templates_dir = Path(templates_dir)
        self.base_path = base_path.rstrip("/")
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(),
        )
        self.reports: List[Dict[str, Any]] = []

    def scan_reports(self) -> None:
        """Read all report directories and metadata."""
        self.reports = []
        if not self.reports_dir.exists():
            return
        for date_dir in sorted(self.reports_dir.iterdir()):
            if not date_dir.is_dir():
                continue
            context_path = date_dir / "context.json"
            if not context_path.exists():
                continue
            try:
                with open(context_path, "r", encoding="utf-8") as f:
                    ctx = json.load(f)
                ctx["date"] = date_dir.name
                ctx["dir"] = date_dir.name
                # Derive simple fields if missing
                ctx.setdefault("composite_score", ctx.get("composite_score", 2.5))
                ctx.setdefault("rating_text", ctx.get("rating_text", "Neutral"))
                ctx.setdefault("sp500_price", ctx.get("sp500_price", 0))
                self.reports.append(ctx)
            except (json.JSONDecodeError, OSError):
                continue
        # Sort descending by date
        self.reports.sort(key=lambda r: r["date"], reverse=True)

    def build(self) -> None:
        """Generate all website pages."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.scan_reports()
        print(f"[Website] Found {len(self.reports)} historical reports.")

        self._build_index()
        self._build_archive()
        self._build_report_pages()
        self._build_about()
        self._copy_assets()
        print(f"[Website] Built to: {self.output_dir}")

    def _build_index(self) -> None:
        template = self.env.get_template("index.html.j2")
        latest = self.reports[0] if self.reports else None
        # Last 30 days for sparkline
        sparkline_data = [
            {"date": r["date"], "score": r.get("composite_score", 2.5)}
            for r in reversed(self.reports[:30])
        ]
        html = template.render(latest=latest, sparkline_data=sparkline_data, report_count=len(self.reports), reports=self.reports, base_path=self.base_path)
        path = self.output_dir / "index.html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[Website] index.html written.")

    def _build_archive(self) -> None:
        template = self.env.get_template("archive.html.j2")
        html = template.render(reports=self.reports, base_path=self.base_path)
        archive_dir = self.output_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        with open(archive_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[Website] archive/index.html written.")

    def _build_report_pages(self) -> None:
        template = self.env.get_template("report_page.html.j2")
        reports_out = self.output_dir / "reports"
        reports_out.mkdir(parents=True, exist_ok=True)
        for i, report in enumerate(self.reports):
            prev_report = self.reports[i + 1] if i + 1 < len(self.reports) else None
            next_report = self.reports[i - 1] if i > 0 else None
            date = report["date"]
            # Read the HTML report if it exists
            html_report_path = self.reports_dir / date / f"wcvs-report-{date}-full.html"
            if not html_report_path.exists():
                html_report_path = self.reports_dir / date / f"wcvs-report-{date}-compact.html"
            report_html = ""
            if html_report_path.exists():
                report_html = html_report_path.read_text(encoding="utf-8")
                # Extract body content
                body_match = re.search(r'<body[^>]*>(.*?)</body>', report_html, re.DOTALL)
                if body_match:
                    report_html = body_match.group(1)
                # Remove footer from embedded report (we'll add our own)
                report_html = re.sub(r'<div class="footer">.*?</div>', '', report_html, flags=re.DOTALL)

            out_dir = reports_out / date
            out_dir.mkdir(parents=True, exist_ok=True)
            html = template.render(
                report=report,
                report_html=report_html,
                prev=prev_report,
                next_report=next_report,
                base_path=self.base_path,
            )
            with open(out_dir / "index.html", "w", encoding="utf-8") as f:
                f.write(html)
            # Copy PDF if exists — look for any report PDF with flexible naming
            import shutil
            report_dir = self.reports_dir / date
            pdf_candidates = list(report_dir.glob("*.pdf"))
            pdf_path = None
            # Prefer full/compact/final naming
            for pattern in [f"wcvs-report-{date}-full.pdf", f"wcvs-report-{date}-compact.pdf",
                            f"wcvs-report-{date}-final.pdf", f"wcvs-report-{date}.pdf",
                            f"wcvs-report-{date}-v*.pdf", f"test-wcvs.pdf"]:
                matches = list(report_dir.glob(pattern))
                if matches:
                    pdf_path = matches[0]
                    break
            if not pdf_path and pdf_candidates:
                pdf_path = pdf_candidates[0]
            if pdf_path:
                # Normalize name for website link consistency
                dest_name = f"wcvs-report-{date}-full.pdf"
                shutil.copy2(pdf_path, out_dir / dest_name)
        print(f"[Website] {len(self.reports)} report pages written.")

    def _build_about(self) -> None:
        template = self.env.get_template("about.html.j2")
        html = template.render(base_path=self.base_path)
        about_dir = self.output_dir / "about"
        about_dir.mkdir(parents=True, exist_ok=True)
        with open(about_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[Website] about/index.html written.")

    def _copy_assets(self) -> None:
        assets_src = self.templates_dir.parent / "assets"
        assets_dst = self.output_dir / "assets"
        if assets_src.exists():
            import shutil
            if assets_dst.exists():
                shutil.rmtree(assets_dst)
            shutil.copytree(assets_src, assets_dst)
            print(f"[Website] Assets copied.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build WCVS Website")
    parser.add_argument("--reports-dir", type=str, default="outputs/reports")
    parser.add_argument("--output-dir", type=str, default="outputs/website")
    parser.add_argument("--templates-dir", type=str, default="src/website/templates")
    parser.add_argument("--base-path", type=str, default="", help="Base path for deployment (e.g., /wcvs-reports)")
    args = parser.parse_args()

    builder = WebsiteBuilder(
        reports_dir=Path(args.reports_dir),
        output_dir=Path(args.output_dir),
        templates_dir=Path(args.templates_dir),
        base_path=args.base_path,
    )
    builder.build()


if __name__ == "__main__":
    main()
