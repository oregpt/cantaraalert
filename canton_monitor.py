"""
Canton Rewards Monitor
Checks if Est.Traffic > Gross and sends notifications via Pushover and Slack
"""

import os
import re
import requests
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

# Pushover config
PUSHOVER_ENABLED = os.getenv("PUSHOVER_ENABLED", "true").lower() == "true"
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")

# Slack config
SLACK_ENABLED = os.getenv("SLACK_ENABLED", "false").lower() == "true"
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNELS = [c.strip() for c in os.getenv("SLACK_CHANNELS", "").split(",") if c.strip()]
SLACK_USERS = [u.strip() for u in os.getenv("SLACK_USERS", "").split(",") if u.strip()]

# Alert 1 exclusions (threshold alerts)
ALERT1_EXCLUDE_CHANNELS = [c.strip() for c in os.getenv("ALERT1_EXCLUDE_CHANNELS", "").split(",") if c.strip()]
ALERT1_EXCLUDE_USERS = [u.strip() for u in os.getenv("ALERT1_EXCLUDE_USERS", "").split(",") if u.strip()]
ALERT1_EXCLUDE_PUSHOVER = os.getenv("ALERT1_EXCLUDE_PUSHOVER", "false").lower() == "true"

# Alert 2 exclusions (status reports)
ALERT2_EXCLUDE_CHANNELS = [c.strip() for c in os.getenv("ALERT2_EXCLUDE_CHANNELS", "").split(",") if c.strip()]
ALERT2_EXCLUDE_USERS = [u.strip() for u in os.getenv("ALERT2_EXCLUDE_USERS", "").split(",") if u.strip()]
ALERT2_EXCLUDE_PUSHOVER = os.getenv("ALERT2_EXCLUDE_PUSHOVER", "false").lower() == "true"

CANTON_URL = "https://canton-rewards.noves.fi/"


def send_pushover(title: str, message: str, priority: int = 1):
    """Send notification via Pushover"""
    if not PUSHOVER_ENABLED:
        print("Pushover disabled, skipping")
        return None

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
        print(f"Pushover sent: {title}")
    else:
        print(f"Pushover failed: {response.text}")
    return response


def send_slack(title: str, message: str, exclude_channels: list = None, exclude_users: list = None):
    """Send notification via Slack to all configured channels and users (minus exclusions)"""
    if not SLACK_ENABLED:
        print("Slack disabled, skipping")
        return []

    if not SLACK_BOT_TOKEN:
        print("Slack bot token not configured")
        return []

    exclude_channels = exclude_channels or []
    exclude_users = exclude_users or []

    # Filter out excluded channels and users
    channels = [c for c in SLACK_CHANNELS if c not in exclude_channels]
    users = [u for u in SLACK_USERS if u not in exclude_users]
    targets = channels + users

    if not targets:
        print("No Slack targets after exclusions")
        return []

    responses = []
    for target in targets:
        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
            json={
                "channel": target,
                "text": f"*{title}*\n```{message}```"
            }
        )
        data = response.json()
        if data.get("ok"):
            print(f"Slack sent to {target}: {title}")
        else:
            print(f"Slack failed for {target}: {data.get('error')}")
        responses.append(response)

    return responses


def send_notification(title: str, message: str, priority: int = 1, alert_type: str = None):
    """Send notification to all enabled channels (Pushover + Slack) with per-alert exclusions

    alert_type: 'alert1' for threshold alerts, 'alert2' for status reports, None for all
    """
    # Determine exclusions based on alert type
    exclude_pushover = False
    exclude_channels = []
    exclude_users = []

    if alert_type == "alert1":
        exclude_pushover = ALERT1_EXCLUDE_PUSHOVER
        exclude_channels = ALERT1_EXCLUDE_CHANNELS
        exclude_users = ALERT1_EXCLUDE_USERS
    elif alert_type == "alert2":
        exclude_pushover = ALERT2_EXCLUDE_PUSHOVER
        exclude_channels = ALERT2_EXCLUDE_CHANNELS
        exclude_users = ALERT2_EXCLUDE_USERS

    # Send to Pushover (unless excluded)
    if not exclude_pushover:
        send_pushover(title, message, priority)
    else:
        print(f"Pushover excluded for {alert_type}")

    # Send to Slack (with exclusions)
    send_slack(title, message, exclude_channels, exclude_users)


def extract_cc_value(text: str) -> float:
    """Extract CC value from text like '12.53 CC'"""
    match = re.search(r'([\d.]+)\s*CC', text)
    if match:
        return float(match.group(1))
    return None


