# Benchmark Collector

A lightweight performance monitoring tool for Android system resource utilization, designed for benchmark testing and continuous performance analysis.
<img width="1259" height="396" alt="default_dashboard" src="https://github.com/user-attachments/assets/d86cdfdb-3751-47cd-b8f9-cfbbda59ef11" />


## Features

- **Real-time metric collection** for Android devices
- **Prometheus-compatible** metrics export
- **Grafana dashboard** for visualization (auto-provisioned)
- **Podman/Docker Compose** setup for quick deployment
- **Lightweight** with minimal overhead

## Metrics Collected

| Metric | Description | Unit | Status |
|--------|-------------|------|--------|
| CPU Usage (Total/User/System) | CPU utilization breakdown | Percentage | ✅ Available |
| Memory Usage | RAM consumption | MB/Percentage | ✅ Available |
| Disk I/O | Read/Write operations | MB/s | 🚧 In Development |
| Network Traffic | RX/TX bytes | KB/s | 🚧 In Development |
| Battery Level | Current battery status | Percentage | 🚧 In Development |
| Temperature | Device thermal status | Celsius | 🚧 In Development |
| FPS | Frames per second | FPS | 🚧 In Development |

## Prerequisites

- Python 3.12
- ADB (Android Debug Bridge) installed and configured
- Android device with USB debugging enabled
- Ready to use Podman virtual machine (Podman recommended, Docker supported but not tested)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/timionius/benchmark_collector.git 
cd benchmark_collector
```

### 2. Set up Python virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Quick Start

1. **Connect your Android device**
   ```bash
   adb devices
   # Ensure your device is listed as "device"
   ```

2. **Run the collector**
   ```bash
   python app/collect_android.py
   ```

### With Prometheus and Grafana (Recommended)

1. **Start the monitoring stack**
   ```bash
   podman machine list
   # check podman VM is running, list command should show you running VMs

   cd infra
   podman-compose up -d
   ```
   *Note: If using Docker, run `docker-compose up -d` (not tested)*

2. **Run the collector with Prometheus endpoint**
   ```bash
   python app/collect_android.py --exporter --port 8000
   ```

3. **Access Grafana dashboard**
   - URL: http://localhost:3000
   - Username: `admin`
   - Password: `admin` (change on first login)
   - Dashboard will be auto-provisioned

4. **View metrics at**
   - Prometheus: http://localhost:9090
   - Metrics endpoint: http://localhost:8000/metrics

## Grafana Dashboard

The dashboard is auto-provisioned and includes:

- **CPU Performance Panel**: Real-time CPU usage breakdown
- **Memory Monitor**: RAM consumption trends
- **Additional panels** for other metrics (disabled until development completes)

No manual import required - the dashboard will appear automatically when the stack starts.

## Performance Impact

- **CPU overhead**: < 5% during collection
- **Memory usage**: ~50MB
- **Network bandwidth**: ~10KB/s (metrics export only)

## License

MIT License

Copyright (c) 2026 Dmitrii Nikishov 

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
