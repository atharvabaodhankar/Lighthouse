# Lighthouse System Architecture

## 1. Overview & Topology

**Lighthouse** is a production-grade Home DNS Shield and Traffic Intelligence companion platform deployed live on AWS EC2 (Elastic IP: `3.111.211.129`, DoT FQDN: `3-111-211-129.sslip.io`, Region: `ap-south-1` Mumbai).

It unifies network-wide ad sinkholing, encrypted DNS-over-TLS (DoT) proxying for off-grid mobile devices, and an executive traffic monitoring dashboard styled after the Notion and Linear design systems.

```
+----------------------------------------------------------------------------------------------------+
|                                      CLIENT INGRESS LAYER                                          |
|                                                                                                    |
|    +-----------------------------+           +-----------------------------+                       |
|    |    Android / iOS Clients    |           |    Home Wi-Fi Router / PC   |                       |
|    |      (DoT Port 853)         |           |       (Standard DNS:53)     |                       |
|    |  3-111-211-129.sslip.io:853 |           |     3.111.211.129:53        |                       |
|    +--------------+--------------+           +--------------+--------------+                       |
+-------------------|-----------------------------------------|--------------------------------------+
                    | TLS (TCP 853)                           | Plaintext DNS (UDP/TCP 53)
                    | (Public Ingress: 0.0.0.0/0)             | (Restricted Ingress: HOME_IP/32)
                    v                                         v
+----------------------------------------------------------------------------------------------------+
|                                    AWS EC2 (Ubuntu 22.04 LTS)                                      |
|                                                                                                    |
|   +----------------------------------------------------+                                           |
|   | AWS Security Group (homewatch-sg)                  |                                           |
|   | - 853/tcp  : 0.0.0.0/0 (Encrypted DNS-over-TLS)    |                                           |
|   | - 53/udp/tcp: HOME_IP/32 (Zero Open Resolver)      |                                           |
|   | - 80/tcp   : 0.0.0.0/0 (ACME Let's Encrypt Cert)   |                                           |
|   | - 8000/tcp : HOME_IP/32 (Lighthouse Dashboard)     |                                           |
|   | - 22/tcp   : HOME_IP/32 (SSH Remote Access)        |                                           |
|   +-------------------------+--------------------------+                                           |
|                             |                                                                      |
|                             v                                                                      |
|   +----------------------------------------------------+                                           |
|   | Nginx Host Reverse Proxy (Stream Module)           |                                           |
|   | - Listens on: 0.0.0.0:853                          |                                           |
|   | - SSL Termination: Let's Encrypt TLS 1.2 / TLS 1.3 |                                           |
|   | - Cert FQDN: 3-111-211-129.sslip.io                |                                           |
|   | - Upstream: 127.0.0.1:53 (TCP)                     |                                           |
|   +-------------------------+--------------------------+                                           |
|                             |                                                                      |
|                             +-----------------------------------+                                  |
|                             |                                   |                                  |
|                             v                                   v                                  |
|   +---------------------------------------+   +------------------------------------------------+   |
|   | Docker Container: Pi-hole v6 FTL      |   | Docker Container: Lighthouse Dashboard         |   |
|   | (pihole/pihole:latest)                |   | (FastAPI + Jinja2 + Uvicorn)                   |   |
|   | - In-memory SQLite Gravity engine     |   | - Web UI: Notion & Linear Obsidian Palette     |   |
|   | - Port 53 (TCP/UDP) resolver          |   | - Async Client: Pi-hole v6 Session REST API    |   |
|   | - NXDOMAIN Sinkhole Mode              |   | - Telemetry: 24h query charts & top trackers   |   |
|   | - 77,759+ blocked ad/tracker domains  |   | - Rules Engine: Allow/Deny List Manager        |   |
|   | - Upstream: Cloudflare 1.1.1.1 (DoH)  |   | - Log Flusher: On-demand engine flush          |   |
|   | - REST API on: 127.0.0.1:8080         |   | - Telegram: Daily automated digests & alerts   |   |
|   +-------------------+-------------------+   +-----------------------+------------------------+   |
|                       |                                               |                            |
|                       +-----------------------------------------------+                            |
|                                       Internal REST API Bridge                                     |
+----------------------------------------------------------------------------------------------------+
                    |                                         |
                    v (Upstream DNS Forwarding)               v (Alerting)
+---------------------------------------+         +---------------------------------------+
|  Cloudflare Public Resolver (1.1.1.1)  |         |      Telegram Cloud Bot API           |
+---------------------------------------+         +---------------------------------------+
```

