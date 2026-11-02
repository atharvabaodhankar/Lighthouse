<div align="center">

# 🗼 Lighthouse

### Production-Grade Home DNS Shield & Traffic Intelligence Platform

[![CI Pipeline](https://github.com/your-username/lighthouse/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/lighthouse/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Pi-hole v6](https://img.shields.io/badge/Pi--hole-v6%20FTL-red.svg?logo=pihole&logoColor=white)](https://pi-hole.net/)
[![DNS-over-TLS](https://img.shields.io/badge/DNS--over--TLS-Port%20853-green.svg)](https://www.rfc-editor.org/rfc/rfc7858)
[![Terraform AWS](https://img.shields.io/badge/Terraform-AWS%20EC2-844FBA.svg?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*An executive home network shield combining Pi-hole v6 FTL, Nginx DNS-over-TLS (DoT), Terraform cloud infrastructure, and an executive Notion & Linear styled monitoring dashboard.*

[Live Deployment](#live-production-instance) • [Features](#key-features) • [Architecture](#system-architecture) • [Quickstart](#quick-start-local-development) • [Setup Guide](docs/SETUP_GUIDE.md) • [API Reference](docs/API.md) • [Security Model](docs/SECURITY.md)

---

</div>

## Executive Summary

**Lighthouse** transforms standard home network privacy into an enterprise-grade defense perimeter. Deployed live on AWS EC2 (`ap-south-1` Mumbai) with a dedicated Elastic IP (`3.111.211.129`), Lighthouse delivers:

1. **Network-Wide Ad & Tracker Sinkholing**: Blocks **77,759+** tracking, telemetry, malware, and advertising domains before requests ever leave your perimeter.
2. **Global Mobile DNS-over-TLS (DoT)**: Secure, encrypted DNS resolution on port 853 for Android (Private DNS) and iOS mobile devices traveling outside the home network.
3. **Zero Open Resolver Exposure**: Restricts UDP/TCP port 53 to your verified home IP, mathematically immunizing the server against DNS amplification DDoS abuse.
4. **Notion & Linear Companion Dashboard**: An ultra-clean, high-density interface featuring real-time Chart.js telemetry, live query streaming, on-demand Pi-hole engine log flushing, client inventory profiling, and Telegram alerts.

---

## Live Production Instance

Lighthouse is currently active and guarding production traffic:

| Service | Target / Value | Protocol / Port | Access Policy |
| :--- | :--- | :--- | :--- |
| **Encrypted Mobile DNS (DoT)** | `3-111-211-129.sslip.io` | TCP / `853` (TLS 1.2 / 1.3) | Public (`0.0.0.0/0`) with valid Let's Encrypt SSL |
| **Home Wi-Fi Standard DNS** | `3.111.211.129` | UDP / TCP `53` | Restricted to authorized Home IP (`${var.home_ip}/32`) |
| **Lighthouse Web Dashboard** | `http://3.111.211.129` | HTTP / `80`, `8000` | Restricted to authorized Home IP |
| **Upstream Resolver** | Cloudflare `1.1.1.1` | DNS-over-HTTPS (DoH) | DNSSEC Validated, Privacy Logging Disabled |
| **Average Query Latency** | **~11.4 ms** | In-memory FTL SQLite Cache | Low-latency peering in Mumbai (`ap-south-1`) |

---

## System Architecture

```
+-----------------------------------------------------------------------------------------+
|                                  CLIENT INGRESS LAYER                                   |
|                                                                                         |
|       Android / iOS Devices (DoT)                       Home Wi-Fi Router / PCs         |
|        3-111-211-129.sslip.io:853                           3.111.211.129:53            |
+-------------------|-------------------------------------------------|-------------------+
                    | TLS (Port 853)                                  | Plain DNS (Port 53)
                    v                                                 v
+-----------------------------------------------------------------------------------------+
|                               AWS EC2 (Ubuntu 22.04 LTS)                                |
|                                                                                         |
|   +---------------------------------------------------------------------------------+   |
|   | AWS Security Group: Port 853 (Public) | Port 53, 8000, 22 (Restricted Home IP)   |   |
|   +----------------------------------------+----------------------------------------+   |
|                                            |                                            |
|                                            v                                            |
|   +---------------------------------------------------------------------------------+   |
|   | Nginx Stream Proxy (Port 853) -> SSL Termination (Let's Encrypt TLS 1.2/1.3)     |   |
|   +----------------------------------------+----------------------------------------+   |
|                                            |                                            |
|                                            v (127.0.0.1:53)                             |
|   +------------------------------------+      +-------------------------------------+   |
|   | Docker: Pi-hole v6 FTL Engine      | <==> | Docker: Lighthouse Dashboard        |   |
|   | - 77,759+ Gravity Blocklist        | REST | - FastAPI + Jinja2 + Chart.js       |   |
|   | - NXDOMAIN Sinkhole Mode           | API  | - Notion & Linear Production UI     |   |
|   | - SQLite in-memory query engine    |      | - Rules Engine & Log Flusher        |   |
|   +-----------------+------------------+      +------------------+------------------+   |
|                     |                                            |                      |
+---------------------|--------------------------------------------|----------------------+
                      v                                            v
           Cloudflare DNS (1.1.1.1)                       Telegram Cloud API
```

*For complete architectural specifications, internal dataflows, and network topology, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).*

---

## Key Features

### 1. Notion & Linear Design System UI
- **Canvas & Surface Palette**: Obsidian slate dark mode (`#09090b`) with translucent hairlines (`rgba(255,255,255,0.08)`), alongside a warm paper light mode (`#f7f6f3`).
- **High-Density Typography**: Clean pairing of Inter and JetBrains Mono with micro-spacing and subtle contrast.
- **Glassmorphic Navigation**: Sticky header with real-time sync beacons, breadcrumbs, single-source navigation sidebar, and responsive mobile drawer.

### 2. Live Query Log & One-Click Log Flush
- Search, filter, and inspect DNS resolution events in real time.
- Filter by query status: `All`, `Blocked (Sinkholed)`, or `Permitted`.
- One-click **Flush Logs** action backed by `/api/logs/flush` interfacing directly with the Pi-hole v6 FTL action engine.

### 3. Guarded Devices Inventory
- Real-time client classification: Laptops, Mobile Phones, Smart TVs, IoT Sensors.
- Tracks per-device query volume, sinkholed ad count, and block efficiency percentage.

### 4. Custom Filtering Rules Engine
- Interactive Blacklist and Whitelist manager.
- Supports both exact domain matching (`ads.tiktok.com`) and wildcard regular expressions (`^(.+[-_.])??telemetry[0-9]*\..+$`).

### 5. Automated Daily Briefings via Telegram
- Dispatches formatted privacy digests to Telegram detailing total queries, blocked ad volume, top sinkholed domains, and network health.

---

## Quick Start (Local Development)

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/your-username/lighthouse.git
cd lighthouse

# Create virtual environment
python -m venv .venv

# Activate on Linux/macOS:
source .venv/bin/activate

# Activate on Windows PowerShell:
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Launch Development Server

```bash
python run.py
# or using Makefile:
make dev
```

Visit **`http://localhost:8000`** in your browser. Lighthouse will start in simulation mock mode automatically if a local Pi-hole instance is not detected.

---

## Client Setup Instructions

| Platform | Setup Method | Connection Target |
| :--- | :--- | :--- |
| **Android 9+** | Settings -> Network -> Private DNS | Hostname: `3-111-211-129.sslip.io` |
| **iOS / iPadOS** | Settings -> Wi-Fi -> DNS -> Manual | Server IP: `3.111.211.129` *(or install DoT profile)* |
| **Home Router** | WAN / LAN DHCP Server DNS Settings | Primary DNS: `3.111.211.129` |
| **macOS** | System Settings -> Network -> Wi-Fi -> DNS | Server IP: `3.111.211.129` |
| **Windows 11/10** | Settings -> Network -> Hardware properties -> DNS | IPv4 Preferred: `3.111.211.129` |
| **Linux** | `/etc/systemd/resolved.conf` | `DNS=3.111.211.129#3-111-211-129.sslip.io` |

*For step-by-step instructions with command-line snippets and router walkthroughs, see [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md).*

---

## Environment Configuration

Configure application behavior using environment variables or a `.env` file:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `PIHOLE_URL` | `http://127.0.0.1:8080` | URL to Pi-hole v6 web interface / API |
| `PIHOLE_API_TOKEN` | *empty* | Web/CLI password for Pi-hole v6 API authentication |
| `MOCK_MODE` | `false` | Force mock mode simulation regardless of engine status |
| `TELEGRAM_BOT_TOKEN`| *empty* | Telegram Bot API token for digest alerts |
| `TELEGRAM_CHAT_ID` | *empty* | Target Telegram chat/channel ID |
| `HOST` | `0.0.0.0` | Bind IP address for FastAPI server |
| `PORT` | `8000` | Port for FastAPI dashboard |
| `DEBUG` | `false` | Enable verbose debug logging |

---

## Verification & Diagnostics

Run the automated diagnostic suite to verify DNS resolution, DoT encryption, and API health:

```bash
python scripts/verify_dns.py
```

Sample output:
```text
=================================================================
[*] Lighthouse DNS Shield & Traffic Intelligence -- Diagnostic Suite
Target Server : 3.111.211.129
DoT Hostname  : 3-111-211-129.sslip.io
Dashboard URL : http://3.111.211.129
=================================================================

1. Testing UDP Port 53 (Standard DNS)...
   [PASS] Resolved in 38.2ms (RCODE=0)

2. Testing TCP Port 853 (DNS-over-TLS Encrypted)...
   [PASS] Resolved via TLS_AES_256_GCM_SHA384 in 121.5ms (RCODE=0)

3. Testing Ad-Blocking & Sinkhole (doubleclick.net via DoT)...
   [PASS] Resolved via TLS_AES_256_GCM_SHA384 in 140.9ms (RCODE=3)

4. Testing Lighthouse Dashboard REST API (/api/health)...
   [PASS] HTTP 200 in 168.7ms (app=Lighthouse)

=================================================================
[SUCCESS] Core DNS-over-TLS Shield is operational and serving queries.
=================================================================
```

### Running Automated Unit Tests

```bash
python -m unittest discover tests -v
# or using Makefile:
make test
```

---

## Repository Layout

```
Lighthouse/
├── .github/
│   └── workflows/
│       └── ci.yml               # Automated CI test & Docker build pipeline
├── app/                         # FastAPI core application
│   ├── static/
│   │   ├── css/
│   │   │   └── notion.css       # Production Notion & Linear design system
│   │   └── js/
│   │       └── app.js           # Client-side SPA controller & Chart.js engine
│   ├── templates/
│   │   └── index.html           # Single-page application shell
│   ├── config.py                # Pydantic v2 application settings
│   ├── main.py                  # API routes & static mount points
│   ├── pihole_client.py         # Async Pi-hole v6 REST client with fallback
│   └── telegram.py              # Telegram notification service
├── docs/                        # Complete technical documentation suite
│   ├── ARCHITECTURE.md          # System topology & component breakdown
│   ├── SETUP_GUIDE.md           # Client configuration guides for all OS
│   ├── API.md                   # REST API documentation & JSON schemas
│   ├── SECURITY.md              # Threat model & open resolver defense
│   └── DEPLOYMENT.md            # Terraform provisioning & SSL automation
├── scripts/
│   ├── prepare_deployment.py    # Cloud-init packer & terraform.tfvars builder
│   └── verify_dns.py            # End-to-end verification & diagnostic utility
├── tests/
│   └── test_api.py              # Automated test suite (FastAPI TestClient + unittest)
├── .env.example                 # Environment configuration template
├── .gitignore                   # Production git ignore rules
├── Dockerfile                   # Dashboard container specification
├── docker-compose.dashboard.yml # Local multi-container Docker stack
├── LICENSE                      # MIT Open Source License
├── Makefile                     # Standard developer commands
├── main.tf                      # Terraform infrastructure manifest
├── pyproject.toml               # Python packaging metadata & tool configurations
├── requirements.txt             # Application dependencies
├── run.py                       # CLI application entrypoint
├── user_data.sh                 # Cloud-init EC2 provisioning script
└── variables.tf                 # Terraform variable definitions
```

---

## Documentation Index

- [System Architecture & Topology](docs/ARCHITECTURE.md)
- [Client Setup Guide (Android, iOS, Router, Windows, Mac, Linux)](docs/SETUP_GUIDE.md)
- [REST API Reference & JSON Schemas](docs/API.md)
- [Security Model & Threat Defense](docs/SECURITY.md)
- [Production Deployment & SSL Guide](docs/DEPLOYMENT.md)
- [Contributing Guidelines](CONTRIBUTING.md)

---

## License

This project is open-source software licensed under the [MIT License](LICENSE).
