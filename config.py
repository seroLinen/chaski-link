"""
Chaski-Link: shared configuration

The single list of servers to monitor. monitor.py, analyze.py and
dashboard.py all read from here, so adding a server is a one-place change.

Column names (the dict keys) become the CSV headers. Don't rename an
existing one, or its history will be split across two columns.
"""

SERVERS = {
    # name:            (ip,               label,        graph color)
    "Google_DNS":     ("8.8.8.8",         "Google",     "#4285F4"),
    "Cloudflare_DNS": ("1.1.1.1",         "Cloudflare", "#F38020"),
    "Quad9_DNS":      ("9.9.9.9",         "Quad9",      "#66C2A5"),
    "OpenDNS":        ("208.67.222.222",  "OpenDNS",    "#8E6BBF"),
    "AdGuard_DNS":    ("94.140.14.14",    "AdGuard",    "#E0568B"),
    "Level3_DNS":     ("4.2.2.1",         "Level3",     "#B8A400"),
}

IPS = {name: ip for name, (ip, _, _) in SERVERS.items()}
LABELS = {name: label for name, (_, label, _) in SERVERS.items()}
COLORS = {name: color for name, (_, _, color) in SERVERS.items()}
