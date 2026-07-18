#!/usr/bin/env python3
"""
dashboard.py  -  Self-Hosted Starter Pack  (PAID tier)
-------------------------------------------------------------
A ZERO-dependency system monitor for any Linux box. Serves a JSON API + a
single-file HTML page showing CPU, memory, disk, temperature, top processes.
No Flask, no pip - stdlib only.

USAGE
  python3 dashboard.py                       # http://0.0.0.0:8000
  python3 dashboard.py --port 9000
Then open the URL. For LAN/VPN access, point the client browser at the
server's VPN IP (e.g. http://10.10.10.1:8000).

SAFETY: binds 0.0.0.0 by default - put behind your VPN or firewall.
Reads /proc and /sys only; writes nothing.
"""
import argparse
import json
import os
import subprocess
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

START = time.time()


def stat_cpu():
    with open("/proc/stat") as f:
        parts = list(map(int, f.readline().split()[1:]))
    idle, total = parts[3], sum(parts)
    time.sleep(0.2)
    with open("/proc/stat") as f:
        parts2 = list(map(int, f.readline().split()[1:]))
    idle2, total2 = parts2[3], sum(parts2)
    return round(100 * (1 - (idle2 - idle) / max(1, total2 - total)), 1)


def stat_mem():
    d = {}
    with open("/proc/meminfo") as f:
        for line in f:
            k, v = line.split()[0].rstrip(":"), int(line.split()[1])
            d[k] = v
    used = d["MemTotal"] - d["MemFree"] - d.get("Buffers", 0) - d.get("Cached", 0)
    return {
        "total_mib": round(d["MemTotal"] / 1024, 1),
        "used_mib": round(used / 1024, 1),
        "free_mib": round(d["MemFree"] / 1024, 1),
        "pct": round(100 * used / d["MemTotal"], 1),
    }


def stat_disk():
    rows = []
    out = subprocess.run(["df", "-h", "/"], capture_output=True, text=True).stdout.splitlines()
    for line in out[1:]:
        c = line.split()
        if c:
            rows.append({"fs": c[0], "size": c[1], "used": c[2], "pct": c[4].rstrip("%")})
    return rows


def stat_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return round(int(f.read().strip()) / 1000, 1)
    except OSError:
        pass
    try:
        return subprocess.run(["vcgencmd", "measure_temp"], capture_output=True, text=True).stdout.strip()
    except Exception:
        return None


def top_procs(n=6):
    out = subprocess.run(
        ["ps", "-eo", "pid,comm,%cpu,%mem", "--sort=-%cpu"],
        capture_output=True, text=True,
    ).stdout.splitlines()[1:n + 1]
    return [dict(zip(["pid", "comm", "cpu", "mem"], l.split(None, 3))) for l in out]


def collect():
    return {
        "uptime_s": int(time.time() - START),
        "cpu_pct": stat_cpu(),
        "mem": stat_mem(),
        "disk": stat_disk(),
        "temp_c": stat_temp(),
        "top": top_procs(),
        "ts": int(time.time()),
    }


PAGE = """<!doctype html><html><head><meta charset=utf-8>
<title>Homelab Dashboard</title><meta http-equiv=refresh content=5>
<style>body{font:14px system-ui;background:#0d1117;color:#c9d1d9;margin:2rem}
h1{color:#58a6ff}.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:1rem;margin:.5rem 0}
.bar{height:10px;background:#30363d;border-radius:5px;overflow:hidden}
.bar>span{display:block;height:100%;background:#3fb950}table{width:100%;border-collapse:collapse}
td,th{text-align:left;padding:.3rem;border-bottom:1px solid #21262d}</style></head>
<body><h1>Homelab Dashboard</h1><div id=app>loading...</div>
<script>async function load(){const d=await (await fetch('/api')).json();
let h=`<div class=card>CPU <b>${d.cpu_pct}%</b><div class=bar><span style="width:${d.cpu_pct}%"></span></div></div>`;
h+=`<div class=card>MEM <b>${d.mem.used_mib}/${d.mem.total_mib} MiB (${d.mem.pct}%)</b><div class=bar><span style="width:${d.mem.pct}%"></span></div></div>`;
h+=`<div class=card>Temp <b>${d.temp_c}C</b></div>`;
h+=`<div class=card>Disk `+d.disk.map(x=>`${x.fs}: ${x.used} (${x.pct}%)`).join('<br>')+`</div>`;
h+=`<div class=card><table><tr><th>PID</th><th>CMD</th><th>CPU</th><th>MEM</th></tr>`+
d.top.map(p=>`<tr><td>${p.pid}</td><td>${p.comm}</td><td>${p.cpu}</td><td>${p.mem}</td></tr>`).join('')+`</table></div>`;
document.getElementById('app').innerHTML=h;}load();setInterval(load,5000);</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api":
            body = json.dumps(collect()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path in ("/", "/index.html"):
            b = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *a):
        pass


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8000)
    a = p.parse_args()
    print(f"[*] Dashboard on http://{a.host}:{a.port}  (Ctrl-C to stop)")
    HTTPServer((a.host, a.port), H).serve_forever()


if __name__ == "__main__":
    main()
