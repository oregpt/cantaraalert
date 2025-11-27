"""
Canton Rewards Monitor - Scheduler
Runs threshold alerts and status reports on independent schedules
"""
print("=== SCHEDULER STARTING ===", flush=True)

import sys
print(f"Python version: {sys.version}", flush=True)

import os
print("Imported os", flush=True)

import time
print("Imported time", flush=True)

import threading
print("Imported threading", flush=True)

import schedule
print("Imported schedule", flush=True)

from http.server import HTTPServer, BaseHTTPRequestHandler
print("Imported http.server", flush=True)

from dotenv import load_dotenv
print("Imported dotenv", flush=True)

print("About to import canton_monitor...", flush=True)
from canton_monitor import run_check, run_status_report, send_notification
print("Imported canton_monitor", flush=True)

load_dotenv()
print("Loaded .env", flush=True)

print("Defining HealthHandler class...", flush=True)

# Simple health check server to keep Railway happy
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')

    def log_message(self, format, *args):
        pass  # Suppress logging

print("HealthHandler class defined", flush=True)

def start_health_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"Health check server running on port {port}")
    server.serve_forever()

print("Loading config from env...", flush=True)

# Alert 1: Threshold alerts (Est.Traffic > Gross)
ALERT1_ENABLED = os.getenv("ALERT1_ENABLED", "true").lower() == "true"
ALERT1_INTERVAL_MINUTES = int(os.getenv("ALERT1_INTERVAL_MINUTES", "15"))
print(f"Alert1: enabled={ALERT1_ENABLED}, interval={ALERT1_INTERVAL_MINUTES}", flush=True)

# Alert 2: Status reports (all values)
ALERT2_ENABLED = os.getenv("ALERT2_ENABLED", "true").lower() == "true"
ALERT2_INTERVAL_MINUTES = int(os.getenv("ALERT2_INTERVAL_MINUTES", "60"))
print(f"Alert2: enabled={ALERT2_ENABLED}, interval={ALERT2_INTERVAL_MINUTES}", flush=True)

print("Config loaded, entering main...", flush=True)


def threshold_check_job():
    """Alert 1: Check thresholds and alert if exceeded"""
    print(f"\n{'='*50}")
    print(f"Running threshold check (Alert 1)...")
    print(f"{'='*50}")
    try:
        run_check()
    except Exception as e:
        error_msg = f"Error during threshold check: {e}"
        print(error_msg)
        send_notification(
            title="Canton Monitor ERROR",
            message=error_msg,
            priority=1
        )


def status_report_job():
    """Alert 2: Send status report with current values"""
    print(f"\n{'='*50}")
    print(f"Running status report (Alert 2)...")
    print(f"{'='*50}")
    try:
        run_status_report()
    except Exception as e:
        error_msg = f"Error during status report: {e}"
        print(error_msg)
        send_notification(
            title="Canton Monitor ERROR",
            message=error_msg,
            priority=1
        )


if __name__ == "__main__":
    print("=== ENTERED MAIN ===", flush=True)

    # Start health check server in background thread
    print("Starting health check thread...", flush=True)
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    print("Health check thread started", flush=True)

    print(f"Canton Rewards Monitor starting...", flush=True)
    print(f"Alert 1 (Threshold): {'ENABLED' if ALERT1_ENABLED else 'DISABLED'} - every {ALERT1_INTERVAL_MINUTES} mins")
    print(f"Alert 2 (Status):    {'ENABLED' if ALERT2_ENABLED else 'DISABLED'} - every {ALERT2_INTERVAL_MINUTES} mins")

    # Build startup message
    config_lines = []
    if ALERT1_ENABLED:
        config_lines.append(f"• Threshold alerts: every {ALERT1_INTERVAL_MINUTES} mins")
    if ALERT2_ENABLED:
        config_lines.append(f"• Status reports: every {ALERT2_INTERVAL_MINUTES} mins")
    if not config_lines:
        config_lines.append("• No alerts enabled!")

    send_notification(
        title="Canton Monitor Started",
        message="Running on Railway.\n" + "\n".join(config_lines),
        priority=0
    )

    # Run enabled checks immediately on start (with is_startup=True for Alert 1)
    if ALERT1_ENABLED:
        print(f"\n{'='*50}")
        print(f"Running startup threshold check (Alert 1)...")
        print(f"{'='*50}")
        try:
            run_check(is_startup=True)
        except Exception as e:
            error_msg = f"Error during startup threshold check: {e}"
            print(error_msg)
            send_notification(
                title="Canton Monitor ERROR",
                message=error_msg,
                priority=1
            )

    if ALERT2_ENABLED:
        status_report_job()

    # Schedule recurring checks
    if ALERT1_ENABLED:
        schedule.every(ALERT1_INTERVAL_MINUTES).minutes.do(threshold_check_job)

    if ALERT2_ENABLED:
        schedule.every(ALERT2_INTERVAL_MINUTES).minutes.do(status_report_job)

    print("Entering main loop - scheduler is running...")
    print(f"Next scheduled jobs: {schedule.get_jobs()}")

    while True:
        schedule.run_pending()
        time.sleep(60)
