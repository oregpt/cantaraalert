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

# Alert 3 config (Est.Traffic spike/drop)
ALERT3_ENABLED = os.getenv("ALERT3_ENABLED", "true").lower() == "true"
ALERT3_THRESHOLD_PERCENT = float(os.getenv("ALERT3_THRESHOLD_PERCENT", "30"))
ALERT3_COMPARISON_PERIOD = os.getenv("ALERT3_COMPARISON_PERIOD", "1hr").lower()
ALERT3_EXCLUDE_CHANNELS = [c.strip() for c in os.getenv("ALERT3_EXCLUDE_CHANNELS", "").split(",") if c.strip()]
ALERT3_EXCLUDE_USERS = [u.strip() for u in os.getenv("ALERT3_EXCLUDE_USERS", "").split(",") if u.strip()]
ALERT3_EXCLUDE_PUSHOVER = os.getenv("ALERT3_EXCLUDE_PUSHOVER", "false").lower() == "true"

# Alert 4 config (Gross spike/drop)
ALERT4_ENABLED = os.getenv("ALERT4_ENABLED", "true").lower() == "true"
ALERT4_THRESHOLD_PERCENT = float(os.getenv("ALERT4_THRESHOLD_PERCENT", "30"))
ALERT4_COMPARISON_PERIOD = os.getenv("ALERT4_COMPARISON_PERIOD", "1hr").lower()
ALERT4_EXCLUDE_CHANNELS = [c.strip() for c in os.getenv("ALERT4_EXCLUDE_CHANNELS", "").split(",") if c.strip()]
ALERT4_EXCLUDE_USERS = [u.strip() for u in os.getenv("ALERT4_EXCLUDE_USERS", "").split(",") if u.strip()]
ALERT4_EXCLUDE_PUSHOVER = os.getenv("ALERT4_EXCLUDE_PUSHOVER", "false").lower() == "true"

# Alert 5 config (Diff change - Gross minus Est.Traffic)
ALERT5_ENABLED = os.getenv("ALERT5_ENABLED", "true").lower() == "true"
ALERT5_THRESHOLD_PERCENT = float(os.getenv("ALERT5_THRESHOLD_PERCENT", "30"))
ALERT5_COMPARISON_PERIOD = os.getenv("ALERT5_COMPARISON_PERIOD", "1hr").lower()
ALERT5_EXCLUDE_CHANNELS = [c.strip() for c in os.getenv("ALERT5_EXCLUDE_CHANNELS", "").split(",") if c.strip()]
ALERT5_EXCLUDE_USERS = [u.strip() for u in os.getenv("ALERT5_EXCLUDE_USERS", "").split(",") if u.strip()]
ALERT5_EXCLUDE_PUSHOVER = os.getenv("ALERT5_EXCLUDE_PUSHOVER", "false").lower() == "true"

# State-change mode: only fire alerts on state transitions (reduces noise)
STATE_CHANGE_MODE = os.getenv("STATE_CHANGE_MODE", "true").lower() == "true"

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

    alert_type: 'alert1' for threshold alerts, 'alert2' for status reports,
                'alert3' for Est.Traffic change, 'alert4' for Gross change,
                'alert5' for Diff change, None for all
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
    elif alert_type == "alert3":
        exclude_pushover = ALERT3_EXCLUDE_PUSHOVER
        exclude_channels = ALERT3_EXCLUDE_CHANNELS
        exclude_users = ALERT3_EXCLUDE_USERS
    elif alert_type == "alert4":
        exclude_pushover = ALERT4_EXCLUDE_PUSHOVER
        exclude_channels = ALERT4_EXCLUDE_CHANNELS
        exclude_users = ALERT4_EXCLUDE_USERS
    elif alert_type == "alert5":
        exclude_pushover = ALERT5_EXCLUDE_PUSHOVER
        exclude_channels = ALERT5_EXCLUDE_CHANNELS
        exclude_users = ALERT5_EXCLUDE_USERS

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


