# FAAMView API Specification for Canton Concentration Monitoring

**Last Updated:** December 10, 2025
**API Version:** v1
**Base URL:** `https://faamview-backend-production.up.railway.app`

---

## Overview

This document provides the API specification for monitoring provider concentration on the Canton Network Featured App Activity Marker (FAAM) rewards system.

### Use Case

Monitor when the top X providers exceed Y% of total rewards during a specific time period, enabling alerting for ecosystem concentration risks.

**Example Requirement:**
- Alert when top 2 providers exceed 50% of total rewards in the last 24 hours
- Check every 6 hours
- Use a rolling 24-hour window

---

## API Endpoint

### GET /api/v1/stats

Returns aggregated statistics for providers with flexible filtering and sorting.

**Authentication:** API Key via `X-API-Key` header

**Rate Limits:** 60 requests/minute, 10,000 requests/day per key

---

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Maximum number of providers to return (for top X queries) |
| `from` | ISO 8601 timestamp | No | Start of time range (e.g., `2025-12-09T11:00:00Z`) |
| `to` | ISO 8601 timestamp | No | End of time range (e.g., `2025-12-10T11:00:00Z`) |
| `sort_by` | string | No | Sort column: `total_amount` (default), `marker_count`, `percent_of_total` |
| `sort_order` | string | No | `asc` or `desc` (default: `desc`) |

---

## Response Format

```json
{
  "success": true,
  "data": [
    {
      "provider": "string",                    // Provider party ID
      "rank": 1,                               // Rank position
      "marker_count": 15307,                   // Total activity markers
      "total_amount": 2461692.38,              // Total reward amount (USD)
      "percent_of_total": 26.0501,             // % of rewards for this time period
      "unique_providers_count": 1,             // Distinct providers (always 1 for provider view)
      "unique_beneficiaries_count": 1          // Distinct beneficiaries
    }
  ],
  "meta": {
    "network_total": 9449838.1,                // Total rewards for time period
    "count": 2,                                // Number of results returned
    "filters": {
      "provider": null,
      "from": "2025-12-09T11:00:00Z",
      "to": "2025-12-10T11:00:00Z",
      "from_round": null,
      "to_round": null
    },
    "sort": {
      "by": "total_amount",
      "order": "desc"
    },
    "limit": 2
  }
}
```

---

## Example Use Case: Top 2 Providers, Last 24 Hours

### Request

```bash
curl -H "X-API-Key: your_api_key_here" \
  "https://faamview-backend-production.up.railway.app/api/v1/stats?limit=2&from=2025-12-09T11:00:00Z&to=2025-12-10T11:00:00Z"
```

### Actual Response (December 9-10, 2025)

```json
{
  "success": true,
  "data": [
    {
      "provider": "cantonloop-mainnet-1::12205fb70ce14897d06baec18a4b889f296c765a8325fd3d99cc084b1f980426ac12",
      "rank": 1,
      "marker_count": 15307,
      "total_amount": 2461692.38,
      "percent_of_total": 26.0501,
      "unique_providers_count": 1,
      "unique_beneficiaries_count": 1
    },
    {
      "provider": "cbtc-network::12205af3b949a04776fc48cdcc05a060f6bda2e470632935f375d1049a8546a3b262",
      "rank": 2,
      "marker_count": 125555,
      "total_amount": 1340962.95,
      "percent_of_total": 14.1903,
      "unique_providers_count": 1,
      "unique_beneficiaries_count": 5
    }
  ],
  "meta": {
    "network_total": 9449838.1,
    "count": 2,
    "filters": {
      "provider": null,
      "from": "2025-12-09T11:00:00Z",
      "to": "2025-12-10T11:00:00Z",
      "from_round": null,
      "to_round": null
    },
    "sort": {
      "by": "total_amount",
      "order": "desc"
    },
    "limit": 2
  }
}
```

### Concentration Analysis

**Top 2 Combined Percentage:**
```
26.0501% + 14.1903% = 40.2404%
```

**Interpretation:** Top 2 providers accounted for 40.24% of total rewards during this 24-hour period.

**Alert Threshold:** If this value exceeds 50%, trigger an alert.

---

## Calculating Rolling 24-Hour Windows

### Example Schedule: Check Every 6 Hours

| Check Time (UTC) | From Timestamp | To Timestamp | Window Description |
|------------------|----------------|--------------|-------------------|
| 2025-12-10 12:00 | 2025-12-09 12:00 | 2025-12-10 12:00 | Previous 24 hours |
| 2025-12-10 18:00 | 2025-12-09 18:00 | 2025-12-10 18:00 | Previous 24 hours |
| 2025-12-11 00:00 | 2025-12-10 00:00 | 2025-12-11 00:00 | Previous 24 hours |
| 2025-12-11 06:00 | 2025-12-10 06:00 | 2025-12-11 06:00 | Previous 24 hours |

