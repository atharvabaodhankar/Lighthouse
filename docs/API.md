# Lighthouse REST API Reference

The **Lighthouse REST API** is an asynchronous, high-throughput interface built with FastAPI that surfaces real-time DNS telemetry, query logs, blocking rules, client inventories, and administrative controls.

---

## 1. General Principles

### Base URL
- **Local Development**: `http://localhost:8000`
- **Live Production**: `http://3.111.211.129:8000` (Access restricted to authorized home IP via AWS Security Group)

### Headers
All JSON-accepting endpoints expect:
```http
Content-Type: application/json
Accept: application/json
```

### Standard Status Codes
| HTTP Status | Meaning | Description |
| :--- | :--- | :--- |
| `200 OK` | Success | Request processed and data returned |
| `400 Bad Request` | Validation Error | Missing required parameter or invalid payload |
| `404 Not Found` | Resource Not Found | Unrecognized route or identifier |
| `422 Unprocessable` | Schema Error | Pydantic type validation failure |
| `500 Server Error` | Internal Failure | Unhandled backend exception |

---

## 2. API Endpoints

### 2.1 Health Check

```http
GET /api/health
```

Verifies that the FastAPI process is responsive and healthy.

#### Response
```json
{
  "status": "ok",
  "app": "Lighthouse"
}
```

#### Example cURL
```bash
curl -s http://localhost:8000/api/health
```

---

### 2.2 System Summary Metrics

```http
GET /api/summary
```

Returns aggregate 24-hour DNS telemetry, blocking statistics, engine status, and latency.

#### Response Schema
```json
{
  "status": "enabled",
  "is_mock": false,
  "domains_being_blocked": 77759,
  "dns_queries_today": 14820,
  "ads_blocked_today": 3210,
  "ads_percentage_today": 21.7,
  "unique_domains": 1845,
  "queries_forwarded": 9410,
  "queries_cached": 2200,
  "clients_ever_seen": 12,
  "unique_clients": 6,
  "dns_queries_all_types": 14820,
  "reply_IP": 11610,
  "reply_NODATA": 420,
  "reply_NXDOMAIN": 2790,
  "reply_CNAME": 0,
  "avg_latency_ms": 11.4,
  "upstream_dns": "1.1.1.1 / 1.0.0.1 (Cloudflare DoH)",
  "server_region": "ap-south-1 (Mumbai)",
  "disabled_until": null
}
```

#### Fields Description
- `status` (`string`): Current blocking status (`"enabled"` or `"disabled"`).
- `domains_being_blocked` (`integer`): Total number of unique domains in the Gravity database.
- `dns_queries_today` (`integer`): Total queries processed within the rolling 24-hour window.
- `ads_blocked_today` (`integer`): Total ad/tracker queries sinkholed.
- `ads_percentage_today` (`float`): Percentage of blocked queries (`(ads_blocked / total) * 100`).
- `avg_latency_ms` (`float`): Average resolution round-trip latency in milliseconds.
- `disabled_until` (`integer | null`): Unix timestamp indicating when temporary disable expires.

---

### 2.3 Chronological Traffic Chart Data

```http
GET /api/chart
```

Fetches hourly chronological query distribution for interactive Chart.js rendering.

#### Response Schema
```json
{
  "labels": ["00:00", "01:00", "02:00", "03:00", "04:00", "05:00", "06:00", "07:00", "08:00", "09:00", "10:00", "11:00"],
  "total_queries": [450, 210, 120, 80, 65, 110, 340, 890, 1420, 1680, 1950, 1820],
  "blocked_queries": [90, 35, 18, 10, 8, 22, 68, 190, 310, 380, 420, 395]
}
```

---

### 2.4 Top Domains and Query Distribution

```http
GET /api/top-items
```

Returns the highest volume permitted destinations, top sinkholed ad/tracking services, and DNS record type breakdown.

#### Response Schema
```json
{
  "top_queries": [
    {
      "domain": "api.github.com",
      "count": 412,
      "category": "Permitted Traffic",
      "sticker": "sky"
    },
    {
      "domain": "netflix.com",
      "count": 318,
      "category": "Permitted Traffic",
      "sticker": "sky"
    }
  ],
  "top_ads": [
    {
      "domain": "fls-na.amazon.com",
      "count": 182,
      "category": "Sinkholed Ad/Tracker",
      "sticker": "pink"
    },
    {
      "domain": "app-measurement.com",
      "count": 144,
      "category": "Sinkholed Ad/Tracker",
      "sticker": "pink"
    }
  ],
  "query_types": {
    "A (IPv4)": 78.4,
    "AAAA (IPv6)": 18.2,
    "HTTPS": 3.4
  }
}
```

---

### 2.5 Guarded Devices Inventory

```http
GET /api/clients
```

Enumerates active client devices sending queries through Lighthouse.

#### Response Schema
```json
{
  "clients": [
    {
      "ip": "106.215.119.11",
      "mac": "Dynamic",
      "name": "Home Network (Airtel Broadband)",
      "type": "mobile",
      "total_queries": 8410,
      "blocked_queries": 1820,
      "block_rate": 21.6,
      "last_seen": "Active",
      "status": "Online"
    },
    {
      "ip": "172.18.0.1",
      "mac": "Dynamic",
      "name": "Mobile Private DNS (DoT / Port 853)",
      "type": "mobile",
      "total_queries": 4200,
      "blocked_queries": 940,
      "block_rate": 22.4,
      "last_seen": "Active",
      "status": "Online"
    }
  ]
}
```

