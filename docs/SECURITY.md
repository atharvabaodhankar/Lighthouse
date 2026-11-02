# Lighthouse Security Model & Threat Defense

Security is foundational to the architecture of **Lighthouse**. Operating a public-facing cloud DNS server presents significant threat vectors if misconfigured — most notably DNS amplification attacks and unauthorized administrative access.

This document describes the threat model, attack mitigations, cryptographic standards, and firewall policies enforced across Lighthouse.

---

## 1. Threat Model & Risk Analysis

| Threat / Attack Vector | Impact Level | Potential Damage | Lighthouse Mitigation |
| :--- | :--- | :--- | :--- |
| **Open Resolver DNS Amplification** | **Critical** | Attacker uses UDP port 53 to bounce massive amplified DDoS traffic against victims. | AWS Security Group restricts UDP/TCP Port 53 strictly to `${var.home_ip}/32`. |
| **Eavesdropping & ISP Tracking** | **High** | Cellular carriers / public Wi-Fi sniff plaintext DNS lookups to profile browsing habits. | DNS-over-TLS (DoT, Port 853) encrypts lookups between mobile devices and EC2 using TLS 1.3. |
| **DNS Spoofing & Cache Poisoning** | **High** | Attackers forge DNS responses to redirect banking or sensitive traffic to phishing sites. | Upstream forwarding to Cloudflare 1.1.1.1 with strict **DNSSEC** validation enabled. |
| **Unauthorized Dashboard Control** | **High** | Unauthorized actor toggles off ad-blocking or injects malicious whitelist rules. | Dashboard port 8000 restricted to `${var.home_ip}/32`; Pi-hole v6 API protected by session tokens. |
| **Host Compromise (SSH Brute Force)** | **Critical** | Malicious botnet gains root shell on Ubuntu EC2 host. | SSH Port 22 locked to `${var.home_ip}/32`; public-key only authentication (`ed25519`); passwords disabled. |

---

## 2. Open Resolver Mitigation: Why Port 53 is Locked Down

### The Open Resolver Problem
Standard DNS operates over connectionless UDP on port 53. An attacker can forge (spoof) the source IP address in a UDP packet to impersonate a victim target, then query the resolver for large records (such as `ANY .` with EDNS0 buffer extensions):
- A 60-byte query can generate a 4,000-byte response.
- This creates an **amplification factor of ~70x**, transforming the resolver into a reflection weapon in distributed denial-of-service (DDoS) campaigns.

### The Lighthouse Defense
Lighthouse strictly **eliminates** open resolver exposure:
1. **Hypervisor Firewall Enforcement**: In `main.tf`, the AWS Security Group rule for port 53 explicitly limits incoming traffic to your single home IP address:
   ```hcl
   ingress {
     description = "DNS over TCP"
     from_port   = 53
     to_port     = 53
     protocol    = "tcp"
     cidr_blocks = ["${var.home_ip}/32"]
   }
   ingress {
     description = "DNS over UDP"
     from_port   = 53
     to_port     = 53
     protocol    = "udp"
     cidr_blocks = ["${var.home_ip}/32"]
   }
   ```
2. **Zero Ingress Leak**: Packets arriving from any IP address other than your authorized home IP are discarded silently by AWS border firewalls before they ever reach the EC2 instance's network interface.

---

## 3. Encrypted DNS: Why Port 853 (DoT) is Safely Public

To enable Android Private DNS and iOS mobile profiles when devices are outside the home (e.g., on 5G cellular networks or coffee shop Wi-Fi), **Port 853** is accessible to `0.0.0.0/0`.

### Why DNS-over-TLS is Resistant to Amplification Attacks
1. **Mandatory TCP Handshake**: Unlike UDP DNS, DNS-over-TLS requires a full 3-way TCP handshake (SYN -> SYN-ACK -> ACK). An attacker cannot spoof their IP address because the SYN-ACK will be sent to the forged IP, preventing the handshake from completing.
2. **TLS Session Cryptography**: No DNS queries can be issued until a full TLS session is established with mutual parameter negotiation, eliminating UDP amplification vectors entirely.
3. **Cryptographic Integrity**: All DNS requests and replies are encrypted inside TLS 1.2 / TLS 1.3 tunnels, preventing local Wi-Fi eavesdropping, ISP telemetry injection, and government censorship.

### TLS Cryptographic Hardening
The Nginx stream proxy terminates TLS 853 with the following security parameters:
- **Protocols**: `TLSv1.2 TLSv1.3` (SSLv2, SSLv3, TLS 1.0, and TLS 1.1 are explicitly disabled).
- **Ciphers**:
  ```nginx
  ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
  ssl_prefer_server_ciphers on;
  ssl_session_cache shared:DoT:10m;
  ssl_session_timeout 1d;
  ssl_session_tickets off;
  ```
- **Certificate Authority**: Automated Let's Encrypt certificates issued for FQDN `3-111-211-129.sslip.io`.

---

## 4. Host & Dashboard Protection

### 1. SSH Hardening
- **Access Scope**: Port 22 restricted exclusively to `${var.home_ip}/32`.
- **Key Authentication**: Modern ED25519 elliptic-curve key pairs only. RSA keys under 2048-bit are refused.
- **Root Password Lockdown**: Cloud-init provisions Ubuntu with password authentication disabled (`PasswordAuthentication no`).

### 2. Pi-hole Credential Management
- Pi-hole admin credentials are generated dynamically on boot via cryptographically secure randomness:
  ```bash
  PIHOLE_PW=$(openssl rand -base64 18)
  ```
- Credentials are written to `/opt/homewatch/.env` with strict file permissions:
  ```bash
  chmod 600 /opt/homewatch/.env
  ```
- No hardcoded passwords exist in git repositories or Dockerfiles.

### 3. Container Isolation & Least Privilege
- Docker containers run on an isolated bridge network (`homewatch_default`).
- Pi-hole requires only `NET_ADMIN` Linux capability for raw socket binding; all other unnecessary capabilities are dropped.
- The Lighthouse dashboard container mounts the Pi-hole configuration directory in **read-only mode** (`:ro`):
  ```yaml
  volumes:
    - ./pihole/etc-pihole:/etc/pihole:ro
  ```

---

## 5. Security Audit & Verification Procedures

Verify the security posture of your deployment from an external machine:

### 1. Verify Port 53 is Blocked from Non-Home IPs
Run an Nmap scan from an external machine or cloud VPS:
```bash
nmap -sU -p 53 3.111.211.129
```
*Expected Result*: `STATE: filtered` or `closed`. No DNS responses should be received.

### 2. Verify Port 853 TLS Cipher Suite
Scan port 853 using `testssl.sh` or `sslscan`:
```bash
sslscan 3.111.211.129:853
```
*Expected Result*: Confirms TLS 1.2 and TLS 1.3 only; insecure ciphers are reported as rejected.

### 3. Verify Open Resolver Status
Use the [Open Resolver Project](https://openresolver.com/) tool or dig:
```bash
dig @3.111.211.129 example.com +short
```
*Expected Result*: Query times out when executed from outside the authorized home network.
