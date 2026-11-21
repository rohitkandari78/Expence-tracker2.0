"""
Configuration Module for AI Controller.
Loads settings from environment variables using Pydantic Settings.
"""
from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path


class Settings(BaseSettings):
    # Environment & Server
    ENVIRONMENT: str = Field(default="development", description="Runtime environment")
    PORT: int = Field(default=8000, description="Server port")
    HOST: str = Field(default="0.0.0.0", description="Server host binding")
    
    # CORS Origins - supports comma-separated string or list
    CORS_ORIGINS: Union[str, List[str]] = Field(
        default="https://expensetracker-phi-lac.vercel.app,https://expence-traker-min.netlify.app,http://localhost:3000,http://127.0.0.1:5500,http://localhost:5500,http://localhost:8000",
        description="Allowed CORS origins"
    )

    # Google Gemini Settings
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API Key")
    GEMINI_MODEL: str = Field(default="gemini-1.5-flash", description="Gemini model name")

    # Firebase Admin Settings
    FIREBASE_PROJECT_ID: str = Field(default="yourmemo-9dec5", description="Firebase project ID")
    FIREBASE_SERVICE_ACCOUNT_PATH: Optional[str] = Field(
        default=None, 
        description="Path to Firebase service account JSON file"
    )
    FIREBASE_SERVICE_ACCOUNT_JSON: Optional[str] = Field(
        default=None,
        description="Raw JSON string or base64 of Firebase service account"
    )

    # ChromaDB Vector Store
    CHROMA_PERSIST_DIRECTORY: str = Field(
        default=str(Path(__file__).resolve().parent / "chroma_db"),
        description="Directory for ChromaDB persistent storage"
    )
    EMBEDDING_MODEL_NAME: str = Field(
        default="all-MiniLM-L6-v2",
        description="SentenceTransformer embedding model name"
    )

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a sanitized list of strings."""
        if isinstance(self.CORS_ORIGINS, list):
            return [o.strip() for o in self.CORS_ORIGINS if o.strip()]
        if isinstance(self.CORS_ORIGINS, str):
            return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        return ["https://expence-traker-min.netlify.app"]


# Singleton instance
settings = Settings()
