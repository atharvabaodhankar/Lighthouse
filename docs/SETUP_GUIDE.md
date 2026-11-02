# Lighthouse Client Setup Guide

Connect your smartphones, computers, smart home devices, and Wi-Fi routers to your **Lighthouse DNS Shield** in minutes.

Lighthouse supports two primary connection methods:
1. **DNS-over-TLS (DoT on Port 853)**: Fully encrypted, authenticated DNS queries using hostname `3-111-211-129.sslip.io`. Ideal for smartphones and laptops traveling outside your home network.
2. **Standard DNS (Port 53)**: Standard UDP/TCP DNS queries directed to static IP `3.111.211.129`. Ideal for whole-home router DHCP deployment.

---

## Quick Reference Connection Parameters

| Parameter | Value | Notes |
| :--- | :--- | :--- |
| **Server IPv4** | `3.111.211.129` | AWS Elastic IP (ap-south-1 Mumbai) |
| **Private DNS Hostname (DoT)** | `3-111-211-129.sslip.io` | Port 853, valid Let's Encrypt TLS certificate |
| **Encrypted Protocol** | DNS-over-TLS (DoT, RFC 7858) | High performance, zero SNI leaks |
| **Standard DNS Port** | `53` (UDP / TCP) | Restricted to your home IP in AWS SG |
| **Dashboard URL** | `http://3.111.211.129:8000` | Restricted to your home IP |

---

## 1. Android (Android 9.0+ Private DNS)

Android natively supports DNS-over-TLS via its **Private DNS** feature. This encrypts all DNS traffic across both Wi-Fi and mobile data (4G/5G).

### Setup Instructions
1. Open **Settings** on your Android device.
2. Tap **Network & Internet** (or **Connections** on Samsung One UI).
3. Tap **More connection settings** -> **Private DNS**.
4. Select **Private DNS provider hostname**.
5. Enter:
   ```text
   3-111-211-129.sslip.io
   ```
6. Tap **Save**.

### Verification
- Check your notification bar or status in Settings. It should display **Active** or `3-111-211-129.sslip.io`.
- Open Chrome or Firefox on your phone and browse to any website.
- In the Lighthouse Dashboard, open **Live Query Log**; you will see incoming requests tagged with client `Mobile Private DNS (DoT / Port 853)`.

### Troubleshooting
- **"Couldn't connect" error**: Ensure your phone has internet connectivity. Android validates TLS connectivity by issuing a test probe to `_dns.resolver.arpa` over port 853. Verify port 853 is open on the EC2 security group.
- **Captive portal Wi-Fi (Airports/Hotels)**: If connecting to a public Wi-Fi network requiring a web login, temporarily switch Private DNS to **Automatic** or **Off** to complete the splash screen, then re-enable Lighthouse.

---

## 2. Apple iOS & iPadOS (iPhone / iPad)

### Method A: Native Wi-Fi Settings (Home Network)
1. Open **Settings** -> **Wi-Fi**.
2. Tap the blue **(i)** icon next to your connected Wi-Fi network.
3. Scroll down and tap **Configure DNS**.
4. Switch from **Automatic** to **Manual**.
5. Tap **Add Server** and enter:
   ```text
   3.111.211.129
   ```
6. Tap **Save** in the top right corner.

### Method B: System-wide Encrypted DNS Profile (DoT / Mobile Data)
To protect iOS across cellular data and external Wi-Fi networks, install an Apple `.mobileconfig` profile that configures DNS-over-TLS:

1. Save the following XML configuration as `lighthouse-dot.mobileconfig`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>PayloadDisplayName</key>
    <string>Lighthouse DNS Shield</string>
    <key>PayloadIdentifier</key>
    <string>io.sslip.3-111-211-129.dns</string>
    <key>PayloadType</key>
    <string>Configuration</string>
    <key>PayloadUUID</key>
    <string>4A8B2C9D-E3F1-4567-890A-BCDEF1234567</string>
    <key>PayloadVersion</key>
    <integer>1</integer>
    <key>PayloadContent</key>
    <array>
        <dict>
            <key>PayloadType</key>
            <string>com.apple.dnsSettings.managed</string>
            <key>PayloadIdentifier</key>
            <string>io.sslip.3-111-211-129.dns.managed</string>
            <key>PayloadUUID</key>
            <string>9F8E7D6C-5B4A-3210-FEDC-BA9876543210</string>
            <key>PayloadVersion</key>
            <integer>1</integer>
            <key>DNSSettings</key>
            <dict>
                <key>DNSProtocol</key>
                <string>TLS</string>
                <key>ServerAddresses</key>
                <array>
                    <string>3.111.211.129</string>
                </array>
                <key>ServerName</key>
                <string>3-111-211-129.sslip.io</string>
            </dict>
        </dict>
    </array>
</dict>
</plist>
```

2. AirDrop or download the file to your iPhone.
3. Go to **Settings** -> **Profile Downloaded** -> **Install**.
4. Confirm installation. All queries are now securely routed through Lighthouse over TLS.

---

## 3. Apple macOS

### Method A: System Settings GUI (macOS Ventura, Sonoma, Sequoia)
1. Open **System Settings** -> **Network**.
2. Select your active connection (**Wi-Fi** or **Ethernet**) and click **Details...**.
3. Select **DNS** from the left sidebar.
4. Under **DNS Servers**, click the **+** (plus) button.
5. Enter:
   ```text
   3.111.211.129
   ```
6. Click **OK** to apply changes.

### Method B: Terminal (CLI Command)
Execute in macOS Terminal:

```bash
# Set primary DNS on Wi-Fi interface
sudo networksetup -setdnsservers Wi-Fi 3.111.211.129

