# Benchmark Collector

A lightweight, dual-platform performance monitoring tool for **Android** and **iOS** system resource utilization, designed for benchmark testing and continuous performance analysis. It exports metrics in a Prometheus-compatible format for easy visualization with Grafana.
<img width="1250" height="641" alt="Screenshot 2026-05-21 at 13 53 25" src="https://github.com/user-attachments/assets/63add489-1f74-4a88-867f-f7674b7bd542" />

## Features

- **Real-time metric collection** for Android and iOS devices
- **Prometheus-compatible** metrics export
- **Grafana dashboard** for visualization (auto-provisioned)
- **Podman/Docker Compose** setup for quick deployment
- **Lightweight** with minimal overhead

## Metrics Collected

| Metric               | Description                    | Unit   | Android | iOS    |
| -------------------- | ------------------------------ | ------ | ------- | ------ |
| CPU Usage            | Total CPU utilization (summed across cores) | % (raw) | ✅ Yes   | ✅ Yes  |
| CPU Cores            | Number of CPU cores            | count  | ✅ Yes   | ✅ Yes  |
| Memory Usage         | Total, used, and free RAM      | bytes  | ✅ Yes   | ✅ Yes  |
| GPU Busy             | GPU load percentage (Mali/Adreno) | %      | ✅ Yes   | ❌ No*  |
| Disk I/O             | Read/Write operations          | KB/s   | ✅ Yes   | ❌ No*  |

*Placeholder metrics exist for feature parity, actively under development.*

## Prerequisites

- **Python 3.12**
- **For Android**: ADB (Android Debug Bridge) installed and configured.
- **For iOS**: `pymobiledevice3` (installed via `pip`) and an iOS device with developer disk image support.
- **Podman** virtual machine (Podman recommended, Docker supported but not tested).

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/timionius/benchmark_collector.git
cd benchmark_collector
```

### 2. Set up Python virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Quick Start

#### Android

1.  **Connect your Android device**:
    ```bash
    adb devices
    # Ensure your device is listed as "device"
    ```

2.  **Run the collector**:
    ```bash
    python app/collect_android.py
    ```

#### iOS

1.  **Start the `remoted` tunneling service (Required)**:
    This command creates a bridge for communication with the iOS device. It requires `sudo` and will run in the foreground.
    ```bash
    sudo pymobiledevice3 remote tunneld
    ```
    *Keep this terminal window open and running.*

2.  **In a new terminal, run the iOS collector**:
    ```bash
    python app/collect_ios.py
    ```

### With Prometheus and Grafana (Recommended)

1.  **Start the monitoring stack**:
    ```bash
    cd infra
    podman-compose up -d
    ```
    *Note: If using Docker, run `docker-compose up -d` (not tested).*

2.  **Run the collector with the Prometheus endpoint**:
    - **Android**:
        ```bash
        python app/collect_android.py
        ```
    - **iOS**:
        - **Terminal 1**: `sudo pymobiledevice3 remote tunneld`
        - **Terminal 2**: `python app/collect_ios.py`
    
    *Collectors default to port `8000`.*

3.  **Access Grafana dashboard**:
    - URL: `http://localhost:3000`
    - Username: `admin`
    - Password: `admin` (change on first login)
    - The dashboard will be auto-provisioned.

4.  **View metrics at**:
    - Prometheus: `http://localhost:9090`
    - Metrics endpoint: `http://localhost:8000/metrics`

## Grafana Dashboard

The dashboard is auto-provisioned and includes:

- **CPU Performance Panel**: Real-time CPU usage normalized by core count.
- **Memory Monitor**: RAM consumption trends (displayed in bytes).
- **Platform Selector**: Toggle between Android and iOS views.
- **CPU Cores Variable**: Allows manual adjustment of core count for accurate normalization.

No manual import is required.

## Architecture Overview

### Android Collector
- Uses ADB to communicate with Android devices
- Reads metrics from `top` command output 
- Reports CPU as summed utilization across all cores (0-800% for 8-core devices)
- Reports RAM in bytes

### iOS Collector
- Uses `pymobiledevice3` with `remote tunneld` for secure communication
- Queries the `sysmon` system service for metrics
- Reports CPU as summed utilization across all cores via `CPU_TotalLoad` (0-600% for 6-core devices)
- Reports RAM in bytes using `physMemSize` and `vmFreeCount`

## Performance Impact

- **CPU overhead**: < 5% during collection
- **Memory usage**: ~50MB
- **Network bandwidth**: ~10KB/s (metrics export only)

## Troubleshooting

### Android

**Issue**: `adb shell top` command times out
**Solution**: The device may be under heavy load. Reduce collection frequency or check USB connection.

**Issue**: No metrics appearing in Prometheus
**Solution**: Verify the collector is running on port 8000 and Prometheus target is configured correctly.

### iOS

**Issue**: `pymobiledevice3 remote tunneld` fails with permission denied
**Solution**: Ensure you're using `sudo` as the command requires root privileges.

**Issue**: No data from sysmon
**Solution**: Verify the tunneld service is running and the iOS device is connected and trusted.

**Issue**: RAM shows 0 bytes free
**Solution**: This is normal iOS behavior. The system aggressively caches memory. Use `vmFreeCount` for accurate free memory reporting.

## License

MIT License

Copyright (c) 2026 Dmitrii Nikishov

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
