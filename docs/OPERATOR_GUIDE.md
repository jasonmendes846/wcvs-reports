# WCVS Platform — Operator Guide

## Overview

The **WCVS Report Platform** generates institutional-grade U.S. equity market valuation reports using the Weighted Composite Valuation Score (WCVS) framework. It produces:

- **Markdown reports** — Source of truth, git-friendly
- **Compact PDF** — 3-page dense edition for email/mobile
- **Full PDF** — Institutional edition with full typography
- **Static website** — Historical archive with sparkline dashboard

## Quick Start

### Prerequisites

- Python 3.12+ installed on Windows
- Internet connection (for live data fetching)

### Installation

```powershell
cd C:\Users\jimmy\Projects\wcvs-platform
python -m pip install -r requirements.txt
python -m playwright install chromium
```

### Generate a Report

#### Via Command Line

```powershell
# Today's report (compact + full)
python -m src.report_engine.generate_report --date 2026-05-11 --compact --full

# Just compact edition
python -m src.report_engine.generate_report --compact

# Specific date
python -m src.report_engine.generate_report --date 2026-05-01
```

#### Via Kimi Agent

Simply invoke the agent:

```
Generate WCVS report for today
```

The `wcvs-reporter` agent will:
1. Fetch live market data
2. Calculate WCVS scores
3. Render Markdown, HTML, and PDF
4. Update the website

### Build the Website

```powershell
python -m src.website.builder
```

The website is built to `outputs/website/` and can be:
- Opened locally in a browser (`index.html`)
- Deployed to GitHub Pages, Netlify, or any static host
- Served via `python -m http.server` for local preview

## Project Structure

```
wcvs-platform/
├── prd/
│   └── WCVS-PRD.md              # Product Requirements Document
├── src/
│   ├── data_ingestion/          # Market data fetchers
│   │   ├── cache.py             # JSON disk cache with TTL
│   │   └── fetchers/
│   │       └── unified.py       # Yahoo Finance + web fetchers
│   ├── report_engine/           # Report generation pipeline
│   │   ├── scoring.py           # WCVS rubric & arithmetic
│   │   ├── renderer.py          # Jinja2 → Markdown → HTML
│   │   ├── pdf_generator.py     # Playwright headless PDF
│   │   ├── generate_report.py   # Main orchestrator
│   │   └── templates/
│   │       ├── report.md.j2     # Markdown Jinja2 template
│   │       ├── compact.css      # 3-page compact stylesheet
│   │       └── full.css         # Institutional stylesheet
│   └── website/                 # Static site generator
│       ├── builder.py           # Archive → website builder
│       ├── templates/           # Jinja2 HTML templates
│       └── assets/              # CSS & JS
├── outputs/
│   ├── reports/YYYY-MM-DD/      # Daily artifacts
│   │   ├── wcvs-report-YYYY-MM-DD.md
│   │   ├── wcvs-report-YYYY-MM-DD-compact.html
│   │   ├── wcvs-report-YYYY-MM-DD-compact.pdf
│   │   ├── wcvs-report-YYYY-MM-DD-full.html
│   │   ├── wcvs-report-YYYY-MM-DD-full.pdf
│   │   ├── context.json         # Structured data for website
│   │   └── data.json            # Raw fetched data
│   └── website/                 # Built static site
├── requirements.txt
└── docs/
    └── OPERATOR_GUIDE.md        # This file
```

## Kimi Integration

### Skill: `wcvs-report-engine`

Located at: `C:\Users\jimmy\.kimi\skills\wcvs-report-engine\`

- **SKILL.md** — Triggering metadata and workflow
- **references/** — Methodology, data sources, markdown template, website rules
- **assets/** — HTML/CSS templates and postprocessor
- **scripts/** — Wrappers delegating to project workspace

### Agent: `wcvs-reporter`

Located at: `C:\Users\jimmy\.kimi\agents\wcvs-reporter\`

- **agent.yaml** — Persona, workflow, guardrails
- **README.md** — Human usage guide

## Data Sources

| Metric | Primary Source | Fallback |
|--------|---------------|----------|
| S&P 500 | Yahoo Finance API | Web search |
| Shiller CAPE | multpl.com | Web search |
| Fear & Greed | CNN API | Web search |
| Treasury Yields | Yahoo Finance | Treasury.gov |
| DXY, Oil, Gold | Yahoo Finance | Web search |
| NAAIM, AAII, HY OAS | — | Cache / Manual input |

*No paid API keys required for baseline operation.*

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `playwright not found` | Run `pip install playwright` then `playwright install chromium` |
| PDF is blank | Ensure Chromium downloaded (~300MB). Re-run `playwright install chromium` |
| Data fetch fails | Check internet. System falls back to cache or asks for manual input |
| Website missing reports | Ensure `context.json` exists in each report directory. Re-run builder |
| Score seems wrong | Check `data.json` for raw inputs. Verify in `scoring.py` rubric |

## Customization

### Adjusting Category Weights

Edit `src/report_engine/scoring.py` — modify the `CATEGORIES` dict.

### Adding New Data Sources

1. Add fetcher method in `src/data_ingestion/fetchers/unified.py`
2. Add cache key and parser logic
3. Update `references/data-sources.md` in the skill

### Changing Report Template

Edit `src/report_engine/templates/report.md.j2` — Jinja2 syntax.

### Website Styling

Edit `src/website/assets/style.css` — CSS custom properties at the top.

## Disclaimer

This system is for **informational and research purposes only**. It does not constitute investment advice. The WCVS score is a heuristic model based on historical relationships that may not persist. Always consult a qualified financial advisor before making investment decisions.
