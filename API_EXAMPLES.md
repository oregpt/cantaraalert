# Canton Monitor API Examples

**Base URL:** `https://cantaraalert-production.up.railway.app`

## Authentication

All `/api/*` endpoints require an API key. Pass it via header:

```bash
# Option 1: X-API-Key header
curl -H "X-API-Key: YOUR_API_KEY" https://cantaraalert-production.up.railway.app/api/status

# Option 2: Bearer token
curl -H "Authorization: Bearer YOUR_API_KEY" https://cantaraalert-production.up.railway.app/api/status
```

---

## Endpoints

### 1. Health Check (No Auth Required)

```bash
curl https://cantaraalert-production.up.railway.app/health
```

**Response:**
```
OK
```

---

### 2. GET /api/status - Live Current Values

Performs a live scrape and returns current metrics with any active alerts.

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "https://cantaraalert-production.up.railway.app/api/status"
```

**Response:**
```json
{
    "timestamp": "2025-11-27T16:51:10.835403+00:00",
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

**Note:** When `est_traffic_cc > gross_cc`, the `alerts` array will contain warning objects.

---

### 3. GET /api/metrics - Query Historical Data

Query stored metrics with optional filters.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | string | Filter by source (e.g., `canton-rewards.noves.fi`) |
| `type` | string | Filter by type (e.g., `EstEarning_latest_round`) |
| `from` | ISO8601 | Start timestamp |
| `to` | ISO8601 | End timestamp |
| `limit` | int | Max rows (default: 100, max: 1000) |

**Example - Get last 5 records:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "https://cantaraalert-production.up.railway.app/api/metrics?limit=5"
```

**Response:**
```json
{
    "count": 5,
    "data": [
        {
            "id": 48,
            "obtained_timestamp": "2025-11-27T16:48:46.069754+00:00",
            "source": "canton-rewards.noves.fi",
            "type": "EstEarning_24hr_avg",
            "value1": "16.35",
            "value2": "11.67",
            "value3": null,
            "value4": null,
            "value5": null
        },
        {
            "id": 47,
            "obtained_timestamp": "2025-11-27T16:48:46.069754+00:00",
            "source": "canton-rewards.noves.fi",
            "type": "EstEarning_1hr_avg",
            "value1": "22.76",
            "value2": "11.67",
            "value3": null,
            "value4": null,
            "value5": null
        }
    ]
}
```

**Example - Filter by type:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "https://cantaraalert-production.up.railway.app/api/metrics?type=EstEarning_latest_round&limit=3"
```

**Response:**
```json
{
    "count": 3,
    "data": [
        {
            "id": 46,
            "obtained_timestamp": "2025-11-27T16:48:46.069754+00:00",
            "source": "canton-rewards.noves.fi",
            "type": "EstEarning_latest_round",
            "value1": "22.11",
            "value2": "11.67",
            "value3": null,
            "value4": null,
            "value5": null
        },
        {
            "id": 43,
            "obtained_timestamp": "2025-11-27T16:48:40.493052+00:00",
            "source": "canton-rewards.noves.fi",
            "type": "EstEarning_latest_round",
            "value1": "22.11",
            "value2": "11.67",
            "value3": null,
            "value4": null,
            "value5": null
        },
        {
            "id": 40,
            "obtained_timestamp": "2025-11-27T16:48:20.178253+00:00",
            "source": "canton-rewards.noves.fi",
            "type": "EstEarning_latest_round",
            "value1": "22.11",
            "value2": "11.67",
            "value3": null,
            "value4": null,
            "value5": null
        }
    ]
}
```

---

### 4. GET /api/metrics/latest - Most Recent Values

Get the most recent value for each source/type combination.

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "https://cantaraalert-production.up.railway.app/api/metrics/latest"
```

**Response:**
```json
{
    "count": 3,
    "data": [
        {
            "id": 47,
            "obtained_timestamp": "2025-11-27T16:48:46.069754+00:00",
            "source": "canton-rewards.noves.fi",
            "type": "EstEarning_1hr_avg",
            "value1": "22.76",
            "value2": "11.67"
        },
        {
            "id": 48,
            "obtained_timestamp": "2025-11-27T16:48:46.069754+00:00",
            "source": "canton-rewards.noves.fi",
            "type": "EstEarning_24hr_avg",
            "value1": "16.35",
            "value2": "11.67"
        },
        {
            "id": 46,
            "obtained_timestamp": "2025-11-27T16:48:46.069754+00:00",
            "source": "canton-rewards.noves.fi",
            "type": "EstEarning_latest_round",
            "value1": "22.11",
            "value2": "11.67"
        }
    ]
}
```

---

### 5. GET /api/schema - Column Definitions

Understand what each value column means for each source/type.

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "https://cantaraalert-production.up.railway.app/api/schema"
```

**Response:**
```json
{
    "count": 3,
    "data": [
        {
            "source": "canton-rewards.noves.fi",
            "type": "EstEarning_1hr_avg",
            "columns": {
                "value1": "gross_cc",
                "value2": "est_traffic_cc"
            }
        },
        {
            "source": "canton-rewards.noves.fi",
            "type": "EstEarning_24hr_avg",
            "columns": {
                "value1": "gross_cc",
                "value2": "est_traffic_cc"
            }
        },
        {
            "source": "canton-rewards.noves.fi",
            "type": "EstEarning_latest_round",
            "columns": {
                "value1": "gross_cc",
                "value2": "est_traffic_cc"
            }
        }
    ]
}
```

---

### 6. GET /api/keys - List API Keys (Admin)

List all available API keys for distribution.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | int | Max keys to return (default: 100, max: 100) |
| `offset` | int | Skip first N keys (for pagination) |

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "https://cantaraalert-production.up.railway.app/api/keys?limit=5"
```

**Response:**
```json
{
    "total": 100,
    "count": 5,
    "data": [
        {
            "id": 1,
            "key": "Zq1rgOrzjbBfHx9pyxY30ACKhsVZf_vaAHX4YE4rqsY",
            "created_at": "2025-11-27T16:48:08.853977+00:00"
        },
        {
            "id": 2,
            "key": "ZS-SZV2I1U6WwQuSGfoGND8K_isbel_QzNwE_6vmG1g",
            "created_at": "2025-11-27T16:48:08.853977+00:00"
        },
        {
            "id": 3,
            "key": "3Eg-yDfR8bbf4h78P920bb3dAs0d395rOrZM6k7qmss",
            "created_at": "2025-11-27T16:48:08.853977+00:00"
        },
        {
            "id": 4,
            "key": "gAFk9mMl49ku6sHcvqG8zteP1fEJcfTdyP7r_YfZSv0",
            "created_at": "2025-11-27T16:48:08.853977+00:00"
        },
        {
            "id": 5,
            "key": "2llOgnw7J29YoXkQAivHBp0PsjgM_bZM-PIDCyOVoms",
            "created_at": "2025-11-27T16:48:08.853977+00:00"
        }
    ]
}
```

---

## Error Responses

### 401 Unauthorized
```json
{"error": "Unauthorized - valid API key required"}
```

### 404 Not Found
```json
{"error": "Not found"}
```

### 500 Internal Server Error
```json
{"error": "Failed to get status: <error details>"}
```

### 503 Service Unavailable
```json
{"error": "Database not configured"}
```

---

## Data Schema

### Canton Rewards Metrics

| Source | Type | value1 | value2 |
|--------|------|--------|--------|
| canton-rewards.noves.fi | EstEarning_latest_round | gross_cc | est_traffic_cc |
| canton-rewards.noves.fi | EstEarning_1hr_avg | gross_cc | est_traffic_cc |
| canton-rewards.noves.fi | EstEarning_24hr_avg | gross_cc | est_traffic_cc |

- **gross_cc**: Gross revenue in Canton Coin (CC)
- **est_traffic_cc**: Estimated traffic in Canton Coin (CC)

Data is collected every 15 minutes (threshold checks) and every 60 minutes (status reports).
