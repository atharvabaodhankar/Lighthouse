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

## Lighthouse Dashboard (FastAPI + Notion Design System)

The companion monitoring dashboard is built with FastAPI and an authentic **Notion Design System** interface matching [`DESIGN-notion.md`](file:///c:/Users/baodh/OneDrive/Desktop/Projects/Lighthouse/DESIGN-notion.md) (paper-soft `#f6f5f4` canvas, deep indigo `#213183` hero night band, NotionInter typography, and decorative sticker badges).

### Features
- **📊 24-Hour Traffic Analytics**: Real-time interactive charts tracking total queries vs. blocked ads and trackers.
- **📜 Live Query Log**: Searchable, filterable DNS query stream (`Ctrl+K` domain search, Blocked/Permitted filter, instant rule toggle).
- **📱 Guarded Devices Inventory**: Breakdown of household clients (laptops, phones, Apple TV, Smart TVs, IoT sensors) with query volume and block ratios.
- **🛡️ Custom Rules Management**: Visual blacklist and whitelist editor for exact and regex domain filters.
- **🔔 Telegram Daily Briefings**: Automated daily threat summaries and network digests on your phone.
- **🔄 Auto-Detect Mock / Live Mode**: If Pi-hole is not reachable locally, it automatically simulates authentic telemetry data for rapid development and testing.

### Running Locally

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the dashboard
python run.py
```
Open **`http://localhost:8000`** in your browser.

### Deploying on the EC2 Box

To run the dashboard alongside Pi-hole on your AWS EC2 instance:
```bash
docker compose -f docker-compose.dashboard.yml up -d --build
```

