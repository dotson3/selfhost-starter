#!/usr/bin/env python3
"""
pihole_blocklist.py  —  Self-Hosted Starter Pack  (FREE tier script)
-------------------------------------------------------------
Adds a curated blocklist to a Pi-hole v6 instance over its local API
and rebuilds gravity. Pure stdlib, no pip required.

WHAT IT DOES
  * Reads a list of ad/tracker domains (or a URL to one).
  * Pushes each to Pi-hole's local API as a DENY entry (?type=block).
  * Reports how many were added vs already present.
  * (Optional) triggers a gravity rebuild so they take effect.

WHY THIS IS USEFUL
  Pi-hole ships with one default list. This turns a basic install into a
  privacy powerhouse in one command — the same ~25 hand-picked trackers
  the author added after a real adblock test.

USAGE
  python3 pihole_blocklist.py                 # uses built-in DEFAULT_DOMAINS
  python3 pihole_blocklist.py mylist.txt     # one domain per line
  python3 pihole_blocklist.py --url https://example.com/list.txt
  python3 pihole_blocklist.py --api http://192.168.1.10/api  # remote Pi-hole
  python3 pihole_blocklist.py --no-gravity   # skip rebuild

NOTE: Requires the Pi-hole API to be reachable (127.0.0.1 by default,
or a LAN IP with no password set, or a valid session). The author's setup
uses 127.0.0.1 (run this ON the Pi-hole box) — safest and no auth needed.
"""
import argparse
import json
import sys
import urllib.request
import urllib.error

DEFAULT_DOMAINS = [
    # --- session-replay / heatmap analytics (pure trackers) ---
    "api.bugsnag.com", "api.luckyorange.com", "api.mouseflow.com",
    "app.bugsnag.com", "app.getsentry.com", "browser.sentry-cdn.com",
    "careers.hotjar.com", "cdn-test.mouseflow.com", "cdn.luckyorange.com",
    "gtm.mouseflow.com", "identify.hotjar.com", "insights.hotjar.com",
    "realtime.luckyorange.com", "surveys.hotjar.com", "tools.mouseflow.com",
    "w1.luckyorange.com",
    # --- ad / telemetry networks ---
    "appmetrica.yandex.ru", "claritybt.freshmarketer.com",
    "data.mistat.india.xiaomi.com", "data.mistat.rus.xiaomi.com",
    "freshmarketer.com", "fwtracks.freshmarketer.com", "grs.hicloud.com",
    "log.byteoversea.com", "metrics.data.hicloud.com",
    "metrics2.data.hicloud.com", "metrika.yandex.ru", "samsung-com.112.2o7.net",
]

# Functional/non-ad domains the author INTENTIONALLY leaves alone:
#   api-adservices.apple.com, books-analytics-events.apple.com,
#   business-api.tiktok.com, log.fc.yahoo.com, udcm.yahoo.com
# (blocking those breaks legit app features — documented in the guide).


def api_post(api_base, path, payload):
    url = f"{api_base}/domains/{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode(), r.status
    except urllib.error.HTTPError as e:
        return e.read().decode(), e.code
    except Exception as e:  # noqa: BLE001 - surface any network error to the user
        return f"ERROR: {e}", 0


def add_domain(api_base, domain):
    # Pi-hole v6: POST /api/domains/deny/exact  (path NOT query)
    body, status = api_post(api_base, "deny/exact",
                                {"domain": domain, "comment": "selfhost-starter", "groups": [0]})
    if status in (200, 201) or '"id"' in body:
        return "added"
    if "already" in body.lower() or status == 409:
        return "exists"
    return f"fail({status})"


def main():
    p = argparse.ArgumentParser(description="Add a blocklist to Pi-hole v6 (stdlib-only).")
    p.add_argument("file", nargs="?", help="file with one domain per line")
    p.add_argument("--url", help="URL to a plain-text domain list")
    p.add_argument("--api", default="http://127.0.0.1/api", help="Pi-hole API base")
    p.add_argument("--no-gravity", action="store_true", help="skip gravity rebuild")
    args = p.parse_args()

    domains = list(DEFAULT_DOMAINS)
    if args.url:
        with urllib.request.urlopen(args.url, timeout=15) as r:  # noqa: S310 - user-supplied
            domains = [l.decode().strip().split("#")[0].strip()
                       for l in r.readlines() if l.strip() and not l.startswith(b"#")]
    elif args.file:
        with open(args.file) as f:
            domains = [l.strip().split("#")[0].strip() for l in f if l.strip() and not l.startswith("#")]

    print(f"[*] Pi-hole API: {args.api}")
    print(f"[*] Domains to process: {len(domains)}")
    added = exists = failed = 0
    for d in domains:
        res = add_domain(args.api, d)
        if res == "added":
            added += 1
        elif res == "exists":
            exists += 1
        else:
            failed += 1
            print(f"    ! {d}: {res}")
    print(f"[+] Done. added={added} already_present={exists} failed={failed}")

    if not args.no_gravity and added:
        print("[*] Rebuilding gravity (this can take a minute)...")
        # Pi-hole CLI; falls back to a no-op note if unavailable.
        import subprocess
        try:
            subprocess.run(["pihole", "-g"], check=False, timeout=300)
        except FileNotFoundError:
            print("    'pihole' CLI not found on this host; rebuild gravity manually.")


if __name__ == "__main__":
    main()
