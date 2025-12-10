# Adding New Alerts to Canton Monitor

**Last Updated:** December 10, 2025

---

## The Universal Alert Pattern

Every alert in Canton Monitor follows the same 4-step pattern:

```
┌─────────────────┐
│ 1. SOURCE DATA  │  Fetch data from somewhere
└────────┬────────┘
         │
┌────────▼────────┐
│ 2. CONDITIONS   │  Define thresholds/rules (from .env)
└────────┬────────┘
         │
┌────────▼────────┐
│ 3. EVALUATE     │  Check if condition is met
└────────┬────────┘
         │
┌────────▼────────┐
│ 4. ALERT        │  Notify via Pushover/Slack
└─────────────────┘
```

**This pattern works for ANY type of alert you want to add!**

---

## Data Source Options

The beauty of this pattern is that **Source Data** can come from anywhere:

| Source Type | Example | Existing Alerts |
|-------------|---------|-----------------|
| **Web Scraping** | Playwright scraping HTML | Alert 1-5 (Canton Rewards website) |
| **REST API** | HTTP GET request | Alert 6 (FAAMView API) |
| **Database Query** | PostgreSQL SELECT | (Future: Alert 7?) |
| **File System** | Read CSV/JSON file | (Future: Alert 8?) |
| **WebSocket** | Real-time stream | (Future: Alert 9?) |
| **Custom Script** | Any Python code | Anything! |

**Only the Source Data step changes. Everything else is identical.**

---

## Complete Walkthrough: Alert 6 (FAAM Concentration)

We'll build **Alert 6: FAAM Concentration Monitor** step-by-step to demonstrate the process.

### **What Alert 6 Does**

**Purpose:** Alert when top X providers control Y% of Canton Network rewards in a rolling time window.

**Example:** "Alert when top 2 providers exceed 50% of rewards in the last 24 hours"

**Data Source:** FAAMView REST API (not web scraping)

---

## Step 1: Design Your Alert

Before writing code, answer these questions:

| Question | Alert 6 Answer |
|----------|----------------|
| What condition triggers the alert? | Top X providers' combined % > threshold |
| Where does data come from? | FAAMView API (`GET /api/v1/stats`) |
| How often should it check? | Every 6 hours (configurable) |
| What time window? | Rolling 24 hours (configurable) |
| What should the notification say? | Provider names, percentages, combined total |
| High or low priority? | High (priority=1) - concentration risk |
| Should it use state-change mode? | Yes - only alert on transitions |

---

## Step 2: Add Configuration Variables

### File: `.env.example`

Add all configuration for your alert:

```env
# ============================================
# ALERT 6: FAAM Concentration Monitor
# ============================================
# Monitors Canton Network provider concentration via FAAMView API
# Alerts when top X providers control Y% of total rewards

# Enable/disable
ALERT6_ENABLED=true

# Scheduling
ALERT6_INTERVAL_MINUTES=360           # Check every 6 hours

# FAAMView API
ALERT6_FAAMVIEW_API_KEY=faam_test_key_abc123def456ghi789jkl012mno345
ALERT6_FAAMVIEW_API_URL=https://faamview-backend-production.up.railway.app

# Alert conditions
ALERT6_TOP_X=2                        # Monitor top 2 providers
ALERT6_THRESHOLD_PERCENT=50           # Alert if combined > 50%
ALERT6_TIME_WINDOW_HOURS=24           # Rolling 24-hour window

# Exclusions (who should NOT receive this alert)
ALERT6_EXCLUDE_PUSHOVER=false
ALERT6_EXCLUDE_CHANNELS=
ALERT6_EXCLUDE_USERS=
```

**Key Points:**
- ✅ Clear comments explaining what each variable does
- ✅ Sensible defaults
- ✅ Follows naming pattern: `ALERT{N}_*`
- ✅ Includes exclusion variables for filtering

---

## Step 3: Load Configuration

### File: `canton_monitor.py` (top of file)

Add config loading after other alerts:

