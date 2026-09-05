#!/usr/bin/env python3
"""
scheduler.py
Automated background scheduler for Daily Market Summary.
Executes update.py on weekdays 30 minutes after US market close (16:30 US Eastern Time).
"""

import argparse
import os
import sys
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import update

NY_TZ = ZoneInfo("America/New_York")
TARGET_HOUR = 16
TARGET_MINUTE = 30


def get_next_run_time(now_ny=None):
    """
    Returns the next datetime (in America/New_York timezone) for a weekday at 16:30.
    Weekdays: Mon=0, Tue=1, Wed=2, Thu=3, Fri=4
    """
    if now_ny is None:
        now_ny = datetime.now(NY_TZ)

    # Candidate time today at 16:30
    candidate = now_ny.replace(hour=TARGET_HOUR, minute=TARGET_MINUTE, second=0, microsecond=0)

    # If today is a weekday and we haven't reached 16:30 yet, run today
    if now_ny.weekday() < 5 and now_ny < candidate:
        return candidate

    # Otherwise look for the next weekday
    days_ahead = 1
    while True:
        next_day = candidate + timedelta(days=days_ahead)
        if next_day.weekday() < 5:  # Monday to Friday
            return next_day
        days_ahead += 1


def format_duration(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours}h {minutes}m {secs}s"


def start_scheduler(run_now=False):
    print("=" * 65)
    print(" Daily Market Summary Automated Scheduler")
    print(" Target: Weekdays at 16:30 US Eastern Time (30m after US close)")
    print("=" * 65)

    if run_now:
        print("\n[Scheduler] Immediate update requested (--run-now). Running pipeline...")
        try:
            update.run_pipeline()
        except Exception as e:
            print(f"[Scheduler] Pipeline error: {e}", file=sys.stderr)

    while True:
        now_ny = datetime.now(NY_TZ)
        next_run = get_next_run_time(now_ny)
        wait_seconds = (next_run - now_ny).total_seconds()

        local_next_run = next_run.astimezone()

        print(f"\n[Scheduler] Current New York time: {now_ny.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"[Scheduler] Next update scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"            (Local system time:      {local_next_run.strftime('%Y-%m-%d %H:%M:%S %Z')})")
        print(f"[Scheduler] Sleeping for {format_duration(wait_seconds)} ({int(wait_seconds)} seconds)...")

        # Sleep in chunks to allow responsive interruption
        try:
            remaining = wait_seconds
            while remaining > 0:
                sleep_chunk = min(remaining, 60)
                time.sleep(sleep_chunk)
                remaining -= sleep_chunk

            print(f"\n[Scheduler] Triggering scheduled update at {datetime.now(NY_TZ).strftime('%Y-%m-%d %H:%M:%S %Z')}...")
            update.run_pipeline()
        except KeyboardInterrupt:
            print("\n[Scheduler] Stopping scheduler.")
            break
        except Exception as e:
            print(f"[Scheduler] Unexpected error during run: {e}", file=sys.stderr)
            time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description="Schedule daily market updates 30 mins after US close.")
    parser.add_argument("--run-now", action="store_true", help="Execute update immediately before waiting")
    args = parser.parse_args()

    start_scheduler(run_now=args.run_now)


if __name__ == "__main__":
    main()
