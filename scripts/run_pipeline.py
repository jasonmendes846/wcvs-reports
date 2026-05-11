#!/usr/bin/env python3
"""
WCVS Full Pipeline Orchestrator
Runs the complete swarm: Reporter → Checker → Publisher
Usage:
    python scripts/run_pipeline.py --date 2026-05-11 [--notify --deploy]
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path("C:/Users/jimmy/Projects/wcvs-platform")
SKILL_DIR = Path("C:/Users/jimmy/.kimi/skills/wcvs-report-engine/scripts")


def run(cmd: list, description: str) -> int:
    print(f"\n{'='*60}")
    print(f"[PIPELINE] {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print(f"[PIPELINE] FAILED: {description}")
    else:
        print(f"[PIPELINE] SUCCESS: {description}")
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="WCVS Full Pipeline")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="Report date")
    parser.add_argument("--compact", action="store_true", help="Generate compact edition")
    parser.add_argument("--full", action="store_true", help="Generate full edition")
    parser.add_argument("--qc-only", action="store_true", help="Skip generation, only run QC")
    parser.add_argument("--build-website", action="store_true", help="Build website after QC")
    parser.add_argument("--notify", action="store_true", help="Send Telegram notification")
    parser.add_argument("--chat-id", help="Telegram chat ID (required with --notify)")
    parser.add_argument("--website-url", default="http://localhost:8000", help="Website base URL")
    args = parser.parse_args()

    date = args.date
    exit_code = 0

    # Stage 1: REPORTER
    if not args.qc_only:
        editions = []
        if args.compact or not args.full:
            editions.append("--compact")
        if args.full or not args.compact:
            editions.append("--full")
        if not editions:
            editions = ["--compact", "--full"]

        report_cmd = [sys.executable, "-m", "src.report_engine.generate_report", "--date", date] + editions
        exit_code = run(report_cmd, f"Reporter: Generate report for {date}")
        if exit_code != 0:
            print("[PIPELINE] ABORT: Report generation failed.")
            sys.exit(1)

    # Stage 2: CHECKER
    qc_cmd = [sys.executable, str(SKILL_DIR / "qc_validate.py"),
              "--date", date,
              "--report-dir", "outputs/reports",
              "--website-dir", "outputs/website"]
    exit_code = run(qc_cmd, f"Checker: QC validation for {date}")
    if exit_code != 0:
        print("[PIPELINE] ABORT: QC validation failed. Fix issues and re-run.")
        sys.exit(1)

    # Stage 3: PUBLISHER (Website Build)
    if args.build_website or not args.qc_only:
        website_cmd = [sys.executable, "-m", "src.website.builder"]
        exit_code = run(website_cmd, "Publisher: Build static website")
        if exit_code != 0:
            print("[PIPELINE] WARNING: Website build failed.")

    # Stage 4: PUBLISHER (Telegram Notification)
    if args.notify:
        if not args.chat_id:
            print("[PIPELINE] ERROR: --chat-id required with --notify")
            sys.exit(1)
        notify_cmd = [sys.executable, "scripts/send_telegram_notification.py",
                      "--date", date,
                      "--chat-id", args.chat_id,
                      "--website-url", args.website_url]
        exit_code = run(notify_cmd, f"Publisher: Send Telegram notification")
        if exit_code != 0:
            print("[PIPELINE] WARNING: Telegram notification failed.")

    # Stage 5: DONE
    print(f"\n{'='*60}")
    print(f"[PIPELINE] COMPLETE — WCVS Report {date}")
    print(f"{'='*60}")
    print(f"Artifacts:   {PROJECT_ROOT / 'outputs' / 'reports' / date}")
    print(f"Website:     {PROJECT_ROOT / 'outputs' / 'website'}")
    print(f"Preview:     python -m http.server 8000 --directory outputs/website")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
