#!/usr/bin/env bash
# run-local-bench.sh — Run the same benchmarks used by cloud-bench on your own machine.
# Usage: sudo bash scripts/run-local-bench.sh
#
# Supported: Debian/Ubuntu (apt), Arch/Manjaro (pacman), Fedora/RHEL (dnf/yum),
#            openSUSE (zypper), Alpine (apk). Installs sysbench, fio, jq if missing.
# Output: JSON result file + terminal summary table.

set -euo pipefail

NUM_RUNS=5
SYSBENCH_CPU_PRIME=20000
SYSBENCH_MEMORY_SIZE=1G
FIO_SIZE=512M
FIO_BLOCK_SIZE=4k
FIO_IODEPTH=32
FIO_RUNTIME=20

RESULTS_DIR=$(mktemp -d)
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
OUTPUT_FILE="bench-$(hostname)-$(date +%Y%m%d-%H%M%S).json"

cleanup() { rm -rf "$RESULTS_DIR"; }
trap cleanup EXIT

# --- helpers ----------------------------------------------------------------

info()  { printf "\033[1;34m[*]\033[0m %s\n" "$*"; }
ok()    { printf "\033[1;32m[+]\033[0m %s\n" "$*"; }
err()   { printf "\033[1;31m[!]\033[0m %s\n" "$*" >&2; }

median_of_file() {
    local idx=$(( (NUM_RUNS + 1) / 2 ))
    sort -n "$1" | sed -n "${idx}p"
}

# --- preflight --------------------------------------------------------------

if [ "$(id -u)" -ne 0 ]; then
    err "Please run as root: sudo bash $0"
    exit 1
fi

info "Checking dependencies..."
MISSING=()
for tool in sysbench fio jq bc; do
    command -v "$tool" &>/dev/null || MISSING+=("$tool")
done

install_packages() {
    if command -v apt-get &>/dev/null; then
        apt-get update -qq
        apt-get install -y -qq "$@"
    elif command -v pacman &>/dev/null; then
        pacman -Sy --noconfirm "$@"
    elif command -v dnf &>/dev/null; then
        dnf install -y "$@"
    elif command -v yum &>/dev/null; then
        yum install -y "$@"
    elif command -v zypper &>/dev/null; then
        zypper install -y "$@"
    elif command -v apk &>/dev/null; then
        apk add "$@"
    else
        err "No supported package manager found (apt, pacman, dnf, yum, zypper, apk)"
        err "Please install manually: $*"
        exit 1
    fi
}

