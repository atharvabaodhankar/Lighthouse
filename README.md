# Homewatch — Terraform infra

Recreatable AWS setup: one EC2 box running Pi-hole (DNS resolver + logger),
locked down to your home IP only, with a static IP so your router's DNS
setting never breaks.

## What this creates
- 1× EC2 instance (`t3.micro`, Ubuntu 22.04)
- 1× Elastic IP (static, survives reboots/recreates)
- 1× Security Group — SSH (22), DNS (53 tcp/udp), HTTPS (443) — all restricted
  to your home IP, nothing public
- Pi-hole running in Docker, auto-started via cloud-init
- Tailscale installed (you run `tailscale up` once, manually, to auth it)

## Prerequisites
1. [Terraform](https://developer.hashicorp.com/terraform/install) ≥ 1.5
2. AWS account + credentials configured (`aws configure`, or env vars
   `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`)
3. An SSH key pair locally: `ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519`
4. Your home's public IP: check whatsmyip.com

## Usage
```bash
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars with your real home_ip and key path

terraform init
terraform plan
terraform apply
```

After it finishes:
```bash
terraform output server_public_ip   # → set this as your router's DNS server
terraform output ssh_command        # → SSH in to check on it
```

SSH in and grab the Pi-hole admin password:
```bash
ssh ubuntu@<server_public_ip> sudo cat /root/pihole_password.txt
```

Then authenticate Tailscale once:
```bash
ssh ubuntu@<server_public_ip>
sudo tailscale up
```

## Recreating / tearing down
```bash
terraform destroy   # tears everything down, zero AWS charges left running
terraform apply     # rebuilds identically from scratch
```

Because the Elastic IP and all config live in code, a full rebuild gives you
back the exact same setup — nothing hand-configured, nothing to remember.

## Note on free tier
`t3.micro` is free-tier eligible for your AWS account's **first 12 months
only** — after that it bills at standard rates (roughly $8–9/month). Set a
reminder, or switch `instance_type` and region to an Oracle Always-Free VM
shape later if you want zero ongoing cost.

## Lighthouse Dashboard (Production FastAPI + Notion/Linear Design System)

The companion monitoring dashboard is built with FastAPI and an authentic **Notion & Linear Production Interface**:
- **Canvas & Surface Palette**: Rich `#09090b` obsidian slate dark mode (no harsh pitch-black) with subtle translucent hairlines (`rgba(255,255,255,0.08)`), alongside a warm paper `#f7f6f3` Notion light mode.
- **Header & Navigation**: Sticky glassmorphic header with live sync beacon, breadcrumbs, unified single-source sidebar navigation, and a responsive slide-out mobile drawer.

### Features
- **📊 24-Hour Traffic Analytics**: Real-time Chart.js interactive graphs tracking total resolved queries vs. sinkholed trackers.
- **📜 Live Query Log & Flush Action**: Live streaming query log with instant search, status filtering, and a one-click **Flush Logs** feature backed by `/api/logs/flush` interfacing directly with the Pi-hole v6 action engine.
- **📱 Multi-Platform Connect & Setup Guide**: Comprehensive, interactive instructions with one-click copy buttons for:
  - **Android (Private DNS)**: `3-111-211-129.sslip.io` (DNS-over-TLS on port 853 with valid TLS certificates).
  - **Apple iOS**: Wi-Fi DNS configuration and DoT profile support.
  - **Home Wi-Fi Router**: Whole-household DHCP DNS routing via `3.111.211.129`.
  - **Windows & macOS**: Native settings and one-line PowerShell / Terminal commands.
- **📱 Guarded Devices Inventory**: Breakdown of household clients (laptops, mobile phones, Smart TVs, IoT sensors) with live query counts and block efficiency.
- **🛡️ Custom Filtering Rules**: Blacklist and whitelist editor with exact domain and wildcard regex matching.
- **🔔 Telegram Daily Briefings**: Automated daily privacy reports and test dispatch tools.

### Running Locally

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Or on Linux: source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run automated test suite
python -m unittest tests/test_api.py -v

# 4. Launch the dashboard
python run.py
```
Open **`http://localhost:8000`** in your browser.

### Deploying to Production (AWS EC2)

The live EC2 deployment runs Pi-hole v6, Nginx DNS-over-TLS (port 853), and Lighthouse Dashboard in Docker:
```bash
# SSH into the server
ssh -i ~/.ssh/id_ed25519 ubuntu@3.111.211.129

# Rebuild and restart dashboard container
cd /opt/homewatch
docker compose up -d --build dashboard
```


