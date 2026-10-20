#!/bin/bash
set -e

apt-get update -y
apt-get install -y ca-certificates curl gnupg

# --- Docker ---
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add ubuntu user to docker group
usermod -aG docker ubuntu

# --- Free Port 53 from systemd-resolved for Pi-hole ---
sed -r -i.orig 's/#?DNSStubListener=yes/DNSStubListener=no/g' /etc/systemd/resolved.conf
systemctl restart systemd-resolved
echo 'nameserver 1.1.1.1' > /etc/resolv.conf

# --- Pi-hole Setup ---
mkdir -p /opt/homewatch/pihole/etc-pihole /opt/homewatch/pihole/etc-dnsmasq.d /opt/homewatch/dashboard
chown -R ubuntu:ubuntu /opt/homewatch

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
      WEBPASSWORD: ""
      FTLCONF_dns_listeningMode: "all"
      DNSMASQ_LISTENING: "all"
    volumes:
      - ./pihole/etc-pihole:/etc/pihole
      - ./pihole/etc-dnsmasq.d:/etc/dnsmasq.d
    restart: unless-stopped
    cap_add:
      - NET_ADMIN
EOF

# Generate random admin password
PIHOLE_PW=$(openssl rand -base64 18)
echo "PIHOLE_WEBPASSWORD=${PIHOLE_PW}" > /opt/homewatch/.env
chmod 600 /opt/homewatch/.env
echo "Pi-hole admin password: ${PIHOLE_PW}" > /root/pihole_password.txt
chmod 600 /root/pihole_password.txt
chown ubuntu:ubuntu /opt/homewatch/.env

# Start Pi-hole container
cd /opt/homewatch && docker compose --env-file .env up -d

# Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
echo "Bootstrap completed successfully."