def init_db(max_retries: int = 5, retry_delay: int = 3):
    """Create tables if they don't exist (safe to call multiple times)

    Retries connection if DB isn't ready yet (common on Railway cold starts)
    """
    if not DB_ENABLED:
        return

    import psycopg2
    import time as time_module

    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(DATABASE_URL)
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

            # Create alert_state table for state-change tracking
            cur.execute("""
                CREATE TABLE IF NOT EXISTS alert_state (
                    alert_type VARCHAR(50) PRIMARY KEY,
                    last_state VARCHAR(20) NOT NULL DEFAULT 'normal',
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)

            # Initialize state for alerts 3, 4, 5 if not exists
            cur.execute("""
                INSERT INTO alert_state (alert_type, last_state)
                VALUES ('alert3', 'normal'), ('alert4', 'normal'), ('alert5', 'normal')
                ON CONFLICT (alert_type) DO NOTHING
            """)

            # Create api_keys table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id SERIAL PRIMARY KEY,
                    key VARCHAR(64) UNIQUE NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)

            # Generate 100 API keys if table is empty
            cur.execute("SELECT COUNT(*) FROM api_keys")
            key_count = cur.fetchone()[0]
            if key_count == 0:
                import secrets
                keys = [secrets.token_urlsafe(32) for _ in range(100)]
                for key in keys:
                    cur.execute("INSERT INTO api_keys (key) VALUES (%s)", (key,))
                print(f"Generated {len(keys)} API keys")

            conn.commit()
            cur.close()
            conn.close()
            print("Database tables initialized")
            return  # Success, exit the retry loop

        except psycopg2.OperationalError as e:
            # Connection failed - DB might not be ready yet
            if attempt < max_retries - 1:
                print(f"DB connection failed (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                time_module.sleep(retry_delay)
            else:
                print(f"Warning: DB init failed after {max_retries} attempts: {e}")

        except Exception as e:
            print(f"Warning: DB init failed: {e}")
            return  # Non-connection error, don't retry


def get_alert_state(alert_type: str) -> str:
    """Get the last state for an alert type from DB. Returns 'normal' if not found."""
    if not DB_ENABLED:
        return "normal"

    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT last_state FROM alert_state WHERE alert_type = %s", (alert_type,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row else "normal"
    except Exception as e:
        print(f"Warning: Failed to get alert state: {e}")
        return "normal"


def set_alert_state(alert_type: str, new_state: str):
    """Update the state for an alert type in DB."""
    if not DB_ENABLED:
        return

    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO alert_state (alert_type, last_state, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (alert_type) DO UPDATE SET last_state = %s, updated_at = NOW()
        """, (alert_type, new_state, new_state))
        conn.commit()
        cur.close()
        conn.close()
        print(f"Alert state updated: {alert_type} -> {new_state}")
    except Exception as e:
        print(f"Warning: Failed to set alert state: {e}")


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


def get_comparison_periods(comparison_period: str) -> list:
    """Get list of periods to compare against based on config value

    comparison_period: '1hr', '24hr', 'both', or 'all'
    Returns: list of period names like ['1-Hour Average'] or ['1-Hour Average', '24-Hour Average']
    """
    period_map = {
        '1hr': ['1-Hour Average'],
        '24hr': ['24-Hour Average'],
        'both': ['1-Hour Average', '24-Hour Average'],
        'all': ['1-Hour Average', '24-Hour Average']
    }
    return period_map.get(comparison_period, ['1-Hour Average'])


def calculate_percent_change(current: float, baseline: float) -> float:
    """Calculate percent change from baseline to current

    Returns positive for increase, negative for decrease
    """
    if baseline == 0:
        return 0.0
    return ((current - baseline) / abs(baseline)) * 100


