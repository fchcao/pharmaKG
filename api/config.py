#===========================================================
# 制药行业知识图谱 - API 配置
# Pharmaceutical Knowledge Graph - API Configuration
#===========================================================
# 版本: v1.0
# 创建日期: 2025-02-06
#===========================================================

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """API配置"""

    # 应用配置
    APP_NAME: str = "PharmaKG API"
    APP_VERSION: str = "v1.0"
    API_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Neo4j 配置
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "pharmaKG2024!"
    NEO4J_DATABASE: str = "neo4j"

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # CORS配置
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:7474",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # 分页配置
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # 缓存配置
    CACHE_TTL: int = 3600  # 1小时

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 限流配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # 秒

    # API密钥配置（可选）
    API_KEY_HEADER: str = "X-API-Key"
    API_KEYS: list[str] = []

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 创建配置实例
settings = Settings()
