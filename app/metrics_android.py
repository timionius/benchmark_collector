import subprocess
import time
from typing import Optional

class AndroidMetricsCollector:
    def __init__(self, settings):
        self.settings = settings

    def collect_system_core_baselines(self) -> dict:
        try:
            result = subprocess.run(['adb', 'shell', 'top', '-n', '1', '-b'], capture_output=True, text=True, timeout=2)
            if result.returncode != 0:
                raise Exception(f"Failed to run adb command: {result.stderr}")
            return self.parse_top_output(result.stdout)
        except subprocess.TimeoutExpired:
            print("adb command timed out")
            return {}
        except Exception as e:
            print(f"Error collecting system core baselines: {e}")
            return {}

    def collect_app_specific_footprint(self, package_name: Optional[str] = None) -> dict:
        try:
            if package_name:
                result = subprocess.run(['adb', 'shell', 'dumpsys', 'meminfo', package_name], capture_output=True, text=True, timeout=2)
                if result.returncode != 0:
                    raise Exception(f"Failed to run adb command: {result.stderr}")
                return self.parse_meminfo_output(result.stdout, package_name)
            else:
                return {}
        except subprocess.TimeoutExpired:
            print("adb command timed out")
            return {}
        except Exception as e:
            print(f"Error collecting app-specific footprint: {e}")
            return {}

    def collect_graphics_and_fluidity(self, package_name: Optional[str] = None) -> dict:
        try:
            if package_name:
                result = subprocess.run(['adb', 'shell', 'dumpsys', 'gfxinfo', package_name], capture_output=True, text=True, timeout=2)
                if result.returncode != 0:
                    raise Exception(f"Failed to run adb command: {result.stderr}")
                return self.parse_gfxinfo_output(result.stdout)
            else:
                return {}
        except subprocess.TimeoutExpired:
            print("adb command timed out")
            return {}
        except Exception as e:
            print(f"Error collecting graphics and fluidity metrics: {e}")
            return {}

    def collect_thermal_and_battery_stress(self) -> dict:
        try:
            result = subprocess.run(['adb', 'shell', 'dumpsys', 'battery'], capture_output=True, text=True, timeout=2)
            if result.returncode != 0:
                raise Exception(f"Failed to run adb command: {result.stderr}")
            return self.parse_battery_output(result.stdout)
        except subprocess.TimeoutExpired:
            print("adb command timed out")
            return {}
        except Exception as e:
            print(f"Error collecting thermal and battery stress metrics: {e}")
            return {}

    @staticmethod
    def parse_top_output(output: str) -> dict:
        lines = output.split('\n')
        for line in lines:
            if 'PID' in line:
                continue
            parts = line.strip().split()
            if len(parts) >= 10:
                pid, user, system, cpu, mem, vss, rss, pss, dtb, cmd = parts[:10]
                return {
                    'cpu': float(cpu),
                    'rss': int(rss)
                }
        return {}

    @staticmethod
    def parse_meminfo_output(output: str, package_name: str) -> dict:
        lines = output.split('\n')
        for line in lines:
            if package_name in line and 'TOTAL' in line:
                parts = line.strip().split()
                pss = int(parts[1])
                rss = int(parts[2])
                return {
                    'pss': pss,
                    'rss': rss
                }
        return {}

    @staticmethod
    def parse_gfxinfo_output(output: str) -> dict:
        lines = output.split('\n')
        total_frames = 0
        janky_frames = 0
        dropped_frames = 0
        for line in lines:
            if 'FrameType' in line:
                parts = line.strip().split()
                frame_type = parts[1]
                if frame_type == 'Total':
                    total_frames = int(parts[2])
                elif frame_type == 'Janky':
                    janky_frames = int(parts[2])
                elif frame_type == 'Dropped':
                    dropped_frames = int(parts[2])
        return {
            'total_frames': total_frames,
            'janky_frames': janky_frames,
            'dropped_frames': dropped_frames
        }

    @staticmethod
    def parse_battery_output(output: str) -> dict:
        lines = output.split('\n')
        temperature = None
        current_draw = None
        for line in lines:
            if 'temperature' in line:
                parts = line.strip().split()
                temperature = float(parts[1]) / 10.0
            elif 'current' in line:
                parts = line.strip().split()
                current_draw = int(parts[1])
        return {
            'temperature': temperature,
            'current_draw': current_draw
        }
