# WCVS Report Platform — Product Requirements Document

**Version:** 1.0  
**Date:** 2026-05-11  
**Owner:** Kimi K2.6 Agent System  
**Status:** Draft → Build

---

## 1. Overview

The **Weighted Composite Valuation Score (WCVS)** Report Platform is an automated market intelligence system that produces institutional-grade U.S. equity valuation reports in PDF, Markdown, and HTML formats, alongside a publishable historical archive website.

### 1.1 Mission
Deliver a daily, on-demand, and historically archived multi-factor valuation snapshot of the U.S. equity market using public data sources, with zero paid API dependencies in the baseline configuration.

### 1.2 Stakeholders
- **Primary User:** You (the operator), triggering reports via Kimi agent
- **Secondary Audience:** Your Telegram subscribers / website visitors consuming historical reports
- **System:** Kimi K2.6 with custom skill + agent

---

## 2. Product Goals

| # | Goal | Success Metric |
|---|------|----------------|
| 1 | Generate a complete WCVS report in < 3 minutes | End-to-end timing from trigger to PDF |
| 2 | Maintain visual fidelity with original WCVS aesthetic | Side-by-side PDF comparison |
| 3 | Zero external API costs in baseline mode | No paid API calls in default config |
| 4 | Website auto-updates on every new report | Reports appear on site within 60s of generation |
| 5 | Windows-native execution | Runs on Windows 10/11 without WSL |

---

## 3. Scope

### 3.1 In Scope
- **Report Generation:** Daily WCVS markdown → styled HTML → PDF pipeline
- **Data Ingestion:** Modular fetchers for ~15 market data points (web search + scraping + manual fallback)
- **Kimi Integration:** Skill (`wcvs-report-engine`) + Agent (`wcvs-reporter`) for `.kimi/`
- **Website:** Static site with report archive, score history chart, and category dashboard
- **Historical Archive:** Storage and indexing of all generated reports

### 3.2 Out of Scope (Future Phases)
- Real-time streaming data websockets
- User authentication / subscription paywall
- Email newsletter delivery system
- Multi-asset class expansion (international equities, crypto, FX)
- Mobile app

---

## 4. Report Specification

### 4.1 Content Structure

```
# WCVS Report — {Date}

## Header Block
- Title, subtitle, report date, analyst attribution

## Hero Score
- WCVS Composite Score (1.0–5.0)
- Rating badge: SEVERELY OVERVALUED / OVERVALUED / FAIRLY VALUED / UNDERVALUED
- Interpretation scale table

## TL;DR
- 2–3 paragraph executive summary

## Composite Score Breakdown Table
- 5 categories, weights, raw scores, contributions

## Category Deep Dives (5 sections)
### 1. Fundamental Valuation (25%)
### 2. Market Internals (20%)
### 3. Sentiment & Psychology (20%)
### 4. Credit & Liquidity (15%)
### 5. Macro & Cross-Asset (20%)
Each: metric table + 1 paragraph narrative + subtotal

## Forward Return Expectations
- CAPE regression table: 1Y, 3Y, 5Y, 10Y, 15Y expected real returns
- Confidence levels

## Tactical Assessment
- Overall stance (Defensive / Neutral / Cautious / Aggressive)
- 3–5 bullet tactical considerations

## Key Drivers This Week
- 5 Bearish Factors
- 5 Bullish Factors

## Summary
- 1 paragraph closing

## Footer
- Disclaimer, data sources, generation timestamp
```

### 4.2 Visual Design
- **Primary palette:** `#1a3a5c` (navy), `#2d5a87` (steel blue), white
- **Rating colors:** Red `#cc3333`, Orange `#ff9933`, Green `#66aa66`
- **Typography:** system-ui stack, 7pt compact / 10pt full institutional
- **Layout:** A4 print-optimized, compact edition targets 3 pages