---

## 2. Core Architectural Components

### 2.1 Pi-hole v6 FTL Engine
- **Engine Core**: Faster-Than-Light (FTL) DNS daemon written in C/C++, running an in-memory SQLite cache for sub-millisecond query evaluation.
- **Gravity Database**: Aggregates verified community blocklists (StevenBlack, AdGuard, MalwareDomainList). Currently blocks **77,759+** malicious, tracking, and advertising domains.
- **Blocking Mode**: Configured with `FTLCONF_dns_blocking_mode: "NX"` (NXDOMAIN). Non-existent domain responses prevent client timeouts, battery drain, and broken layout rendering on mobile devices.
- **Upstream Forwarding**: High-speed, privacy-respecting upstream DNS servers (`1.1.1.1`, `1.0.0.1` Cloudflare DNS with DNSSEC validation enabled).
- **v6 REST API**: Pi-hole v6 introduces a native OpenAPI-compliant HTTP JSON API. Lighthouse communicates directly with `/api/auth`, `/api/stats/summary`, `/api/history`, `/api/stats/top_domains`, `/api/queries`, `/api/stats/top_clients`, and `/api/action/flush/logs`.

### 2.2 Nginx DNS-over-TLS (DoT) Reverse Proxy
- **Protocol**: DNS-over-TLS (RFC 7858) operating on TCP port `853`.
- **Nginx Stream Subsystem**: Nginx runs on the EC2 host with `--with-stream` and `--with-stream_ssl_module`.
- **TLS Termination**:
  - Valid Let's Encrypt certificate issued for `3-111-211-129.sslip.io`.
  - Modern TLS 1.2 and TLS 1.3 ciphers (`ECDHE-ECDSA-AES128-GCM-SHA256`, `ECDHE-RSA-AES256-GCM-SHA384`).
  - Strict SNI matching and session ticket resumption.
- **Upstream Forwarding**: Decrypted DNS requests are proxied via a local loopback TCP connection to `127.0.0.1:53` where the Pi-hole container processes the lookup.

### 2.3 Lighthouse Companion Dashboard
- **Web Application Stack**:
  - **Framework**: FastAPI (Python 3.11+) with asynchronous coroutines.
  - **Server**: Uvicorn ASGI production server running behind containerized loopback.
  - **Templates**: Jinja2 rendering single-page application shells.
  - **HTTP Client**: `httpx.AsyncClient` with connection pooling, timeout protections, and auto-session renewal.
- **Design System & Aesthetics**:
  - Authentic **Notion & Linear design system** implementation.
  - Dark Mode: Obsidian Slate (`#09090b`), translucent border hairlines (`rgba(255,255,255,0.08)`), high-density typography (Inter, JetBrains Mono).
  - Light Mode: Warm Notion paper (`#f7f6f3`), slate borders (`#e6e6e6`), rich ink headers.
  - Single-source navigation drawer, real-time Chart.js interactive telemetry, one-click code copy snippets, and live status beacons.
- **Resilience & Fallback Engine**:
  - `app/pihole_client.py` implements an automatic fallback mechanism. If the Pi-hole v6 container is restarting or unreachable during provisioning, Lighthouse seamlessly serves structured mock data without throwing 500 errors, then automatically re-establishes the live connection once the FTL engine reports healthy.