```python
# Alert 6 config (FAAM Concentration)
ALERT6_ENABLED = os.getenv("ALERT6_ENABLED", "true").lower() == "true"
ALERT6_INTERVAL_MINUTES = int(os.getenv("ALERT6_INTERVAL_MINUTES", "360"))
ALERT6_FAAMVIEW_API_KEY = os.getenv("ALERT6_FAAMVIEW_API_KEY")
ALERT6_FAAMVIEW_API_URL = os.getenv("ALERT6_FAAMVIEW_API_URL", "https://faamview-backend-production.up.railway.app")
ALERT6_TOP_X = int(os.getenv("ALERT6_TOP_X", "2"))
ALERT6_THRESHOLD_PERCENT = float(os.getenv("ALERT6_THRESHOLD_PERCENT", "50"))
ALERT6_TIME_WINDOW_HOURS = int(os.getenv("ALERT6_TIME_WINDOW_HOURS", "24"))
ALERT6_EXCLUDE_CHANNELS = [c.strip() for c in os.getenv("ALERT6_EXCLUDE_CHANNELS", "").split(",") if c.strip()]
ALERT6_EXCLUDE_USERS = [u.strip() for u in os.getenv("ALERT6_EXCLUDE_USERS", "").split(",") if u.strip()]
ALERT6_EXCLUDE_PUSHOVER = os.getenv("ALERT6_EXCLUDE_PUSHOVER", "false").lower() == "true"
```

---

## Step 4: Update Notification System

### File: `canton_monitor.py` (in `send_notification()` function)

Add Alert 6 exclusion handling:

```python
def send_notification(title: str, message: str, priority: int = 1, alert_type: str = None):
    """Send notification to all enabled channels (Pushover + Slack) with per-alert exclusions

    alert_type: 'alert1', 'alert2', 'alert3', 'alert4', 'alert5', 'alert6', None
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
    elif alert_type == "alert6":  # NEW
        exclude_pushover = ALERT6_EXCLUDE_PUSHOVER
        exclude_channels = ALERT6_EXCLUDE_CHANNELS
        exclude_users = ALERT6_EXCLUDE_USERS

    # Send to Pushover (unless excluded)
    if not exclude_pushover:
        send_pushover(title, message, priority)

    # Send to Slack (with exclusions)
    send_slack(title, message, exclude_channels, exclude_users)
```

---

## Step 5: Implement the Alert Logic

### File: `canton_monitor.py` (add new functions)

#### 5a. Fetch Data (Source Data)

```python
def fetch_faam_stats(top_x: int, window_hours: int) -> dict:
    """Fetch provider concentration data from FAAMView API

    Returns:
        {
            "providers": [{"provider": str, "percent_of_total": float}, ...],
            "network_total": float,
            "time_window": {"from": str, "to": str}
        }
    """
    try:
        # Calculate rolling window
        now = datetime.now(timezone.utc)
        from_time = now - timedelta(hours=window_hours)

        # Build API request
        url = f"{ALERT6_FAAMVIEW_API_URL}/api/v1/stats"
        params = {
            "limit": top_x,
            "from": from_time.isoformat(),
            "to": now.isoformat()
        }
        headers = {"X-API-Key": ALERT6_FAAMVIEW_API_KEY}

        # Make request
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Extract relevant data
        return {
            "providers": data["data"],
            "network_total": data["meta"]["network_total"],
            "time_window": {
                "from": data["meta"]["filters"]["from"],
                "to": data["meta"]["filters"]["to"]
            }
        }

    except Exception as e:
        print(f"Failed to fetch FAAM stats: {e}")
        return None
```

#### 5b. Evaluate Condition

```python
def check_concentration_threshold(faam_data: dict) -> dict:
    """Check if concentration exceeds threshold

    Returns:
        {
            "triggered": bool,
            "concentration": float,
            "providers": list,
            "threshold": float
        }
    """
    if not faam_data or not faam_data.get("providers"):
        return {"triggered": False, "concentration": 0}

    # Calculate total concentration
    providers = faam_data["providers"]
    concentration = sum(p["percent_of_total"] for p in providers)

    # Check threshold
    triggered = concentration > ALERT6_THRESHOLD_PERCENT

    return {
        "triggered": triggered,
        "concentration": concentration,
        "providers": providers,
        "threshold": ALERT6_THRESHOLD_PERCENT,
        "network_total": faam_data["network_total"],
        "time_window": faam_data["time_window"]
    }
```

#### 5c. Format Notification Message

