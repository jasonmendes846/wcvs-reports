#!/usr/bin/env python3
"""
WCVS Telegram Notification Sender
Usage:
    python send_telegram_notification.py --date 2026-05-11 --chat-id YOUR_CHAT_ID
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path("C:/Users/jimmy/Projects/wcvs-platform")


def build_message(date: str, ctx: dict, website_url: str) -> str:
    score = ctx.get("composite_score", "—")
    rating = ctx.get("rating_text", "—")
    stance = ctx.get("tactical_stance", "—")
    sp500 = ctx.get("sp500_price", "—")
    if isinstance(sp500, (int, float)):
        sp500 = f"{sp500:,.0f}"

    # Get 10Y expected return
    ret_10y = "—"
    for fr in ctx.get("forward_returns", []):
        if "10 Year" in fr.get("horizon", ""):
            ret_10y = fr.get("expected_return", "—")
            break

    report_url = f"{website_url}/reports/{date}/"
    pdf_url = f"{website_url}/reports/{date}/wcvs-report-{date}-full.pdf"

    return f"""📊 *WCVS Daily Report — {date}*

S&P 500: {sp500}
Composite Score: *{score} / 5.0*
Rating: {rating}
Stance: {stance}
10Y Expected Return: {ret_10y}

📄 [Full Report]({report_url})
📥 [Download PDF]({pdf_url})

⚠️ Not financial advice.
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Report date YYYY-MM-DD")
    parser.add_argument("--chat-id", required=True, help="Telegram chat ID")
    parser.add_argument("--website-url", default="http://localhost:8000", help="Base website URL")
    parser.add_argument("--dry-run", action="store_true", help="Print message instead of sending")
    args = parser.parse_args()

    ctx_path = PROJECT_ROOT / "outputs" / "reports" / args.date / "context.json"
    if not ctx_path.exists():
        print(f"Error: context.json not found for {args.date}", file=sys.stderr)
        sys.exit(1)

    ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
    message = build_message(args.date, ctx, args.website_url.rstrip("/"))

    if args.dry_run:
        print("=== TELEGRAM MESSAGE (dry run) ===")
        print(message)
        print("===================================")
        sys.exit(0)

    try:
        from send_markdown_message_as_telegram_bot import send_markdown_message_as_telegram_bot
        send_markdown_message_as_telegram_bot(messageText=message, chatId=args.chat_id)
        print(f"Telegram notification sent to {args.chat_id}")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