### 4.3 Output Formats
| Format | Purpose | File Naming |
|--------|---------|-------------|
| Markdown | Source of truth, git-friendly | `wcvs-report-YYYY-MM-DD.md` |
| PDF (Compact) | Shareable, email-friendly | `wcvs-report-YYYY-MM-DD-compact.pdf` |
| PDF (Full) | Institutional, detailed | `wcvs-report-YYYY-MM-DD-full.pdf` |
| HTML | Website rendering, browser view | `wcvs-report-YYYY-MM-DD.html` |

---

## 5. Data Requirements

### 5.1 Required Inputs

| Data Point | Source Tier 1 | Source Tier 2 | Source Tier 3 |
|------------|---------------|---------------|---------------|
| S&P 500 Price | web search | yahoo finance scrape | manual input |
| Shiller CAPE | web search | multpl.com scrape | manual input |
| Forward P/E | web search | ycharts scrape | manual input |
| Market Cap / GDP | web search | macromicro.me | manual input |
| % Stocks > 50D MA | web search | stockcharts.com | manual input |
| % Stocks > 200D MA | web search | stockcharts.com | manual input |
| Advance-Decline Line | web search | stockcharts.com | manual input |
| NYSE New Highs/Lows | web search | wsj.com market data | manual input |
| Fear & Greed Index | web search | CNN Business | manual input |
| NAAIM Exposure | web search | NAAIM website | manual input |
| AAII Bull-Bear | web search | AAII website | manual input |
| Put/Call Ratio | web search | CBOE website | manual input |
| 10Y Treasury Yield | web search | treasury.gov | manual input |
| 10Y–2Y Spread | web search | treasury.gov / FRED | manual input |
| 10Y–3M Spread | web search | treasury.gov / FRED | manual input |
| Credit Spreads (HY-OAS) | web search | FRED / ICE | manual input |
| DXY Dollar Index | web search | wsj / investing.com | manual input |
| WTI Oil | web search | wsj / investing.com | manual input |
| Gold Price | web search | wsj / investing.com | manual input |
| Fed Funds Futures / CME Watch | web search | CME FedWatch | manual input |

### 5.2 Data Freshness Rules
- **Hard real-time:** Not required; market-close snapshots sufficient
- **Tolerance:** Data up to 24 hours old is acceptable
- **Stale fallback:** If fetcher fails, use last known value with `[STALE]` annotation

---

## 6. Technical Architecture

### 6.1 Kimi Ecosystem — Multi-Agent Swarm

The WCVS system uses a **3-agent swarm** with strict quality gates:

```
.kimi/
├── agents/
│   ├── wcvs-reporter/      # Producer: data → scores → report artifacts
│   │   ├── agent.yaml
│   │   └── README.md
│   ├── wcvs-checker/       # Quality gate: arithmetic, design, compliance review
│   │   ├── agent.yaml      # Detailed QC rubric, taste-driven design critique
│   │   └── README.md
│   └── wcvs-publisher/     # Deployer: website build + distribution (future)
│       └── (placeholder)
└── skills/wcvs-report-engine/
    ├── SKILL.md            # Triggering metadata + core workflow
    ├── references/
    │   ├── methodology.md  # Scoring rubric (1.0–5.0 per category)
    │   ├── data-sources.md # Fetcher protocols & failover rules
    │   ├── markdown-template.md # Report markdown Jinja template
    │   ├── website-publishing.md # Site generation rules
    │   └── quality-control.md # Complete QC rubric, checklists, severity scale
    ├── assets/
    │   ├── template.html   # Full pandoc HTML template
    │   ├── template.css    # Standalone stylesheet
    │   └── postprocess.py  # HTML injector (compact + full)
    └── scripts/
        ├── generate_report.py   # Data → md → html → pdf orchestrator
        ├── build_website.py     # Historical reports → static site
        └── qc_validate.py       # Automated QC validator
```

