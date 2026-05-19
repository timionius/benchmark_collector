from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    
    POLL_INTERVAL_SECONDS: int = 1
    PROMETHEUS_METRICS_PORT: int = 8000
    ENABLE_ANDROID: bool = True
    ENABLE_IOS: bool = True
    TARGET_PACKAGE_OR_BUNDLE_ID: Optional[str] = None
