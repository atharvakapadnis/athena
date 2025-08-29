from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path
import os

class WebSettings(BaseSettings):
    """Enhanced web interface configuration for internal network deployment"""
    
    # Server settings optimized for internal network
    host: str = "0.0.0.0"  # Accept connections from entire internal network
    port: int = 8000
    debug: bool = False  # Always False in production
    environment: str = "production"
    workers: int = 4  # Optimize for internal server hardware
    
    # Security settings for trusted internal network
    secret_key: str = "athena-internal-network-key-change-in-production"
    access_token_expire_minutes: int = 480  # 8 hours for internal use
    allowed_origins: List[str] = [
        "http://localhost:3000", 
        "http://localhost:8000",
        "http://192.168.*",  # Internal network range
        "http://10.*",       # Internal network range
        "http://172.16.*"    # Internal network range
    ]
    allowed_hosts: List[str] = ["*"]  # Accept from any internal host
    
    # Athena system integration
    athena_data_dir: Path = Path("data")
    athena_settings_file: Optional[str] = None
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Performance settings for internal deployment
    websocket_heartbeat_interval: int = 30
    max_websocket_connections: int = 50  # Reasonable for internal use
    request_timeout: int = 300  # 5 minutes for long-running operations
    
    # Caching for internal network
    enable_caching: bool = True
    cache_ttl: int = 300  # 5 minutes default
    max_cache_size: int = 1000  # Reasonable memory usage
    
    # Rate limiting (relaxed for internal network)
    rate_limit_requests: int = 1000  # High limit for internal users
    rate_limit_window: int = 60
    
    # Logging optimized for internal deployment
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: Optional[str] = "logs/web.log"
    enable_access_log: bool = True
    
    # Development and debugging features for internal use
    enable_docs: bool = True  # Keep API docs available internally
    enable_metrics: bool = True
    enable_profiling: bool = False  # Enable only when needed
    
    class Config:
        env_file = ".env"
        env_prefix = "ATHENA_WEB_"

settings = WebSettings()

# Internal network deployment validation
def validate_internal_deployment():
    """Validate configuration for internal network deployment"""
    issues = []
    
    if settings.debug:
        issues.append("Debug mode should be disabled in production")
    
    if settings.secret_key == "athena-internal-network-key-change-in-production":
        issues.append("Please change the default secret key")
    
    if not settings.openai_api_key:
        issues.append("OpenAI API key not found - AI features will be disabled")
    
    if not settings.athena_data_dir.exists():
        settings.athena_data_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created data directory: {settings.athena_data_dir}")
    
    if issues:
        print("⚠️  Configuration Issues (Internal Deployment):")
        for issue in issues:
            print(f"   • {issue}")
        print()
    
    print("🏢 Internal Network Deployment Configuration:")
    print(f"   • Server: http://{settings.host}:{settings.port}")
    print(f"   • Environment: {settings.environment}")
    print(f"   • Workers: {settings.workers}")
    print(f"   • Data Directory: {settings.athena_data_dir}")
    print(f"   • API Documentation: http://{settings.host}:{settings.port}/api/docs")
    print(f"   • AI Features: {'Enabled' if settings.openai_api_key else 'Disabled'}")
    print()