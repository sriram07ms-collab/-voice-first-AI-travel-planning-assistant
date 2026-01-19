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
    
    @field_validator('port', mode='before')
    @classmethod
    def parse_port(cls, v: Any) -> int:
        """Parse port from string or int."""
        if v is None:
            return 8000
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return 8000
        return int(v)
    
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
        # Always include GitHub Pages URL for production deployment
        github_pages_url = "https://sriram07ms-collab.github.io"
        
        if not self.cors_origins_raw:
            origins = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003"]
        else:
            # Parse comma-separated string
            parsed = [item.strip() for item in self.cors_origins_raw.split(',') if item.strip()]
            
            if not parsed:
                origins = ["http://localhost:3000"]
            else:
                origins = list(parsed)
                
                # Check if any localhost ports are present
                has_localhost = any('localhost' in origin.lower() or '127.0.0.1' in origin.lower() for origin in origins)
                
                if has_localhost:
                    # Add common development ports if not already present
                    default_ports = [3000, 3001, 3002, 3003]
                    for port in default_ports:
                        localhost_url = f"http://localhost:{port}"
                        if localhost_url not in origins:
                            origins.append(localhost_url)
        
        # Always add GitHub Pages URL if not already present
        if github_pages_url not in origins:
            origins.append(github_pages_url)
        
        return origins
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    
    # Store as strings to avoid JSON parsing issues
    cors_allow_methods_raw: str = Field(
        default="*",
        env="CORS_ALLOW_METHODS"
    )
    cors_allow_headers_raw: str = Field(
        default="*",
        env="CORS_ALLOW_HEADERS"
    )
    
    @field_validator('cors_allow_methods_raw', mode='before')
    @classmethod
    def parse_cors_methods(cls, v: Any) -> str:
        """Parse CORS methods from string or list."""
        if v is None:
            return "*"
        if isinstance(v, list):
            return ",".join(str(item) for item in v if item)
        if isinstance(v, str):
            try:
                parsed_json = json.loads(v)
                if isinstance(parsed_json, list):
                    return ",".join(str(item) for item in parsed_json if item)
            except (json.JSONDecodeError, ValueError):
                pass
            return v.strip() if v.strip() else "*"
        return str(v)
    
    @field_validator('cors_allow_headers_raw', mode='before')
    @classmethod
    def parse_cors_headers(cls, v: Any) -> str:
        """Parse CORS headers from string or list."""
        if v is None:
            return "*"
        if isinstance(v, list):
            return ",".join(str(item) for item in v if item)
        if isinstance(v, str):
            try:
                parsed_json = json.loads(v)
                if isinstance(parsed_json, list):
                    return ",".join(str(item) for item in parsed_json if item)
            except (json.JSONDecodeError, ValueError):
                pass
            return v.strip() if v.strip() else "*"
        return str(v)
    
    @computed_field
    def cors_allow_methods(self) -> List[str]:
        """Parse the raw CORS methods string into a list."""
        if not self.cors_allow_methods_raw:
            return ["*"]
        parsed = [item.strip() for item in self.cors_allow_methods_raw.split(',') if item.strip()]
        return parsed if parsed else ["*"]
    
    @computed_field
    def cors_allow_headers(self) -> List[str]:
        """Parse the raw CORS headers string into a list."""
        if not self.cors_allow_headers_raw:
            return ["*"]
        parsed = [item.strip() for item in self.cors_allow_headers_raw.split(',') if item.strip()]
        return parsed if parsed else ["*"]
    
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
        
        Maps CORS env vars to _raw fields to avoid JSON parsing.
        """
        if isinstance(data, dict):
            # Map CORS_ORIGINS to cors_origins_raw
            if 'CORS_ORIGINS' in data:
                data['cors_origins_raw'] = data.pop('CORS_ORIGINS')
            elif 'cors_origins' in data:
                data['cors_origins_raw'] = data.pop('cors_origins')
            
            # Map CORS_ALLOW_METHODS to cors_allow_methods_raw
            if 'CORS_ALLOW_METHODS' in data:
                data['cors_allow_methods_raw'] = data.pop('CORS_ALLOW_METHODS')
            elif 'cors_allow_methods' in data:
                data['cors_allow_methods_raw'] = data.pop('cors_allow_methods')
            
            # Map CORS_ALLOW_HEADERS to cors_allow_headers_raw
            if 'CORS_ALLOW_HEADERS' in data:
                data['cors_allow_headers_raw'] = data.pop('CORS_ALLOW_HEADERS')
            elif 'cors_allow_headers' in data:
                data['cors_allow_headers_raw'] = data.pop('cors_allow_headers')
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
try:
    settings = get_settings()
    
    # Validate required settings
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is required")
except Exception as e:
    import sys
    print(f"ERROR: Failed to load settings: {e}", file=sys.stderr)
    print("Please ensure all required environment variables are set:", file=sys.stderr)
    print("  - GROQ_API_KEY (required)", file=sys.stderr)
    print("  - PORT (optional, defaults to 8000)", file=sys.stderr)
    print("  - CORS_ORIGINS (optional)", file=sys.stderr)
    sys.exit(1)
