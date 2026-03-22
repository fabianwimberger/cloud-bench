# Run Benchmarks Locally

Run the same benchmarks used by cloud-bench on your own machine or server to get a point of reference against the [official results](https://fabianwimberger.github.io/cloud-bench/).

## Quick Start

```bash
git clone https://github.com/fabianwimberger/cloud-bench.git
cd cloud-bench
sudo bash scripts/run-local-bench.sh
```

## Requirements

- Linux with a supported package manager (apt, pacman, dnf, yum, zypper, apk)
- Root access (for installing tools and direct disk I/O)
- The script installs `sysbench`, `fio`, `jq`, and `bc` if not already present

## What It Runs

| Benchmark | Tool | Parameters |
|-----------|------|------------|
| CPU single-thread | sysbench | `--cpu-max-prime=20000 --threads=1` |
| CPU multi-thread | sysbench | `--cpu-max-prime=20000 --threads=<nproc>` |
| Memory read | sysbench | `--memory-oper=read --memory-total-size=1G` |
| Memory write | sysbench | `--memory-oper=write --memory-total-size=1G` |
| Disk IOPS | fio | `randread bs=4k iodepth=32 direct=1 runtime=20s` |

Each benchmark runs **5 times** and the **median** is taken — identical to the official cloud-bench methodology.

## Output

- A JSON file (`bench-<hostname>-<date>.json`) in the current directory
- A summary table printed to the terminal

The JSON format matches the official benchmark result structure, so you can directly compare values against the results on the [dashboard](https://fabianwimberger.github.io/cloud-bench/).

## Notes

- Results are local only and are not uploaded anywhere.
- Disk IOPS depends heavily on the storage type (NVMe vs SSD vs HDD) and filesystem. For a fair comparison, ensure `direct=1` I/O is supported on your setup.
- Running on a busy system will affect results. For best accuracy, minimize other workloads during the benchmark.
