"""
Configuration management for the application.
Loads and validates environment variables.
"""

import os
import json
from typing import Optional, Union, Any, List
from pydantic import Field, field_validator, model_validator, computed_field
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys - Groq (OpenAI-compatible)
    groq_api_key: str = Field(..., env="GROQ_API_KEY")
    groq_api_url: str = Field(default="https://api.groq.com/openai/v1", env="GROQ_API_URL")
    groq_voice_api_key: Optional[str] = Field(None, env="GROQ_VOICE_API_KEY")
    groq_voice_api_url: str = Field(default="https://api.groq.com/openai/v1/audio", env="GROQ_VOICE_API_URL")
    
    # Database
    database_url: Optional[str] = Field(None, env="DATABASE_URL")
    
    # ChromaDB
    chroma_persist_dir: str = Field(default="./chroma_db", env="CHROMA_PERSIST_DIR")
    
    # External APIs
    overpass_api_url: str = Field(
        default="https://overpass-api.de/api/interpreter",
        env="OVERPASS_API_URL"
    )
    open_meteo_api_url: str = Field(
        default="https://api.open-meteo.com/v1",
        env="OPEN_METEO_API_URL"
    )
    
    # Google Maps API (Optional - falls back to OSRM if not set)
    google_maps_api_key: Optional[str] = Field(None, env="GOOGLE_MAPS_API_KEY")
    
    # n8n
    n8n_webhook_url: Optional[str] = Field(None, env="N8N_WEBHOOK_URL")
    
    # Application Settings
    app_name: str = Field(default="Voice-First Travel Assistant", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(None, env="LOG_FILE")
    
    # Server Settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # CORS Settings
    # Store as string to avoid JSON parsing issues, then parse via computed_field
    cors_origins_raw: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003",
        env="CORS_ORIGINS"
    )
    
    @field_validator('cors_origins_raw', mode='before')
    @classmethod
    def parse_cors_origins(cls, v: Any) -> str:
        """Parse CORS origins from string (comma-separated) or list.
        
        Always returns a string (comma-separated) to avoid JSON parsing issues.
        Handles:
        - Comma-separated string: "https://example.com,https://other.com"
        - Single string: "https://example.com"
        - JSON array string: '["https://example.com"]'
        - List: ["https://example.com"]
        """
        if v is None:
            return "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003"
        
        if isinstance(v, list):
            # Convert list to comma-separated string
            return ",".join(str(item) for item in v if item)
        
        if isinstance(v, str):
            # Try to parse as JSON first (for JSON array strings)
            try:
                parsed_json = json.loads(v)
                if isinstance(parsed_json, list):
                    return ",".join(str(item) for item in parsed_json if item)
                elif isinstance(parsed_json, str):
                    # Single string in JSON format
                    return parsed_json
            except (json.JSONDecodeError, ValueError):
                # Not JSON, treat as comma-separated string - return as is
                pass
            
            # Return the string as-is (already comma-separated or single value)
            return v.strip() if v.strip() else "http://localhost:3000"
        
        # Fallback: convert to string
        return str(v)
    
    @computed_field
    def cors_origins(self) -> List[str]:
        """Parse the raw CORS origins string into a list."""
        if not self._cors_origins_raw:
            return ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003"]
        
        # Parse comma-separated string
        parsed = [item.strip() for item in self._cors_origins_raw.split(',') if item.strip()]
        
        if not parsed:
            return ["http://localhost:3000"]
        
        # Check if any localhost ports are present
        has_localhost = any('localhost' in origin.lower() or '127.0.0.1' in origin.lower() for origin in parsed)
        
        if has_localhost:
            final_origins = list(parsed)
            # Add common development ports if not already present
            default_ports = [3000, 3001, 3002, 3003]
            for port in default_ports:
                localhost_url = f"http://localhost:{port}"
                if localhost_url not in final_origins:
                    final_origins.append(localhost_url)
            return final_origins
        
        return parsed
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: list = Field(
        default=["*"],
        env="CORS_ALLOW_METHODS"
    )
    cors_allow_headers: list = Field(
        default=["*"],
        env="CORS_ALLOW_HEADERS"
    )
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # Session Settings
    session_timeout_minutes: int = Field(default=60, env="SESSION_TIMEOUT_MINUTES")
    max_clarifying_questions: int = Field(default=6, env="MAX_CLARIFYING_QUESTIONS")
    
    # LLM Settings
    llm_model: str = Field(default="llama-3.3-70b-versatile", env="LLM_MODEL")  # Best Groq model for quality
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    max_tokens: int = Field(default=2000, env="MAX_TOKENS")
    
    # RAG Settings
    rag_top_k: int = Field(default=5, env="RAG_TOP_K")
    embedding_model: str = Field(
        default="text-embedding-3-small",
        env="EMBEDDING_MODEL"
    )
    
    @model_validator(mode='before')
    @classmethod
    def parse_cors_fields(cls, data: Any) -> Any:
        """Parse CORS fields from comma-separated strings before validation.
        
        Maps CORS_ORIGINS env var to cors_origins_raw field to avoid JSON parsing.
        """
        if isinstance(data, dict):
            # Map CORS_ORIGINS to cors_origins_raw to avoid JSON parsing
            if 'CORS_ORIGINS' in data:
                data['cors_origins_raw'] = data.pop('CORS_ORIGINS')
            elif 'cors_origins' in data:
                data['cors_origins_raw'] = data.pop('cors_origins')
            
            # Handle other CORS fields
            for key, value in list(data.items()):
                key_lower = key.lower()
                if key_lower in ['cors_allow_methods', 'cors_allow_headers']:
                    if isinstance(value, str):
                        parsed = [item.strip() for item in value.split(',') if item.strip()]
                        data[key] = parsed if parsed else ["*"]
                    elif value is None or value == '':
                        data[key] = ["*"]
        return data
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from env file


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings (cached).
    
    Returns:
        Settings instance
    """
    return Settings()


# Validate settings on import
settings = get_settings()

# Validate required settings
if not settings.groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable is required")
