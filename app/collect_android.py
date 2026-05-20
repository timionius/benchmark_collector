import subprocess
import time
import re
from typing import Optional
from prometheus_client import start_http_server, Gauge

# Define standard Prometheus metrics
CPU_USAGE = Gauge('android_cpu_utilization_percent', 'Overall Android CPU utilization percent')
RAM_TOTAL = Gauge('android_ram_total_bytes', 'Total system RAM in bytes')
RAM_USED = Gauge('android_ram_used_bytes', 'Used system RAM in bytes')
RAM_FREE = Gauge('android_ram_free_bytes', 'Free system RAM in bytes')
GPU_FREQ = Gauge('android_gpu_frequency_mhz', 'Current GPU Frequency in MHz')
GPU_BUSY = Gauge('android_gpu_busy_percent', 'Current GPU load percentage')
DISK_READ_SPEED = Gauge('android_disk_read_kb_per_sec', 'Disk read speed in KB/s')
DISK_WRITE_SPEED = Gauge('android_disk_write_kb_per_sec', 'Disk write speed in KB/s')

class AndroidMetricsCollector:
    def __init__(self):
        pass

    def collect_all_metrics(self):
        """Main execution loop that feeds all metrics to Prometheus."""
        self.collect_system_core_baselines()
        self.collect_gpu_metrics()
        self.collect_disk_io()

    def collect_system_core_baselines(self):
        try:
            result = subprocess.run(['adb', 'shell', 'top', '-n', '1', '-b'], capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                self.parse_top_output(result.stdout)
        except Exception as e:
            print(f"Error checking CPU/RAM: {e}")

    def parse_top_output(self, output: str):
        lines = output.split('\n')
        for line in lines:
            # 1. Parse RAM Statistics (e.g., "Mem:      5.3G total,      4.9G used...")
            if "Mem:" in line:
                parts = line.strip().split()
                # Helper closure to normalize units (G/M) to standard bytes for Prometheus
                def to_bytes(val_str):
                    num = float(re.sub(r'[a-zA-Z]', '', val_str))
                    if 'G' in val_str: return num * 1024 * 1024 * 1024
                    if 'M' in val_str: return num * 1024 * 1024
                    return num
                
                RAM_TOTAL.set(to_bytes(parts[1]))
                RAM_USED.set(to_bytes(parts[3]))
                RAM_FREE.set(to_bytes(parts[5]))

            # 2. Parse CPU Statistics (e.g., "800%cpu  31%user...")
            if "%cpu" in line:
                parts = line.strip().split()
                # Find the element with idle data (e.g., "745%idle")
                idle_str = next((x for x in parts if "idle" in x), "0%idle")
                total_cpu_str = next((x for x in parts if "cpu" in x), "100%cpu")
                
                max_cpu = float(total_cpu_str.replace('%cpu', ''))
                idle_cpu = float(idle_str.replace('%idle', ''))
                
                # Active CPU = Total Available Core Capacity - Idle Capacity
                active_cpu_pct = max_cpu - idle_cpu
                CPU_USAGE.set(active_cpu_pct)

    def collect_gpu_metrics(self):
        """Grabs architecture-independent rendering load metrics."""
        try:
            # Check Qualcomm Adreno counters first
            res = subprocess.run(['adb', 'shell', 'cat', '/sys/class/kgsl/kgsl-3d0/gpu_busy_percentage'], capture_output=True, text=True, timeout=1)
            if res.returncode == 0 and res.stdout.strip():
                GPU_BUSY.set(float(res.stdout.strip().replace('%', '')))
                return

            # Check MediaTek Mali counters (your top dump shows an 'mivr' MediaTek thread)
            res = subprocess.run(['adb', 'shell', 'cat', '/sys/module/mali_kbase/parameters/mali_gpu_utilization'], capture_output=True, text=True, timeout=1)
            if res.returncode == 0 and res.stdout.strip():
                GPU_BUSY.set(float(res.stdout.strip()))
        except Exception:
            pass

    def collect_disk_io(self):
        """Parses active block layer read/write changes via iostat."""
        try:
            res = subprocess.run(['adb', 'shell', 'iostat', '1', '1'], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                lines = res.stdout.strip().split('\n')
                for line in lines:
                    # Look for the primary hardware flash drive partition
                    if 'mmcblk0' in line or 'dm-0' in line or 'sda' in line:
                        parts = line.split()
                        # standard iostat structure columns 3 & 4 contain kB_read/s and kB_wrtn/s
                        DISK_READ_SPEED.set(float(parts[2]))
                        DISK_WRITE_SPEED.set(float(parts[3]))
                        break
        except Exception:
            pass

if __name__ == '__main__':
    # Start Prometheus scraper daemon endpoint on port 8000
    start_http_server(8000)
    print("Prometheus Android exporter running on port :8000...")
    
    collector = AndroidMetricsCollector()
    while True:
        collector.collect_all_metrics()
        time.sleep(0.5)  # Scraper resolution step interval

