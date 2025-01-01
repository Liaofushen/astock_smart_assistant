from pydantic import BaseSettings
from typing import Optional
from pathlib import Path
import os

class Settings(BaseSettings):
    """应用配置类"""
    # 环境设置
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # 数据存储设置
    DATA_DIR: Path = Path("data")
    CACHE_DIR: Path = Path("cache")
    
    # API 设置
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    
    # 数据更新设置
    AUTO_UPDATE_INTERVAL: int = int(os.getenv("AUTO_UPDATE_INTERVAL", "3600"))  # 秒
    
    # 日志设置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: Path = Path("logs")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    def setup_directories(self):
        """确保所需目录存在"""
        for directory in [self.DATA_DIR, self.CACHE_DIR, self.LOG_DIR]:
            directory.mkdir(exist_ok=True)

# 创建全局设置实例
settings = Settings()
settings.setup_directories() 