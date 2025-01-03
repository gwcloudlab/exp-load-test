#!/bin/bash
# External dependencies:
# - https://www.selenic.com/smem/
# - https://stedolan.github.io/jq/
# - iproute2 (for ss command)
set -eEuo pipefail

trap 'last_command=$BASH_COMMAND;signal_received="EXIT";cleanup "$cpuf" "$memf" "$bandwidthf" "$sockf" "$vusf" "$rpsf" "$url_without_protocol" "$error_log" "$exp_dir";exit 0' EXIT
trap 'last_command=$BASH_COMMAND;signal_received="INT";trap - INT; cleanup "$cpuf" "$memf" "$bandwidthf" "$sockf" "$vusf" "$rpsf" "$url_without_protocol" "$error_log" "$exp_dir";kill -INT $$' INT
trap 'last_command=$BASH_COMMAND;signal_received="TERM";trap - TERM;cleanup "$cpuf" "$memf" "$bandwidthf" "$sockf" "$vusf" "$rpsf" "$url_without_protocol" "$error_log" "$exp_dir";kill -TERM $$' TERM
trap 'last_command=$BASH_COMMAND;signal_received="ERR";cleanup "$cpuf" "$memf" "$bandwidthf" "$sockf" "$vusf" "$rpsf" "$url_without_protocol" "$error_log" "$exp_dir";exit 1' ERR

# Create temp files to store the output of each collection command.
cpuf=$(mktemp)
memf=$(mktemp)
bandwidthf=$(mktemp)
sockf=$(mktemp)
vusf=$(mktemp)
rpsf=$(mktemp)
error_log=$(mktemp)

