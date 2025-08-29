from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path

class WebSettings(BaseSettings):
    """ Web interface settings """

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    environment: str = "development"

    # Security settings
    secret_key: str = "your-secret-key" #TODO: change in production
    access_token_expire_minutes: int = 30
    allowed_origins: List[str] = ["http://localhost:3000","http://localhost:8000"]
    allowed_hosts: List[str] = ["localhost","127.0.0.1"]

    # Athena system integration
    athena_data_dir: Path("data")
    athena_settings_file: Optional[str] = None

    # Websocket settings
    websocket_heartbeat_interval: int = 30
    max_websocket_connections: int = 100

    # Rate limiting settings
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    class Config:
        env_file = ".env"
        env_prefix = "ATHENA_WEB_"

settings = WebSettings()