**Swarm Workflow:**
1. **Reporter** generates draft report → saves artifacts
2. **Checker** reviews via automated script + agent judgment → produces QC memo
3. **Reporter** fixes issues → re-submits if needed
4. **Checker** approves (PASS) → hands off to publisher
5. **Publisher** builds website and deploys

### 6.2 Project Workspace

```
~/Projects/wcvs-platform/
├── prd/
│   └── WCVS-PRD.md
├── src/
│   ├── data_ingestion/
│   │   ├── __init__.py
│   │   ├── fetcher_base.py
│   │   ├── fetchers/
│   │   │   ├── __init__.py
│   │   │   ├── equity_market.py      # S&P 500, breadth
│   │   │   ├── valuation.py          # CAPE, P/E, MktCap/GDP
│   │   │   ├── sentiment.py          # Fear&Greed, NAAIM, AAII, Put/Call
│   │   │   ├── credit_macro.py       # Yields, spreads, Fed
│   │   │   └── cross_asset.py        # DXY, oil, gold
│   │   └── cache.py                  # JSON disk cache with TTL
│   ├── report_engine/
│   │   ├── __init__.py
│   │   ├── renderer.py               # Markdown → HTML (Jinja2)
│   │   ├── pdf_generator.py          # Playwright headless PDF
│   │   ├── scoring.py                # WCVS arithmetic engine
│   │   └── templates/
│   │       ├── report.md.j2          # Main markdown template
│   │       ├── compact.css           # 3-page compact CSS
│   │       └── full.css              # Institutional CSS
│   └── website/
│       ├── __init__.py
│       ├── builder.py                # Static site generator
│       ├── templates/
│       │   ├── index.html.j2         # Landing page
│       │   ├── archive.html.j2       # Report list
│       │   └── report_page.html.j2   # Individual report view
│       └── assets/
│           ├── chart.js              # Score history line chart
│           └── style.css             # Site-wide styles
├── outputs/
│   ├── reports/YYYY-MM-DD/           # Daily report artifacts
│   └── website/                      # Built static site
└── docs/
    └── OPERATOR_GUIDE.md
```

### 6.3 Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Language | Python 3.12+ | Cross-platform, rich ecosystem |
| Templating | Jinja2 | Proven, readable, logic-light |
| PDF Engine | Playwright + Chromium | Best CSS support on Windows |
| HTML Processing | BeautifulSoup4 | Robust DOM manipulation |
| Data Fetching | `requests` + `SearchWeb` / `FetchURL` MCP | Baseline: free web scraping |
| Caching | `diskcache` or JSON files | Simple, inspectable, no DB needed |
| Website | Static HTML + vanilla JS | Zero build step, fast, portable |
| Charts | Chart.js CDN | Lightweight, no bundler needed |

---

## 7. Scoring Engine Specification

### 7.1 Category Scoring Rubric

Each category scored 1.0–5.0. Composite = Σ(weight_i × score_i).

| Category | Weight | 1.0 (Extreme) | 2.0 (Unfavorable) | 3.0 (Neutral) | 4.0 (Favorable) | 5.0 (Attractive) |
|----------|--------|---------------|-------------------|---------------|-----------------|------------------|
| Fundamental Valuation | 25% | CAPE > 35x, P/E > 22x | CAPE 28–35x | CAPE 20–28x | CAPE 15–20x | CAPE < 15x |
| Market Internals | 20% | <30% >200D MA, A-D neg | <45% >200D MA | 45–60% | 60–75% | >75%, strong A-D |
| Sentiment | 20% | Extreme greed, NAAIM >95% | Greed, NAAIM >85% | Neutral | Fear, NAAIM <50% | Extreme fear, NAAIM <20% |
| Credit & Liquidity | 15% | Inverted curve, HY spreads >600bp | Flat curve, spreads 400–600bp | Mild steepening | Steep curve, spreads <300bp | Very steep, tight spreads |
| Macro & Cross-Asset | 20% | Stagflation, oil spike, $ crash | Rising oil, weak $ | Balanced | Strong $, stable commodities | Goldilocks conditions |

