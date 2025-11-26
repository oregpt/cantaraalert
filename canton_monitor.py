"""
Canton Rewards Monitor
Checks if Est.Traffic > Gross and sends Pushover notification
"""

import os
import re
import requests
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")
CANTON_URL = "https://canton-rewards.noves.fi/"


def send_pushover(title: str, message: str, priority: int = 1):
    """Send notification via Pushover"""
    response = requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": PUSHOVER_API_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "title": title,
            "message": message,
            "priority": priority,
        }
    )
    if response.status_code == 200:
        print(f"Notification sent: {title}")
    else:
        print(f"Failed to send notification: {response.text}")
    return response


def extract_cc_value(text: str) -> float:
    """Extract CC value from text like '12.53 CC'"""
    match = re.search(r'([\d.]+)\s*CC', text)
    if match:
        return float(match.group(1))
    return None


def scrape_canton_rewards():
    """Scrape the Canton Rewards page and extract metrics"""
    print(f"Fetching {CANTON_URL}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(CANTON_URL, wait_until="networkidle")
        page.wait_for_timeout(3000)

        # Get all the card/row elements
        all_text = page.inner_text("body")
        browser.close()

    return all_text


def parse_metrics(raw_text: str) -> dict:
    """Parse the raw text to extract Est.Traffic and Gross values"""
    results = {}

    # Split into sections by the period headers
    sections = re.split(r'(Latest Round|1-Hour Average|24-Hour Average)', raw_text)

    current_section = None
    for part in sections:
        part = part.strip()
        if part in ['Latest Round', '1-Hour Average', '24-Hour Average']:
            current_section = part
            results[current_section] = {"gross": None, "est_traffic": None}
        elif current_section and current_section in results:
            # Look for Gross and Est. Traffic values
            lines = part.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if line == 'Gross' and i + 1 < len(lines):
                    val = extract_cc_value(lines[i + 1])
                    if val is not None:
                        results[current_section]["gross"] = val
                elif line == 'Est. Traffic' and i + 1 < len(lines):
                    val = extract_cc_value(lines[i + 1])
                    if val is not None:
                        results[current_section]["est_traffic"] = val

    return results


def check_and_alert(metrics: dict) -> bool:
    """Check if Est.Traffic > Gross and send alert if so"""
    alerts = []

    # Only check these periods (exclude 24-Hour Average)
    check_periods = ['Latest Round', '1-Hour Average']

    print("\n--- Current Values ---")
    for period, values in metrics.items():
        est = values.get("est_traffic")
        gross = values.get("gross")
        print(f"{period}: Gross={gross} CC, Est.Traffic={est} CC")

        # Only alert for Latest Round and 1-Hour Average
        if period in check_periods and est is not None and gross is not None:
            if est > gross:
                diff = est - gross
                alerts.append(f"{period}: Est.Traffic ({est}) > Gross ({gross}) by {diff:.2f} CC")

    print("----------------------\n")

    if alerts:
        message = "\n".join(alerts)
        print(f"ALERT: {message}")
        send_pushover(
            title="Canton: Est.Traffic > Gross!",
            message=message,
            priority=1
        )
        return True
    else:
        print("No alerts - Est.Traffic <= Gross for all periods")
        return False


def test_pushover():
    """Send a test notification to verify Pushover is working"""
    send_pushover(
        title="Canton Monitor Test",
        message="Your Canton Rewards monitor is set up and working!",
        priority=0
    )


def run_check():
    """Main check function"""
    raw_text = scrape_canton_rewards()
    metrics = parse_metrics(raw_text)
    return check_and_alert(metrics)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("Sending test notification...")
        test_pushover()
    else:
        print("Starting Canton Rewards check...")
        run_check()
