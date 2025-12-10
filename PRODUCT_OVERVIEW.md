# Canton Rewards Monitor - Product Overview

**Version:** 1.0
**Last Updated:** December 10, 2025
**Deployment:** https://cantaraalert-production.up.railway.app

---

## Executive Summary

Canton Rewards Monitor is an automated financial monitoring system that tracks revenue and traffic metrics from Canton Rewards (https://canton-rewards.noves.fi/) and delivers intelligent alerts via Pushover and Slack. The system features 7 configurable alert types (including multi-instance FAAM concentration monitoring and status reports), state-change notifications to reduce noise, optional PostgreSQL storage, and a REST API for programmatic access.

---

## What It Does

### Core Monitoring

**Data Source:** Scrapes https://canton-rewards.noves.fi/ using Playwright (headless Chromium)

**Metrics Tracked:**

| Metric | Description |
|--------|-------------|
| **Gross** | Gross revenue in Canton Coin (CC) |
| **Est. Traffic** | Estimated traffic cost in Canton Coin (CC) |

**Time Periods:**

| Period | Description |
|--------|-------------|
| **Latest Round** | Most recent round data |
| **1-Hour Average** | Rolling 1-hour average |
| **24-Hour Average** | Rolling 24-hour average |

---

## Alert System Architecture

### Alert Types (7 Total)

#### **Alert 1: Threshold Alerts** (Condition-Based)

**Trigger:** `Est. Traffic > Gross`

**Purpose:** Proactive warning when traffic costs exceed revenue

**Scope:** Latest Round + 1-Hour Average only (excludes 24-Hour to reduce noise)

**Priority:** High (priority=1 for Pushover)

**Configuration:**
```env
ALERT1_ENABLED=true
ALERT1_INTERVAL_MINUTES=15
ALERT1_EXCLUDE_PUSHOVER=false
ALERT1_EXCLUDE_CHANNELS=
ALERT1_EXCLUDE_USERS=
```

**Example:**
```
Canton: Est.Traffic > Gross!

Latest Round: Est.Traffic (15.23) > Gross (12.10) by 3.13 CC
1-Hour Average: Est.Traffic (14.50) > Gross (13.20) by 1.30 CC
```

---

#### **Alert 2: Status Reports** (Scheduled)

**Trigger:** Time-based (no condition)

**Purpose:** Periodic snapshot of all current values

**Scope:** All 3 time periods

**Priority:** Low (priority=0 for Pushover)

**Configuration:**
```env
ALERT2_ENABLED=true
ALERT2_INTERVAL_MINUTES=60
ALERT2_EXCLUDE_PUSHOVER=false
ALERT2_EXCLUDE_CHANNELS=
ALERT2_EXCLUDE_USERS=
```

**Example:**
```
Canton Status Report

✓ Latest Round:
   Gross: 12.53 CC
   Est.Traffic: 10.21 CC
   Diff: -2.32 CC
⚠️ 1-Hour Average:
   Gross: 8.10 CC
   Est.Traffic: 9.50 CC
   Diff: +1.40 CC
```

---

#### **Alert 3: Est.Traffic Change** (% Change Detection)

**Trigger:** Est.Traffic changes > threshold % vs comparison period

**Purpose:** Detect significant network traffic spikes or drops

**Scope:** Compares Latest Round vs 1-Hour Average (configurable: `1hr`, `24hr`, or `both`)

**Priority:** High (priority=1)

**Configuration:**
```env
ALERT3_ENABLED=true
ALERT3_THRESHOLD_PERCENT=30
ALERT3_COMPARISON_PERIOD=1hr
ALERT3_EXCLUDE_PUSHOVER=false
ALERT3_EXCLUDE_CHANNELS=
ALERT3_EXCLUDE_USERS=
```

**Example:**
```
Canton: Est.Traffic Change >30%!

Network traffic is spiking - more transactions flowing through.

Latest: 15.5 CC

vs 1-Hour Average: ↑ 35.2% ⚠️
```

---

#### **Alert 4: Gross Change** (% Change Detection)

**Trigger:** Gross revenue changes > threshold % vs comparison period

**Purpose:** Detect significant revenue spikes or drops

**Scope:** Compares Latest Round vs 1-Hour Average (configurable)

**Priority:** High (priority=1)

**Configuration:**
```env
ALERT4_ENABLED=true
ALERT4_THRESHOLD_PERCENT=30
ALERT4_COMPARISON_PERIOD=1hr
ALERT4_EXCLUDE_PUSHOVER=false
ALERT4_EXCLUDE_CHANNELS=
ALERT4_EXCLUDE_USERS=
```

**Example:**
```
Canton: Gross Change >30%!

Gross revenue is down - earning less per round.

Latest: 10.2 CC

vs 1-Hour Average: ↓ 42.1% ⚠️
```

---

#### **Alert 5: Profitability Change** (% Change Detection)

**Trigger:** Diff (Gross - Est.Traffic) changes > threshold % vs comparison period

**Purpose:** Detect margin compression or expansion

**Scope:** Compares Latest Round vs 1-Hour Average (configurable)

**Priority:** High (priority=1)

**Configuration:**
```env
ALERT5_ENABLED=true
ALERT5_THRESHOLD_PERCENT=30
ALERT5_COMPARISON_PERIOD=1hr
ALERT5_EXCLUDE_PUSHOVER=false
ALERT5_EXCLUDE_CHANNELS=
ALERT5_EXCLUDE_USERS=
```

**Example:**
```
Canton: Profitability Change >30%!

Profitability declining - margin between Gross and Traffic is shrinking.

Latest Diff: +2.50 CC
(Gross 12.5 - Est.Traffic 10.0)

vs 1-Hour Average (+5.20 CC): ↓ 51.9% ⚠️
```

---

#### **Alert 6: FAAM Concentration Monitor** (Multi-Instance, Multi-Rule)

**Trigger:** Top X providers exceed Y% of total rewards in rolling time window

**Purpose:** Monitor provider concentration risk on Canton Network

**Data Source:** FAAMView API (https://faamview-backend-production.up.railway.app)

**Scope:** Tracks AppRewardCoupons across rolling time windows (e.g., 24 hours)

**Priority:** High (priority=1) when triggered, Low (priority=0) when resolved

**Architecture:** Supports up to 10 independent instances, each monitoring multiple concentration rules

**Configuration:**
```env
# Shared API configuration
ALERT6_FAAMVIEW_API_KEY=faam_test_key_abc123def456ghi789jkl012mno345
ALERT6_FAAMVIEW_API_URL=https://faamview-backend-production.up.railway.app

# Instance 1: Personal Monitor
ALERT6_1_ENABLED=true
ALERT6_1_NAME=Personal Monitor
ALERT6_1_RULES=2:50,3:60                    # Top 2 > 50%, Top 3 > 60%
ALERT6_1_TIME_WINDOW_HOURS=24
ALERT6_1_INTERVAL_MINUTES=360               # Check every 6 hours
ALERT6_1_EXCLUDE_PUSHOVER=false             # Send to phone
ALERT6_1_EXCLUDE_CHANNELS=
ALERT6_1_EXCLUDE_USERS=

# Instance 2: Trading Desk Monitor
ALERT6_2_ENABLED=false
ALERT6_2_NAME=Trading Desk Monitor
ALERT6_2_RULES=5:75,10:90                   # Top 5 > 75%, Top 10 > 90%
ALERT6_2_TIME_WINDOW_HOURS=24
ALERT6_2_INTERVAL_MINUTES=360
ALERT6_2_EXCLUDE_PUSHOVER=true              # No phone alerts
ALERT6_2_EXCLUDE_CHANNELS=
ALERT6_2_EXCLUDE_USERS=
```

**Use Cases:**
- **Instance 1:** Personal monitoring (phone) → Top 2 > 50%, Top 3 > 60%
- **Instance 2:** Trading desk (Slack #trading) → Top 5 > 75%, Top 10 > 90%
- **Instance 3:** Executive alerts (Slack #executives) → Top 2 > 50% only

**Example Notification (Multi-Rule):**
```
Personal Monitor: Concentration Alert!

Period: Dec 10, 06:00 - Dec 10, 18:00 UTC
Network Total: $9,449,838

⚠️ Top 2: 52.40% > 50% threshold
   1. cantonloop-mainnet-1: 26.05% ($2,460,654)
   2. cbtc-network: 26.35% ($2,489,832)

✓ Top 3: 58.20% < 60% threshold

✓ Top 5: 72.10% < 75% threshold
```

**How It Works:**
1. Every 6 hours (configurable), fetch provider stats from FAAMView API for rolling 24h window
2. Parse RULES string: "2:50,3:60" → [(2, 50), (3, 60)]
3. Check each rule: sum percent_of_total for top X providers vs threshold Y%
4. Send ONE notification showing ALL rules with status (⚠️ triggered, ✓ OK)
5. State-change mode: only alert on transitions (normal ↔ triggered)
6. Per-instance exclusions enable audience targeting (phone vs Slack channels/users)

**API Details:**
- Endpoint: `GET /api/v1/stats?limit={top_x}&from={time}&to={time}`
- Authentication: X-API-Key header
- Rate Limits: 60/min, 10K/day (plenty for 6-hour polling = 4 calls/day)
- Response: Pre-calculated `percent_of_total` for each provider
- Supports timestamp-based (ISO 8601) or round-based filtering

**Benefits of Multi-Instance + Multi-Rule Design:**
- **Flexibility:** Different teams monitor different thresholds independently
- **Efficiency:** One API call per instance (fetches max top_x needed across all rules)
- **Clarity:** Single notification shows complete concentration picture for that instance
- **Targeting:** Per-instance exclusions route alerts to relevant audiences
- **Scalability:** Add instances 1-10 as needed without code changes

---

#### **Alert 7: FAAM Status Reports** (Scheduled Reports)

**Trigger:** Time-based (no conditions) - scheduled concentration reports

**Purpose:** Show "what's happening" (vs Alert 6 "what's wrong")

**Data Source:** FAAMView API (same as Alert 6)

**Scope:** Configurable time window (default 1 hour for snapshots, or 24 hours for daily summaries)

**Priority:** Low (priority=0) - informational only

**Configuration:**
```env
ALERT7_ENABLED=true
ALERT7_INTERVAL_MINUTES=60              # Report every hour
ALERT7_TIME_WINDOW_HOURS=1              # Show last 1 hour (or 24 for daily)
ALERT7_SHOW_TOP_X=5,10,20               # Show top 5, 10, and 20 percentages
ALERT7_BREAKDOWN_COUNT=5                # Detailed breakdown for top 5
ALERT7_EXCLUDE_PUSHOVER=true            # Usually no phone for reports
ALERT7_EXCLUDE_CHANNELS=
ALERT7_EXCLUDE_USERS=

# Reuses Alert 6 API configuration
# ALERT6_FAAMVIEW_API_KEY and ALERT6_FAAMVIEW_API_URL
```

**Example Notification:**
```
Canton: FAAM Concentration Report

Period: Dec 10, 18:00 - Dec 10, 19:00 UTC (1h window)
Network Total: $1,245,832

Top  5:  42.15%
Top 10:  68.23%
Top 20:  87.91%

Breakdown (Top 5):
1. cantonloop-mainnet-1: 14.20% ($176,908)
2. cbtc-network: 12.85% ($160,090)
3. provider-xyz: 8.91% ($110,998)
4. node-fortress: 3.61% ($44,979)
5. canton-pool: 2.58% ($32,139)
```

**Use Cases:**
- **Hourly Snapshots:** 1-hour window, every 60 minutes → trending analysis
- **Daily Summaries:** 24-hour window, every 1440 minutes → executive reports
- **Analyst Updates:** Slack #reports channel, no phone alerts

**vs Alert 6 (Exception Mode):**

| Feature | Alert 6 (Exception) | Alert 7 (Report) |
|---------|-------------------|------------------|
| Trigger | Threshold exceeded | Time-based |
| Priority | High (1) | Low (0) |
| State-Change | Yes | No (always reports) |
| Frequency | Every 6 hours | Every 1 hour |
| Audience | #alerts, phone | #reports, no phone |
| Purpose | "Wake me when problem" | "Show me stats" |

---

## State-Change Mode (Noise Reduction)

Alerts 3, 4, 5, and 6 support **state-change mode** to prevent alert fatigue.

**Configuration:**
```env
STATE_CHANGE_MODE=true  # Default
```

**How It Works:**

| State Transition | Notification |
|------------------|--------------|
| normal → triggered | 🚨 Alert fires (e.g., "Est.Traffic Change >30%!") |
| triggered → triggered | 🔇 Silence (no repeat) |
| triggered → normal | ✅ "Returned to Benchmark" notification |
| normal → normal | 🔇 Silence |

**Database Storage:**

State is persisted in the `alert_state` table:

| alert_type | last_state | updated_at |
|------------|------------|------------|
| alert3 | triggered | 2025-11-30 10:15:00 |
| alert4 | normal | 2025-11-30 10:15:00 |
| alert5 | normal | 2025-11-30 09:45:00 |

**To Disable:** Set `STATE_CHANGE_MODE=false` (get alerts every check)

---

## Notification Channels

### Pushover (Mobile Push)

Native iOS/Android push notifications.

**Configuration:**
```env
PUSHOVER_ENABLED=true
PUSHOVER_USER_KEY=your_user_key
PUSHOVER_API_TOKEN=your_api_token
```

**Features:**
- Priority levels (high for alerts, low for status)
- Offline queuing
- Sound/vibration customization

---

### Slack

Team notifications via Slack bot.

**Configuration:**
```env
SLACK_ENABLED=false
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNELS=#alerts,#ops
SLACK_USERS=U01ABC,U02XYZ
```

**Required Scopes:**
- `chat:write` - Send to channels
- `chat:write.public` - Post without joining
- `im:write` - Send DMs

**Channel Types:**
- Public channels: Auto-post with `chat:write.public`
- Private channels: Must invite bot first (`/invite @botname`)
- DMs: Use user ID (e.g., `U01ABC123`)

---

## Per-Alert Exclusions

Fine-grained control over who receives which alerts. **Default: Everyone gets everything.**

### Use Cases

| Scenario | Configuration |
|----------|---------------|
| Status reports to Slack only (not phone) | `ALERT2_EXCLUDE_PUSHOVER=true` |
| Bob doesn't want status reports | `ALERT2_EXCLUDE_USERS=U0BOB123` |
| #ops only wants threshold alerts | `ALERT2_EXCLUDE_CHANNELS=#ops` |
| #general gets status only | `ALERT1_EXCLUDE_CHANNELS=#general` |

---

## Optional Database & API

### Database (PostgreSQL)

**Purpose:**
- Store historical metrics
- Enable REST API
- Persist alert state

**Configuration:**
```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

**Tables Created Automatically:**

| Table | Purpose |
|-------|---------|
| `metrics_raw` | Time-series metrics storage |
| `api_keys` | API authentication (100 keys auto-generated) |
| `alert_state` | State-change mode persistence |
| `column_definitions` | Schema metadata |

**If Not Set:** Alerting still works, just no historical storage or API

---

### REST API

**Base URL:** `https://cantaraalert-production.up.railway.app`

**Authentication:** API key via `X-API-Key` header or `Bearer` token

**Endpoints:**

| Endpoint | Purpose | Auth |
|----------|---------|------|
| `GET /health` | Health check | No |
| `GET /api/status` | Live current values | Yes |
| `GET /api/metrics` | Query historical data | Yes |
| `GET /api/metrics/latest` | Most recent values | Yes |
| `GET /api/schema` | Column definitions | Yes |
| `GET /api/keys` | List API keys (admin) | Yes |

**Example:**
```bash
curl -H "X-API-Key: YOUR_KEY" \
  "https://cantaraalert-production.up.railway.app/api/status"
```

**Response:**
```json
{
  "timestamp": "2025-11-27T16:51:10Z",
  "source": "canton-rewards.noves.fi",
  "metrics": {
    "latest_round": {
      "gross_cc": 22.11,
      "est_traffic_cc": 11.75
    },
    "1hr_avg": {
      "gross_cc": 22.76,
      "est_traffic_cc": 11.75
    },
    "24hr_avg": {
      "gross_cc": 16.35,
      "est_traffic_cc": 11.75
    }
  },
  "alerts": []
}
```

---

## Technical Architecture

### Tech Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.11 |
| **Web Scraping** | Playwright (headless Chromium) |
| **HTTP Client** | Requests |
| **Scheduling** | schedule library |
| **Database** | PostgreSQL (optional) |
| **Configuration** | python-dotenv |
| **Deployment** | Docker / Railway |

---

### File Structure

```
canton-monitor/
├── canton_monitor.py        # Core logic (scraping, parsing, notifications, alerts)
├── scheduler.py             # Scheduling engine + REST API server
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container configuration
├── .env                     # Environment secrets (gitignored)
├── .env.example             # Configuration template
├── FEATURES.md              # Detailed feature documentation
├── API_EXAMPLES.md          # REST API usage examples
├── PRODUCT_OVERVIEW.md      # This document
└── README.md                # Quick start
```

---

### Dependencies

```txt
playwright
python-dotenv
requests
schedule
psycopg2-binary  # If using database
```

---

## How to Add New Alert Types

The system is designed to be extensible. To add Alert 6 (or any new alert):

### Step 1: Add Configuration Variables

In `.env.example` and your `.env`:

```env
# Alert 6: Your new alert
ALERT6_ENABLED=true
ALERT6_INTERVAL_MINUTES=30
ALERT6_THRESHOLD_PERCENT=50  # If applicable
ALERT6_COMPARISON_PERIOD=1hr  # If applicable
ALERT6_EXCLUDE_PUSHOVER=false
ALERT6_EXCLUDE_CHANNELS=
ALERT6_EXCLUDE_USERS=
```

### Step 2: Load Config in canton_monitor.py

```python
# Alert 6 config
ALERT6_ENABLED = os.getenv("ALERT6_ENABLED", "true").lower() == "true"
ALERT6_THRESHOLD_PERCENT = float(os.getenv("ALERT6_THRESHOLD_PERCENT", "50"))
ALERT6_EXCLUDE_CHANNELS = [c.strip() for c in os.getenv("ALERT6_EXCLUDE_CHANNELS", "").split(",") if c.strip()]
ALERT6_EXCLUDE_USERS = [u.strip() for u in os.getenv("ALERT6_EXCLUDE_USERS", "").split(",") if u.strip()]
ALERT6_EXCLUDE_PUSHOVER = os.getenv("ALERT6_EXCLUDE_PUSHOVER", "false").lower() == "true"
```

### Step 3: Update send_notification()

Add Alert 6 exclusion logic in the `send_notification()` function:

```python
def send_notification(title: str, message: str, priority: int = 1, alert_type: str = None):
    # ... existing code ...
    elif alert_type == "alert6":
        exclude_pushover = ALERT6_EXCLUDE_PUSHOVER
        exclude_channels = ALERT6_EXCLUDE_CHANNELS
        exclude_users = ALERT6_EXCLUDE_USERS
    # ... rest of function ...
```

### Step 4: Implement Alert Logic

Create a function for your alert logic:

```python
def run_alert6():
    """Alert 6: Your custom logic"""
    if not ALERT6_ENABLED:
        return

    try:
        # 1. Scrape data
        raw_text = scrape_canton_rewards()
        metrics = parse_metrics(raw_text)

        # 2. Extract values
        latest = metrics.get("Latest Round", {})
        gross = latest.get("gross")
        est = latest.get("est_traffic")

        # 3. Check condition
        if your_condition_here:
            title = "Canton: Alert 6 Triggered!"
            message = f"Your alert message here\n\nGross: {gross}\nEst: {est}"
            send_notification(title, message, priority=1, alert_type="alert6")

            # 4. Store to database if enabled
            if DB_ENABLED:
                store_to_db(metrics)

    except Exception as e:
        print(f"Alert 6 failed: {e}")
```

### Step 5: Schedule It (scheduler.py)

Add scheduling logic in `scheduler.py`:

```python
# Import your alert function
from canton_monitor import run_alert6, ALERT6_ENABLED

# Get interval
ALERT6_INTERVAL_MINUTES = int(os.getenv("ALERT6_INTERVAL_MINUTES", "30"))

# Schedule it
if ALERT6_ENABLED:
    schedule.every(ALERT6_INTERVAL_MINUTES).minutes.do(run_alert6)
    run_alert6()  # Run immediately on startup
```

### Step 6: Update Documentation

Update `FEATURES.md` with Alert 6 details.

**That's it!** Your new alert type is now integrated with the same notification system, exclusions, and scheduling as the existing 5 alerts.

---

## Deployment

### Railway

1. Connect GitHub repository
2. Set environment variables in Railway dashboard
3. Deploy (auto-detects Dockerfile)

**Live URL:** https://cantaraalert-production.up.railway.app

---

### Docker

```bash
# Build
docker build -t canton-monitor .

# Run
docker run --env-file .env canton-monitor
```

---

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Single check
python canton_monitor.py

# Test notifications
python canton_monitor.py test

# Continuous monitoring
python scheduler.py
```

---

## Configuration Reference

### Complete .env Template

See `.env.example` for the complete configuration template with all 5 alert types, notification channels, exclusions, and optional database settings.

**Key Sections:**
1. Database (optional)
2. Notification Channels (Pushover, Slack)
3. Alert 1: Threshold Alerts
4. Alert 2: Status Reports
5. Alert 3-5: Change Alerts (Est.Traffic, Gross, Diff)
6. State-Change Mode
7. Per-Alert Exclusions

---

## Key Features Summary

| Feature | Status |
|---------|--------|
| Web scraping (Playwright) | ✅ |
| 5 independent alert types | ✅ |
| Pushover notifications | ✅ |
| Slack channel notifications | ✅ |
| Slack DM notifications | ✅ |
| State-change mode (noise reduction) | ✅ |
| Per-alert exclusions | ✅ |
| Optional PostgreSQL storage | ✅ |
| REST API with auth | ✅ |
| 100 auto-generated API keys | ✅ |
| Docker deployment | ✅ |
| Railway deployment | ✅ |
| Extensible alert system | ✅ |

---

## Use Cases

### Financial Monitoring
- Track profitability in real-time
- Alert when traffic costs exceed revenue
- Monitor margin compression

### Operational Awareness
- Detect traffic spikes (increased network activity)
- Detect revenue drops (decreased earnings)
- Periodic status reports for operations team

### Team Notifications
- Phone alerts for critical issues (Pushover)
- Slack channels for team visibility
- DMs for individual stakeholders
- Exclude specific channels/users per alert type

### Historical Analysis
- Store metrics in PostgreSQL
- Query via REST API
- Build custom dashboards
- Analyze trends over time

---

## Future Extensibility

The system is designed to easily accommodate:
- ✅ Additional alert types (Alert 6, 7, 8...)
- ✅ New data sources (different scrapers)
- ✅ Additional notification channels (email, webhooks, Discord, etc.)
- ✅ Custom comparison periods (3hr, 12hr, 7day averages)
- ✅ More complex conditions (multi-metric thresholds)
- ✅ Machine learning anomaly detection
- ✅ GraphQL API layer

The modular architecture (scraping → parsing → alert logic → notification) makes adding new features straightforward.

---

## Summary

Canton Rewards Monitor is a production-grade alerting system for financial metrics monitoring. It combines intelligent alerting (5 alert types), flexible notifications (Pushover + Slack), noise reduction (state-change mode), optional data storage (PostgreSQL), programmatic access (REST API), and extensible architecture to provide comprehensive monitoring for Canton Rewards operations.

**Key Value:**
- ✅ Proactive alerts prevent revenue loss
- ✅ State-change mode reduces alert fatigue
- ✅ Flexible per-alert exclusions fit team workflows
- ✅ REST API enables custom integrations
- ✅ Extensible design supports future growth

---

**For detailed feature descriptions, see:** `FEATURES.md`
**For API usage examples, see:** `API_EXAMPLES.md`
**For quick start, see:** `README.md`
