"""
Application configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    app_name: str = "Web Music Analyzer"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "music_analyzer"

    # OpenAI API
    openai_api_key: Optional[str] = None

    # Google Drive API
    google_credentials_path: Optional[str] = None

    # File upload
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    upload_dir: str = "/tmp/music_uploads"

    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
