"""
Configuration settings following SOLID principles
Single Responsibility: Configuration management only
"""

from functools import lru_cache
from typing import List
from pydantic import BaseSettings, validator
import os


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Application
    APP_NAME: str = "APRA Compliance Monitoring"
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: str = "mysql+pymysql://compliance:password@localhost:3306/compliance_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Redis (for caching and background tasks)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Compliance Rules
    APRA_RULES_ENABLED: bool = True
    REAL_TIME_MONITORING: bool = True
    VIOLATION_ALERT_THRESHOLD: float = 0.8
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    LOG_LEVEL: str = "INFO"
    
    @validator("ALLOWED_HOSTS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    Following DRY principle - single source of configuration
    """
    return Settings()
