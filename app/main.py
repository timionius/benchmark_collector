import os
import signal
import time
from typing import Optional

import click
from dotenv import load_dotenv
from prometheus_client import start_http_server

from app.metrics_android import AndroidMetricsCollector
from app.metrics_ios import IOSMetricsCollector, collect_ios_metrics
from infra.settings import Settings

def signal_handler(sig, frame):
    print("Received signal to stop the engine gracefully.")
    os._exit(0)

@click.group()
def cli():
    pass

@cli.command()
def run_local():
    load_dotenv()

    settings = Settings()

    start_http_server(settings.prometheus_metrics_port)
    print(f"Prometheus metrics server started on port {settings.prometheus_metrics_port}")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    android_collector = None
    ios_collector = None

    if settings.enable_android:
        android_collector = AndroidMetricsCollector(settings)

    if settings.enable_ios:
        ios_collector = IOSMetricsCollector(settings)

    while True:
        try:
            print("Starting polling loop...")
            if settings.enable_android and android_collector:
                android_metrics = android_collector.collect_system_core_baselines()
                # Map parsed results to Prometheus Client Gauge metrics
                pass

            if settings.enable_ios and ios_collector:
                ios_metrics = ios_collector.collect_system_core_baselines()
                ios_app_specific_footprint = ios_collector.collect_app_specific_footprint(settings.ios_bundle_id)
                ios_thermal_and_battery_stress = ios_collector.collect_thermal_and_battery_stress()

                # Map parsed results to Prometheus Client Gauge metrics
                pass

            if settings.enable_ios:
                collect_ios_metrics(ios_metrics, ios_app_specific_footprint, ios_thermal_and_battery_stress)

            print("Polling loop completed. Sleeping for {settings.poll_interval_seconds} seconds.")
            time.sleep(settings.poll_interval_seconds)
        except Exception as e:
            print(f"An error occurred: {e}")
