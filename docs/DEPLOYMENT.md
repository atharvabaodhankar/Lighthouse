# Lighthouse Production Deployment Guide

This guide details the end-to-end production deployment of **Lighthouse** on AWS EC2 using Terraform, Docker Compose, Pi-hole v6, Nginx DNS-over-TLS (DoT), and automated Let's Encrypt SSL certificates.

---

## 1. Prerequisites

Before provisioning infrastructure, ensure you have the following installed and configured on your workstation:

1. **Terraform**: Version `>= 1.5.0` ([Download Terraform](https://developer.hashicorp.com/terraform/install)).
2. **AWS CLI**: Version `>= 2.0` configured with administrative permissions:
   ```bash
   aws configure
   ```
3. **SSH Key Pair**: An ED25519 key pair stored locally:
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -C "lighthouse-admin"
   ```
4. **Home Public IPv4 Address**: Determine your current external IP address:
   ```bash
   curl -s https://checkip.amazonaws.com
   ```

---

## 2. Preparing the Deployment Payload

Lighthouse automatically packages its application code and embeds it into cloud-init so that new instances bootstrap with zero manual file transfers.

### Run the Preparation Script
```bash
python scripts/prepare_deployment.py
```

This utility performs two automated actions:
1. Compresses `app/`, `Dockerfile`, `run.py`, and `requirements.txt` into a gzipped tarball, encodes it as base64, and injects it into `user_data.sh`.
2. Generates `terraform.tfvars` populated with your home IP and SSH public key path.

---

## 3. Provisioning AWS Infrastructure with Terraform

### 1. Initialize Terraform Providers
```bash
terraform init
```

### 2. Verify terraform.tfvars Configuration
Ensure your `terraform.tfvars` matches your environment:
```hcl
home_ip             = "YOUR_HOME_PUBLIC_IP"
ssh_public_key_path = "~/.ssh/id_ed25519.pub"
aws_region          = "ap-south-1"
instance_type       = "t3.micro"
```

### 3. Review the Execution Plan
```bash
terraform plan
```

Terraform will declare the creation of 4 resources:
- `aws_security_group.homewatch`: Fine-grained firewall rules for ports 22, 53, 80, 853, 8000.
- `aws_key_pair.homewatch`: Public key registration.
- `aws_instance.homewatch`: Ubuntu 22.04 LTS `t3.micro` instance with attached 20 GB gp3 root disk.
- `aws_eip.homewatch`: Static public Elastic IP address (`3.111.211.129`).

### 4. Apply Infrastructure
```bash
terraform apply -auto-approve
```

Upon completion, Terraform will output:
```text
Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:
server_public_ip = "3.111.211.129"
ssh_command = "ssh -i ~/.ssh/id_ed25519 ubuntu@3.111.211.129"
```

---

## 5. First-Boot Cloud-Init Lifecycle

When the EC2 instance powers on, cloud-init automatically:
1. Installs Docker CE, Containerd, and Docker Compose v2.
2. Creates `/opt/homewatch/` directories for Pi-hole and Lighthouse.
3. Unpacks the dashboard application archive.
4. Generates a secure random 24-character Pi-hole admin password.
5. Writes the password to `/root/pihole_password.txt` and `/opt/homewatch/.env`.
6. Launches the Docker Compose stack containing `pihole` and `lighthouse-dashboard`.

You can inspect the live cloud-init bootstrap progress:
```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@3.111.211.129
sudo tail -f /var/log/cloud-init-output.log
```

---

## 6. Configuring Nginx DNS-over-TLS (Port 853)

To terminate encrypted DNS requests from mobile devices on port 853, configure Nginx stream proxy on the EC2 host:

### 1. Install Nginx and Certbot
```bash
sudo apt-get update -y
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

### 2. Issue Let's Encrypt TLS Certificate
Lighthouse uses `sslip.io` wildcard DNS, which maps `3-111-211-129.sslip.io` directly to `3.111.211.129`:

```bash
sudo certbot certonly --standalone \
  --preferred-challenges http \
  -d 3-111-211-129.sslip.io \
  --agree-tos -m your-email@example.com --non-interactive
```

### 3. Configure Nginx Stream Block
Append the stream configuration to `/etc/nginx/nginx.conf`:

```nginx
stream {
    upstream pihole_dns {
        server 127.0.0.1:53;
    }

    server {
        listen 853 ssl;
        proxy_pass pihole_dns;
        proxy_timeout 20s;
        proxy_connect_timeout 2s;

        ssl_certificate /etc/letsencrypt/live/3-111-211-129.sslip.io/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/3-111-211-129.sslip.io/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_session_cache shared:DoT:10m;
        ssl_session_timeout 1d;
    }
}
```

### 4. Test and Reload Nginx
```bash
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## 7. Automated SSL Certificate Renewal

Let's Encrypt certificates are valid for 90 days. Certbot installs a systemd timer by default. To ensure Nginx reloads automatically when certificates refresh, create a renewal deploy hook:

```bash
sudo tee /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh << 'EOF'
#!/bin/bash
systemctl reload nginx
EOF
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
```

Test the renewal workflow in dry-run mode:
```bash
sudo certbot renew --dry-run
```

---

## 8. Ongoing Maintenance & Operations

### Viewing Container Status
```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@3.111.211.129
cd /opt/homewatch
docker compose ps
```

### Retrieving Pi-hole Admin Password
```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@3.111.211.129 sudo cat /root/pihole_password.txt
```

### Updating Lighthouse Dashboard Code
When updates are committed to the repository, push them to the server:
```bash
# 1. Regenerate payload locally
python scripts/prepare_deployment.py

# 2. Copy updated user_data or archive to EC2 and rebuild
ssh -i ~/.ssh/id_ed25519 ubuntu@3.111.211.129
cd /opt/homewatch
docker compose build dashboard
docker compose up -d dashboard
```

### Teardown & Rebuilding
To completely tear down the cloud infrastructure and eliminate AWS charges:
```bash
terraform destroy
```
Because the Elastic IP and all configuration are codified in Terraform, running `terraform apply` subsequently will recreate an identical setup from scratch in under 90 seconds.
