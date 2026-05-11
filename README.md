# WCVS Report Platform

**Weighted Composite Valuation Score (WCVS)** — Automated U.S. equity market valuation reports with PDF generation, historical archive, and static website.

## Quick Start

```powershell
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run full pipeline (reporter → checker → publisher)
python scripts/run_pipeline.py --date 2026-05-11 --build-website

# Preview website locally
python -m http.server 8000 --directory outputs/website
# Open http://localhost:8000
```

## Project Structure

```
wcvs-platform/
├── prd/
│   └── WCVS-PRD.md              # Product Requirements Document
├── src/
│   ├── data_ingestion/          # Market data fetchers (Yahoo Finance, web)
│   ├── report_engine/           # Scoring, rendering, PDF generation
│   └── website/                 # Static site generator
├── scripts/
│   ├── run_pipeline.py          # Full swarm orchestrator
│   ├── setup_task_scheduler.ps1 # Windows automation setup
│   ├── deploy_local.ps1         # Local preview server
│   └── send_telegram_notification.py  # Telegram bot integration
├── outputs/
│   ├── reports/YYYY-MM-DD/      # Daily report artifacts
│   └── website/                 # Built static site
├── requirements.txt
└── docs/OPERATOR_GUIDE.md       # Detailed usage guide
```

## Multi-Agent Swarm

| Agent | Role | Location |
|-------|------|----------|
| `wcvs-reporter` | Data collection, scoring, drafting, rendering | `.kimi/agents/wcvs-reporter/` |
| `wcvs-checker` | QC review: arithmetic, design, compliance | `.kimi/agents/wcvs-checker/` |
| `wcvs-publisher` | Website build, deployment, notifications | `.kimi/agents/wcvs-publisher/` |

## Outputs

Each report produces:
- `wcvs-report-YYYY-MM-DD.md` — Markdown source
- `wcvs-report-YYYY-MM-DD-compact.pdf` — 3-page dense edition
- `wcvs-report-YYYY-MM-DD-full.pdf` — Institutional edition
- `wcvs-report-YYYY-MM-DD-{compact,full}.html` — Styled HTML
- `context.json` — Structured data for website indexing
- `data.json` — Raw fetched market data

## Automation

### Windows Task Scheduler
Run as Administrator:
```powershell
.\scripts\setup_task_scheduler.ps1
```
Schedules daily generation at 4:30 PM ET (after US market close).

### Manual Pipeline
```powershell
python scripts/run_pipeline.py --date 2026-05-11 --compact --full --build-website --notify --chat-id YOUR_CHAT_ID
```

## Kimi Integration

Invoke via Kimi agent:
```
Generate WCVS report for today
```

The reporter agent will:
1. Fetch live market data
2. Calculate WCVS scores
3. Render Markdown/HTML/PDF
4. Hand off to checker for QC
5. Build website upon approval

## Disclaimer

This system is for **informational and research purposes only**. It does not constitute investment advice.
