"""
Canton Rewards Monitor - Scheduler
Runs the check every X minutes continuously
"""

import time
import schedule
from canton_monitor import run_check

CHECK_INTERVAL_MINUTES = 15


def job():
    print(f"\n{'='*50}")
    print(f"Running scheduled check...")
    print(f"{'='*50}")
    try:
        run_check()
    except Exception as e:
        print(f"Error during check: {e}")


if __name__ == "__main__":
    print(f"Canton Rewards Monitor starting...")
    print(f"Checking every {CHECK_INTERVAL_MINUTES} minutes")

    # Send startup notification
    from canton_monitor import send_pushover
    send_pushover(
        title="Canton Monitor Started",
        message=f"Running on Railway. Checking every {CHECK_INTERVAL_MINUTES} mins.",
        priority=0
    )

    # Run immediately on start
    job()

    # Schedule recurring checks
    schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(60)
