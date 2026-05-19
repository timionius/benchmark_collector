import os
import signal
import time
from typing import Optional

import click
from dotenv import load_dotenv
from prometheus_client import start_http_server

from app.metrics_android import AndroidMetricsCollector
from app.metrics_ios import collect_ios_metrics
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
    if settings.enable_android:
        android_collector = AndroidMetricsCollector(settings)

    while True:
        try:
            print("Starting polling loop...")
            if settings.enable_android and android_collector:
                android_metrics = android_collector.collect_system_core_baselines()
                # Map parsed results to Prometheus Client Gauge metrics
                pass

            if settings.enable_ios:
                collect_ios_metrics()

            print("Polling loop completed. Sleeping for {settings.poll_interval_seconds} seconds.")
            time.sleep(settings.poll_interval_seconds)
        except Exception as e:
            print(f"An error occurred: {e}")
