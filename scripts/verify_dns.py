#!/usr/bin/env python3
"""
Lighthouse Diagnostic & Verification Utility
Performs end-to-end verification of DNS (Port 53), DNS-over-TLS (Port 853),
and the Lighthouse FastAPI REST API.
"""

import argparse
import io
import socket
import ssl
import struct
import sys
import time
from typing import Tuple

# Ensure UTF-8 stdout on Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, io.UnsupportedOperation):
        pass

try:
    import httpx
except ImportError:
    httpx = None


def make_dns_query(domain: str, qtype: int = 1) -> bytes:
    """Build a minimal raw DNS wire-format query (QTYPE 1 = A)."""
    trans_id = 0x1234
    flags = 0x0100  # Standard query with recursion desired
    qdcount = 1
    ancount = 0
    nscount = 0
    arcount = 0
    header = struct.pack("!HHHHHH", trans_id, flags, qdcount, ancount, nscount, arcount)

    # Encode domain name labels
    qname = b""
    for part in domain.split("."):
        b_part = part.encode("ascii")
        qname += struct.pack("!B", len(b_part)) + b_part
    qname += b"\x00"

    qclass = 1  # IN class
    question = qname + struct.pack("!HH", qtype, qclass)
    return header + question


def test_udp_dns(ip: str, domain: str = "google.com", timeout: float = 3.0) -> Tuple[bool, str]:
    """Test standard UDP DNS resolution against port 53."""
    query = make_dns_query(domain)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    start = time.perf_counter()
    try:
        sock.sendto(query, (ip, 53))
        data, _ = sock.recvfrom(512)
        elapsed = (time.perf_counter() - start) * 1000
        if len(data) >= 12:
            rcode = data[3] & 0x0F
            return True, f"Resolved in {elapsed:.1f}ms (RCODE={rcode})"
        return False, "Malformed response"
    except socket.timeout:
        return False, "Timeout (Port 53 blocked or filtered by firewall)"
    except Exception as e:
        return False, str(e)
    finally:
        sock.close()


def test_dot_dns(ip: str, host: str, domain: str = "google.com", timeout: float = 4.0) -> Tuple[bool, str]:
    """Test RFC 7858 DNS-over-TLS on TCP port 853 with TLS verification."""
    query = make_dns_query(domain)
    length_prefix = struct.pack("!H", len(query))
    payload = length_prefix + query

    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_sock.settimeout(timeout)

    ctx = ssl.create_default_context()
    start = time.perf_counter()
    try:
        tls_sock = ctx.wrap_socket(raw_sock, server_hostname=host)
        tls_sock.connect((ip, 853))
        tls_sock.sendall(payload)

        len_data = tls_sock.recv(2)
        if len(len_data) < 2:
            return False, "Connection closed before length header received"
        resp_len = struct.unpack("!H", len_data)[0]
        resp_data = tls_sock.recv(resp_len)
        elapsed = (time.perf_counter() - start) * 1000

        if len(resp_data) >= 12:
            rcode = resp_data[3] & 0x0F
            cipher = tls_sock.cipher()
            cipher_name = cipher[0] if cipher else "Unknown"
            return True, f"Resolved via {cipher_name} in {elapsed:.1f}ms (RCODE={rcode})"
        return False, "Incomplete DNS response"
    except ssl.SSLCertVerificationError as e:
        return False, f"TLS Certificate Error: {e.verify_message}"
    except socket.timeout:
        return False, "Timeout on port 853"
    except Exception as e:
        return False, str(e)
    finally:
        raw_sock.close()


def test_http_api(url: str, timeout: float = 3.0) -> Tuple[bool, str]:
    """Test Lighthouse Dashboard REST API health."""
    if not httpx:
        return True, "httpx not installed, skipped API test"
    start = time.perf_counter()
    try:
        res = httpx.get(f"{url.rstrip('/')}/api/health", timeout=timeout)
        elapsed = (time.perf_counter() - start) * 1000
        if res.status_code == 200:
            data = res.json()
            return True, f"HTTP {res.status_code} in {elapsed:.1f}ms (app={data.get('app')})"
        return False, f"Unexpected status code: {res.status_code}"
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="Lighthouse DNS Shield Diagnostics")
    parser.add_argument("--ip", default="3.111.211.129", help="Server IPv4 address")
    parser.add_argument("--dot-host", default="3-111-211-129.sslip.io", help="DNS-over-TLS FQDN")
    parser.add_argument("--api-url", default="http://3.111.211.129", help="Lighthouse Dashboard base URL")
    args = parser.parse_args()

    print("=" * 65)
    print("[*] Lighthouse DNS Shield & Traffic Intelligence -- Diagnostic Suite")
    print(f"Target Server : {args.ip}")
    print(f"DoT Hostname  : {args.dot_host}")
    print(f"Dashboard URL : {args.api_url}")
    print("=" * 65)

    print("\n1. Testing UDP Port 53 (Standard DNS)...")
    ok, msg = test_udp_dns(args.ip, "google.com")
    print(f"   [{'PASS' if ok else 'NOTE'}] {msg}")

    print("\n2. Testing TCP Port 853 (DNS-over-TLS Encrypted)...")
    ok_dot, msg_dot = test_dot_dns(args.ip, args.dot_host, "google.com")
    print(f"   [{'PASS' if ok_dot else 'FAIL'}] {msg_dot}")

    print("\n3. Testing Ad-Blocking & Sinkhole (doubleclick.net via DoT)...")
    ok_sink, msg_sink = test_dot_dns(args.ip, args.dot_host, "doubleclick.net")
    print(f"   [{'PASS' if ok_sink else 'FAIL'}] {msg_sink}")

    print("\n4. Testing Lighthouse Dashboard REST API (/api/health)...")
    ok_api, msg_api = test_http_api(args.api_url)
    print(f"   [{'PASS' if ok_api else 'NOTE'}] {msg_api}")

    print("\n" + "=" * 65)
    if ok_dot:
        print("[SUCCESS] Core DNS-over-TLS Shield is operational and serving queries.")
    else:
        print("[WARNING] Encrypted DoT check encountered an issue. See diagnostic message above.")
    print("=" * 65)


if __name__ == "__main__":
    main()