```python
def format_concentration_alert(result: dict) -> str:
    """Format concentration alert message"""
    concentration = result["concentration"]
    threshold = result["threshold"]
    providers = result["providers"]
    network_total = result["network_total"]
    time_window = result["time_window"]

    # Header
    message = f"Top {len(providers)} providers control {concentration:.2f}% of rewards!\n"
    message += f"(Threshold: {threshold}%)\n\n"

    # Time window
    from_time = datetime.fromisoformat(time_window["from"].replace('Z', '+00:00'))
    to_time = datetime.fromisoformat(time_window["to"].replace('Z', '+00:00'))
    message += f"Period: {from_time.strftime('%b %d, %H:%M')} - {to_time.strftime('%b %d, %H:%M')} UTC\n"
    message += f"Network Total: ${network_total:,.0f}\n\n"

    # Provider breakdown
    message += "Breakdown:\n"
    for i, provider in enumerate(providers, 1):
        # Shorten provider ID for readability
        provider_id = provider["provider"]
        provider_short = provider_id.split("::")[0]  # Get prefix before ::
        percent = provider["percent_of_total"]
        amount = provider["total_amount"]

        message += f"{i}. {provider_short}\n"
        message += f"   {percent:.2f}% (${amount:,.0f})\n"

    message += f"\nCombined: {concentration:.2f}%"

    return message
```

#### 5d. Main Alert Function (The 4-Step Pattern)

```python
def run_alert6():
    """Alert 6: FAAM Concentration Monitor

    Monitors Canton Network provider concentration via FAAMView API.
    Alerts when top X providers control Y% of total rewards.

    Uses state-change mode to reduce noise.
    """
    if not ALERT6_ENABLED:
        return

    # Validate configuration
    if not ALERT6_FAAMVIEW_API_KEY:
        print("Alert 6: No API key configured (ALERT6_FAAMVIEW_API_KEY)")
        return

    try:
        # ============================================
        # 1. SOURCE DATA - Fetch from API
        # ============================================
        faam_data = fetch_faam_stats(
            top_x=ALERT6_TOP_X,
            window_hours=ALERT6_TIME_WINDOW_HOURS
        )

        if not faam_data:
            print("Alert 6: Failed to fetch data")
            return

        # ============================================
        # 2. CONDITIONS - Load from config (already loaded)
        # ============================================
        # ALERT6_THRESHOLD_PERCENT = threshold
        # ALERT6_TOP_X = number of providers to monitor

        # ============================================
        # 3. EVALUATE - Check condition
        # ============================================
        result = check_concentration_threshold(faam_data)

        # State-change mode: only alert on transitions
        if STATE_CHANGE_MODE:
            last_state = get_alert_state("alert6")
            current_state = "triggered" if result["triggered"] else "normal"

            # Only alert if state changed
            if current_state != last_state:
                update_alert_state("alert6", current_state)

                if current_state == "triggered":
                    # Threshold exceeded - send alert
                    title = f"Canton: Top {ALERT6_TOP_X} Concentration >{ALERT6_THRESHOLD_PERCENT}%!"
                    message = format_concentration_alert(result)
                    send_notification(title, message, priority=1, alert_type="alert6")
                    print(f"Alert 6: TRIGGERED - {result['concentration']:.2f}% > {ALERT6_THRESHOLD_PERCENT}%")
                else:
                    # Returned to normal
                    title = "Canton: Concentration Returned to Normal"
                    message = f"Provider concentration back below {ALERT6_THRESHOLD_PERCENT}%.\n\n"
                    message += f"Current: {result['concentration']:.2f}%"
                    send_notification(title, message, priority=0, alert_type="alert6")
                    print(f"Alert 6: RESOLVED - {result['concentration']:.2f}% < {ALERT6_THRESHOLD_PERCENT}%")
            else:
                print(f"Alert 6: No state change ({current_state}) - no notification")

        else:
            # ============================================
            # 4. ALERT - Send notification (if triggered)
            # ============================================
            if result["triggered"]:
                title = f"Canton: Top {ALERT6_TOP_X} Concentration >{ALERT6_THRESHOLD_PERCENT}%!"
                message = format_concentration_alert(result)
                send_notification(title, message, priority=1, alert_type="alert6")
                print(f"Alert 6: TRIGGERED - {result['concentration']:.2f}% > {ALERT6_THRESHOLD_PERCENT}%")
            else:
                print(f"Alert 6: OK - {result['concentration']:.2f}% < {ALERT6_THRESHOLD_PERCENT}%")

        # Store to database if enabled
        if DB_ENABLED:
            store_faam_metrics(faam_data)

    except Exception as e:
        print(f"Alert 6 failed: {e}")
        import traceback
        traceback.print_exc()
```

#### 5e. Optional: Database Storage

```python
def store_faam_metrics(faam_data: dict):
    """Store FAAM concentration metrics to database (optional)"""
    if not DB_ENABLED:
        return

    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        timestamp = datetime.now(timezone.utc)

        for provider in faam_data["providers"]:
            cur.execute("""
                INSERT INTO metrics_raw (obtained_timestamp, source, type, value1, value2, value3)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                timestamp,
                "faamview-api",
                "concentration_top_provider",
                provider["provider"],
                provider["percent_of_total"],
                provider["total_amount"]
            ))

        conn.commit()
        cur.close()
        conn.close()
        print("Alert 6: Metrics stored to database")

    except Exception as e:
        print(f"Failed to store FAAM metrics: {e}")
```

