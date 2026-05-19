import logging
from typing import Optional

import pymobiledevice3.lockdown
from pymobiledevice3.services.diagnostics import DiagnosticsService
from pymobiledevice3.services.device_info import DeviceInfo

logger = logging.getLogger(__name__)

class IOSMetricsCollector:
    def __init__(self, settings):
        self.settings = settings
        self.lockdownd_client = None
        self.diagnostics_service = None
        self.device_info = None

    def initialize_device(self):
        try:
            self.lockdownd_client = pymobiledevice3.lockdown.LockdownClient()
            self.diagnostics_service = DiagnosticsService(self.lockdownd_client)
            self.device_info = DeviceInfo(self.lockdownd_client)
        except Exception as e:
            logger.error(f"Failed to initialize iOS device: {e}")
            return False
        return True

    def collect_system_core_baselines(self) -> dict:
        if not self.initialize_device():
            return {}

        try:
            cpu_usage = self.device_info.cpuUsage()
            memory_allocations = self.device_info.memoryAllocations()
            return {
                'cpu_usage': cpu_usage,
                'memory_allocations': memory_allocations
            }
        except Exception as e:
            logger.error(f"Failed to collect system core baselines: {e}")
            return {}

    def collect_app_specific_footprint(self, bundle_id: Optional[str] = None) -> dict:
        if not self.initialize_device():
            return {}

        try:
            if bundle_id:
                app_info = self.diagnostics_service.getAppInfo(bundle_id)
                return {
                    'app_name': app_info['CFBundleName'],
                    'app_version': app_info['CFBundleVersion']
                }
            else:
                # Fallback metric baseline if detailed application isolation is blocked
                return {
                    'app_specific_footprint': 0
                }
        except Exception as e:
            logger.error(f"Failed to collect app-specific footprint: {e}")
            return {}

    def collect_thermal_and_battery_stress(self) -> dict:
        if not self.initialize_device():
            return {}

        try:
            battery_info = self.diagnostics_service.getBatteryInfo()
            thermal_state = self.device_info.thermalState()
            return {
                'battery_current_draw': battery_info['CurrentCapacity'],
                'thermal_state': thermal_state
            }
        except Exception as e:
            logger.error(f"Failed to collect thermal and battery stress: {e}")
            return {}
