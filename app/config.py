"""
Application configuration loaded from environment variables.
Copy .env.example to .env and fill in your credentials before running.
"""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Microsoft Azure / Entra ID credentials
    AZURE_TENANT_ID: str = ""
    AZURE_CLIENT_ID: str = ""
    AZURE_CLIENT_SECRET: str = ""

    # SharePoint / Graph settings
    SHAREPOINT_SITE_ID: str = ""          # Graph site-id (GUID or hostname:path)
    SHAREPOINT_DRIVE_ID: str = ""         # Drive id inside the site (optional)
    SHAREPOINT_ROOT_FOLDER: str = "root"  # Default folder path inside the drive

    # Analysis settings
    OPENAI_API_KEY: str = ""              # Optional – used for LLM-based analysis
    OPENAI_MODEL: str = "gpt-4o-mini"

    # App settings
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