def check_est_traffic_change(metrics: dict) -> bool:
    """Alert 3: Check if Est.Traffic changed by threshold % vs comparison period(s)"""
    if not ALERT3_ENABLED:
        return False

    latest = metrics.get('Latest Round', {})
    latest_est = latest.get('est_traffic')

    if latest_est is None:
        print("Alert 3: No Latest Round Est.Traffic data")
        return False

    comparison_periods = get_comparison_periods(ALERT3_COMPARISON_PERIOD)
    alerts = []
    details = []

    for period in comparison_periods:
        if period not in metrics:
            continue
        baseline_est = metrics[period].get('est_traffic')
        if baseline_est is None:
            continue

        pct_change = calculate_percent_change(latest_est, baseline_est)
        direction = "↑" if pct_change > 0 else "↓"

        if abs(pct_change) >= ALERT3_THRESHOLD_PERCENT:
            alerts.append(f"vs {period}: {direction} {abs(pct_change):.1f}% ⚠️")
        else:
            details.append(f"vs {period}: {direction} {abs(pct_change):.1f}% ✓")

    # Determine current state
    current_state = "triggered" if alerts else "normal"
    last_state = get_alert_state("alert3") if STATE_CHANGE_MODE else "normal"

    # State-change mode: only notify on transitions
    if STATE_CHANGE_MODE and current_state == last_state:
        print(f"Alert 3: State unchanged ({current_state}), skipping notification")
        return False

    if alerts:
        # Determine overall direction for narrative
        first_baseline = None
        for period in comparison_periods:
            if period in metrics and metrics[period].get('est_traffic') is not None:
                first_baseline = metrics[period]['est_traffic']
                break

        if first_baseline and latest_est > first_baseline:
            narrative = "Network traffic is spiking - more transactions flowing through."
        else:
            narrative = "Network traffic is dropping - fewer transactions flowing through."

        message_lines = [
            narrative,
            "",
            f"Latest: {latest_est} CC",
            ""
        ] + alerts
        if details:
            message_lines += [""] + details

        message = "\n".join(message_lines)
        print(f"ALERT 3 (Est.Traffic Change):\n{message}")
        send_notification(
            title=f"Canton: Est.Traffic Change >{ALERT3_THRESHOLD_PERCENT}%!",
            message=message,
            priority=1,
            alert_type="alert3"
        )
        set_alert_state("alert3", "triggered")
        return True
    else:
        # Check if returning to benchmark from triggered state
        if STATE_CHANGE_MODE and last_state == "triggered":
            message = f"Est.Traffic back within {ALERT3_THRESHOLD_PERCENT}% of benchmark.\n\nLatest: {latest_est} CC"
            print(f"ALERT 3 RETURNED TO BENCHMARK:\n{message}")
            send_notification(
                title="Canton: Est.Traffic Returned to Benchmark",
                message=message,
                priority=0,
                alert_type="alert3"
            )
            set_alert_state("alert3", "normal")
        else:
            print(f"Alert 3: Est.Traffic within {ALERT3_THRESHOLD_PERCENT}% threshold")
        return False


def check_gross_change(metrics: dict) -> bool:
    """Alert 4: Check if Gross changed by threshold % vs comparison period(s)"""
    if not ALERT4_ENABLED:
        return False

    latest = metrics.get('Latest Round', {})
    latest_gross = latest.get('gross')

    if latest_gross is None:
        print("Alert 4: No Latest Round Gross data")
        return False

    comparison_periods = get_comparison_periods(ALERT4_COMPARISON_PERIOD)
    alerts = []
    details = []

    for period in comparison_periods:
        if period not in metrics:
            continue
        baseline_gross = metrics[period].get('gross')
        if baseline_gross is None:
            continue

        pct_change = calculate_percent_change(latest_gross, baseline_gross)
        direction = "↑" if pct_change > 0 else "↓"

        if abs(pct_change) >= ALERT4_THRESHOLD_PERCENT:
            alerts.append(f"vs {period}: {direction} {abs(pct_change):.1f}% ⚠️")
        else:
            details.append(f"vs {period}: {direction} {abs(pct_change):.1f}% ✓")

    # Determine current state
    current_state = "triggered" if alerts else "normal"
    last_state = get_alert_state("alert4") if STATE_CHANGE_MODE else "normal"

    # State-change mode: only notify on transitions
    if STATE_CHANGE_MODE and current_state == last_state:
        print(f"Alert 4: State unchanged ({current_state}), skipping notification")
        return False

    if alerts:
        # Determine overall direction for narrative
        first_baseline = None
        for period in comparison_periods:
            if period in metrics and metrics[period].get('gross') is not None:
                first_baseline = metrics[period]['gross']
                break

        if first_baseline and latest_gross > first_baseline:
            narrative = "Gross revenue is up - earning more per round."
        else:
            narrative = "Gross revenue is down - earning less per round."

        message_lines = [
            narrative,
            "",
            f"Latest: {latest_gross} CC",
            ""
        ] + alerts
        if details:
            message_lines += [""] + details

        message = "\n".join(message_lines)
        print(f"ALERT 4 (Gross Change):\n{message}")
        send_notification(
            title=f"Canton: Gross Change >{ALERT4_THRESHOLD_PERCENT}%!",
            message=message,
            priority=1,
            alert_type="alert4"
        )
        set_alert_state("alert4", "triggered")
        return True
    else:
        # Check if returning to benchmark from triggered state
        if STATE_CHANGE_MODE and last_state == "triggered":
            message = f"Gross back within {ALERT4_THRESHOLD_PERCENT}% of benchmark.\n\nLatest: {latest_gross} CC"
            print(f"ALERT 4 RETURNED TO BENCHMARK:\n{message}")
            send_notification(
                title="Canton: Gross Returned to Benchmark",
                message=message,
                priority=0,
                alert_type="alert4"
            )
            set_alert_state("alert4", "normal")
        else:
            print(f"Alert 4: Gross within {ALERT4_THRESHOLD_PERCENT}% threshold")
        return False