*Note: The agent may adjust raw scores ±0.5 based on narrative judgment; document all overrides.*

### 7.2 Forward Returns Model

Based on historical CAPE regression (simplified):

```python
def expected_return(cape, horizon_years):
    # Simplified log-linear regression approximation
    # Real return ≈ -0.08 * ln(cape/17) + 0.03 * sqrt(horizon_years/15)
    base = -0.08 * math.log(cape / 17.0)
    term_premium = 0.03 * math.sqrt(min(horizon_years, 15) / 15.0)
    return base + term_premium
```

Confidence levels: Low (1Y), Moderate (3–5Y), Higher (10–15Y).

---

## 8. Website Specification

### 8.1 Pages

| Page | Route | Content |
|------|-------|---------|
| Home | `/index.html` | Latest hero score, 30-day sparkline, latest report embed |
| Archive | `/archive/index.html` | Paginated table of all reports with scores and ratings |
| Report | `/reports/YYYY-MM-DD/index.html` | Full HTML report with print-friendly CSS |
| About | `/about/index.html` | Methodology explainer, disclaimer, data sources |

### 8.2 Design Tokens
- Reuse WCVS navy `#1a3a5c` as primary
- Dark mode supported via `prefers-color-scheme`
- Responsive: mobile-first, max-width 1200px desktop

---

## 9. Quality Assurance

### 9.1 Automated Tests
- **Scoring arithmetic:** Unit tests for composite score calculation
- **Template rendering:** Snapshot tests for markdown output
- **PDF generation:** Visual diff (pixel comparison) against golden master
- **Website build:** Link checking, HTML validation

### 9.2 Manual QC Checklist
- [ ] PDF prints correctly on A4 (no overflow, colors render)
- [ ] All tables align and zebra-striping visible
- [ ] Hero score and rating match narrative text
- [ ] Forward returns are monotonically decreasing with horizon
- [ ] Website renders on mobile Safari and Chrome
- [ ] All external links in About page are live

---

## 10. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Data source breakage (scraping) | High | High | Multi-tier failover; manual input fallback; cache last good value |
| Playwright install failure | Medium | High | Bundle install script; fallback to Edge/Chromium system binary |
| Context window overflow in agent | Medium | Medium | Chunked category generation; reference files for methodology only |
| PDF CSS rendering drift | Medium | Medium | Freeze Chromium version; visual regression tests |
| Website scope creep | High | Medium | MVP = static archive; dashboard v2 post-MVP |

---

## 11. Milestones & Timeline

| Phase | Deliverable | Est. Duration |
|-------|-------------|---------------|
| 0 | PRD + Project scaffolding | 1 session |
| 1 | Kimi skill + agent files | 1 session |
| 2 | Data ingestion layer | 1–2 sessions |
| 3 | Report engine (md → html → pdf) | 2 sessions |
| 4 | Website generator | 1–2 sessions |
| 5 | Multi-agent integration & QC | 1–2 sessions |
| 6 | Testing & validation | 1 session |
| 7 | Documentation + packaging | 1 session |

**Total:** 7–10 active sessions.

---

## 12. Appendices

### Appendix A: Original Artifact Mapping
- `wcvs-postprocess.py` → `assets/postprocess.py` + `src/report_engine/renderer.py`
- `wcvs-template.html` → `assets/template.html`
- `wcvs-template.css` → `assets/template.css` + `src/report_engine/templates/`
- `wcvs-generate.sh` → `scripts/generate_report.py` (Windows-native)
- Historical `.md`/`.pdf` → `outputs/reports/` (seed archive)

### Appendix B: Operator Quick Start
```bash
# 1. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 2. Generate today's report
python -m src.report_engine.generate_report --date 2026-05-11

# 3. Build website
python -m src.website.builder

# 4. Or invoke via Kimi agent
# "Generate WCVS report for today"
```
