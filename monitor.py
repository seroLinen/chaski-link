import socket
import time
import csv
import os
from datetime import datetime
from plyer import notification
from config import IPS
from incidents import update_incidents

# --- CONFIGURATION ---
# Threshold in milliseconds to trigger a Windows notification
LATENCY_THRESHOLD = 100.0 
LOG_FILE = 'network_log.csv'

def check_connectivity():
    """Checks latency for specific DNS servers individually."""
    servers = IPS

    results = {}
    any_high_latency = False
    
    for name, ip in servers.items():
        start = time.time()
        try:
            # Attempt a TCP connection to Port 53 (DNS)
            socket.create_connection((ip, 53), timeout=3).close()
            latency = (time.time() - start) * 1000
            results[name] = f"{latency:.2f}ms"
            
            if latency > LATENCY_THRESHOLD:
                any_high_latency = True
        except Exception:
            results[name] = "Offline"
            any_high_latency = True # Treat offline as a critical alert
            
    return results, any_high_latency

def send_chaski_alert(title, message):
    """Sends a Windows Toast Notification."""
    try:
        notification.notify(
            title=f"Chaski-Link: {title}",
            message=message,
            app_name="Chaski-Link NPM",
            timeout=10
        )
    except Exception as e:
        print(f"Notification failed: {e}")

def prepare_log(wanted):
    """
    Makes sure the log's header covers every column in `wanted`, and returns
    the full list of columns to write. If servers were added since the log
    was created, the header is widened and old rows get blanks for the new
    columns, so history is kept. Columns for servers that were later removed
    are kept too, so no data is ever dropped.
    """
    if not os.path.isfile(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
        return wanted

    with open(LOG_FILE, mode='r', newline='') as f:
        reader = csv.DictReader(f)
        existing = reader.fieldnames or []
        rows = list(reader)

    merged = list(existing) + [c for c in wanted if c not in existing]
    if merged != list(existing):
        with open(LOG_FILE, mode='w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=merged, restval='')
            writer.writeheader()
            writer.writerows(rows)
        print(f"Chaski-Link: log header widened to {len(merged)} columns")
    return merged


def main():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    results, alert_needed = check_connectivity()
    
    fieldnames = prepare_log(["Timestamp"] + list(results.keys()))

    with open(LOG_FILE, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, restval='')

        if f.tell() == 0:
            writer.writeheader()
            
        # Combine timestamp with our results dictionary
        row = {"Timestamp": timestamp}
        row.update(results)
        writer.writerow(row)

    print(f"Chaski-Link: Log updated at {timestamp}")

    # Open/close incidents based on this run's readings
    still_open = update_incidents(results, LATENCY_THRESHOLD, timestamp)
    if still_open:
        open_summary = ", ".join(f"{i['Server']} ({i['Severity']})" for i in still_open)
        print(f"Chaski-Link: {len(still_open)} open incident(s): {open_summary}")

    # Trigger local notification if thresholds were hit
    if alert_needed:
        status_summary = ", ".join([f"{k}: {v}" for k, v in results.items()])
        send_chaski_alert("Network Alert", status_summary)

if __name__ == "__main__":
    main()