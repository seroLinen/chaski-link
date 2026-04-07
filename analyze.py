import pandas as pd
import matplotlib.pyplot as plt

# 1. Load the data
try:
    df = pd.read_csv('network_log.csv')
except FileNotFoundError:
    print("Error: network_log.csv not found.")
    exit()

# 2. Data Cleaning: Convert 'Timeout/Error' or 'Offline' to 100ms (for the graph)
df.replace(['Timeout/Error', 'Offline'], 100.0, inplace=True)

# 3. Strip 'ms' and convert to floats for math
for col in ['Google_DNS', 'Cloudflare_DNS', 'Quad9_DNS']:
    df[col] = df[col].astype(str).str.replace('ms', '').astype(float)

# 4. Create the plot
plt.figure(figsize=(12, 6))

plt.plot(df['Timestamp'], df['Google_DNS'], label='Google', marker='o', markersize=4)
plt.plot(df['Timestamp'], df['Cloudflare_DNS'], label='Cloudflare', marker='o', markersize=4)
plt.plot(df['Timestamp'], df['Quad9_DNS'], label='Quad9', marker='o', markersize=4)

# Formatting the "Eyes"
plt.title('Chaski-Link: Network Latency Analysis', fontsize=14)
plt.xlabel('Time of Check', fontsize=10)
plt.ylabel('Latency (ms)', fontsize=10)
plt.xticks(rotation=45, ha='right')
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()

# 5. Save and Show
plt.savefig('latency_report.png')
print("Success! 'latency_report.png' has been generated in your folder.")