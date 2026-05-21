import subprocess
import time
import re
from prometheus_client import start_http_server, Gauge

# Define standard Prometheus metrics for iOS (matches Android dashboards)
CPU_USAGE = Gauge('ios_cpu_utilization_percent', 'Overall iOS CPU utilization percent (summed across cores, 0-600% for 6 cores)')
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
        
        # Page size on iOS is typically 16384 bytes (16KB)
        self.page_size = 16384
        
        # Get total RAM from sysmon
        self.device_total_ram = self.get_total_ram_from_sysmon()
        RAM_TOTAL.set(self.device_total_ram)
        
        print(f"Device total RAM: {self.device_total_ram:,} bytes ({self.device_total_ram / (1024*1024*1024):.1f} GB)")

    def get_total_ram_from_sysmon(self) -> int:
        """Get total RAM from sysmon physMemSize."""
        try:
            result = subprocess.run(
                ['pymobiledevice3', 'developer', 'dvt', 'sysmon', 'system', '--tunnel', ''],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # Use physMemSize for total physical RAM
                phys_mem_match = re.search(r'physMemSize:\s*(\d+)', output)
                if phys_mem_match:
                    total_pages = int(phys_mem_match.group(1))
                    total_bytes = total_pages * self.page_size
                    print(f"Found RAM via physMemSize: {total_pages} pages → {total_bytes:,} bytes ({total_bytes / (1024*1024*1024):.1f} GB)")
                    return total_bytes
                    
        except subprocess.TimeoutExpired:
            print("Timeout getting RAM from sysmon")
        except Exception as e:
            print(f"Error getting RAM from sysmon: {e}")
        
        # Fallback: Try to get from device model
        return self.get_ram_from_device_model()

    def get_ram_from_device_model(self) -> int:
        """Fallback: Get RAM based on device model."""
        try:
            result = subprocess.run(
                ['pymobiledevice3', 'lockdown', 'info'],
                capture_output=True, text=True, timeout=3
            )
            
            if result.returncode == 0:
                product_match = re.search(r'"ProductType":\s*"([^"]+)"', result.stdout)
                if product_match:
                    product_type = product_match.group(1)
                    
                    # iPhone RAM lookup table (in bytes)
                    ram_map = {
                        "iPhone15,4": 6 * 1024 * 1024 * 1024,  # iPhone 15 (6GB)
                        "iPhone15,5": 8 * 1024 * 1024 * 1024,  # iPhone 15 Plus (8GB)
                        "iPhone16,1": 8 * 1024 * 1024 * 1024,  # iPhone 15 Pro (8GB)
                        "iPhone16,2": 8 * 1024 * 1024 * 1024,  # iPhone 15 Pro Max (8GB)
                        "iPhone14,5": 6 * 1024 * 1024 * 1024,  # iPhone 14 (6GB)
                        "iPhone14,6": 4 * 1024 * 1024 * 1024,  # iPhone SE 3rd (4GB)
                        "iPhone13,2": 4 * 1024 * 1024 * 1024,  # iPhone 12 (4GB)
                        "iPhone13,3": 6 * 1024 * 1024 * 1024,  # iPhone 12 Pro (6GB)
                    }
                    
                    if product_type in ram_map:
                        print(f"Using device model fallback: {product_type} → {ram_map[product_type] / (1024*1024*1024):.1f} GB")
                        return ram_map[product_type]
                        
        except Exception as e:
            print(f"Error getting RAM from device model: {e}")
        
        print("Using default fallback: 6GB")
        return 6 * 1024 * 1024 * 1024

    def collect_all_metrics(self):
        """Main execution loop that feeds all metrics to Prometheus."""
        self.collect_system_core_baselines()

    def collect_system_core_baselines(self):
        try:
            # Query sysmon for system metrics
            result = subprocess.run(
                ['pymobiledevice3', 'developer', 'dvt', 'sysmon', 'system', '--tunnel', ''],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                self.parse_sysmon_system_output(result.stdout)
            else:
                print("Error: No data from sysmon. Verify tunneld is running.")
                
        except subprocess.TimeoutExpired:
            print("pymobiledevice3 command timed out")
        except Exception as e:
            print(f"Error checking iOS metrics: {e}")

    def parse_sysmon_system_output(self, output: str):
        """Parse key: value format from sysmon output."""
        try:
            metrics = {}
            
            # Parse each line in the output
            for line in output.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Convert numeric values
                    try:
                        if '.' in value:
                            metrics[key] = float(value)
                        else:
                            metrics[key] = int(value)
                    except ValueError:
                        metrics[key] = value
            
            # Extract CPU metrics - keep raw summed value (0-600% for 6 cores)
            if 'CPU_TotalLoad' in metrics:
                cpu_load = metrics['CPU_TotalLoad']
                CPU_USAGE.set(cpu_load)
                print(f"CPU Usage: {cpu_load:.1f}% (summed across {metrics.get('CPUCount', 6)} cores)")
            
            # Use physMemSize for total RAM (most accurate)
            if 'physMemSize' in metrics:
                total_pages = metrics['physMemSize']
                total_bytes = total_pages * self.page_size
                RAM_TOTAL.set(total_bytes)
                print(f"RAM Total: {total_bytes:,} bytes ({total_bytes / (1024*1024*1024):.2f} GB)")
            
            # Handle RAM Free and Used
            if 'vmFreeCount' in metrics:
                free_pages = metrics['vmFreeCount']
                free_bytes = free_pages * self.page_size
                RAM_FREE.set(free_bytes)
                print(f"RAM Free: {free_bytes:,} bytes ({free_bytes / (1024*1024*1024):.2f} GB)")
                
                # Calculate used = total - free
                if 'physMemSize' in metrics:
                    used_bytes = (metrics['physMemSize'] - free_pages) * self.page_size
                    RAM_USED.set(used_bytes)
                    print(f"RAM Used: {used_bytes:,} bytes ({used_bytes / (1024*1024*1024):.2f} GB)")
            elif 'vmUsedCount' in metrics and 'physMemSize' in metrics:
                # Alternative: use vmUsedCount if vmFreeCount not available
                used_bytes = metrics['vmUsedCount'] * self.page_size
                RAM_USED.set(used_bytes)
                print(f"RAM Used: {used_bytes:,} bytes ({used_bytes / (1024*1024*1024):.2f} GB)")
                
                # Calculate free = total - used
                free_bytes = (metrics['physMemSize'] - metrics['vmUsedCount']) * self.page_size
                RAM_FREE.set(free_bytes)
                print(f"RAM Free: {free_bytes:,} bytes ({free_bytes / (1024*1024*1024):.2f} GB)")
            
            # Print CPU core count for debugging
            if 'CPUCount' in metrics:
                print(f"CPU Cores: {metrics['CPUCount']} (max raw CPU: {metrics['CPUCount'] * 100}%)")
                
        except Exception as e:
            print(f"Error parsing sysmon output: {e}")

if __name__ == '__main__':
    # Start Prometheus scraper daemon endpoint on port 8000
    start_http_server(8000)
    print("=" * 60)
    print("Prometheus iOS Exporter")
    print("=" * 60)
    print("Metrics are reported in BYTES to match Android collector:")
    print("  - RAM values: bytes")
    print("  - CPU: raw summed utilization (0-600% for 6 cores)")
    print("  - Dashboard should divide CPU by cpu_cores for normalization")
    print("\nMake sure 'sudo pymobiledevice3 remote tunneld' is running in another terminal")
    print("=" * 60 + "\n")
    
    collector = IOSMetricsCollector()
    
    # Main collection loop
    while True:
        collector.collect_all_metrics()
        print("---")
        time.sleep(0.5)