### Dynamic Timestamp Calculation

To calculate the rolling 24-hour window dynamically:

```
to = current_time (now)
from = current_time - 24 hours
```

**Example in ISO 8601:**
```
to = 2025-12-10T11:00:00Z
from = 2025-12-09T11:00:00Z
```

---

## Key Data Points for Alerting

From each API response, extract:

1. **`data[].percent_of_total`** - Percentage for each provider
2. **`meta.network_total`** - Total rewards for the time period (for reference)
3. **`meta.filters.from`** and **`meta.filters.to`** - Confirmation of time window queried

### Concentration Calculation

To check if top X exceeds Y%:

```
concentration = sum(data[0..X-1].percent_of_total)

if concentration > Y:
    trigger_alert()
```

**Example (Top 2 > 50%):**
```
concentration = data[0].percent_of_total + data[1].percent_of_total
// 26.0501 + 14.1903 = 40.2404

if concentration > 50:
    trigger_alert()  // False in this example
```

---

## Additional Query Examples

### Top 3 Providers, Last 24 Hours

```bash
curl -H "X-API-Key: your_api_key_here" \
  "https://faamview-backend-production.up.railway.app/api/v1/stats?limit=3&from=2025-12-09T11:00:00Z&to=2025-12-10T11:00:00Z"
```

### Top 5 Providers, Last 7 Days

```bash
curl -H "X-API-Key: your_api_key_here" \
  "https://faamview-backend-production.up.railway.app/api/v1/stats?limit=5&from=2025-12-03T00:00:00Z&to=2025-12-10T00:00:00Z"
```

### Top 10 Providers, All Time (No Date Filter)

```bash
curl -H "X-API-Key: your_api_key_here" \
  "https://faamview-backend-production.up.railway.app/api/v1/stats?limit=10"
```

---

## Error Responses

### 401 Unauthorized (Missing or Invalid API Key)

```json
{
  "error": "Unauthorized",
  "message": "Missing X-API-Key header"
}
```

### 429 Too Many Requests (Rate Limit Exceeded)

```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded. Please try again later."
}
```

---

## API Key Request

To obtain an API key for your monitoring system, contact the FAAMView administrator.

**Test API Key (Development Only):**
```
faam_test_key_abc123def456ghi789jkl012mno345
```

**Note:** Replace with production API key before deploying your alerting system.

---

## Implementation Considerations

### Polling Frequency

Recommended: **Every 6 hours** for 24-hour concentration monitoring.

- More frequent polling acceptable (respects rate limits)
- Less frequent polling may miss concentration spikes

### Time Window Selection

- **24 hours:** Good balance between responsiveness and stability
- **12 hours:** More responsive to short-term concentration
- **7 days:** Better for long-term trend monitoring

### Threshold Selection

Common concentration thresholds:
- **50%** - High concentration risk (top 2)
- **60%** - High concentration risk (top 3)
- **75%** - Very high concentration risk (top 5)

---

## Data Freshness

The FAAMView backend syncs data from Canton Network every 5 seconds. API responses reflect near real-time data with a 60-second cache on the `/stats` endpoint.

**Expected Data Delay:** < 1 minute from Canton Network ledger

---

## Support

For API issues, questions, or production API key requests:
- **Project:** FAAMTracker / FAAMView
- **Repository:** https://github.com/oregpt/Agenticledger_App_FAAMView.git
- **Documentation:** See `EXTERNAL_API_DOCUMENTATION.md` in project root

---

## Appendix: Complete Working Example

### Request (Copy-Paste Ready)

```bash
curl -H "X-API-Key: faam_test_key_abc123def456ghi789jkl012mno345" \
  "https://faamview-backend-production.up.railway.app/api/v1/stats?limit=2&from=2025-12-09T11:00:00Z&to=2025-12-10T11:00:00Z"
```

### Response Data Points

| Field | Value | Description |
|-------|-------|-------------|
| `data[0].percent_of_total` | 26.0501 | Top provider: 26.05% of 24h rewards |
| `data[1].percent_of_total` | 14.1903 | 2nd provider: 14.19% of 24h rewards |
| **Combined** | **40.2404** | **Top 2 total: 40.24%** |
| `meta.network_total` | 9449838.1 | Total rewards in 24h period: $9.4M |

**Alert Status:** ✅ No alert (40.24% < 50% threshold)

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-10 | Initial specification created |