def scrape_canton_rewards():
    """Scrape the Canton Rewards page and extract metrics"""
    print(f"Fetching {CANTON_URL}...")

    try:
        with sync_playwright() as p:
            print("Launching browser...")
            browser = p.chromium.launch(headless=True)
            print("Browser launched, creating page...")
            page = browser.new_page()
            print("Navigating to URL...")
            page.goto(CANTON_URL, wait_until="networkidle")
            print("Page loaded, waiting for content...")
            page.wait_for_timeout(3000)

            # Get all the card/row elements
            all_text = page.inner_text("body")
            print(f"Scraped {len(all_text)} characters")
            browser.close()
            print("Browser closed successfully")

        return all_text
    except Exception as e:
        print(f"SCRAPE ERROR: {e}")
        raise


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
            # Debug: print raw section content for Latest Round
            if current_section == 'Latest Round':
                print(f"DEBUG Latest Round raw content:\n{part[:500]}")

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

    # Debug: print parsed metrics
    print(f"Parsed metrics: {results}")
    return results


def check_and_alert(metrics: dict, is_startup: bool = False) -> bool:
    """Alert 1: Check if Est.Traffic > Gross and send alert if so

    is_startup: If True, sends notification even when values are normal
    """
    alerts = []
    status_lines = []

    # Only check these periods (exclude 24-Hour Average)
    check_periods = ['Latest Round', '1-Hour Average']

    print("\n--- Current Values ---")
    for period, values in metrics.items():
        est = values.get("est_traffic")
        gross = values.get("gross")
        print(f"{period}: Gross={gross} CC, Est.Traffic={est} CC")

        # Only alert for Latest Round and 1-Hour Average
        if period in check_periods and est is not None and gross is not None:
            diff = gross - est
            if est > gross:
                alerts.append(f"⚠️ {period}: Est.Traffic ({est}) > Gross ({gross}) by {diff:.2f} CC")
            else:
                status_lines.append(f"✓ {period}: Gross ({gross}) >= Est.Traffic ({est})")

    print("----------------------\n")

    if alerts:
        message = "\n".join(alerts)
        print(f"ALERT: {message}")
        send_notification(
            title="Canton: Est.Traffic > Gross!",
            message=message,
            priority=1,
            alert_type="alert1"
        )
        return True
    elif is_startup:
        # On startup, send "all normal" notification
        message = "All values normal:\n" + "\n".join(status_lines)
        print(f"STARTUP CHECK: {message}")
        send_notification(
            title="Canton: All Values Normal",
            message=message,
            priority=0,
            alert_type="alert1"
        )
        return False
    else:
        print("No alerts - Est.Traffic <= Gross for all periods")
        return False


def send_status_report(metrics: dict):
    """Alert 2: Send status report with all current values (all 3 periods)"""
    lines = []

    # Include all periods in order
    all_periods = ['Latest Round', '1-Hour Average', '24-Hour Average']

    for period in all_periods:
        if period in metrics:
            values = metrics[period]
            est = values.get("est_traffic")
            gross = values.get("gross")
            if est is not None and gross is not None:
                diff = gross - est
                status = "⚠️" if est > gross else "✓"
                lines.append(f"{status} {period}:")
                lines.append(f"   Gross: {gross} CC")
                lines.append(f"   Est.Traffic: {est} CC")
                lines.append(f"   Diff: {diff:+.2f} CC")

    if lines:
        message = "\n".join(lines)
        print(f"STATUS REPORT:\n{message}")
        send_notification(
            title="Canton Status Report",
            message=message,
            priority=0,  # Low priority for status reports
            alert_type="alert2"
        )
    else:
        print("No metrics available for status report")


def run_status_report():
    """Run a status report (Alert 2)"""
    raw_text = scrape_canton_rewards()
    metrics = parse_metrics(raw_text)
    send_status_report(metrics)


def test_notifications():
    """Send a test notification to verify all channels are working"""
    send_notification(
        title="Canton Monitor Test",
        message="Your Canton Rewards monitor is set up and working!",
        priority=0
    )


def run_check(is_startup: bool = False):
    """Main check function"""
    raw_text = scrape_canton_rewards()
    metrics = parse_metrics(raw_text)
    return check_and_alert(metrics, is_startup=is_startup)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("Sending test notifications...")
        test_notifications()
    else:
        print("Starting Canton Rewards check...")
        run_check()