url=${BENCHMARK_URL:-http://localhost:8080}
url_without_protocol=$(echo "$url" | sed 's|http[s]*://||; s|/$||')
sint="${BENCH_SAMPLE_INTERVAL:-1}"
device=$(ip route get "$url_without_protocol" | awk '{for (i=1; i<NF; i++) if ($i == "dev") print $(i+1)}')

function cleanup {
    exit_status=$?
    cpuf=${1:-}
    memf=${2:-}
    bandwidthf=${3:-}
    sockf=${4:-}
    vusf=${5:-}
    rpsf=${6:-}
    url_without_protocol=${7:-}
    error_log=${8:-}
    exp_dir=${9:-}
  
    echo "Cleaning up..."
    echo "Sending benchmarking end signal to the server." && \
        echo "BENCHMARKING_END" | nc ${url_without_protocol} 30000 || true
    if [ $exit_status -ne 0 ]; then
        echo "Received signal: $signal_received" || true
        echo "Last command: $last_command" || true
        echo "Exit status: $exit_status" || true
    fi

    rm -f "$cpuf" "$memf" "$bandwidthf" "$sockf" "$vusf" "$rpsf"
    cp $error_log ${exp_dir}/error.log
    echo "Error log saved to ${exp_dir}/error.log"
    echo "Cleanup complete."
}

# Redirect all stdout to both the console and the error_log file
exec > >(tee -a "$error_log") 2>&1

echo "cpu file: $cpuf"
echo "mem file: $memf"
echo "bandwidth file: $bandwidthf"
echo "sock file: $sockf"
echo "vus file: $vusf"
echo "rps file: $rpsf"
echo "error log: $error_log"

# 5s is the default interval between samples.
# Note that this might be greater if either smem or the k6 API takes more time
# than this to return a response.

echo "benchmarking $url endpoint ($url_without_protocol) with tool $TOOL"
echo "benchmark url: ${BENCHMARK_URL}<"

if [ -z "${TOOL:-}" ]; then
    echo "TOOL environment variable must be set to specify the tool to benchmark"
    exit 1
fi
tool=${TOOL}

exp_dir="${EXPERIMENT_DIR}"

mkdir -p "$exp_dir"
results_file="${exp_dir}/results.csv"
out_file="${exp_dir}/out.txt"

rm -f "$results_file" "$out_file"
touch "$results_file" "$out_file"

echo "error log: $error_log"

# Maximum bandwidth capacity in KB/s (e.g., 1 Gbps = 125000 KB/s)
# Get the maximum bandwidth capacity using ethtool
max_bandwidth_mbps=$(sudo ethtool "$device" | awk '/Speed:/ {print $2}' | sed 's/Mb\/s//')
if [ -z "$max_bandwidth_mbps" ]; then
  echo "Error: Unable to determine max bandwidth for device $device"
  exit 1
fi
max_bandwidth_kbps=$((max_bandwidth_mbps * 1024 / 8))

echo "using device $device with max bandwidth $max_bandwidth_kbps KB/s"

# Run the collection processes in parallel to avoid blocking.
# For details see https://stackoverflow.com/a/68316571

K6_WEB_DASHBOARD=true K6_WEB_DASHBOARD_EXPORT=${exp_dir}/exp_report.html k6 run "$@" -e URL="$url" -e EXP_DIR="${exp_dir}" >$out_file 2>&1 &
pid="$!"

echo "pid is $pid"
echo '"Timestamp (s)","CPU (%)","MEM (KB)","Bandwidth (KB/s)","Bandwidth Utilization (%)","Open Sockets","VUS","RPS"' > $results_file
while true; do

    # Check if the process is still running
    if ! ps -p "$pid" > /dev/null; then
        echo "Process $pid has terminated. Exiting loop."
        break
    fi
  
    echo "Collecting metrics for process $pid"

    pids=()
    
    { 
        exec >"$bandwidthf" 2>>"$error_log"; sudo ifstat -i "$device" "$sint" 1 | awk 'NR==3 {print $1 + $2}'; 
    } &
    pids+=($!)

    { 
        exec >"$cpuf" 2>>"$error_log"; top -b -n 2 -d "$sint" -p "$pid" | { grep "$pid" || echo; } | tail -1 | awk '{print (NF>0 ? $9 : "0")}'; 
    } &
    pids+=($!)

    { 
        exec >"$memf" 2>>"$error_log"; sudo smem -H -U "$USER" -c 'pid pss' -P "$tool" | { grep "$pid" || echo 0; } | awk '{ sum += $NF } END { print sum }'; 
    } &
    pids+=($!)


    { 
        exec >"$sockf" 2>>"$error_log"; sudo ss -tp | grep -c "$tool" || true; 
    } &
    pids+=($!)

    { 
        exec >"$vusf"; { 
            curl -fsSL http://localhost:6565/v1/metrics/vus 2>/dev/null || echo '{}'
        } | jq '.data.attributes.sample.value // 0'; 
    } &
    pids+=($!)
  
    { 
        exec >"$rpsf"; { 
            curl -fsSL http://localhost:6565/v1/metrics/http_reqs 2>/dev/null || echo '{}'
        } | jq '.data.attributes.sample.rate // 0'; 
    } &
    pids+=($!)

    trap - EXIT
    trap - INT
    trap - TERM
    trap - ERR
    wait "${pids[@]}" 
    waitstatus=$?
    if [ $waitstatus -ne 0 ]; then
        echo "Error: One or more background processes failed with exit status $waitstatus"
        cat "$error_log"
        exit 1
    fi
    
    trap 'last_command=$BASH_COMMAND;signal_received="EXIT";cleanup "$cpuf" "$memf" "$bandwidthf" "$sockf" "$vusf" "$rpsf" "$url_without_protocol" "$error_log" "$exp_dir";exit 0' EXIT
    trap 'last_command=$BASH_COMMAND;signal_received="INT";trap - INT; cleanup "$cpuf" "$memf" "$bandwidthf" "$sockf" "$vusf" "$rpsf" "$url_without_protocol" "$error_log" "$exp_dir";kill -INT $$' INT
    trap 'last_command=$BASH_COMMAND;signal_received="TERM";trap - TERM;cleanup "$cpuf" "$memf" "$bandwidthf" "$sockf" "$vusf" "$rpsf" "$url_without_protocol" "$error_log" "$exp_dir";kill -TERM $$' TERM
    trap 'last_command=$BASH_COMMAND;signal_received="ERR";cleanup "$cpuf" "$memf" "$bandwidthf" "$sockf" "$vusf" "$rpsf" "$url_without_protocol" "$error_log" "$exp_dir";exit 1' ERR

    
    bandwidth=$(cat "$bandwidthf")
    bandwidth_utilization=$(awk -v bw="$bandwidth" -v max_bw="$max_bandwidth_kbps" 'BEGIN { printf "%.2f", (bw / max_bw) * 100 }')
    open_sockets=$(cat "$sockf")
    timestamp=$(date +%s)
    vus=$(cat "$vusf")
    rps=$(cat "$rpsf")
    echo "${timestamp},$(cat "$cpuf"),$(cat "$memf"),${bandwidth},${bandwidth_utilization},${open_sockets},${vus},${rps}" >> $results_file
done