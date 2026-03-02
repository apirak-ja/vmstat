"""
Sangfor VM Management Backend Configuration
"""
import os
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
from typing import Any, List
from pydantic import validator

# Find .env file in project root
def find_env_file():
    """Search for .env file in parent directories"""
    current = Path(__file__).resolve().parent
    for _ in range(5):  # Search up to 5 levels
        env_file = current / ".env"
        if env_file.exists():
            return str(env_file)
        # Also check in parent sangfor_scp directory
        parent_env = current.parent / ".env"
        if parent_env.exists():
            return str(parent_env)
        current = current.parent
    return None

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "VMStat API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database - read from environment or .env file
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "sangfor_scp"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    
    # Alternative env var names for compatibility
    pgSQL_HOST: str = ""
    pgSQL_HOST_PORT: int = 5432
    pgSQL_DBNAME: str = ""
    pgSQL_USERNAME: str = ""
    pgSQL_PASSWORD: str = ""
    
    @property
    def DATABASE_URL(self) -> str:
        # Prefer pgSQL_* vars if set, fallback to DB_* vars
        host = self.pgSQL_HOST or self.DB_HOST
        port = self.pgSQL_HOST_PORT if self.pgSQL_HOST else self.DB_PORT
        name = self.pgSQL_DBNAME or self.DB_NAME
        user = self.pgSQL_USERNAME or self.DB_USER
        password = self.pgSQL_PASSWORD or self.DB_PASSWORD
        
        encoded_password = quote_plus(password)
        return f"postgresql://{user}:{encoded_password}@{host}:{port}/{name}"
    
    # JWT Authentication
    SECRET_KEY: str = "vmstat-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS - ถ้าระบุเป็นสตริงให้คั่นด้วยจุลภาค เช่น CORS_ORIGINS=https://a,https://b
    #       หรือสามารถกำหนดเป็น JSON list ในตัวแปร environment ได้เลย
    CORS_ORIGINS: Any = "https://10.251.150.222:3345"

    @validator("CORS_ORIGINS", pre=True)
    def _parse_cors_origins(cls, v):
        # Accept comma-separated string or JSON array or list
        if isinstance(v, str):
            try:
                # try parse JSON array
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            # fallback split by comma
            return [o.strip() for o in v.split(",") if o.strip()]
        if isinstance(v, list):
            return v
        return [v]

    @property
    def CORS_ORIGINS_LIST(self) -> list:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [self.CORS_ORIGINS]
    
    # Sangfor SCP API Configuration
    SCP_IP: str = ""
    SCP_USERNAME: str = ""  # Sangfor admin username
    SCP_PASSWORD: str = ""  # Sangfor admin password
    SCP_TOKEN: str = ""     # Sangfor API Token for VM Control
    
    # Sync Settings
    SYNC_INTERVAL_MINUTES: int = 5
    SYNC_AUTO_START: bool = True  # เปิด auto-start scheduler เมื่อ backend restart
    
    class Config:
        # Try to find .env file
        env_file = find_env_file() or ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()