# Verify DNS configuration
networksetup -getdnsservers Wi-Fi

# Flush local DNS cache
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
```

---

## 4. Home Wi-Fi Router (Whole-Home Protection)

Configuring your home Wi-Fi router protects every device connected to your household network automatically — including Smart TVs, game consoles, IoT sensors, voice assistants, and guest devices — with zero per-device configuration.

### General Instructions
1. Open your web browser and navigate to your router's administration portal (commonly `192.168.1.1` or `192.168.0.1`).
2. Log in with your router administrative credentials.
3. Locate the **DNS Settings** section:
   - For most routers, this is located under **WAN / Internet Setup** or **LAN / DHCP Server**.
4. Set **Primary DNS Server**:
   ```text
   3.111.211.129
   ```
5. Set **Secondary DNS Server**:
   - Leave empty or set to `1.1.1.1` as a backup.
   - *Security recommendation*: Leaving secondary DNS blank prevents client devices from silently bypassing ad-blocking when queries race between resolvers.
6. Save and apply settings.
7. Restart your router or disconnect and reconnect your devices to renew their DHCP leases.

### Popular Router Quick Steps

#### Airtel Xstream Fiber (Nokia / ZTE / Sercomm)
- Navigate to **Network** -> **LAN** -> **DHCP Server**.
- Set **Primary DNS**: `3.111.211.129`.
- Click **Save**.

#### TP-Link Archer / Deco Mesh
- Log in to **Advanced** -> **Network** -> **Internet**.
- Change **DNS Address** to **Use the Following DNS Addresses**.
- **Primary DNS**: `3.111.211.129`.
- Click **Save**.

#### Asus (Asuswrt / ZenWiFi)
- Go to **WAN** -> **Internet Connection**.
- Under **WAN DNS Setting**, set **Connect to DNS Server automatically** to **No**.
- **DNS Server 1**: `3.111.211.129`.
- Click **Apply**.

---

## 5. Microsoft Windows (Windows 11 / 10)

### Method A: Windows Settings GUI
1. Open **Settings** (`Win + I`) -> **Network & internet**.
2. Click **Wi-Fi** (or **Ethernet**) -> **Hardware properties**.
3. Under **DNS server assignment**, click **Edit**.
4. Select **Manual** from the dropdown and toggle **IPv4** to **On**.
5. Set **Preferred DNS**:
   ```text
   3.111.211.129
   ```
6. Click **Save**.

### Method B: PowerShell (Run as Administrator)
```powershell
# Set DNS on all active network adapters
Get-NetAdapter | Where-Object Status -eq 'Up' | Set-DnsClientServerAddress -ServerAddresses ("3.111.211.129")

# Flush Windows DNS resolver cache
Clear-DnsClientCache

# Verify the active DNS configuration
Get-DnsClientServerAddress -AddressFamily IPv4
```

---

## 6. Linux (Ubuntu, Debian, Fedora, Arch)

### Method A: systemd-resolved (DNS-over-TLS Native)
Modern Linux distributions using `systemd-resolved` can enforce encrypted DNS-over-TLS natively:

1. Edit `/etc/systemd/resolved.conf`:
```ini
[Resolve]
DNS=3.111.211.129#3-111-211-129.sslip.io
FallbackDNS=1.1.1.1
DNSOverTLS=yes
DNSSEC=yes
```

2. Restart `systemd-resolved`:
```bash
sudo systemctl restart systemd-resolved
```

3. Verify connection status:
```bash
resolvectl status
```

### Method B: NetworkManager CLI (`nmcli`)
```bash
# Identify active connection name
nmcli connection show --active

# Set DNS server on interface (replace 'Wired connection 1' with your connection name)
sudo nmcli connection modify "Wired connection 1" ipv4.dns "3.111.211.129" ipv4.ignore-auto-dns yes

# Reapply connection
sudo nmcli connection up "Wired connection 1"
```

---

## 7. Verification & Diagnostic Commands

Test your connection from any terminal to confirm that ad-blocking and encrypted routing are working properly:

### 1. Test Standard DNS Resolution
Query a known benign domain against Lighthouse:
```bash
nslookup google.com 3.111.211.129
```
*Expected Output*: Returns valid public IP addresses for google.com in under 15ms.

### 2. Verify Ad-Blocking & Sinkholing
Query a known tracking domain:
```bash
nslookup doubleclick.net 3.111.211.129
```
*Expected Output*: Returns `0.0.0.0` or `NXDOMAIN`, indicating that the Pi-hole gravity blocklist successfully sinkholed the threat.

### 3. Verify DNS-over-TLS (Port 853)
Using `kdig` (Knot DNS utility):
```bash
kdig -d @3.111.211.129 +tls-ca +tls-host=3-111-211-129.sslip.io doubleclick.net
```
*Expected Output*: Confirms successful TLS handshake using Let's Encrypt CA certificate and responds with `NXDOMAIN` over TLS 1.3.

### 4. Test TLS Handshake with OpenSSL
```bash
openssl s_client -connect 3.111.211.129:853 -servername 3-111-211-129.sslip.io < /dev/null
```
*Expected Output*: Returns `Verify return code: 0 (ok)` and displays the valid certificate chain issued to `3-111-211-129.sslip.io`.
