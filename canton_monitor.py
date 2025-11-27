"""
Canton Rewards Monitor
Checks if Est.Traffic > Gross and sends notifications via Pushover and Slack
"""

import os
import re
from datetime import datetime, timezone
import requests
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

# Database config (optional - if not set, skips DB storage)
DATABASE_URL = os.getenv("DATABASE_URL")
DB_ENABLED = DATABASE_URL is not None

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
        return []

    if not SLACK_BOT_TOKEN:
        return []

    exclude_channels = exclude_channels or []
    exclude_users = exclude_users or []

    # Filter out excluded channels and users
    channels = [c for c in SLACK_CHANNELS if c not in exclude_channels]
    users = [u for u in SLACK_USERS if u not in exclude_users]
    targets = channels + users

    if not targets:
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

    # Send to Slack (with exclusions)
    send_slack(title, message, exclude_channels, exclude_users)


def extract_cc_value(text: str) -> float:
    """Extract CC value from text like '12.53 CC'"""
    match = re.search(r'([\d.]+)\s*CC', text)
    if match:
        return float(match.group(1))
    return None


def init_db():
    """Create tables if they don't exist (safe to call multiple times)"""
    print(f"init_db() called, DB_ENABLED={DB_ENABLED}", flush=True)
    if not DB_ENABLED:
        print("DB not enabled, skipping init", flush=True)
        return

    try:
        import psycopg2
        print("Connecting to database...", flush=True)
        conn = psycopg2.connect(DATABASE_URL)
        print("Connected to database", flush=True)
        cur = conn.cursor()

        # Create metrics_raw table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS metrics_raw (
                id SERIAL PRIMARY KEY,
                obtained_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                source VARCHAR(255) NOT NULL,
                type VARCHAR(255) NOT NULL,
                value1 VARCHAR(500),
                value2 VARCHAR(500),
                value3 VARCHAR(500),
                value4 VARCHAR(500),
                value5 VARCHAR(500),
                value6 VARCHAR(500),
                value7 VARCHAR(500),
                value8 VARCHAR(500),
                value9 VARCHAR(500),
                value10 VARCHAR(500),
                value11 VARCHAR(500),
                value12 VARCHAR(500),
                value13 VARCHAR(500),
                value14 VARCHAR(500),
                value15 VARCHAR(500),
                value16 VARCHAR(500),
                value17 VARCHAR(500),
                value18 VARCHAR(500),
                value19 VARCHAR(500),
                value20 VARCHAR(500)
            )
        """)

        # Create indexes if they don't exist
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_raw_source_type
            ON metrics_raw(source, type)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_raw_timestamp
            ON metrics_raw(obtained_timestamp)
        """)

        # Create metrics_schema table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS metrics_schema (
                id SERIAL PRIMARY KEY,
                source VARCHAR(255) NOT NULL,
                type VARCHAR(255) NOT NULL,
                value1_name VARCHAR(255),
                value2_name VARCHAR(255),
                value3_name VARCHAR(255),
                value4_name VARCHAR(255),
                value5_name VARCHAR(255),
                value6_name VARCHAR(255),
                value7_name VARCHAR(255),
                value8_name VARCHAR(255),
                value9_name VARCHAR(255),
                value10_name VARCHAR(255),
                value11_name VARCHAR(255),
                value12_name VARCHAR(255),
                value13_name VARCHAR(255),
                value14_name VARCHAR(255),
                value15_name VARCHAR(255),
                value16_name VARCHAR(255),
                value17_name VARCHAR(255),
                value18_name VARCHAR(255),
                value19_name VARCHAR(255),
                value20_name VARCHAR(255),
                UNIQUE(source, type)
            )
        """)

        # Insert Canton schema definitions (ignore if already exist)
        cur.execute("""
            INSERT INTO metrics_schema (source, type, value1_name, value2_name)
            VALUES
                ('canton-rewards.noves.fi', 'EstEarning_latest_round', 'gross_cc', 'est_traffic_cc'),
                ('canton-rewards.noves.fi', 'EstEarning_1hr_avg', 'gross_cc', 'est_traffic_cc'),
                ('canton-rewards.noves.fi', 'EstEarning_24hr_avg', 'gross_cc', 'est_traffic_cc')
            ON CONFLICT (source, type) DO NOTHING
        """)

        conn.commit()
        cur.close()
        conn.close()
        print("Database tables initialized", flush=True)

    except Exception as e:
        print(f"Warning: DB init failed (will retry on next scrape): {e}", flush=True)


def store_metrics_to_db(metrics: dict):
    """Store scraped metrics to database (fire-and-forget, won't break alerting)"""
    if not DB_ENABLED:
        return

    try:
        import psycopg2

        # Map period names to DB type names
        type_mapping = {
            'Latest Round': 'EstEarning_latest_round',
            '1-Hour Average': 'EstEarning_1hr_avg',
            '24-Hour Average': 'EstEarning_24hr_avg'
        }

        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        obtained_ts = datetime.now(timezone.utc)
        source = 'canton-rewards.noves.fi'

        for period, values in metrics.items():
            db_type = type_mapping.get(period)
            if not db_type:
                continue

            gross = values.get("gross")
            est_traffic = values.get("est_traffic")

            # Only store if we have at least one value
            if gross is not None or est_traffic is not None:
                cur.execute("""
                    INSERT INTO metrics_raw (obtained_timestamp, source, type, value1, value2)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    obtained_ts,
                    source,
                    db_type,
                    str(gross) if gross is not None else None,
                    str(est_traffic) if est_traffic is not None else None
                ))

        conn.commit()
        cur.close()
        conn.close()
        print(f"Stored {len(metrics)} metrics to database")

    except Exception as e:
        # Fire-and-forget - log warning but don't break alerting
        print(f"Warning: DB storage failed (alerting continues): {e}")


def scrape_canton_rewards():
    """Scrape the Canton Rewards page and extract metrics"""
    print(f"Fetching {CANTON_URL}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(CANTON_URL, wait_until="networkidle")
        page.wait_for_timeout(3000)

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
            # Only initialize if not already set (avoid overwriting with second occurrence)
            if current_section not in results:
                results[current_section] = {"gross": None, "est_traffic": None}
        elif current_section and current_section in results:
            # Look for Gross and Est. Traffic values
            lines = part.split('\n')

            for i, line in enumerate(lines):
                line_stripped = line.strip()
                # Match "Gross" (exact or close)
                if line_stripped.lower() == 'gross' and i + 1 < len(lines):
                    val = extract_cc_value(lines[i + 1])
                    if val is not None:
                        results[current_section]["gross"] = val
                # Match "Est. Traffic" or "Est Traffic" (flexible)
                elif re.match(r'^est\.?\s*traffic$', line_stripped, re.IGNORECASE) and i + 1 < len(lines):
                    val = extract_cc_value(lines[i + 1])
                    if val is not None:
                        results[current_section]["est_traffic"] = val

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
            priority=0,
            alert_type="alert2"
        )
    else:
        print("No metrics available for status report")


def run_status_report():
    """Run a status report (Alert 2)"""
    raw_text = scrape_canton_rewards()
    metrics = parse_metrics(raw_text)
    store_metrics_to_db(metrics)  # Fire-and-forget DB storage
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
    store_metrics_to_db(metrics)  # Fire-and-forget DB storage
    return check_and_alert(metrics, is_startup=is_startup)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("Sending test notifications...")
        test_notifications()
    else:
        print("Starting Canton Rewards check...")
        run_check()
