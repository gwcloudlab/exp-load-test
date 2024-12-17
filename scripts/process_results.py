import os
import re
import argparse

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def process_results(src_file: str, dest_file: str) -> None:

    if not os.path.exists(src_file):
        print(f'File not found: {src_file}')
        return

    # Read the log file
    with open(src_file, 'r') as f:
        lines = f.readlines()

    # Extract CSV-like data from log lines
    pattern = r'msg="([^"]+)"'
    data = [re.search(pattern, line).group(1) for line in lines if 'msg=' in line]

    # Split the CSV-like data into columns
    columns = ['timestamp', 'url', 'method', 'status', 'response_time', 'body_size']
    rows = [row.split(',') for row in data]

    # Create a DataFrame and save it as a CSV
    df = pd.DataFrame(rows, columns=columns)
    df.to_csv(dest_file, index=False)


def plot_rps_vs_cpu(df_join: pd.DataFrame, exp_dir: str) -> None:
    fig, ax1 = plt.subplots()

    ax1.set_xlabel('timestamp')
    ax1.set_ylabel('rps_loadgen', color='tab:blue')
    ax1.plot(df_join['timestamp'], df_join['rps_loadgen'], color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    ax2 = ax1.twinx()
    ax2.set_ylabel('cpu_server', color='tab:red')
    ax2.plot(df_join['timestamp'], df_join['cpu_server'], color='tab:red')
    ax2.tick_params(axis='y', labelcolor='tab:red')

    fig.tight_layout()

    os.makedirs(f"{exp_dir}/metrics/processed/plots", exist_ok=True)

    plt.savefig(f"{exp_dir}/metrics/processed/plots/rps_vs_cpu.png")


def plot_rps_vs_mem(df_join: pd.DataFrame, exp_dir: str) -> None:
    fig, ax1 = plt.subplots()

    ax1.set_xlabel('timestamp')
    ax1.set_ylabel('rps_loadgen', color='tab:blue')
    ax1.plot(df_join['timestamp'], df_join['rps_loadgen'], color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    ax2 = ax1.twinx()
    ax2.set_ylabel('mem_server', color='tab:red')
    ax2.plot(df_join['timestamp'], df_join['mem_server'], color='tab:red')
    ax2.tick_params(axis='y', labelcolor='tab:red')

    fig.tight_layout()

    os.makedirs(f"{exp_dir}/metrics/processed/plots", exist_ok=True)

    plt.savefig(f"{exp_dir}/metrics/processed/plots/rps_vs_mem.png")


def plot_response_time_vs_cpu(agg_merge: pd.DataFrame, exp_dir: str) -> None:
    fig, ax1 = plt.subplots()

    ax1.set_xlabel('timestamp')
    ax1.set_ylabel('response_time_mean', color='tab:blue')
    ax1.plot(agg_merge['timestamp'], agg_merge['response_time_mean'], color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    ax2 = ax1.twinx()
    ax2.set_ylabel('cpu_server', color='tab:red')
    ax2.plot(agg_merge['timestamp'], agg_merge['cpu_server'], color='tab:red')
    ax2.tick_params(axis='y', labelcolor='tab:red')

    fig.tight_layout()

    os.makedirs(f"{exp_dir}/metrics/processed/plots", exist_ok=True)

    plt.savefig(f"{exp_dir}/metrics/processed/plots/response_time_vs_cpu.png")



def plot_response_time_vs_mem(agg_merge: pd.DataFrame, exp_dir: str) -> None:
    fig, ax1 = plt.subplots()

    ax1.set_xlabel('timestamp')
    ax1.set_ylabel('response_time_mean', color='tab:blue')
    ax1.plot(agg_merge['timestamp'], agg_merge['response_time_mean'], color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    ax2 = ax1.twinx()
    ax2.set_ylabel('mem_server', color='tab:red')
    ax2.plot(agg_merge['timestamp'], agg_merge['mem_server'], color='tab:red')
    ax2.tick_params(axis='y', labelcolor='tab:red')

    fig.tight_layout()

    os.makedirs(f"{exp_dir}/metrics/processed/plots", exist_ok=True)

    plt.savefig(f"{exp_dir}/metrics/processed/plots/response_time_vs_mem.png")



def generate_merged_data(exp_dir: str) -> None:

    os.makedirs(f'{exp_dir}/metrics/processed/data', exist_ok=True)
    os.makedirs(f'{exp_dir}/metrics/processed/plots', exist_ok=True)

    loadgen_results = f"{exp_dir}/metrics/loadgen/results.csv"
    server_results = f"{exp_dir}/metrics/server/results.csv"

    if not os.path.exists(loadgen_results) or not os.path.exists(server_results):
        print(f'Files not found: {loadgen_results} or {server_results}')
        return
    
    df_l = pd.read_csv(loadgen_results).drop_duplicates(subset=["Timestamp (s)"])
    df_s = pd.read_csv(server_results).drop_duplicates(subset=["TIMESTAMP"])

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

    # replace time_server and time_loadgen with a single column named timestamp
    df_join['timestamp'] = df_join['time_server']
    df_join.drop(columns=['time_server', 'time_loadgen'], inplace=True)

    cols = list(df_join.columns)
    cols = cols[-1:] + cols[:-1]

    df_join = df_join[cols]

    df_join.to_csv(f'{exp_dir}/metrics/processed/data/merged_results.csv', index=False)

    plot_rps_vs_cpu(df_join, exp_dir)
    plot_rps_vs_mem(df_join, exp_dir)


    if os.path.exists(f"{exp_dir}/metrics/loadgen/per_req_results.csv"):
        per_req_data = pd.read_csv(f"{exp_dir}/metrics/loadgen/per_req_results.csv")

        agg_data = per_req_data.groupby('timestamp').agg({
            'response_time': ['mean', 'std', 'min', 'max'],
        }).reset_index()

        agg_data.columns = ['timestamp', 'response_time_mean', 'response_time_std', 'response_time_min', 'response_time_max']


        agg_merge = pd.merge(agg_data, df_join, how='inner', left_on='timestamp', right_on='timestamp')

        agg_merge.to_csv(f'{exp_dir}/metrics/processed/data/per_req_agg.csv', index=False)

        plot_response_time_vs_cpu(agg_merge, exp_dir)
        plot_response_time_vs_mem(agg_merge, exp_dir)


def parse_args():
    parser = argparse.ArgumentParser(description='Process log file and save as CSV')
    parser.add_argument('--exp-dir', type=str, help='Path to the log file')
    return parser.parse_args()


def main():
    args = parse_args()
    process_results(f'{args.exp_dir}/metrics/loadgen/out.txt', f'{args.exp_dir}/metrics/loadgen/per_req_results.csv') 
    generate_merged_data(args.exp_dir)

if __name__ == '__main__':
    main()