---

## Step 6: Schedule the Alert

### File: `scheduler.py` (add scheduling)

Add scheduling logic for Alert 6:

```python
# At top of file, add import
from canton_monitor import (
    run_check, run_status_report, run_change_alerts, send_notification, init_db,
    scrape_canton_rewards, parse_metrics, DATABASE_URL, DB_ENABLED,
    ALERT3_ENABLED, ALERT3_THRESHOLD_PERCENT, ALERT3_COMPARISON_PERIOD,
    ALERT4_ENABLED, ALERT4_THRESHOLD_PERCENT, ALERT4_COMPARISON_PERIOD,
    ALERT5_ENABLED, ALERT5_THRESHOLD_PERCENT, ALERT5_COMPARISON_PERIOD,
    run_alert6, ALERT6_ENABLED, ALERT6_INTERVAL_MINUTES  # NEW
)

# In main() function, after other alerts:
def main():
    """Main scheduler loop"""

    # ... existing alert scheduling ...

    # Schedule Alert 6: FAAM Concentration
    if ALERT6_ENABLED:
        schedule.every(ALERT6_INTERVAL_MINUTES).minutes.do(run_alert6)
        print(f"✓ Alert 6 (FAAM Concentration): every {ALERT6_INTERVAL_MINUTES} minutes")
        run_alert6()  # Run immediately on startup

    # ... rest of scheduler ...
```

---

## Step 7: Update Documentation

### Files to Update:

#### 1. `PRODUCT_OVERVIEW.md`

Add Alert 6 section:

```markdown
#### **Alert 6: FAAM Concentration Monitor** (API-Based)

**Trigger:** Top X providers exceed Y% of total rewards in rolling time window

**Purpose:** Monitor ecosystem concentration risk

**Data Source:** FAAMView REST API (not web scraping)

**Scope:** Configurable top X providers, configurable time window

**Priority:** High (priority=1)

**Configuration:**
```env
ALERT6_ENABLED=true
ALERT6_INTERVAL_MINUTES=360
ALERT6_TOP_X=2
ALERT6_THRESHOLD_PERCENT=50
ALERT6_TIME_WINDOW_HOURS=24
ALERT6_FAAMVIEW_API_KEY=your_key
ALERT6_EXCLUDE_PUSHOVER=false
ALERT6_EXCLUDE_CHANNELS=
ALERT6_EXCLUDE_USERS=
```

**Example:**
```
Canton: Top 2 Concentration >50%!

Top 2 providers control 52.43% of rewards!
(Threshold: 50%)

Period: Dec 09, 12:00 - Dec 10, 12:00 UTC
Network Total: $9,449,838

Breakdown:
1. cantonloop-mainnet-1
   26.05% ($2,461,692)
2. cbtc-network
   26.38% ($2,493,481)

Combined: 52.43%
```
```

#### 2. `FEATURES.md`

Add detailed Alert 6 documentation following existing format.

#### 3. `.env.example`

Already added in Step 2.

#### 4. This Document (`ADDING_NEW_ALERTS.md`)

Update the example count and reference Alert 6 as a completed example.

#### 5. Create Alert Configuration Document (Optional but Recommended)

Create a standalone configuration reference document for your alert. This helps users understand all configuration options at a glance.

**Example: `ALERT6_CONFIGURATION.md`**

```markdown
# Alert 6: FAAM Concentration Monitor - Configuration Reference

## Overview

Monitors Canton Network provider concentration via FAAMView API. Alerts when top X providers control Y% of total rewards in a rolling time window.

## Required Configuration

```env
# API Configuration (required)
ALERT6_FAAMVIEW_API_KEY=your_api_key_here
ALERT6_FAAMVIEW_API_URL=https://faamview-backend-production.up.railway.app
```

## Basic Configuration

```env
# Enable/disable
ALERT6_ENABLED=true

# Scheduling
ALERT6_INTERVAL_MINUTES=360         # Check every 6 hours (recommended)

