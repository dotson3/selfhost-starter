# Self-Hosted Homelab & Automation Starter Pack

**4 production-grade Python scripts + this guide. Zero dependencies. Pure standard
library — no `pip install`, no Flask, no paid tools. Runs on any
Raspberry Pi, VPS, or old laptop with Python 3.8+.**

> Built and battle-tested on a real Raspberry Pi running Pi-hole, WireGuard,
> and a system dashboard — the same setup this pack helps you recreate.

---

## What's inside

| Script | What it does | Tier |
|---|---|---|
| `pihole_blocklist.py` | Turns a basic Pi-hole into a privacy powerhouse: pushes 25 hand-picked tracker/ad domains to the Pi-hole v6 API and rebuilds gravity. | **FREE** |
| `dashboard.py` | A live system monitor (CPU/mem/disk/temp/top procs) served as a JSON API + single-file HTML page. No Flask. | PAID |
| `wg_peer.py` | Generates a new WireGuard client in 30 seconds: writes the `.conf`, prints a scannable QR, and prints the `[Peer]` block to paste into your server. | PAID |
| `cron_task.py` | Scaffolds a correct systemd service+timer pair from a template — no more fighting systemd syntax. | PAID (bonus) |

---

## Quick start

```bash
# 1. Copy the pack to your box
git clone <your-link> selfhost-starter && cd selfhost-starter

# 2. FREE tier — strengthen Pi-hole (run ON the Pi-hole box)
python3 pihole_blocklist.py

# 3. PAID — live dashboard on :8000
python3 dashboard.py --port 8000
# open http://<your-ip>:8000  (put it behind your VPN!)

# 4. PAID — onboard a phone to your WireGuard VPN
WG_PUB=$(sudo wg show wg0 public-key)
python3 wg_peer.py --name phone \
    --server-endpoint YOUR.PUBLIC.IP:51820 \
    --server-public "$WG_PUB"
# scan the QR with the WireGuard app

# 5. PAID — schedule a nightly backup
python3 cron_task.py --name backup-pihole \
    --on "*-*-* 03:00:00" --cmd "/usr/local/bin/backup.sh"
```

Each script has `--help` with every option. They are commented line-by-line
so you can learn from them and adapt them.

---

## Why this pack exists

Most "homelab" content is a YouTube video you forget in 3 days. Most
"starter" scripts need `pip install` a dozen packages that break on your
Pi's old Python. This pack is the opposite:

- **It actually runs** on a stock Raspberry Pi OS / Ubuntu with nothing extra.
- **It's safe by design** — `wg_peer.py` never touches your running
  `wg0.conf`; it prints the block for *you* to paste. `pihole_blocklist.py`
  is additve and reversible from the Pi-hole UI.
- **You learn** — every script is readable, commented, and a real pattern
  you'll reuse.

---

## Safety & honesty notes

- `dashboard.py` binds `0.0.0.0` by default. **Put it behind your VPN
  or a firewall** before exposing it. It reads `/proc` and `/sys` only;
  it writes nothing.
- `pihole_blocklist.py` intentionally leaves a few *functional* domains
  alone (Apple attribution, Yahoo metrics, TikTok business API) — blocking
  those breaks real app features, not ads. They're documented in the script.
- These scripts manage system services. Always keep a backup of anything
  they touch (Pi-hole's UI has one-click allow/deny; WireGuard configs
  are plain text). The author runs all four of these on production hardware.

---

## Tiers

- **FREE** — `pihole_blocklist.py` (the privacy upgrade everyone wants).
- **PAY-WHAT-YOU-WANT** — the full pack, suggested $9.
- **PAID ($19)** — full pack + the "From Zero to VPN" written walkthrough
  (exact commands to stand up Pi-hole + WireGuard from a fresh SD card,
  the same path the author used) as a bonus `SETUP.md`.

Questions? The scripts are self-documenting — start with `--help`.

---

## Get the bundle + walkthrough
The scripts above are the full pack, free and open. If you want them as a
ready-to-download ZIP plus the "From Zero to VPN" written walkthrough, there's
a paid bundle: https://dotsonia08.gumroad.com/l/homelab-starter-pack
