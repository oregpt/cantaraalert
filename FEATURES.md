# Canton Rewards Monitor

## Product Feature Document

---

## Overview

Canton Rewards Monitor is an automated monitoring tool that tracks financial metrics from the Canton Rewards platform (https://canton-rewards.noves.fi/) and delivers real-time alerts and status reports via multiple notification channels.

---

## Core Functionality

### What It Monitors

The monitor scrapes the Canton Rewards website and extracts two key metrics across three time periods:

| Metric | Description |
|--------|-------------|
| **Gross** | Gross revenue in CC (Canton Coin) |
| **Est. Traffic** | Estimated traffic in CC |

| Time Period | Description |
|-------------|-------------|
| **Latest Round** | Most recent round data |
| **1-Hour Average** | Rolling 1-hour average |
| **24-Hour Average** | Rolling 24-hour average |

---

## Alert Types

### Alert 1: Threshold Alerts

**Purpose:** Proactive warning when a critical condition is met

**Trigger:** `Est. Traffic > Gross`

**Scope:** Only monitors Latest Round and 1-Hour Average (excludes 24-Hour Average to reduce noise)

**Priority:** High (priority=1 for Pushover)

**Example Notification:**
```
Canton: Est.Traffic > Gross!

Latest Round: Est.Traffic (15.23) > Gross (12.10) by 3.13 CC
1-Hour Average: Est.Traffic (14.50) > Gross (13.20) by 1.30 CC
```

---

### Alert 2: Status Reports

**Purpose:** Periodic snapshot of all current values

**Trigger:** Scheduled (no condition required)

**Scope:** All three time periods (Latest Round, 1-Hour Average, 24-Hour Average)

**Priority:** Low (priority=0 for Pushover)

**Example Notification:**
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
✓ 24-Hour Average:
   Gross: 15.00 CC
   Est.Traffic: 14.20 CC
   Diff: -0.80 CC
```

**Indicators:**
- `✓` = Healthy (Est.Traffic ≤ Gross)
- `⚠️` = Warning (Est.Traffic > Gross)

---

### Alert 3: Est.Traffic Change

**Purpose:** Detect significant spikes or drops in network traffic

**Trigger:** Est.Traffic changes by more than threshold % vs comparison period

**Scope:** Compares Latest Round against 1-Hour Average (configurable)

**Priority:** High (priority=1 for Pushover)

| Variable | Default | Description |
|----------|---------|-------------|
| `ALERT3_ENABLED` | `true` | Enable/disable |
| `ALERT3_THRESHOLD_PERCENT` | `30` | % change to trigger alert |
| `ALERT3_COMPARISON_PERIOD` | `1hr` | Compare against: `1hr`, `24hr`, or `both` |

**Example Notification:**
```
Canton: Est.Traffic Change >30%!

Network traffic is spiking - more transactions flowing through.

Latest: 15.5 CC

vs 1-Hour Average: ↑ 35.2% ⚠️
```

---

### Alert 4: Gross Change

**Purpose:** Detect significant spikes or drops in gross revenue

**Trigger:** Gross changes by more than threshold % vs comparison period

**Scope:** Compares Latest Round against 1-Hour Average (configurable)

**Priority:** High (priority=1 for Pushover)

| Variable | Default | Description |
|----------|---------|-------------|
| `ALERT4_ENABLED` | `true` | Enable/disable |
| `ALERT4_THRESHOLD_PERCENT` | `30` | % change to trigger alert |
| `ALERT4_COMPARISON_PERIOD` | `1hr` | Compare against: `1hr`, `24hr`, or `both` |

**Example Notification:**
```
Canton: Gross Change >30%!

Gross revenue is down - earning less per round.

Latest: 10.2 CC

vs 1-Hour Average: ↓ 42.1% ⚠️
```

---

### Alert 5: Profitability (Diff) Change

**Purpose:** Detect significant changes in the margin between Gross and Est.Traffic

**Trigger:** Diff (Gross - Est.Traffic) changes by more than threshold % vs comparison period

**Scope:** Compares Latest Round against 1-Hour Average (configurable)

**Priority:** High (priority=1 for Pushover)

| Variable | Default | Description |
|----------|---------|-------------|
| `ALERT5_ENABLED` | `true` | Enable/disable |
| `ALERT5_THRESHOLD_PERCENT` | `30` | % change to trigger alert |
| `ALERT5_COMPARISON_PERIOD` | `1hr` | Compare against: `1hr`, `24hr`, or `both` |

**Example Notification:**
```
Canton: Profitability Change >30%!

Profitability declining - margin between Gross and Traffic is shrinking.

Latest Diff: +2.50 CC
(Gross 12.5 - Est.Traffic 10.0)

vs 1-Hour Average (+5.20 CC): ↓ 51.9% ⚠️
```

---

### Startup Notification

**Purpose:** Confirm successful deployment and show active configuration

**Trigger:** On application start

**Scope:** Sent to all channels (no exclusions)

**Example Notification:**
```
Canton Monitor Started

Running on Railway.
• Threshold alerts: every 15 mins
• Status reports: every 60 mins
```

---

## State-Change Mode (Noise Reduction)

Alerts 3, 4, and 5 support **state-change mode** to reduce notification noise. Instead of firing every time the condition is met, alerts only fire on **state transitions**.

| Variable | Default | Description |
|----------|---------|-------------|
| `STATE_CHANGE_MODE` | `true` | Only notify on state changes |

**How it works:**

| Transition | Notification |
|------------|--------------|
| normal → triggered | Alert fires (e.g., "Est.Traffic Change >30%!") |
| triggered → triggered | Silence (no repeat notifications) |
| triggered → normal | "Returned to Benchmark" notification |
| normal → normal | Silence |

**Example "Returned to Benchmark" Notification:**
```
Canton: Est.Traffic Returned to Benchmark

Est.Traffic back within 30% of benchmark.

Latest: 11.2 CC
```

**Database:** State is stored in the `alert_state` table (created automatically):

| alert_type | last_state | updated_at |
|------------|------------|------------|
| alert3 | triggered | 2025-11-30 10:15:00 |
| alert4 | normal | 2025-11-30 10:15:00 |
| alert5 | normal | 2025-11-30 09:45:00 |

**To disable** (get alerts every check): Set `STATE_CHANGE_MODE=false`

---

## Notification Channels

### Pushover (Mobile Push)

Native mobile push notifications for iOS/Android via Pushover service.

| Variable | Required | Description |
|----------|----------|-------------|
| `PUSHOVER_ENABLED` | No | Enable/disable (default: `true`) |
| `PUSHOVER_USER_KEY` | Yes* | Your Pushover user key |
| `PUSHOVER_API_TOKEN` | Yes* | Your Pushover API token |

*Required if enabled

**Features:**
- Priority levels (high for alerts, low for status reports)
- Works offline (queued until device online)
- Sound/vibration customization in Pushover app

---

### Slack

Team notifications via Slack bot.

| Variable | Required | Description |
|----------|----------|-------------|
| `SLACK_ENABLED` | No | Enable/disable (default: `false`) |
| `SLACK_BOT_TOKEN` | Yes* | Bot token (`xoxb-...`) |
| `SLACK_CHANNELS` | No | Comma-separated channel list (e.g., `#alerts,#ops`) |
| `SLACK_USERS` | No | Comma-separated user IDs for DMs (e.g., `U01ABC,U02XYZ`) |

*Required if enabled

**Required Bot Permissions (OAuth Scopes):**
| Scope | Purpose |
|-------|---------|
| `chat:write` | Send messages to channels |
| `chat:write.public` | Post to public channels without joining |
| `im:write` | Send direct messages to users |

**Channel Types:**
- Public channels: Bot can post with `chat:write.public`
- Private channels: Bot must be invited first (`/invite @botname`)
- DMs: Use user ID (e.g., `U01ABC123`) as channel value

---

## Scheduling

Both alert types run on independent, configurable schedules.

| Variable | Default | Description |
|----------|---------|-------------|
| `ALERT1_ENABLED` | `true` | Enable/disable threshold alerts |
| `ALERT1_INTERVAL_MINUTES` | `15` | Frequency of threshold checks |
| `ALERT2_ENABLED` | `true` | Enable/disable status reports |
| `ALERT2_INTERVAL_MINUTES` | `60` | Frequency of status reports |

**Behavior:**
- Both checks run immediately on startup
- Then repeat at configured intervals
- Schedules are independent (can run at different frequencies)
- Either alert type can be disabled entirely

---

## Per-Alert Exclusions

Fine-grained control over who receives which alert type. **Default: Everyone gets everything.**

### Alert 1 Exclusions (Threshold Alerts)

| Variable | Type | Description |
|----------|------|-------------|
| `ALERT1_EXCLUDE_PUSHOVER` | `true/false` | Exclude Pushover from Alert 1 |
| `ALERT1_EXCLUDE_CHANNELS` | comma-separated | Slack channels to exclude |
| `ALERT1_EXCLUDE_USERS` | comma-separated | Slack user IDs to exclude |

### Alert 2 Exclusions (Status Reports)

| Variable | Type | Description |
|----------|------|-------------|
| `ALERT2_EXCLUDE_PUSHOVER` | `true/false` | Exclude Pushover from Alert 2 |
| `ALERT2_EXCLUDE_CHANNELS` | comma-separated | Slack channels to exclude |
| `ALERT2_EXCLUDE_USERS` | comma-separated | Slack user IDs to exclude |

### Use Case Examples

| Scenario | Configuration |
|----------|---------------|
| Status reports to Slack only (not phone) | `ALERT2_EXCLUDE_PUSHOVER=true` |
| User Bob doesn't want status reports | `ALERT2_EXCLUDE_USERS=U0BOB123` |
| #ops channel only wants threshold alerts | `ALERT2_EXCLUDE_CHANNELS=#ops` |
| #general gets status only, no threshold alerts | `ALERT1_EXCLUDE_CHANNELS=#general` |
| Phone only for urgent threshold alerts | `ALERT2_EXCLUDE_PUSHOVER=true` |

---

## Technical Architecture

### Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11 |
| Web Scraping | Playwright (headless Chromium) |
| HTTP Client | Requests |
| Scheduling | schedule library |
| Configuration | python-dotenv |
| Deployment | Docker / Railway |

### File Structure

```
canton-monitor/
├── canton_monitor.py   # Core logic (scraping, parsing, notifications)
├── scheduler.py        # Scheduling engine
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container configuration
├── .env                # Environment secrets (gitignored)
├── .env.example        # Configuration template
├── FEATURES.md         # This document
└── README.md           # Quick start guide
```

### Dependencies

```
playwright
python-dotenv
requests
schedule
```

---

## Deployment

### Docker

```bash
# Build
docker build -t canton-monitor .

# Run
docker run --env-file .env canton-monitor
```

### Railway

1. Connect GitHub repository
2. Add environment variables in Railway dashboard
3. Deploy (auto-detects Dockerfile)

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

## CLI Commands

| Command | Description |
|---------|-------------|
| `python canton_monitor.py` | Run single threshold check |
| `python canton_monitor.py test` | Send test notification to all channels |
| `python scheduler.py` | Start continuous monitoring |

---

## Complete Configuration Reference

```env
# ============================================
# NOTIFICATION CHANNELS
# ============================================

# Pushover (mobile push notifications)
PUSHOVER_ENABLED=true
PUSHOVER_USER_KEY=your_user_key_here
PUSHOVER_API_TOKEN=your_api_token_here

# Slack
SLACK_ENABLED=false
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_CHANNELS=#canton-alerts,#trading-desk
SLACK_USERS=U01ABC123,U04XYZ789

# ============================================
# ALERT SCHEDULES
# ============================================

# Alert 1: Threshold alerts (when Est.Traffic > Gross)
ALERT1_ENABLED=true
ALERT1_INTERVAL_MINUTES=15

# Alert 2: Status reports (all current values)
ALERT2_ENABLED=true
ALERT2_INTERVAL_MINUTES=60

# ============================================
# EXCLUSIONS (per-alert filtering)
# ============================================
# Targets in these lists will NOT receive that alert type
# Everyone else gets everything by default

# Alert 1 exclusions (threshold alerts)
ALERT1_EXCLUDE_PUSHOVER=false
ALERT1_EXCLUDE_CHANNELS=
ALERT1_EXCLUDE_USERS=

# Alert 2 exclusions (status reports)
ALERT2_EXCLUDE_PUSHOVER=false
ALERT2_EXCLUDE_CHANNELS=
ALERT2_EXCLUDE_USERS=
```

---

## Feature Summary

| Feature | Status |
|---------|--------|
| Web scraping with Playwright | ✓ |
| Alert 1: Threshold alerts (Est.Traffic > Gross) | ✓ |
| Alert 2: Scheduled status reports | ✓ |
| Alert 3: Est.Traffic % change detection | ✓ |
| Alert 4: Gross % change detection | ✓ |
| Alert 5: Profitability (Diff) % change detection | ✓ |
| State-change mode (noise reduction) | ✓ |
| "Returned to Benchmark" notifications | ✓ |
| Pushover notifications | ✓ |
| Slack channel notifications | ✓ |
| Slack DM notifications | ✓ |
| Multi-channel support (comma-separated) | ✓ |
| Multi-user DM support (comma-separated) | ✓ |
| Independent alert schedules | ✓ |
| Per-alert enable/disable | ✓ |
| Per-alert channel exclusions | ✓ |
| Per-alert user exclusions | ✓ |
| Per-alert Pushover exclusions | ✓ |
| Startup notification | ✓ |
| Docker deployment | ✓ |
| Railway deployment | ✓ |