# Alert conditions
ALERT6_TOP_X=2                      # Monitor top 2 providers
ALERT6_THRESHOLD_PERCENT=50         # Alert if combined > 50%
ALERT6_TIME_WINDOW_HOURS=24         # Rolling 24-hour window
```

## Notification Exclusions

```env
# Exclude from specific notification channels
ALERT6_EXCLUDE_PUSHOVER=false       # Set true to disable Pushover
ALERT6_EXCLUDE_CHANNELS=            # Comma-separated Slack channels to exclude
ALERT6_EXCLUDE_USERS=               # Comma-separated Slack users to exclude
```

## Configuration Examples

### Example 1: High-Risk Alert (Tight Threshold)
Monitor top 2 providers, alert if they exceed 40% combined:
```env
ALERT6_ENABLED=true
ALERT6_INTERVAL_MINUTES=180         # Check every 3 hours
ALERT6_TOP_X=2
ALERT6_THRESHOLD_PERCENT=40         # Lower threshold = more sensitive
ALERT6_TIME_WINDOW_HOURS=24
```

### Example 2: Ecosystem Health Check (Loose Threshold)
Monitor top 5 providers, alert only if extreme concentration:
```env
ALERT6_ENABLED=true
ALERT6_INTERVAL_MINUTES=720         # Check every 12 hours
ALERT6_TOP_X=5
ALERT6_THRESHOLD_PERCENT=80         # Higher threshold = less sensitive
ALERT6_TIME_WINDOW_HOURS=168        # 7-day window
```

### Example 3: Phone Alerts Only (No Slack)
```env
ALERT6_ENABLED=true
ALERT6_INTERVAL_MINUTES=360
ALERT6_TOP_X=2
ALERT6_THRESHOLD_PERCENT=50
ALERT6_EXCLUDE_PUSHOVER=false       # Send to phone
ALERT6_EXCLUDE_CHANNELS=general,alerts  # Exclude all Slack channels
```

## Advanced: Multi-Instance Configuration

For multiple independent monitors with different rules:

```env
# Shared API configuration
ALERT6_FAAMVIEW_API_KEY=your_key
ALERT6_FAAMVIEW_API_URL=https://faamview-backend-production.up.railway.app

# Instance 1: Personal high-risk monitor
ALERT6_1_ENABLED=true
ALERT6_1_NAME=Personal Monitor
ALERT6_1_RULES=2:50,3:60            # Multiple rules: top 2 > 50%, top 3 > 60%
ALERT6_1_TIME_WINDOW_HOURS=24
ALERT6_1_INTERVAL_MINUTES=360
ALERT6_1_EXCLUDE_PUSHOVER=false     # Phone alerts

# Instance 2: Trading desk monitor
ALERT6_2_ENABLED=true
ALERT6_2_NAME=Trading Desk Monitor
ALERT6_2_RULES=5:75,10:90           # Different thresholds
ALERT6_2_TIME_WINDOW_HOURS=24
ALERT6_2_INTERVAL_MINUTES=360
ALERT6_2_EXCLUDE_PUSHOVER=true      # Slack only
```

## Parameter Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ALERT6_ENABLED` | boolean | false | Enable/disable alert |
| `ALERT6_INTERVAL_MINUTES` | integer | 360 | How often to check (minutes) |
| `ALERT6_TOP_X` | integer | 2 | Number of top providers to monitor |
| `ALERT6_THRESHOLD_PERCENT` | float | 50 | Alert if combined concentration > this % |
| `ALERT6_TIME_WINDOW_HOURS` | integer | 24 | Rolling time window (hours) |
| `ALERT6_FAAMVIEW_API_KEY` | string | (required) | FAAMView API authentication key |
| `ALERT6_FAAMVIEW_API_URL` | string | (see above) | FAAMView API base URL |
| `ALERT6_EXCLUDE_PUSHOVER` | boolean | false | Skip Pushover notifications |
| `ALERT6_EXCLUDE_CHANNELS` | string | "" | Comma-separated Slack channels to exclude |
| `ALERT6_EXCLUDE_USERS` | string | "" | Comma-separated Slack users to exclude |

## Troubleshooting

**No alerts firing:**
- Check `ALERT6_ENABLED=true`
- Verify `ALERT6_FAAMVIEW_API_KEY` is set
- Check logs for API errors

**Too many alerts:**
- Increase `ALERT6_THRESHOLD_PERCENT` (higher = less sensitive)
- Increase `ALERT6_INTERVAL_MINUTES` (check less frequently)
- Verify `STATE_CHANGE_MODE=true` to only alert on transitions

**API errors:**
- Verify API key is valid
- Check network connectivity
- Review rate limits (60/min, 10K/day)

## Related Documentation

