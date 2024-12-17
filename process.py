import seaborn as sns
import pandas as pd

df_l = pd.read_csv('metrics/loadgen/results.csv')
df_s = pd.read_csv('metrics/server/results.csv')

df_s.rename(
    columns={
        "TIMESTAMP": "time_server",
        "CPU": "cpu_server",
        "MEM": "mem_server",
    },
    inplace=True
)

df_l.rename(
    columns={
        "Timestamp (s)": "time_loadgen",
        "CPU (%)": "cpu_loadgen",
        "MEM (KB)": "mem_loadgen",
        "Bandwidth (KB/s)": "bandwidth_loadgen",
        "Bandwidth Utilization (%)": "bandwidth_utilization_loadgen",
        "Open Sockets": "open_sockets_loadgen",
        "VUS": "vus_loadgen",
        "RPS": "rps_loadgen"
    },
    inplace=True
)

last_timestamp_l = int(df_l['time_loadgen'].iloc[-1])
last_timestamp_s = int(df_s['time_server'].iloc[-1])


min_last_ts = min(last_timestamp_l, last_timestamp_s)

df_s = df_s[df_s['time_server'] <= min_last_ts]
df_l = df_l[df_l['time_loadgen'] <= min_last_ts]

df_join = pd.merge(df_s, df_l, how='inner', left_on='time_server', right_on='time_loadgen')

import re
import pandas as pd

# Read the log file
with open('metrics/loadgen/out.txt', 'r') as f:
    lines = f.readlines()

# Extract CSV-like data from log lines
pattern = r'msg="([^"]+)"'
data = [re.search(pattern, line).group(1) for line in lines if 'msg=' in line]

# Split the CSV-like data into columns
columns = ['timestamp', 'url', 'method', 'status', 'response_time', 'body_size']
rows = [row.split(',') for row in data]

# Create a DataFrame and save it as a CSV
df = pd.DataFrame(rows, columns=columns)
df.to_csv('metrics/loadgen/per_req_data.csv', index=False)

# line plot of two y axis and one x axis
# y1 = cpu_loadgen
# y2 = rps_loadgen
# x = time_loadgen

import seaborn as sns
import matplotlib.pyplot as plt

sns.set(rc={'figure.figsize':(15, 5)})
sns.lineplot(x='time_loadgen', y='cpu_loadgen', data=df_join, color='blue')
plt.show()
sns.lineplot(x='time_loadgen', y='rps_loadgen', data=df_join, color='red')
plt.show()

