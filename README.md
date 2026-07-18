# Self-Hosted Homelab Scripts

**4 production-grade Python scripts. Zero dependencies. Pure standard library —
no `pip install`, no Flask, no paywall. Runs on any Raspberry Pi, VPS, or old
laptop with Python 3.8+.**

> Built and battle-tested on a real Raspberry Pi running Pi-hole, WireGuard,
> and a system dashboard — the same setup these scripts help you run.

**This pack is free and open. Use it, modify it, learn from it. If it saved you
a weekend, a tip keeps the projects coming: https://www.paypal.com/paypalme/ddotson321**

---

## What's inside (all free)

| Script | What it does |
|---|---|
| `pihole_blocklist.py` | Turns a basic Pi-hole into a privacy powerhouse: pushes 25 hand-picked tracker/ad domains to the Pi-hole v6 API and rebuilds gravity. |
| `dashboard.py` | A live system monitor (CPU/mem/disk/temp/top procs) served as a JSON API + single-file HTML page. No Flask. |
| `wg_peer.py` | Generates a new WireGuard client in 30 seconds: writes the `.conf`, prints a scannable QR, and prints the `[Peer]` block to paste into your server. |
| `cron_task.py` | Scaffolds a correct systemd service+timer pair from a template — no more fighting systemd syntax. |

---

## Quick start

```bash
# 1. Clone the pack to your box
git clone https://github.com/dotson3/selfhost-starter.git selfhost-starter && cd selfhost-starter

# 2. Strengthen Pi-hole (run ON the Pi-hole box)
python3 pihole_blocklist.py

# 3. Live dashboard on :8000
python3 dashboard.py --port 8000
# open http://<your-ip>:8000  (put it behind your VPN!)

# 4. Onboard a phone to your WireGuard VPN
WG_PUB=$(sudo wg show wg0 public-key)
python3 wg_peer.py --name phone \
    --server-endpoint YOUR.PUBLIC.IP:51820 \
    --server-public "$WG_PUB"
# scan the QR with the WireGuard app

# 5. Schedule a nightly backup
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
  is additive and reversible from the Pi-hole UI.
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

## Free, with optional tip

There is no paid tier. All four scripts are free and open right here in this
repo. If they were useful to you, a tip of any amount is appreciated and
helps fund more tools like this:

**Tip:** https://www.paypal.com/paypalme/ddotson321

Questions? The scripts are self-documenting — start with `--help`.
