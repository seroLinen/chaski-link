import socket
import time
import csv
import os
from datetime import datetime
from plyer import notification
from incidents import update_incidents

# --- CONFIGURATION ---
# Threshold in milliseconds to trigger a Windows notification
LATENCY_THRESHOLD = 100.0 
LOG_FILE = 'network_log.csv'

def check_connectivity():
    """Checks latency for specific DNS servers individually."""
    servers = {
        "Google_DNS": "8.8.8.8",
        "Cloudflare_DNS": "1.1.1.1",
        "Quad9_DNS": "9.9.9.9"
    }
    
    results = {}
    any_high_latency = False
    
    for name, ip in servers.items():
        start = time.time()
        try:
            # Attempt a TCP connection to Port 53 (DNS)
            socket.create_connection((ip, 53), timeout=3)
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

def main():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    results, alert_needed = check_connectivity()
    
    # Check if file exists to write headers
    file_exists = os.path.isfile(LOG_FILE)
    
    with open(LOG_FILE, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["Timestamp"] + list(results.keys()))
        
        if not file_exists:
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