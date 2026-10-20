import tarfile
import io
import base64
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def build_user_data():
    # 1. Create compressed archive
    buf = io.BytesIO()
    def filter_pyc(tarinfo):
        if '__pycache__' in tarinfo.name or tarinfo.name.endswith('.pyc') or '.git' in tarinfo.name:
            return None
        return tarinfo

    with tarfile.open(fileobj=buf, mode='w:gz') as t:
        t.add(BASE_DIR / 'app', arcname='app', filter=filter_pyc)
        t.add(BASE_DIR / 'Dockerfile', arcname='Dockerfile')
        t.add(BASE_DIR / 'requirements.txt', arcname='requirements.txt')
        t.add(BASE_DIR / 'run.py', arcname='run.py')

    b64_data = base64.b64encode(buf.getvalue()).decode('ascii')
    print(f"Archive compressed & encoded: {len(b64_data)} bytes")

    # 2. Generate user_data.sh
    user_data_content = f"""#!/bin/bash
set -e

apt-get update -y
apt-get install -y ca-certificates curl gnupg

# --- Docker Installation ---
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo \\
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \\
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# --- Setup Directories ---
mkdir -p /opt/homewatch/pihole/etc-pihole /opt/homewatch/pihole/etc-dnsmasq.d /opt/homewatch/dashboard

# --- Unpack Dashboard Application ---
cat > /opt/homewatch/dashboard.tar.gz.b64 <<'EOF_ARCHIVE'
{b64_data}
EOF_ARCHIVE

base64 -d /opt/homewatch/dashboard.tar.gz.b64 | tar -xz -C /opt/homewatch/dashboard
rm -f /opt/homewatch/dashboard.tar.gz.b64

# --- Docker Compose Definition (Pi-hole + Lighthouse Dashboard) ---
cat > /opt/homewatch/docker-compose.yml <<'EOF'
services:
  pihole:
    image: pihole/pihole:latest
    container_name: pihole
    ports:
      - "53:53/tcp"
      - "53:53/udp"
      - "127.0.0.1:8080:80"
    environment:
      TZ: "Asia/Kolkata"
      WEBPASSWORD: "${{PIHOLE_WEBPASSWORD}}"
    volumes:
      - ./pihole/etc-pihole:/etc/pihole
      - ./pihole/etc-dnsmasq.d:/etc/dnsmasq.d
    restart: unless-stopped
    cap_add:
      - NET_ADMIN

  dashboard:
    build:
      context: ./dashboard
      dockerfile: Dockerfile
    container_name: lighthouse-dashboard
    ports:
      - "80:8000"
      - "8000:8000"
    environment:
      - PIHOLE_URL=http://pihole:80
      - PIHOLE_API_TOKEN=${{PIHOLE_WEBPASSWORD}}
      - TELEGRAM_BOT_TOKEN=${{TELEGRAM_BOT_TOKEN}}
      - TELEGRAM_CHAT_ID=${{TELEGRAM_CHAT_ID}}
      - HOST=0.0.0.0
      - PORT=8000
    depends_on:
      - pihole
    restart: unless-stopped
EOF

# Generate Pi-hole admin password
PIHOLE_PW=$(openssl rand -base64 18)
echo "PIHOLE_WEBPASSWORD=${{PIHOLE_PW}}" > /opt/homewatch/.env
echo "TELEGRAM_BOT_TOKEN=" >> /opt/homewatch/.env
echo "TELEGRAM_CHAT_ID=" >> /opt/homewatch/.env
chmod 600 /opt/homewatch/.env
echo "Pi-hole admin password: ${{PIHOLE_PW}}" > /root/pihole_password.txt
chmod 600 /root/pihole_password.txt

# Start containers
cd /opt/homewatch && docker compose --env-file .env up -d --build

# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
echo "Bootstrap complete. Lighthouse is running."
"""

    (BASE_DIR / 'user_data.sh').write_text(user_data_content, encoding='utf-8')
    print("Updated user_data.sh successfully.")


def build_tfvars(home_ip="106.215.119.11", key_path="C:/Users/baodh/.ssh/id_ed25519.pub"):
    content = f"""home_ip             = "{home_ip}"
ssh_public_key_path = "{key_path}"
aws_region          = "ap-south-1"
instance_type       = "t3.micro"
"""
    (BASE_DIR / 'terraform.tfvars').write_text(content, encoding='utf-8')
    print(f"Created terraform.tfvars with home_ip={home_ip}")

if __name__ == '__main__':
    build_user_data()
    build_tfvars()