### 2.4 Cloud Infrastructure (AWS EC2 + Terraform)
- **Compute Instance**: `t3.micro` (2 vCPU, 1 GB RAM) running Ubuntu 22.04 LTS Jammy Jellyfish, located in AWS region `ap-south-1` (Mumbai) for low sub-15ms round-trip latency to Indian residential broadband and mobile cellular networks.
- **Elastic IP (EIP)**: Dedicated static public IPv4 (`3.111.211.129`). Guarantees that home router WAN DNS settings and mobile Private DNS configurations never break during EC2 reboots or instance recreation.
- **Storage**: 20 GB gp3 SSD with 3,000 baseline IOPS for fast SQLite query logging and SQLite WAL flushing.
- **Provisioning Automation**: Declarative Terraform manifests (`main.tf`, `variables.tf`, `outputs.tf`) generating an immutable cloud-init script (`user_data.sh`) that installs Docker, unpacks application code, configures system services, and bootstraps the stack automatically.

---

## 3. Dataflow & Request Lifecycles

### Scenario A: Mobile Client Query over DoT (e.g., Android Private DNS)
1. **Initiation**: Android device requests resolution for `telemetry.samsung.com` via TLS over TCP port 853 to `3-111-211-129.sslip.io`.
2. **TLS Handshake**: Nginx stream proxy on EC2 receives packet, verifies SNI, and terminates TLS using the Let's Encrypt certificate.
3. **Internal Stream**: Decrypted DNS payload is forwarded via loopback TCP to `127.0.0.1:53` (Pi-hole container).
4. **FTL Evaluation**: Pi-hole checks in-memory gravity blocklist:
   - Match found in blocklist -> Pi-hole immediately responds with `NXDOMAIN` (0.0.0.0).
   - The ad/tracker request is sinkholed instantly (< 1 ms); no remote network traffic is generated.
5. **Logging**: The query is logged in Pi-hole's SQLite database with status `GRAVITY` and client IP `172.18.0.1` (Docker bridge gateway).
6. **Telemetry Sync**: Lighthouse dashboard polls Pi-hole v6 API; the blocked query appears in real-time under Live Query Log and increments the sinkhole counter.

### Scenario B: Home Network Query over Standard DNS
1. **Initiation**: A Smart TV on home Wi-Fi requests `api.netflix.com` over UDP port 53 to static IP `3.111.211.129`.
2. **Firewall Verification**: AWS Security Group inspects packet origin. Packet IP matches `${var.home_ip}/32` -> packet accepted. (All non-home IP packets to port 53 are dropped immediately to prevent DNS amplification).
3. **Resolution**: Pi-hole evaluates domain:
   - Domain is permitted -> Checks local cache (cache hit ~0.3 ms).
   - If not cached -> Forwards upstream to Cloudflare `1.1.1.1` via encrypted upstream tunnel.
4. **Response**: Upstream answer returned to Smart TV; query cached locally with upstream TTL.

### Scenario C: Dashboard Monitoring & Log Flush Action
1. User clicks **"Flush Logs"** button in Lighthouse UI.
2. Web browser issues `POST /api/logs/flush`.
3. FastAPI endpoint calls `pihole.flush_logs()`.
4. Client acquires session SID via Pi-hole v6 `/api/auth` and executes `POST /api/action/flush/logs` to the Pi-hole FTL engine.
5. Pi-hole engine flushes active query log buffers in-memory; Lighthouse records the flush timestamp and returns `{ "success": true, "message": "Pi-hole DNS query logs flushed successfully" }`.
6. UI clears existing log table rows instantly and re-syncs state.

---

## 4. High Availability & Failure Recovery

| Potential Failure Mode | Built-in Mitigation Strategy |
| :--- | :--- |
| **Pi-hole container crash** | Docker Compose policy `restart: unless-stopped` triggers instant container restart within 2 seconds. |
| **EC2 Host reboot / maintenance** | Elastic IP (`3.111.211.129`) is static and automatically binds to the instance on boot; systemd services auto-start Docker daemon. |
| **SSL Certificate expiration** | Automated cron/systemd timer triggers Certbot renew; hooks reload Nginx stream subsystem upon certificate refresh. |
| **FTL Database corruption** | Persistent volumes stored in `/opt/homewatch/pihole/etc-pihole/` with hourly SQLite WAL checkpoints; rebuildable in 30 seconds via `docker compose down -v && docker compose up -d`. |
| **Internet transit degradation** | AWS `ap-south-1` direct peering with major Indian ISPs (Airtel, Jio, ACT, Tata) ensures sub-15ms round-trip latency. |
