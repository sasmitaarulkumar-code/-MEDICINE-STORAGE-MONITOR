import os
from dataclasses import dataclass

@dataclass
class Settings:
    PROJECT_NAME: str = "MEDGUARD"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("MEDGUARD_SECRET_KEY", "medguard-super-secure-production-key-2026-hackathon")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    DEVICE_API_KEY: str = os.getenv("MEDGUARD_DEVICE_KEY", "medguard-device-secret-key-2026")
    
    # Database (SQLite with WAL mode)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///C:/Users/HP/.gemini/antigravity/scratch/medguard/backend/medguard.db"
    )
    
    # Threshold & Risk Defaults
    DEFAULT_MIN_TEMP: float = 2.0
    DEFAULT_MAX_TEMP: float = 8.0
    DEFAULT_MIN_HUMIDITY: float = 30.0
    DEFAULT_MAX_HUMIDITY: float = 65.0
    DOOR_OPEN_WARNING_SECONDS: int = 45
    DOOR_OPEN_CRITICAL_SECONDS: int = 180

settings = Settings()