- `PRODUCT_OVERVIEW.md` - Complete system architecture
- `FEATURES.md` - Detailed alert features
- `FAAMVIEW_API_SPECIFICATION.md` - API endpoint documentation
```

**Benefits of Configuration Documentation:**
- ✅ Users can quickly understand all options
- ✅ Provides copy-paste ready examples
- ✅ Reduces support questions
- ✅ Shows advanced patterns (multi-instance)
- ✅ Includes troubleshooting guidance
- ✅ Parameter reference table for quick lookup

---

## Step 8: Testing

### Test Checklist:

```bash
# 1. Test API connectivity
python -c "from canton_monitor import fetch_faam_stats; print(fetch_faam_stats(2, 24))"

# 2. Test alert logic (dry run)
python -c "from canton_monitor import run_alert6; run_alert6()"

# 3. Test with different configurations
# Edit .env and change ALERT6_THRESHOLD_PERCENT to low value (e.g., 10)
# Run again to trigger alert

# 4. Test exclusions
# Set ALERT6_EXCLUDE_PUSHOVER=true
# Verify Pushover doesn't get notification

# 5. Test state-change mode
# Run multiple times - should only alert on state transitions

# 6. Test in scheduler
python scheduler.py
# Watch logs for "Alert 6:" messages
```

---

## The Complete Pattern Visualized

```
┌──────────────────────────────────────────────────────────────┐
│                    ALERT 6: FAAM CONCENTRATION               │
└──────────────────────────────────────────────────────────────┘

1. SOURCE DATA (fetch_faam_stats)
   ↓
   API Call: GET /api/v1/stats?limit=2&from=...&to=...
   ↓
   Returns: [{"provider": "...", "percent_of_total": 26.05}, ...]

2. CONDITIONS (from .env)
   ↓
   ALERT6_THRESHOLD_PERCENT = 50
   ALERT6_TOP_X = 2

3. EVALUATE (check_concentration_threshold)
   ↓
   concentration = sum([26.05, 14.19]) = 40.24%
   triggered = 40.24 > 50.0 ? → FALSE

4. ALERT (send_notification)
   ↓
   If triggered:
     - Format message (format_concentration_alert)
     - Send to Pushover (unless excluded)
     - Send to Slack (with exclusions)
     - Store state (if state-change mode)

   State-change mode:
     - Only alert on normal → triggered
     - Only alert on triggered → normal
     - Silent if no state change
```

---

## Quick Reference: Alert Implementation Checklist

When adding a new alert, complete these steps:

### Configuration
- [ ] Add env variables to `.env.example`
- [ ] Load config in `canton_monitor.py`
- [ ] Add exclusion handling in `send_notification()`

### Logic
- [ ] Write data fetch function (Source Data)
- [ ] Write condition check function (Evaluate)
- [ ] Write message formatter
- [ ] Write main alert function (`run_alertN()`)
- [ ] (Optional) Add database storage

### Scheduling
- [ ] Import alert function in `scheduler.py`
- [ ] Add scheduling logic in `main()`
- [ ] Run immediately on startup

### Documentation
- [ ] Update `PRODUCT_OVERVIEW.md` with new alert
- [ ] Update `FEATURES.md` with detailed description
- [ ] Update `.env.example` (already done in config step)
- [ ] Add example to this guide if novel pattern

### Testing
- [ ] Test data fetch
- [ ] Test alert logic (dry run)
- [ ] Test with different thresholds
- [ ] Test exclusions work
- [ ] Test state-change mode (if applicable)
- [ ] Test in full scheduler

---

## Data Source Patterns

### Pattern 1: Web Scraping (Alerts 1-5)

```python
def fetch_data_via_scraping():
    # Use Playwright to scrape website
    raw_text = scrape_canton_rewards()
    metrics = parse_metrics(raw_text)
    return metrics
```

**Use when:** Data only available on a website, no API

---

### Pattern 2: REST API (Alert 6)

```python
def fetch_data_via_api():
    # Use requests to call API
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()
```

**Use when:** Clean API available with authentication

---

### Pattern 3: Database Query (Future Alert 7?)

```python
def fetch_data_via_database():
    # Query PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT * FROM metrics WHERE ...")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
```

**Use when:** Data already in database (historical analysis)

---

### Pattern 4: File System (Future Alert 8?)

```python
def fetch_data_via_file():
    # Read CSV/JSON file
    with open('/path/to/data.json', 'r') as f:
        data = json.load(f)
    return data
```

**Use when:** Batch processing, periodic file drops

---

### Pattern 5: Custom Script (Flexible)

```python
def fetch_data_custom():
    # Any Python code that returns data
    # Could combine multiple sources
    # Could do complex calculations
    return computed_data
