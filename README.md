# 🏃‍♂️ Chaski-Link

**A small network performance monitor with automated logging, incident tracking, and a live status page.**

Chaski-Link is a lightweight, Python-based network performance monitor inspired by the ancient Incan messenger system. Every 30 minutes it checks whether major public DNS servers are reachable and how fast they respond, logs the result, opens and closes incidents when something goes wrong, and publishes the current state as a status page.

**Live status page:** https://serolinen.github.io/chaski-link/status.html

---

## 🚀 Features

* **Automated checks:** A GitHub Actions workflow runs every 30 minutes. GitHub doesn't guarantee exact timing for scheduled runs, so expect some drift.
* **Layer 4 monitoring:** Opens a TCP connection to port 53 on Google (8.8.8.8), Cloudflare (1.1.1.1) and Quad9 (9.9.9.9). This works where ICMP ping is blocked and confirms the DNS service itself is accepting connections.
* **Incident tracking:** A server that fails to connect is logged as an **Offline** incident. One that responds slower than 100 ms is logged as **Degraded**. The incident closes automatically, with its duration, when the server recovers. A Degraded incident is upgraded if the server then goes Offline.
* **Status dashboard:** A static `status.html` shows current latency, uptime percentage and recent incidents per server, in Central time.
* **Latency graph:** `latency_report.png` plots the full history, with outages marked as red X's instead of being hidden.
* **Local notifications:** When run on a Windows machine, `monitor.py` can show a toast notification for high latency or timeouts. These only appear locally, never on the GitHub runner.
* **Persistent logging:** Results are appended to `network_log.csv` and committed back to the repo after every run.

## 🧩 How it fits together

```
monitor.py     checks the servers, appends a row to network_log.csv
   └─ incidents.py   opens / escalates / closes records in incidents.csv
analyze.py     draws latency_report.png from network_log.csv
dashboard.py   builds status.html from network_log.csv + incidents.csv
```

The workflow in `.github/workflows/daily_check.yml` runs these in order, then commits the updated CSVs, graph and status page. GitHub Pages serves `status.html` from the `main` branch.

## 🗂️ Files

| File | Purpose |
| --- | --- |
| `monitor.py` | Runs the checks and writes the log |
| `incidents.py` | Incident open/close logic and `incidents.csv` handling |
| `analyze.py` | Generates the latency graph |
| `dashboard.py` | Generates the status page (standard library only) |
| `network_log.csv` | Full check history (timestamps in UTC) |
| `incidents.csv` | Open and resolved incidents (timestamps in UTC) |
| `latency_report.png` | Latest latency graph |
| `status.html` | Latest status page |

## 🛠️ Technical stack

* **Language:** Python 3.9+
* **Automation:** GitHub Actions, GitHub Pages
* **Libraries:** `plyer` (desktop notifications), `pandas` and `matplotlib` (graph), `tzdata` (timezone data); `socket`, `csv` and `datetime` from the standard library

## 📦 Run it locally

```bash
git clone https://github.com/seroLinen/chaski-link.git
cd chaski-link
pip install -r requirements.txt

python monitor.py     # run one check (appends to the CSV files)
python analyze.py     # rebuild the graph
python dashboard.py   # rebuild the status page, then open status.html
```

## ⚙️ Configuration

* **Latency threshold:** `LATENCY_THRESHOLD` in `monitor.py` (default 100 ms) decides what counts as Degraded.
* **Servers:** the `servers` dictionary in `monitor.py`. If you add one, also add it to `SERVERS` and `LABELS` in `dashboard.py` and to the plotted columns in `analyze.py`.
* **Schedule:** the `cron` line in `.github/workflows/daily_check.yml`.
* **Display timezone:** `DISPLAY_TZ` in `dashboard.py`. Logs always stay in UTC.

## 📝 Notes

* Timestamps in the CSV files are UTC because that is the GitHub runner's clock. Only the status page converts them for display.
* Running every 30 minutes means up to 48 automated commits a day.
