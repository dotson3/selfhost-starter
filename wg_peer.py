#!/usr/bin/env python3
"""
wg_peer.py  —  Self-Hosted Starter Pack  (PAID tier script)
-------------------------------------------------------------
Generates a new WireGuard client (peer) for an existing wg0 server.
Pure stdlib: writes the client .conf, shows a QR (or writes a PNG via qrencode
if installed), and prints the server-side `Peer` block to paste into wg0.conf.

WHY: the #1 friction in self-hosting a VPN is onboarding devices.
This makes "give my phone/laptop VPN access" a 30-second command.

USAGE
  python3 wg_peer.py --name phone --server-endpoint 71.94.241.70:51820 \
        --dns 10.10.10.1 --allowed "0.0.0.0/0,::/0"
  # outputs: phone.conf  +  prints QR to terminal  +  prints [Peer] block

SAFETY
  * Generates REAL keys with cryptography.hazmat if available, else falls back
    to calling `wg genkey` (wireguard-tools). If neither exists, refuses (no weak keys).
  * Never touches your running wg0.conf — it only PRINTS the Peer block for you
    to paste. (Smallest-change principle: you stay in control.)
"""
import argparse
import base64
import ipaddress
import os
import subprocess
import sys

def genkey():
    """Return (private_b64, public_b64). Prefer wg CLI; else hazmat; else fail."""
    try:
        priv = subprocess.run(["wg", "genkey"], capture_output=True, text=True, check=True).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        try:
            from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
            from cryptography.hazmat.primitives import serialization
            k = X25519PrivateKey.generate()
            priv = base64.b64encode(k.private_bytes_raw()).decode()
        except Exception:
            print("[!] No key backend: install wireguard-tools (`wg`) or `pip install cryptography`.", file=sys.stderr)
            sys.exit(2)
    pub = subprocess.run(["wg", "pubkey"], input=priv, capture_output=True, text=True, check=True).stdout.strip() \
        if subprocess.run(["which","wg"], capture_output=True).returncode == 0 \
        else _pub_from_priv(priv)
    return priv, pub

def _pub_from_priv(priv_b64):
    """Derive public key via hazmat when wg CLI is absent."""
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    raw = base64.b64decode(priv_b64)
    k = X25519PrivateKey.from_private_bytes(raw)
    return base64.b64encode(k.public_key().public_bytes_raw()).decode()

def next_ip(base_net, used):
    net = ipaddress.ip_network(base_net)
    # assume /24 server subnet; hand out .2, .3, ... skipping .1 (server) and used
    hosts = list(net.hosts())
    for ip in hosts[1:]:  # skip .1 (server)
        if str(ip) not in used and not str(ip).endswith(".1"):
            return str(ip)
    raise RuntimeError("subnet exhausted")

def main():
    p = argparse.ArgumentParser(description="Generate a WireGuard peer config (stdlib).")
    p.add_argument("--name", required=True, help="peer name, e.g. phone")
    p.add_argument("--server-endpoint", required=True, help="host:port, e.g. 71.94.241.70:51820")
    p.add_argument("--server-public", required=True, help="wg0 server public key")
    p.add_argument("--subnet", default="10.10.10.0/24", help="VPN subnet (default 10.10.10.0/24)")
    p.add_argument("--dns", default="10.10.10.1", help="DNS for client (use Pi-hole IP)")
    p.add_argument("--allowed", default="0.0.0.0/0,::/0", help="AllowedIPs")
    p.add_argument("--out-dir", default=".", help="where to write <name>.conf")
    p.add_argument("--used", nargs="*", default=[], help="already-assigned client IPs to skip")
    args = p.parse_args()

    client_priv, client_pub = genkey()
    client_ip = next_ip(args.subnet, set(args.used))

    conf = f"""[Interface]
PrivateKey = {client_priv}
Address = {client_ip}/24
DNS = {args.dns}

[Peer]
PublicKey = {args.server_public}
Endpoint = {args.server_endpoint}
AllowedIPs = {args.allowed}
PersistentKeepalive = 25
"""
    os.makedirs(args.out_dir, exist_ok=True)
    path = os.path.join(args.out_dir, f"{args.name}.conf")
    with open(path, "w") as f:
        f.write(conf)
    os.chmod(path, 0o600)
    print(f"[+] Wrote client config: {path}  (client IP {client_ip})")
    print("\n--- PASTE THIS into /etc/wireguard/wg0.conf on the SERVER ---")
    print(f"[Peer]\n# {args.name}\nPublicKey = {client_pub}\nAllowedIPs = {client_ip}/32\n")
    print("--- QR CODE (scan with WireGuard app) ---")
    if subprocess.run(["which","qrencode"], capture_output=True).returncode == 0:
        subprocess.run(["qrencode", "-t", "ansiutf8", path])
    else:
        print(f"(install `qrencode` for a scannable QR, or open {path} on the device)")

if __name__ == "__main__":
    main()