```

**Use when:** Unique requirements, multiple data sources

---

## Common Pitfalls & Solutions

### Pitfall 1: Forgetting to Update send_notification()

**Problem:** New alert doesn't respect exclusions

**Solution:** Always add alert type to `send_notification()` elif chain

---

### Pitfall 2: Not Testing with Different Thresholds

**Problem:** Alert never triggers or triggers too often

**Solution:** Test with low threshold first (e.g., 1%) to verify triggering works

---

### Pitfall 3: Missing Documentation Updates

**Problem:** Future developers don't know alert exists or how to configure it

**Solution:** Follow documentation checklist - update all 3 docs

---

### Pitfall 4: Hardcoded Values

**Problem:** Can't configure alert without code changes

**Solution:** Everything should be in .env with sensible defaults

---

### Pitfall 5: Not Handling API Failures

**Problem:** Alert crashes on network error

**Solution:** Wrap API calls in try/except, return None on failure

---

## Advanced: State-Change Mode

For percentage-based or threshold alerts, implement state-change mode to reduce noise:

```python
if STATE_CHANGE_MODE:
    last_state = get_alert_state("alert6")
    current_state = "triggered" if condition_met else "normal"

    if current_state != last_state:
        update_alert_state("alert6", current_state)

        if current_state == "triggered":
            # Send "Alert triggered" notification
            send_notification(...)
        else:
            # Send "Returned to normal" notification
            send_notification(...)
```

**Benefits:**
- Get 1 alert when threshold breached
- Get 1 alert when returned to normal
- No repeated alerts while condition persists

---

## Advanced: Multi-Instance + Multi-Rule Pattern

**Alert 6 implements a hybrid multi-instance + multi-rule architecture that can be reused for future alerts requiring flexibility.**

### Use Case

Multiple teams want to monitor the same data source but with different rules and different notification audiences:

- **Personal:** Top 2 > 50%, Top 3 > 60% → Phone
- **Trading Desk:** Top 5 > 75%, Top 10 > 90% → Slack #trading
- **Executives:** Top 2 > 50% only → Slack #executives

### Architecture

**Multi-Instance:** Up to 10 independent alert instances (Alert 6.1, 6.2, 6.3, ...)

**Multi-Rule per Instance:** Each instance can check multiple rules simultaneously (e.g., "2:50,3:60,5:75")

**Single Notification:** Each instance sends ONE notification showing ALL rules with status (⚠️ triggered, ✓ OK)

### Configuration Pattern

```env
# Shared API configuration (all instances use same API)
ALERT6_FAAMVIEW_API_KEY=...
ALERT6_FAAMVIEW_API_URL=...

# Instance 1
ALERT6_1_ENABLED=true
ALERT6_1_NAME=Personal Monitor
ALERT6_1_RULES=2:50,3:60                    # Comma-separated topX:threshold
ALERT6_1_TIME_WINDOW_HOURS=24
ALERT6_1_INTERVAL_MINUTES=360
ALERT6_1_EXCLUDE_PUSHOVER=false
ALERT6_1_EXCLUDE_CHANNELS=
ALERT6_1_EXCLUDE_USERS=

# Instance 2
ALERT6_2_ENABLED=true
ALERT6_2_NAME=Trading Desk
ALERT6_2_RULES=5:75,10:90
ALERT6_2_TIME_WINDOW_HOURS=24
ALERT6_2_INTERVAL_MINUTES=360
ALERT6_2_EXCLUDE_PUSHOVER=true              # No phone
ALERT6_2_EXCLUDE_CHANNELS=
ALERT6_2_EXCLUDE_USERS=
```

### Code Pattern

**Step 1: Load instances dynamically**

```python
# Load all enabled instances (supports 1-10)
ALERT6_INSTANCES = []
for instance_id in range(1, 11):
    if os.getenv(f"ALERT6_{instance_id}_ENABLED", "false").lower() == "true":
        ALERT6_INSTANCES.append({
            "id": instance_id,
            "name": os.getenv(f"ALERT6_{instance_id}_NAME", f"Instance {instance_id}"),
            "rules": os.getenv(f"ALERT6_{instance_id}_RULES", "2:50"),
            "time_window_hours": int(os.getenv(f"ALERT6_{instance_id}_TIME_WINDOW_HOURS", "24")),
            "interval_minutes": int(os.getenv(f"ALERT6_{instance_id}_INTERVAL_MINUTES", "360")),
            "exclude_pushover": os.getenv(f"ALERT6_{instance_id}_EXCLUDE_PUSHOVER", "false").lower() == "true",
            "exclude_channels": [c.strip() for c in os.getenv(f"ALERT6_{instance_id}_EXCLUDE_CHANNELS", "").split(",") if c.strip()],
            "exclude_users": [u.strip() for u in os.getenv(f"ALERT6_{instance_id}_EXCLUDE_USERS", "").split(",") if u.strip()]
        })