def check_diff_change(metrics: dict) -> bool:
    """Alert 5: Check if Diff (Gross - Est.Traffic) changed by threshold % vs comparison period(s)"""
    if not ALERT5_ENABLED:
        return False

    latest = metrics.get('Latest Round', {})
    latest_gross = latest.get('gross')
    latest_est = latest.get('est_traffic')

    if latest_gross is None or latest_est is None:
        print("Alert 5: No Latest Round data")
        return False

    latest_diff = latest_gross - latest_est

    comparison_periods = get_comparison_periods(ALERT5_COMPARISON_PERIOD)
    alerts = []
    details = []

    for period in comparison_periods:
        if period not in metrics:
            continue
        baseline_gross = metrics[period].get('gross')
        baseline_est = metrics[period].get('est_traffic')
        if baseline_gross is None or baseline_est is None:
            continue

        baseline_diff = baseline_gross - baseline_est
        pct_change = calculate_percent_change(latest_diff, baseline_diff)
        direction = "↑" if pct_change > 0 else "↓"

        if abs(pct_change) >= ALERT5_THRESHOLD_PERCENT:
            alerts.append(f"vs {period} ({baseline_diff:+.2f} CC): {direction} {abs(pct_change):.1f}% ⚠️")
        else:
            details.append(f"vs {period} ({baseline_diff:+.2f} CC): {direction} {abs(pct_change):.1f}% ✓")

    # Determine current state
    current_state = "triggered" if alerts else "normal"
    last_state = get_alert_state("alert5") if STATE_CHANGE_MODE else "normal"

    # State-change mode: only notify on transitions
    if STATE_CHANGE_MODE and current_state == last_state:
        print(f"Alert 5: State unchanged ({current_state}), skipping notification")
        return False

    if alerts:
        # Determine overall direction for narrative
        first_baseline_diff = None
        for period in comparison_periods:
            if period in metrics:
                bg = metrics[period].get('gross')
                be = metrics[period].get('est_traffic')
                if bg is not None and be is not None:
                    first_baseline_diff = bg - be
                    break

        if first_baseline_diff is not None and latest_diff > first_baseline_diff:
            narrative = "Profitability improving - margin between Gross and Traffic is widening."
        else:
            narrative = "Profitability declining - margin between Gross and Traffic is shrinking."

        message_lines = [
            narrative,
            "",
            f"Latest Diff: {latest_diff:+.2f} CC",
            f"(Gross {latest_gross} - Est.Traffic {latest_est})",
            ""
        ] + alerts
        if details:
            message_lines += [""] + details

        message = "\n".join(message_lines)
        print(f"ALERT 5 (Diff Change):\n{message}")
        send_notification(
            title=f"Canton: Profitability Change >{ALERT5_THRESHOLD_PERCENT}%!",
            message=message,
            priority=1,
            alert_type="alert5"
        )
        set_alert_state("alert5", "triggered")
        return True
    else:
        # Check if returning to benchmark from triggered state
        if STATE_CHANGE_MODE and last_state == "triggered":
            message = f"Profitability back within {ALERT5_THRESHOLD_PERCENT}% of benchmark.\n\nLatest Diff: {latest_diff:+.2f} CC\n(Gross {latest_gross} - Est.Traffic {latest_est})"
            print(f"ALERT 5 RETURNED TO BENCHMARK:\n{message}")
            send_notification(
                title="Canton: Profitability Returned to Benchmark",
                message=message,
                priority=0,
                alert_type="alert5"
            )
            set_alert_state("alert5", "normal")
        else:
            print(f"Alert 5: Diff within {ALERT5_THRESHOLD_PERCENT}% threshold")
        return False


def run_change_alerts():
    """Run Alerts 3, 4, 5 (percentage change alerts)"""
    raw_text = scrape_canton_rewards()
    metrics = parse_metrics(raw_text)
    store_metrics_to_db(metrics)  # Fire-and-forget DB storage

    alert3_triggered = check_est_traffic_change(metrics)
    alert4_triggered = check_gross_change(metrics)
    alert5_triggered = check_diff_change(metrics)

    return alert3_triggered or alert4_triggered or alert5_triggered


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
