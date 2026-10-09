import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# 1. Load the data
try:
    df = pd.read_csv('network_log.csv')
except FileNotFoundError:
    print("Error: network_log.csv not found.")
    exit()

# 2. Data Cleaning: mark outages distinctly instead of flattening them to 100ms.
#    (monitor.py writes the literal string "Offline" on a failed connection)
OUTAGE_LABELS = ['Timeout/Error', 'Offline']
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

cols = ['Google_DNS', 'Cloudflare_DNS', 'Quad9_DNS']
outage_mask = df[cols].isin(OUTAGE_LABELS)

for col in cols:
    df[col] = df[col].astype(str).str.replace('ms', '', regex=False)
    df[col] = pd.to_numeric(df[col], errors='coerce')  # outages become NaN (gap in the line)

# 3. Create the plot — bigger canvas and higher DPI so it's actually legible
fig, ax = plt.subplots(figsize=(16, 8), dpi=200)

colors = {'Google_DNS': '#4285F4', 'Cloudflare_DNS': '#F38020', 'Quad9_DNS': '#66C2A5'}
labels = {'Google_DNS': 'Google', 'Cloudflare_DNS': 'Cloudflare', 'Quad9_DNS': 'Quad9'}

for col in cols:
    ax.plot(df['Timestamp'], df[col], label=labels[col], color=colors[col],
            marker='o', markersize=3, linewidth=1.3)
    # Mark outages as red X's at the bottom of the chart so they're visible
    # even though the line itself has a gap there.
    outages = df.loc[outage_mask[col], 'Timestamp']
    if not outages.empty:
        ax.scatter(outages, [0] * len(outages), color='red', marker='x',
                   s=60, zorder=5, label=f'{labels[col]} outage' if col == cols[0] else None)

# 4. Formatting
ax.set_title('Chaski-Link: Network Latency Analysis', fontsize=18, pad=15)
ax.set_xlabel('Time of Check', fontsize=12)
ax.set_ylabel('Latency (ms)', fontsize=12)
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(fontsize=11, loc='upper left')
ax.tick_params(axis='both', labelsize=10)

# Only show a handful of evenly-spaced x-axis labels instead of every single
# timestamp, which is what was crushing them together unreadably.
ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=15, prune=None))
fig.autofmt_xdate(rotation=45, ha='right')

fig.tight_layout()

# 5. Save
fig.savefig('latency_report.png', dpi=200, bbox_inches='tight')
print("Success! 'latency_report.png' has been generated in your folder.")