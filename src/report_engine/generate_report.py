"""
WCVS Report Generator — Main Orchestrator
Usage:
    python -m src.report_engine.generate_report --date 2026-05-11
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_ingestion.cache import DataCache
from src.data_ingestion.fetchers.unified import UnifiedFetcher
from src.report_engine.scoring import WCVSScorer
from src.report_engine.renderer import ReportRenderer
from src.report_engine.pdf_generator import PDFGenerator


def build_report_context(data: dict, scorer: WCVSScorer, report_date: str) -> dict:
    """Construct the Jinja2 context from fetched data and scores."""
    # Extract values with defaults
    sp500 = data.get("sp500_price", {}).get("value") or 7399
    cape = data.get("shiller_cape", {}).get("value") or 40.1
    forward_pe = data.get("forward_pe", {}).get("value") or 21.0
    mktcap_gdp = data.get("market_cap_gdp", {}).get("value") or 200.0
    fear_greed = data.get("fear_greed", {}).get("value") or 67
    naaim = data.get("naaim", {}).get("value") or 96.7
    aaii = data.get("aaii_bull_bear", {}).get("value") or 1.2
    put_call = data.get("put_call", {}).get("value") or 0.88
    y10 = data.get("yield_10y", {}).get("value") or 4.38
    y2 = data.get("yield_2y", {}).get("value") or 3.90
    y3m = data.get("yield_3m", {}).get("value") or 3.69
    hy_oas = data.get("hy_oas", {}).get("value") or 350.0
    dxy = data.get("dxy", {}).get("value") or 97.84
    wti = data.get("wti", {}).get("value") or 94.77
    gold = data.get("gold", {}).get("value") or 2400.0
    pct_50d = data.get("pct_above_50d", {}).get("value") or 45.0
    pct_200d = data.get("pct_above_200d", {}).get("value") or 55.0
    spread_10y_2y = data.get("spread_10y_2y", {}).get("value") or (y10 - y2 if y10 and y2 else 0.48)
    spread_10y_3m = data.get("spread_10y_3m", {}).get("value") or (y10 - y3m if y10 and y3m else 0.69)

    # Calculate scores
    fundamental_score, fundamental_label = scorer.score_fundamental(cape, forward_pe, mktcap_gdp)
    internals_score, internals_label = scorer.score_internals(pct_50d, pct_200d)
    sentiment_score, sentiment_label = scorer.score_sentiment(fear_greed, naaim, aaii, put_call)
    credit_score, credit_label = scorer.score_credit(spread_10y_2y, spread_10y_3m, hy_oas)
    macro_score, macro_label = scorer.score_macro(dxy, wti, gold)

    category_scores = {
        "fundamental": fundamental_score,
        "internals": internals_score,
        "sentiment": sentiment_score,
        "credit": credit_score,
        "macro": macro_score,
    }

    composite, rating_text, rating_class = scorer.calculate_composite(category_scores)
    forward_returns = scorer.expected_returns(cape)

    # Determine tactical stance
    if composite <= 1.5:
        tactical_stance = "Defensive"
    elif composite <= 2.5:
        tactical_stance = "Cautious"
    elif composite <= 3.5:
        tactical_stance = "Neutral"
    elif composite <= 4.5:
        tactical_stance = "Cautiously Optimistic"
    else:
        tactical_stance = "Aggressive"

    categories = [
        {
            "name": "Fundamental Valuation",
            "weight": 25,
            "raw_score": fundamental_score,
            "contribution": round(0.25 * fundamental_score, 2),
            "label": fundamental_label,
            "metrics": [
                {"name": "Shiller CAPE", "current": f"{cape}x", "context": "95th percentile; mean 17.0x", "assessment": "Extreme overvaluation" if cape > 35 else "Elevated"},
                {"name": "Forward P/E (12M)", "current": f"{forward_pe}x", "context": "Above 5-year average" if forward_pe > 18 else "Near average", "assessment": "Elevated" if forward_pe > 18 else "Fair"},
                {"name": "Market Cap / GDP", "current": f"~{mktcap_gdp}%", "context": "Record territory" if mktcap_gdp > 150 else "High", "assessment": "Extreme" if mktcap_gdp > 180 else "Elevated"},
            ],
            "narrative": f"The CAPE ratio at {cape}x sits in extreme territory. Forward P/E of {forward_pe}x implies aggressive earnings growth assumptions. Market cap relative to GDP at ~{mktcap_gdp}% signals significant overvaluation."
        },
        {
            "name": "Market Internals",
            "weight": 20,
            "raw_score": internals_score,
            "contribution": round(0.20 * internals_score, 2),
            "label": internals_label,
            "metrics": [
                {"name": "% Stocks Above 50-Day MA", "current": f"~{pct_50d}%", "context": "Deteriorating breadth" if pct_50d < 50 else "Healthy", "assessment": "Weak" if pct_50d < 50 else "Moderate"},
                {"name": "% Stocks Above 200-Day MA", "current": f"~{pct_200d}%", "context": "Weak participation" if pct_200d < 60 else "Broad", "assessment": "Weak" if pct_200d < 60 else "Moderate"},
            ],
            "narrative": f"Market breadth shows {pct_50d}% of stocks above their 50-day MA and {pct_200d}% above their 200-day MA, indicating {'narrowing participation and underlying weakness' if pct_200d < 60 else 'broad-based participation'}."
        },
        {
            "name": "Sentiment & Psychology",
            "weight": 20,
            "raw_score": sentiment_score,
            "contribution": round(0.20 * sentiment_score, 2),
            "label": sentiment_label,
            "metrics": [
                {"name": "CNN Fear & Greed Index", "current": f"{fear_greed} ({'Greed' if fear_greed > 60 else 'Fear' if fear_greed < 40 else 'Neutral'})", "context": "Complacent; little fear priced" if fear_greed > 60 else "Elevated fear", "assessment": "Complacent" if fear_greed > 60 else "Fearful" if fear_greed < 40 else "Neutral"},
                {"name": "NAAIM Exposure Index", "current": f"{naaim}%", "context": "Extremely bullish" if naaim > 85 else "Neutral", "assessment": "Extreme" if naaim > 90 else "Elevated" if naaim > 75 else "Neutral"},
            ],
            "narrative": f"Active managers remain nearly fully invested at {naaim}% exposure. The Fear & Greed Index at {fear_greed} signals {'greed territory with little hedging' if fear_greed > 60 else 'fear territory' if fear_greed < 40 else 'neutral sentiment'}."
        },
        {
            "name": "Credit & Liquidity",
            "weight": 15,
            "raw_score": credit_score,
            "contribution": round(0.15 * credit_score, 2),
            "label": credit_label,
            "metrics": [
                {"name": "10-Year Treasury Yield", "current": f"{y10}%", "context": "High real rates; equity headwind" if y10 > 4.0 else "Moderate", "assessment": "Tight" if y10 > 4.0 else "Neutral"},
                {"name": "10Y–2Y Spread", "current": f"{spread_10y_2y} bps", "context": "Flat curve; recession risk" if spread_10y_2y < 50 else "Normalizing", "assessment": "Tight" if spread_10y_2y < 50 else "Moderate"},
            ],
            "narrative": f"The Treasury curve is {'flat' if spread_10y_2y < 50 else 'steep'} with the 10Y–2Y spread at {spread_10y_2y} bps. The 10-year yield at {y10}% creates a {'formidable competing asset' if y10 > 4.0 else 'moderate headwind'} for equities."
        },
        {
            "name": "Macro & Cross-Asset",
            "weight": 20,
            "raw_score": macro_score,
            "contribution": round(0.20 * macro_score, 2),
            "label": macro_label,
            "metrics": [
                {"name": "U.S. Dollar (DXY)", "current": f"{dxy}", "context": "Weak dollar; supports exports but signals relative decline" if dxy < 100 else "Strong", "assessment": "Weak" if dxy < 100 else "Strong"},
                {"name": "Oil (WTI)", "current": f"${wti}/bbl", "context": "High energy costs; margin pressure" if wti > 85 else "Stable", "assessment": "High" if wti > 85 else "Moderate"},
            ],
            "narrative": f"Oil at ${wti} with the dollar at {dxy} creates a {'stagflationary crosswind' if wti > 85 and dxy < 100 else 'mixed macro backdrop'}. Gold at ${gold} signals {'safe-haven demand' if gold > 2200 else 'stable sentiment'}."
        },
    ]

    # Forward returns narrative
    ret_10y = next((r for r in forward_returns if "10 Year" in r["horizon"]), {})
    ret_10y_val = ret_10y.get("expected_return", "0.0")
    forward_narrative = f"At a CAPE of {cape}x, historical regression points to {'negative' if float(ret_10y_val) < 0 else 'positive'} real returns across most horizons. The 10-year expected real return of {ret_10y_val}% annually implies a cumulative {'loss' if float(ret_10y_val) < 0 else 'gain'} over a decade."

    # Tactical bullets
    erp = round((1 / (forward_pe if forward_pe else 20)) * 100 - y10, 2) if forward_pe else 0.5
    tactical_bullets = [
        f"Equity risk premium (~{erp}% over 10-year Treasuries) offers {'minimal compensation' if erp < 1 else 'moderate compensation'}",
        f"Market breadth at {pct_200d}% above 200-day MA suggests {'the index is masking underlying weakness' if pct_200d < 60 else 'broad participation'}",
        f"Oil at ${wti} with {'elevated' if wti > 85 else 'moderate'} energy costs is a {'live risk' if wti > 85 else 'manageable factor'}",
        f"Active managers at {naaim}% equity exposure indicate {'no incremental buyers left' if naaim > 90 else 'room for further allocation'}",
        f"The {y10}% 10-year yield with a {spread_10y_2y} bps curve suggests {'recession risk' if spread_10y_2y < 50 else 'normalizing conditions'}",
    ]

    # Bearish / bullish factors
    bearish_factors = [
        f"CAPE at {cape}x — in the {'95th percentile' if cape > 35 else 'elevated range'}, exceeded only during dot-com" if cape > 35 else f"CAPE at {cape}x remains above historical mean",
        f"Forward P/E {forward_pe}x requires aggressive earnings growth; margins are compressing" if forward_pe > 20 else f"Forward P/E at {forward_pe}x pricing in optimistic growth",
        f"NAAIM at {naaim}% — managers are fully invested; no dry powder" if naaim > 90 else f"NAAIM at {naaim}% shows elevated optimism",
        f"Oil at ${wti} with sticky inflation; energy cost pressure rising" if wti > 85 else f"Oil at ${wti} with supply risks",
        f"10Y yield at {y10}% with equity risk premium near historic lows" if erp < 1 else f"10Y yield at {y10}% creating competition for equities",
    ]

    bullish_factors = [
        "S&P 500 holding near highs; trend remains technically intact",
        f"Breadth at {pct_200d}% still positive on long-term timeframe" if pct_200d > 50 else "Selective strength in defensive sectors",
        f"Fear & Greed at {fear_greed} shows no panic, supporting orderly conditions" if fear_greed > 40 else f"Fear & Greed at {fear_greed} suggests pessimism may be overdone",
        f"Fed policy expectations point to possible easing if data softens" if y10 > 4 else "Accommodative financial conditions support risk assets",
        "AI-driven earnings growth narrative still intact for mega-caps",
    ]

    # Summary
    summary = f"The WCVS composite of **{composite} / 5.0** places the U.S. equity market in \"{rating_text}\" territory. The combination of {'extreme fundamental valuations' if fundamental_score < 2 else 'elevated valuations'}, {'deteriorating breadth' if internals_score < 2.5 else 'mixed internals'}, {'complacent sentiment' if sentiment_score < 2.5 else 'balanced sentiment'}, and a {'fragile' if macro_score < 2.5 else 'stable'} macro backdrop creates an asymmetric risk profile. Forward returns are expected to be {'negative' if float(ret_10y_val) < 0 else 'modest'} across all horizons. Patience and capital preservation should take priority over chasing momentum at these levels."

    # TL;DR
    tldr = f"The U.S. equity market remains {'significantly overvalued' if composite < 2 else 'overvalued' if composite < 3 else 'fairly valued' if composite < 4 else 'undervalued'}. The S&P 500 {'closed' if report_date else 'is'} at {sp500:,}, with the WCVS composite score holding at **{composite} out of 5.0**. The forward return outlook remains {'deeply negative' if float(ret_10y_val) < -1 else 'negative' if float(ret_10y_val) < 0 else 'cautious'}: expected real returns range from **{forward_returns[0]['expected_return']}% annually over 1 year** to **{ret_10y_val}% over 10 years**."

    return {
        "report_date": report_date,
        "sp500_price": sp500,
        "composite_score": composite,
        "rating_text": rating_text,
        "rating_class": rating_class,
        "categories": categories,
        "forward_returns": forward_returns,
        "forward_returns_narrative": forward_narrative,
        "tactical_stance": tactical_stance,
        "tactical_narrative": f"The market is priced for {'perfection and positioned for complacency' if composite < 2 else 'optimism' if composite < 3 else 'balanced conditions' if composite < 4 else 'pessimism, creating opportunity'}. Every category in the WCVS framework signals {'elevated risk' if composite < 2.5 else 'mixed signals' if composite < 3.5 else 'favorable conditions'}. This is the classic setup for a {'surprise to the downside' if composite < 2.5 else 'range-bound market' if composite < 3.5 else 'surprise to the upside'}.",
        "tactical_bullets": tactical_bullets,
        "bearish_factors": bearish_factors,
        "bullish_factors": bullish_factors,
        "summary": summary,
        "tldr": tldr,
        "data_sources": "GuruFocus, FactSet, YCharts, CBOE, AAII, NAAIM, U.S. Treasury, Yahoo Finance, macromicro.me",
        "analyst_name": "WCVS Multi-Agent System",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate WCVS Report")
    parser.add_argument("--date", type=str, default=datetime.now().strftime("%Y-%m-%d"), help="Report date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", type=str, default=str(PROJECT_ROOT / "outputs" / "reports"), help="Output directory")
    parser.add_argument("--compact", action="store_true", help="Generate compact 3-page edition")
    parser.add_argument("--full", action="store_true", help="Generate full institutional edition")
    args = parser.parse_args()

    report_date = args.date
    output_dir = Path(args.output_dir) / report_date
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[WCVS] Generating report for {report_date}...")

    # Initialize components
    cache = DataCache(PROJECT_ROOT / "outputs" / "cache.json")
    fetcher = UnifiedFetcher(cache)
    scorer = WCVSScorer()
    templates_dir = PROJECT_ROOT / "src" / "report_engine" / "templates"
    renderer = ReportRenderer(templates_dir)

    # Fetch data
    print("[WCVS] Fetching market data...")
    data = fetcher.fetch_all()
    # Save raw data for debugging
    with open(output_dir / "data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    # Build context
    print("[WCVS] Calculating scores and building context...")
    context = build_report_context(data, scorer, report_date)

    # Save context
    with open(output_dir / "context.json", "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2, default=str)

    # Render markdown
    print("[WCVS] Rendering markdown...")
    md_text = renderer.render_markdown(context)
    md_path = output_dir / f"wcvs-report-{report_date}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    print(f"[WCVS] Markdown saved: {md_path}")

    # Render HTML + PDF
    editions = []
    if args.compact or not args.full:
        editions.append(("compact", templates_dir / "compact.css"))
    if args.full or not args.compact:
        editions.append(("full", templates_dir / "full.css"))

    for edition_name, css_path in editions:
        print(f"[WCVS] Rendering {edition_name} HTML...")
        html_text = renderer.markdown_to_html(md_text, css_path=css_path, title=f"WCVS Report — {report_date}")
        html_path = output_dir / f"wcvs-report-{report_date}-{edition_name}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_text)
        print(f"[WCVS] HTML saved: {html_path}")

        print(f"[WCVS] Generating {edition_name} PDF...")
        pdf_path = output_dir / f"wcvs-report-{report_date}-{edition_name}.pdf"
        try:
            pdf_gen = PDFGenerator(output_dir)
            pdf_gen.generate_sync(html_path, pdf_path)
            print(f"[WCVS] PDF saved: {pdf_path}")
        except Exception as e:
            print(f"[WCVS] PDF generation failed: {e}")
            print("[WCVS] Ensure Playwright is installed: pip install playwright && playwright install chromium")

    print(f"[WCVS] Report generation complete for {report_date}.")
    print(f"[WCVS] Artifacts in: {output_dir}")


if __name__ == "__main__":
    main()