if [ ${#MISSING[@]} -gt 0 ]; then
    info "Installing: ${MISSING[*]}"
    install_packages "${MISSING[@]}"
fi

VCPUS=$(nproc)
info "Detected $VCPUS vCPU(s)"
info "Running $NUM_RUNS iterations per benchmark (median taken)"
echo

# --- CPU single-thread ------------------------------------------------------

info "CPU single-thread (sysbench cpu --threads=1 --cpu-max-prime=$SYSBENCH_CPU_PRIME)"
for i in $(seq 1 $NUM_RUNS); do
    sysbench cpu --cpu-max-prime=$SYSBENCH_CPU_PRIME --threads=1 run \
        | grep "events per second" | awk '{print $4}'
done > "$RESULTS_DIR/cpu-single-raw.txt"
CPU_SINGLE=$(median_of_file "$RESULTS_DIR/cpu-single-raw.txt")
ok "CPU single-thread: $CPU_SINGLE events/sec"

# --- CPU multi-thread -------------------------------------------------------

info "CPU multi-thread (sysbench cpu --threads=$VCPUS --cpu-max-prime=$SYSBENCH_CPU_PRIME)"
for i in $(seq 1 $NUM_RUNS); do
    sysbench cpu --cpu-max-prime=$SYSBENCH_CPU_PRIME --threads=$VCPUS run \
        | grep "events per second" | awk '{print $4}'
done > "$RESULTS_DIR/cpu-multi-raw.txt"
CPU_MULTI=$(median_of_file "$RESULTS_DIR/cpu-multi-raw.txt")
ok "CPU multi-thread:  $CPU_MULTI events/sec"

# --- Memory read ------------------------------------------------------------

info "Memory read (sysbench memory --memory-oper=read --memory-total-size=$SYSBENCH_MEMORY_SIZE)"
for i in $(seq 1 $NUM_RUNS); do
    sysbench memory --memory-oper=read --memory-total-size=$SYSBENCH_MEMORY_SIZE --threads=$VCPUS run \
        | grep "transferred" | sed -n 's/.*(\([0-9.]*\) MiB\/sec.*/\1/p' | head -1
done > "$RESULTS_DIR/mem-read-raw.txt"
MEM_READ=$(median_of_file "$RESULTS_DIR/mem-read-raw.txt")
ok "Memory read:       $MEM_READ MiB/sec"

# --- Memory write -----------------------------------------------------------

info "Memory write (sysbench memory --memory-oper=write --memory-total-size=$SYSBENCH_MEMORY_SIZE)"
for i in $(seq 1 $NUM_RUNS); do
    sysbench memory --memory-oper=write --memory-total-size=$SYSBENCH_MEMORY_SIZE --threads=$VCPUS run \
        | grep "transferred" | sed -n 's/.*(\([0-9.]*\) MiB\/sec.*/\1/p' | head -1
done > "$RESULTS_DIR/mem-write-raw.txt"
MEM_WRITE=$(median_of_file "$RESULTS_DIR/mem-write-raw.txt")
ok "Memory write:      $MEM_WRITE MiB/sec"

# --- Disk IOPS --------------------------------------------------------------

info "Disk IOPS (fio randread bs=$FIO_BLOCK_SIZE iodepth=$FIO_IODEPTH runtime=${FIO_RUNTIME}s)"
for i in $(seq 1 $NUM_RUNS); do
    fio --name=randread --ioengine=libaio --iodepth=$FIO_IODEPTH \
        --rw=randread --bs=$FIO_BLOCK_SIZE --direct=1 --size=$FIO_SIZE \
        --numjobs=1 --runtime=$FIO_RUNTIME \
        --group_reporting --output-format=json \
        | jq '.jobs[0].read.iops | round'
done > "$RESULTS_DIR/disk-iops-raw.txt"
DISK_IOPS=$(median_of_file "$RESULTS_DIR/disk-iops-raw.txt")
ok "Disk IOPS:         $DISK_IOPS"

# --- Compute totals ---------------------------------------------------------

MEM_TOTAL=$(echo "$MEM_READ + $MEM_WRITE" | bc)

# --- Build JSON output ------------------------------------------------------

jq -n \
    --arg hostname "$(hostname)" \
    --arg timestamp "$TIMESTAMP" \
    --argjson runs "$NUM_RUNS" \
    --argjson vcpus "$VCPUS" \
    --arg arch "$(uname -m)" \
    --arg kernel "$(uname -r)" \
    --argjson ram_kb "$(grep MemTotal /proc/meminfo | awk '{print $2}')" \
    --argjson cpu_single "$CPU_SINGLE" \
    --argjson cpu_multi "$CPU_MULTI" \
    --argjson mem_read "$MEM_READ" \
    --argjson mem_write "$MEM_WRITE" \
    --argjson mem_total "$MEM_TOTAL" \
    --argjson disk_iops "$DISK_IOPS" \
    '{
      hostname: $hostname,
      timestamp: $timestamp,
      benchmark_runs: $runs,
      aggregation: "median",
      system: {
        arch: $arch,
        kernel: $kernel,
        vcpus: $vcpus,
        ram_gb: (($ram_kb / 1048576) | round)
      },
      cpu: {
        single_thread_events: $cpu_single,
        multi_thread_events: $cpu_multi
      },
      memory: {
        read_mib_per_sec: $mem_read,
        write_mib_per_sec: $mem_write,
        total_throughput_mib: $mem_total
      },
      disk: {
        read_iops: $disk_iops
      }
    }' > "$OUTPUT_FILE"

# --- Summary ----------------------------------------------------------------

echo
echo "================================================================"
echo "  cloud-bench local results — $(hostname)"
echo "================================================================"
printf "  %-24s %s\n" "CPU single-thread:" "$CPU_SINGLE events/sec"
printf "  %-24s %s\n" "CPU multi-thread:" "$CPU_MULTI events/sec"
printf "  %-24s %s\n" "Memory read:" "$MEM_READ MiB/sec"
printf "  %-24s %s\n" "Memory write:" "$MEM_WRITE MiB/sec"
printf "  %-24s %s\n" "Memory total:" "$MEM_TOTAL MiB/sec"
printf "  %-24s %s\n" "Disk IOPS:" "$DISK_IOPS"
echo "================================================================"
echo "  vCPUs: $VCPUS | Arch: $(uname -m) | Kernel: $(uname -r)"
echo "  Results saved to: $OUTPUT_FILE"
echo "================================================================"
echo
echo "Compare your results at https://fabianwimberger.github.io/cloud-bench/"