---

### 2.6 Live Query Log Search & Stream

```http
GET /api/queries
```

Retrieves recent DNS resolution events with real-time filtering and search capabilities.

#### Query Parameters
| Parameter | Type | Default | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `limit` | integer | `50` | `1 <= limit <= 200` | Max queries to return |
| `filter_type` | string | `"all"` | `all`, `blocked`, `permitted` | Filter status |
| `search` | string | `""` | Max 100 characters | Substring search against domain or client |

#### Response Schema
```json
{
  "queries": [
    {
      "id": "q-10492",
      "timestamp": "12:34:56",
      "time_iso": "2026-11-02T12:34:56",
      "domain": "adservice.google.com",
      "status": "Blocked",
      "query_type": "A",
      "client_name": "Mobile Private DNS",
      "client_ip": "172.18.0.1",
      "client_type": "mobile",
      "resolved_by": "Pi-hole Gravity",
      "sticker": "pink"
    },
    {
      "id": "q-10491",
      "timestamp": "12:34:52",
      "time_iso": "2026-11-02T12:34:52",
      "domain": "cloudflare.com",
      "status": "Permitted",
      "query_type": "AAAA",
      "client_name": "Airtel Wi-Fi",
      "client_ip": "106.215.119.11",
      "client_type": "host",
      "resolved_by": "Local Cache",
      "sticker": "sky"
    }
  ]
}
```

#### Example cURL
```bash
# Fetch last 20 blocked tracker queries matching 'telemetry'
curl -s "http://localhost:8000/api/queries?limit=20&filter_type=blocked&search=telemetry"
```

---

### 2.7 Custom Filtering Rules

#### List All Rules
```http
GET /api/rules
```

#### Response
```json
{
  "blocked": [
    {
      "domain": "telemetry-test.example.com",
      "type": "exact",
      "added_at": "2026-11-02 10:15:00",
      "enabled": true,
      "comment": "Custom tracking rule"
    }
  ],
  "allowed": [
    {
      "domain": "internal-tool.company.com",
      "type": "exact",
      "added_at": "2026-11-02 09:30:00",
      "enabled": true,
      "comment": "Allow internal domain"
    }
  ]
}
```

---

#### Add a Rule
```http
POST /api/rules
```

#### Request Payload
```json
{
  "domain": "analytics.tracking-domain.com",
  "list_type": "blocked",
  "rule_type": "exact",
  "comment": "Added via Lighthouse UI"
}
```

#### Validation
- `domain` (`string`, required): Valid FQDN or regex pattern. Returns `400` if empty.
- `list_type` (`string`): `"blocked"` or `"allowed"`.
- `rule_type` (`string`): `"exact"` or `"regex"`.

#### Response
```json
{
  "success": true,
  "rule": {
    "domain": "analytics.tracking-domain.com",
    "type": "exact",
    "added_at": "2026-11-02 12:45:00",
    "enabled": true,
    "comment": "Added via Lighthouse UI"
  }
}
```

---

#### Delete a Rule
```http
DELETE /api/rules
```

#### Request Payload
```json
{
  "domain": "analytics.tracking-domain.com",
  "list_type": "blocked"
}
```

#### Response
```json
{
  "success": true
}
```

---

### 2.8 Toggle Protection Engine

```http
POST /api/toggle
```

Temporarily disables or enables Pi-hole DNS sinkholing.

#### Request Payload
```json
{
  "enable": false,
  "duration": 300
}
```
*Note: `duration` specifies seconds (e.g., `300` = 5 minutes). Pass `0` for indefinite.*

#### Response
```json
{
  "success": true,
  "status": "disabled",
  "disabled_until": 1793623500
}
```

---

### 2.9 Flush DNS Query Logs

```http
POST /api/logs/flush
```

Executes a log flush action on the underlying Pi-hole v6 FTL engine.

#### Response
```json
{
  "success": true,
  "message": "Pi-hole DNS query logs flushed successfully",
  "flushed_at": 1793620000.123
}
```

#### Example cURL
```bash
curl -s -X POST http://localhost:8000/api/logs/flush
```

---

### 2.10 Telegram Alert Dispatch & Preview

```http
POST /api/telegram/test
```

Formats and dispatches the daily privacy report to Telegram, or returns a rendered Markdown preview.

#### Request Payload
```json
{
  "bot_token": "123456789:ABCdefGhIJKlmNoPQRstuVWXyz",
  "chat_id": "987654321",
  "preview_only": false
}
```

#### Response
```json
{
  "success": true,
  "details": "Message dispatched successfully",
  "preview": "🗼 *Lighthouse Home Shield — Daily Report*\n━━━━━━━━━━━━━━━━━━━━━━\n• *Status:* 🟢 ACTIVE\n• *Total Queries (24h):* `14,820`\n• *Blocked Trackers & Ads:* `3,210` (*21.7%*)\n• *Active Devices Protected:* `6`\n• *Gravity Blocklist:* `77,759` domains\n\n🛑 *Top Blocked Threats & Trackers:*\n  1. `fls-na.amazon.com` (182 hits)\n  2. `app-measurement.com` (144 hits)\n\n⚡ *Response Latency:* ~11.4 ms\n📍 *Resolver Region:* AWS ap-south-1 (Mumbai)\n━━━━━━━━━━━━━━━━━━━━━━\n🔒 _Protected via Lighthouse Static EIP_"
}
```
