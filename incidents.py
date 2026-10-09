"""
Chaski-Link: Incident Tracking

Turns raw latency readings into open/closed incident records, the same
basic concept a ticketing system (ServiceNow, Zendesk, etc.) uses: a
problem opens a record when it starts, and the record closes itself when
the problem goes away.

A server is considered "Offline" if the connection failed outright, or
"Degraded" if it responded but slower than LATENCY_THRESHOLD. Anything
else is healthy and has no open incident.
"""

import csv
import json
import os
from datetime import datetime

INCIDENTS_FILE = 'incidents.csv'
# Written fresh on every run (not committed): what opened or closed this run,
# so the workflow can turn it into GitHub issues.
EVENTS_FILE = 'incident_events.json'
FIELDNAMES = ['Incident_ID', 'Server', 'Severity', 'Start_Time', 'End_Time', 'Duration_Minutes']


def load_incidents():
    """Returns all incident rows (open and closed) as a list of dicts."""
    if not os.path.isfile(INCIDENTS_FILE):
        return []
    with open(INCIDENTS_FILE, mode='r', newline='') as f:
        return list(csv.DictReader(f))


def save_incidents(rows):
    with open(INCIDENTS_FILE, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def _parse_latency(value):
    """Returns a float ms value, or None if the server was offline or unparsable."""
    if value == 'Offline':
        return None
    try:
        return float(str(value).replace('ms', ''))
    except ValueError:
        return None


def _severity(value, threshold):
    """Returns 'Offline', 'Degraded', or None (healthy) for one reading."""
    if value == 'Offline':
        return 'Offline'
    latency = _parse_latency(value)
    if latency is not None and latency > threshold:
        return 'Degraded'
    return None


def update_incidents(results, threshold, timestamp):
    """
    Given this run's {server_name: reading} results, open new incidents,
    escalate existing ones (Degraded -> Offline), and close incidents for
    servers that have recovered. Returns the list of incidents still open
    after this update, so the caller can decide whether to alert.
    """
    rows = load_incidents()
    open_by_server = {row['Server']: row for row in rows if not row['End_Time']}
    next_id = (max((int(r['Incident_ID']) for r in rows), default=0)) + 1
    opened, closed = [], []

    for server, value in results.items():
        severity = _severity(value, threshold)
        existing = open_by_server.get(server)

        if severity:
            if existing:
                # Escalate silently if it got worse (Degraded -> Offline)
                if severity == 'Offline' and existing['Severity'] != 'Offline':
                    existing['Severity'] = 'Offline'
            else:
                new_row = {
                    'Incident_ID': str(next_id),
                    'Server': server,
                    'Severity': severity,
                    'Start_Time': timestamp,
                    'End_Time': '',
                    'Duration_Minutes': '',
                }
                rows.append(new_row)
                opened.append(dict(new_row, Reading=value))
                next_id += 1
        else:
            if existing:
                existing['End_Time'] = timestamp
                start_dt = datetime.strptime(existing['Start_Time'], '%Y-%m-%d %H:%M:%S')
                end_dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                duration = (end_dt - start_dt).total_seconds() / 60
                existing['Duration_Minutes'] = f"{duration:.1f}"
                closed.append(dict(existing))

    save_incidents(rows)
    with open(EVENTS_FILE, mode='w') as f:
        json.dump({'opened': opened, 'closed': closed}, f, indent=2)
    return [row for row in rows if not row['End_Time']]
