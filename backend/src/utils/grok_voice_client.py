"""
Groq Voice API client for speech-to-text.
Handles audio transcription using Groq's voice API (OpenAI-compatible).
Note: Groq may not have a separate voice API. This client is kept for compatibility.
For production, use client-side Web Speech API in the frontend.
"""

import requests
from typing import Optional, Dict, Any
import logging
import base64
from pathlib import Path
from .config import settings

logger = logging.getLogger(__name__)

GROQ_VOICE_API_BASE_URL = "https://api.groq.com/openai/v1/audio"


class GrokVoiceClient:
    """Client for Groq Voice API (speech-to-text) - OpenAI-compatible endpoint."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize Groq Voice client.
        
        Args:
            api_key: Groq Voice API key (defaults to settings.groq_voice_api_key)
            base_url: API base URL (defaults to settings.groq_voice_api_url)
        """
        self.api_key = api_key or getattr(settings, 'groq_voice_api_key', None)
        self.base_url = base_url or getattr(settings, 'groq_voice_api_url', GROQ_VOICE_API_BASE_URL)
        
        if not self.api_key:
            logger.warning("GROQ_VOICE_API_KEY not set. Voice transcription may not work.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}" if self.api_key else None,
            "Content-Type": "application/json"
        }
        # Remove None values
        self.headers = {k: v for k, v in self.headers.items() if v is not None}
    
    def transcribe_audio(
        self,
        audio_file_path: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text using Groq Voice API.
        
        Args:
            audio_file_path: Path to audio file
            language: Optional language code (e.g., 'en', 'hi')
            prompt: Optional prompt to guide transcription
            
        Returns:
            Dictionary with transcription text and metadata
        """
        if not self.api_key:
            raise ValueError("GROQ_VOICE_API_KEY is required for transcription")
        
        url = f"{self.base_url}/transcriptions"
        
        # Read audio file
        audio_path = Path(audio_file_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        # Prepare multipart form data
        files = {
            "file": (audio_path.name, open(audio_path, "rb"), "audio/mpeg")
        }
        
        data = {}
        if language:
            data["language"] = language
        if prompt:
            data["prompt"] = prompt
        
        # Remove Content-Type from headers for multipart form
        headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
        
        try:
            logger.debug(f"Transcribing audio file: {audio_path.name}")
            response = requests.post(
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            
            logger.debug(f"Transcription successful: {len(result.get('text', ''))} chars")
            return {
                "text": result.get("text", ""),
                "language": result.get("language"),
                "duration": result.get("duration"),
                "full_response": result
            }
        
        except requests.RequestException as e:
            logger.error(f"Groq Voice API request failed: {e}")
            raise Exception(f"Groq Voice API request failed: {e}")
        finally:
            files["file"][1].close()
    
    def transcribe_audio_bytes(
        self,
        audio_data: bytes,
        filename: str = "audio.mp3",
        language: Optional[str] = None
    ) -> str:
        """
        Transcribe audio bytes to text.
        
        Args:
            audio_data: Audio file as bytes
            filename: Filename for the audio
            language: Optional language code
            
        Returns:
            Transcribed text
        """
        if not self.api_key:
            raise ValueError("GROQ_VOICE_API_KEY is required for transcription")
        
        url = f"{self.base_url}/transcriptions"
        
        files = {
            "file": (filename, audio_data, "audio/mpeg")
        }
        
        data = {}
        if language:
            data["language"] = language
        
        headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
        
        try:
            response = requests.post(
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("text", "")
        
        except requests.RequestException as e:
            logger.error(f"Groq Voice API request failed: {e}")
            raise Exception(f"Groq Voice API request failed: {e}")


# Global Groq Voice client instance
_grok_voice_client: Optional[GrokVoiceClient] = None


def get_grok_voice_client() -> GrokVoiceClient:
    """
    Get or create global Groq Voice client instance.
    
    Returns:
        GrokVoiceClient instance
    """
    global _grok_voice_client
    if _grok_voice_client is None:
        _grok_voice_client = GrokVoiceClient()
    return _grok_voice_client
