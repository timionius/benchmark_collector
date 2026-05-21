import subprocess
import time
import json
import re
from prometheus_client import start_http_server, Gauge

# Define standard Prometheus metrics for iOS (matches Android dashboards)
CPU_USAGE = Gauge('ios_cpu_utilization_percent', 'Overall iOS CPU utilization percent')
RAM_TOTAL = Gauge('ios_ram_total_bytes', 'Total system RAM in bytes')
RAM_USED = Gauge('ios_ram_used_bytes', 'Used system RAM in bytes')
RAM_FREE = Gauge('ios_ram_free_bytes', 'Free system RAM in bytes')

# Placeholders to maintain metric parity with your Grafana layout
GPU_BUSY = Gauge('ios_gpu_busy_percent', 'Current GPU load percentage (Placeholder)')
DISK_READ_SPEED = Gauge('ios_disk_read_kb_per_sec', 'Disk read speed in KB/s (Placeholder)')
DISK_WRITE_SPEED = Gauge('ios_disk_write_kb_per_sec', 'Disk write speed in KB/s (Placeholder)')

class IOSMetricsCollector:
    def __init__(self):
        # Static zero initialization for hardware counters unsupported on stock iOS
        GPU_BUSY.set(0.0)
        DISK_READ_SPEED.set(0.0)
        DISK_WRITE_SPEED.set(0.0)
        
        # Cache the device's real physical RAM total
        self.device_total_ram = self.get_device_hardware_ram()
        RAM_TOTAL.set(self.device_total_ram)

    def get_device_hardware_ram(self) -> int:
        """Queries lockdown architecture to pull precise physical hardware memory size."""
        try:
            # Executes a quick command to fetch native hardware specifications
            res = subprocess.run(
                ['pymobiledevice3', 'lockdown', 'device-info'],
                capture_output=True, text=True, timeout=3
            )
            if res.returncode == 0 and res.stdout.strip():
                # Extract digits matching byte boundaries
                match = re.search(r'(?:TotalSystemMemory|MemorySize)\D+(\d+)', res.stdout, re.IGNORECASE)
                if match:
                    return int(match.group(1))
        except Exception:
            pass
        return 6 * 1024 * 1024 * 1024  # Fallback baseline floor (6GB) if lookup fails

    def collect_all_metrics(self):
        """Main execution loop that feeds all metrics to Prometheus."""
        self.collect_system_core_baselines()

    def collect_system_core_baselines(self):
        try:
            # Query Apple's sysmon architecture via the active tunneld local daemon
            result = subprocess.run(
                ['pymobiledevice3', 'developer', 'dvt', 'sysmon', 'process', 'single', '--tunnel', ''], 
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                self.parse_sysmon_output(result.stdout)
            else:
                print("Error: No data from tunneld proxy. Verify 'sudo pymobiledevice3 remote tunneld' is running.")
        except subprocess.TimeoutExpired:
            print("pymobiledevice3 command timed out")
        except Exception as e:
            print(f"Error checking iOS CPU/RAM: {e}")

    def parse_sysmon_output(self, output: str):
        try:
            # Extract valid JSON bounds if terminal noise or headers exist
            if "[" in output or "{" in output:
                json_start = min(output.find("[") if "[" in output else len(output), output.find("{") if "{" in output else len(output))
                clean_json = output[json_start:]
                data = json.loads(clean_json)
                
                # Check for standard process array payload format
                if isinstance(data, list):
                    total_cpu = 0.0
                    total_used_ram = 0
                    
                    for proc in data:
                        # FIX: Handle cases where cpuUsage is None or missing entirely
                        raw_cpu = proc.get('cpuUsage')
                        if raw_cpu is not None:
                            total_cpu += float(raw_cpu)
                        
                        # FIX: Handle cases where memory footprint keys are None or missing
                        ram_val = proc.get('memResidentSize', proc.get('physFootprint'))
                        if ram_val is not None:
                            total_used_ram += int(ram_val)
                    
                    # Publish data endpoints to Prometheus
                    CPU_USAGE.set(total_cpu)
                    RAM_USED.set(total_used_ram)
                    
                    # Dynamically calculate exact free RAM space
                    RAM_FREE.set(max(0, self.device_total_ram - total_used_ram))
                    return

                # Handle alternative system dictionary format
                elif isinstance(data, dict):
                    system_stats = data.get('systemAttributes', data)
                    if 'cpuUser' in system_stats or 'cpuUsage' in system_stats:
                        user_cpu = system_stats.get('cpuUser', system_stats.get('cpuUsage', 0.0))
                        sys_cpu = system_stats.get('cpuSystem', 0.0)
                        
                        user_val = float(user_cpu) if user_cpu is not None else 0.0
                        sys_val = float(sys_cpu) if sys_cpu is not None else 0.0
                        CPU_USAGE.set(user_val + sys_val)
                        
                        # Handle memory variables safely
                        m_total = system_stats.get('memTotal', self.device_total_ram)
                        m_used = system_stats.get('memUsed', 0)
                        m_free = system_stats.get('memFree', 0)
                        
                        RAM_TOTAL.set(int(m_total) if m_total is not None else self.device_total_ram)
                        RAM_USED.set(int(m_used) if m_used is not None else 0)
                        RAM_FREE.set(int(m_free) if m_free is not None else 0)
                        return
                    
            print("Warning: Parsed output but could not map keys. Check structure.")
        except json.JSONDecodeError:
            print("Parsing error: Could not interpret data stream format.")

if __name__ == '__main__':
    # Start Prometheus scraper daemon endpoint on port 8000
    start_http_server(8000)
    print("Prometheus iOS exporter running on port :8000...")
    
    collector = IOSMetricsCollector()
    while True:
        collector.collect_all_metrics()
        time.sleep(0.5)

