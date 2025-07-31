"""
Smart Greenhouse IoT System - Configuration Settings
Environment-based configuration management
"""

from typing import List
from pydantic import validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Database Configuration
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "greenhouse"
    POSTGRES_USER: str = "greenhouse_user"
    POSTGRES_PASSWORD: str = "greenhouse_pass"
    
    @property
    def database_url(self) -> str:
        """Generate synchronous database URL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def async_database_url(self) -> str:
        """Generate asynchronous database URL"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # TimescaleDB Configuration
    TIMESCALEDB_ENABLED: bool = True
    TIMESCALE_CHUNK_TIME_INTERVAL: str = "1d"
    TIMESCALE_COMPRESSION_ENABLED: bool = True
    TIMESCALE_RETENTION_POLICY: str = "1y"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 100
    
    # Security Configuration
    JWT_SECRET_KEY: str = "your-super-secure-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    API_KEY_CACHE_TTL: int = 300  # 5 minutes
    SESSION_TTL: int = 86400  # 24 hours
    
    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = True
    DEFAULT_RATE_LIMIT: int = 120  # requests per minute
    SENSOR_DATA_RATE_LIMIT: int = 60
    ACTUATOR_CONTROL_RATE_LIMIT: int = 30
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    ALLOWED_HOSTS: List[str] = ["*"]  # Allow all hosts for IoT device access
    
    # File Storage Configuration
    UPLOAD_DIR: str = "/app/uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Monitoring Configuration
    ENABLE_METRICS: bool = True
    METRICS_RETENTION_DAYS: int = 30
    
    # Node Configuration
    NODE_HEARTBEAT_TIMEOUT_MINUTES: int = 5
    NODE_OFFLINE_THRESHOLD_MINUTES: int = 10
    
    # Data Retention Configuration
    SENSOR_DATA_RETENTION_DAYS: int = 365
    API_LOG_RETENTION_DAYS: int = 90
    
    # Background Tasks Configuration
    ENABLE_BACKGROUND_TASKS: bool = True
    CLEANUP_INTERVAL_HOURS: int = 24
    
    # Email Configuration (for alerts)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    
    @validator('ALLOWED_ORIGINS', pre=True)
    @classmethod
    def parse_origins(cls, v):
        """Parse ALLOWED_ORIGINS from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('ALLOWED_HOSTS', pre=True)
    @classmethod
    def parse_hosts(cls, v):
        """Parse ALLOWED_HOSTS from string or list"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(',')]
        return v
    
    @property
    def database_url(self) -> str:
        """Get PostgreSQL database URL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def async_database_url(self) -> str:
        """Get async PostgreSQL database URL"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()

# API Constants
API_V1_PREFIX = "/api"

# Node API Keys (in production, these should be in environment variables or database)
NODE_API_KEYS = {
    "gh001_api_key_abc123": "greenhouse_001",
    "gh002_api_key_def456": "greenhouse_002", 
    "gh003_api_key_ghi789": "greenhouse_003"
}

# User Roles
USER_ROLES = ["admin", "manager", "operator", "viewer"]

# Sensor Types
SENSOR_TYPES = ["temperature", "humidity", "soil_moisture", "light", "ph", "ec", "battery_percentage", "signal_strength", "voltage"]

# Actuator Types
ACTUATOR_TYPES = ["solenoid", "pump", "fan", "heater", "led", "valve"]

# Zone IDs (3x3 grid)
ZONE_IDS = [
    "A1", "A2", "A3",
    "B1", "B2", "B3", 
    "C1", "C2", "C3"
]

# Rate Limit Configurations
RATE_LIMITS = {
    "sensor_data": 60,      # requests per minute
    "actuator_control": 30,  # requests per minute
    "general_api": 120,     # requests per minute
    "auth": 10,             # requests per minute
    "analytics": 30         # requests per minute
}

# Default pagination
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000

# Time formats
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
DATE_FORMAT = "%Y-%m-%d"

# Health check configuration
HEALTH_CHECK_SERVICES = [
    "postgres",
    "timescaledb", 
    "redis"
]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
