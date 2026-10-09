"""
Chaski-Link: Status Dashboard

Reads network_log.csv and incidents.csv and renders a single static
status.html — current state per server, uptime over the logged history,
and a table of recent incidents. No server, no JS framework; it's a
plain HTML file you can open locally or publish with GitHub Pages.
"""

import csv
import os
from datetime import datetime

LOG_FILE = 'network_log.csv'
INCIDENTS_FILE = 'incidents.csv'
OUTPUT_FILE = 'status.html'
SERVERS = ['Google_DNS', 'Cloudflare_DNS', 'Quad9_DNS']
LABELS = {'Google_DNS': 'Google', 'Cloudflare_DNS': 'Cloudflare', 'Quad9_DNS': 'Quad9'}


def load_log():
    if not os.path.isfile(LOG_FILE):
        return []
    with open(LOG_FILE, mode='r', newline='') as f:
        return list(csv.DictReader(f))


def load_incidents():
    if not os.path.isfile(INCIDENTS_FILE):
        return []
    with open(INCIDENTS_FILE, mode='r', newline='') as f:
        return list(csv.DictReader(f))


def uptime_pct(rows, server):
    """% of logged checks where the server was not Offline."""
    total = len(rows)
    if total == 0:
        return 100.0
    down = sum(1 for r in rows if r.get(server) == 'Offline')
    return 100.0 * (total - down) / total


def current_status(rows, server, threshold=100.0):
    """Returns (state, reading) for the most recent check of a server."""
    if not rows:
        return 'unknown', 'No data'
    reading = rows[-1].get(server, 'No data')
    if reading == 'Offline':
        return 'down', reading
    try:
        latency = float(str(reading).replace('ms', ''))
        if latency > threshold:
            return 'degraded', reading
        return 'up', reading
    except ValueError:
        return 'unknown', reading


def render(rows, incidents):
    last_check = rows[-1]['Timestamp'] if rows else 'No data yet'

    status_cards = ""
    for server in SERVERS:
        state, reading = current_status(rows, server)
        uptime = uptime_pct(rows, server)
        status_cards += f"""
        <div class="card">
          <div class="card-header">
            <span class="dot {state}"></span>
            <span class="server-name">{LABELS[server]}</span>
          </div>
          <div class="reading">{reading}</div>
          <div class="uptime">{uptime:.2f}% uptime ({len(rows)} checks)</div>
        </div>"""

    # Most recent incidents first; open ones (no End_Time) sort to the top
    sorted_incidents = sorted(
        incidents,
        key=lambda i: (i['End_Time'] == '', i['Start_Time']),
        reverse=True
    )[:15]

    if sorted_incidents:
        incident_rows = ""
        for i in sorted_incidents:
            status = "OPEN" if not i['End_Time'] else "Resolved"
            duration = i['Duration_Minutes'] + " min" if i['Duration_Minutes'] else "ongoing"
            sev_class = i['Severity'].lower()
            incident_rows += f"""
        <tr>
          <td><span class="pill {sev_class}">{i['Severity']}</span></td>
          <td>{LABELS.get(i['Server'], i['Server'])}</td>
          <td>{i['Start_Time']}</td>
          <td>{i['End_Time'] or '—'}</td>
          <td>{duration}</td>
          <td>{status}</td>
        </tr>"""
        incidents_table = f"""
        <table>
          <thead>
            <tr><th>Severity</th><th>Server</th><th>Started</th><th>Ended</th><th>Duration</th><th>Status</th></tr>
          </thead>
          <tbody>{incident_rows}
          </tbody>
        </table>"""
    else:
        incidents_table = '<p class="empty">No incidents recorded. All checks have been healthy.</p>'

    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Chaski-Link Status</title>
<style>
  :root {{
    --bg: #0f1115;
    --card: #1a1d24;
    --border: #2a2e38;
    --text: #e8e9ec;
    --muted: #9aa0ab;
    --up: #3ddc84;
    --degraded: #f4b740;
    --down: #ef4444;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    margin: 0;
    padding: 32px 16px;
  }}
  .container {{ max-width: 860px; margin: 0 auto; }}
  h1 {{ font-size: 1.6rem; margin-bottom: 4px; }}
  .subtitle {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 28px; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-bottom: 36px; }}
  .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 16px 18px; }}
  .card-header {{ display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }}
  .server-name {{ font-weight: 600; }}
  .dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
  .dot.up {{ background: var(--up); }}
  .dot.degraded {{ background: var(--degraded); }}
  .dot.down {{ background: var(--down); }}
  .dot.unknown {{ background: var(--muted); }}
  .reading {{ font-size: 1.3rem; font-weight: 600; margin-bottom: 4px; }}
  .uptime {{ color: var(--muted); font-size: 0.85rem; }}
  h2 {{ font-size: 1.1rem; margin-bottom: 14px; }}
  table {{ width: 100%; border-collapse: collapse; background: var(--card); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }}
  th, td {{ text-align: left; padding: 10px 14px; font-size: 0.88rem; border-bottom: 1px solid var(--border); }}
  th {{ color: var(--muted); font-weight: 600; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; }}
  tr:last-child td {{ border-bottom: none; }}
  .pill {{ padding: 2px 9px; border-radius: 999px; font-size: 0.78rem; font-weight: 600; }}
  .pill.offline {{ background: rgba(239,68,68,0.15); color: var(--down); }}
  .pill.degraded {{ background: rgba(244,183,64,0.15); color: var(--degraded); }}
  .empty {{ color: var(--muted); font-size: 0.9rem; }}
  .footer {{ color: var(--muted); font-size: 0.78rem; margin-top: 28px; }}
</style>
</head>
<body>
  <div class="container">
    <h1>Chaski-Link Status</h1>
    <p class="subtitle">Last check: {last_check}</p>

    <div class="cards">{status_cards}
    </div>

    <h2>Recent Incidents</h2>
    {incidents_table}

    <p class="footer">Generated {generated_at} &middot; <a href="https://github.com/seroLinen/chaski-link" style="color:var(--muted)">seroLinen/chaski-link</a></p>
  </div>
</body>
</html>
"""


def main():
    rows = load_log()
    incidents = load_incidents()
    html = render(rows, incidents)
    with open(OUTPUT_FILE, 'w') as f:
        f.write(html)
    print(f"Chaski-Link: {OUTPUT_FILE} generated.")


if __name__ == "__main__":
    main()