```

**Step 2: Parse multi-rule format**

```python
def parse_concentration_rules(rules_string: str) -> list:
    """Parse 'topX:threshold,topX:threshold' → [(2, 50), (3, 60)]"""
    parsed_rules = []
    for rule in rules_string.split(","):
        parts = rule.strip().split(":")
        if len(parts) == 2:
            top_x = int(parts[0])
            threshold = float(parts[1])
            parsed_rules.append((top_x, threshold))
    return parsed_rules
```

**Step 3: Check all rules for instance**

```python
def run_alert6_instance(instance: dict):
    instance_id = instance["id"]
    alert_type = f"alert6_{instance_id}"

    # Parse rules
    rules = parse_concentration_rules(instance["rules"])  # [(2, 50), (3, 60)]

    # Fetch data once (use max top_x needed)
    max_top_x = max(rule[0] for rule in rules)
    faam_data = fetch_faam_stats(top_x=max_top_x, window_hours=instance["time_window_hours"])

    # Check all rules
    rule_results = check_concentration_rules(faam_data, rules)

    # Any rule triggered?
    any_triggered = any(r["triggered"] for r in rule_results)

    # Format multi-rule notification
    message = format_concentration_alert(instance["name"], rule_results, any_triggered)

    # Send with instance-specific exclusions
    send_notification(
        title=f"Canton: {instance['name']} Alert!" if any_triggered else f"Canton: {instance['name']} Resolved",
        message=message,
        priority=1 if any_triggered else 0,
        alert_type=alert_type,
        alert6_instance=instance  # Pass instance for exclusions
    )
```

**Step 4: Update send_notification() for dynamic exclusions**

```python
def send_notification(title, message, priority=1, alert_type=None, alert6_instance=None):
    # ... existing alert1-5 handling ...

    elif alert_type and alert_type.startswith("alert6_") and alert6_instance:
        # Alert 6 instances: use exclusions from instance config
        exclude_pushover = alert6_instance.get("exclude_pushover", False)
        exclude_channels = alert6_instance.get("exclude_channels", [])
        exclude_users = alert6_instance.get("exclude_users", [])
```

**Step 5: Run all instances**

```python
def run_alert6():
    """Run Alert 6: FAAM Concentration Monitor for all enabled instances"""
    for instance in ALERT6_INSTANCES:
        run_alert6_instance(instance)
```

### Benefits

- **Flexibility:** Different teams monitor different thresholds independently
- **Efficiency:** One API call per instance (not per rule)
- **Clarity:** Single notification shows complete picture with all rules
- **Targeting:** Per-instance exclusions route alerts to right audiences
- **Scalability:** Add instances 1-10 without code changes

### When to Use This Pattern

Use multi-instance + multi-rule pattern when:

1. **Multiple teams** need to monitor same data source with different thresholds
2. **Different audiences** need different alerts (phone vs Slack channels)
3. **Multiple conditions** should be checked together (show complete status in one notification)
4. **Future flexibility** is important (easy to add more instances/rules)

**Extra effort:** ~10% (parsing rules, loop checks, multi-rule formatting) vs single-rule implementation

---

## Summary

Adding a new alert to Canton Monitor is straightforward:

1. **Design** - Define trigger condition and data source
2. **Configure** - Add env variables to .env.example
3. **Load Config** - Parse config in canton_monitor.py
4. **Update Notifications** - Add alert exclusions to send_notification()
5. **Implement** - Write fetch, evaluate, format, alert functions
6. **Schedule** - Add to scheduler.py
7. **Document** - Update PRODUCT_OVERVIEW.md, FEATURES.md, create config doc
8. **Test** - Verify all scenarios

**The 4-step pattern (Source → Conditions → Evaluate → Alert) works for any alert type.**

**Reference Alert 6 (FAAM Concentration) as the complete example of adding an API-based alert.**

---

## Questions?

- **Existing alerts:** See Alert 1-5 in `canton_monitor.py`
- **API-based alert:** See Alert 6 (this guide)
- **Architecture:** See `PRODUCT_OVERVIEW.md`
- **Features:** See `FEATURES.md`
- **Project rules:** See `CLAUDE.md`

**Happy alerting!** 🚨
