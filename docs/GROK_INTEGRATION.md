# Groq API Integration Guide

This document describes how the project uses Groq API instead of OpenAI.

## Overview

The project uses:
- **Groq API** for LLM text generation (OpenAI-compatible)
- **Web Speech API** (client-side) for speech-to-text transcription

## Configuration

### Environment Variables

**backend/.env:**
```env
# Groq API Configuration (OpenAI-compatible)
# Get your API key from: https://console.groq.com/keys
GROQ_API_KEY=your_groq_api_key_here
GROQ_API_URL=https://api.groq.com/openai/v1

# Groq Model Selection
# Best models: llama3-70b-8192 (best quality), llama3-8b-8192 (faster), mixtral-8x7b-32768, gemma-7b-it
GROQ_MODEL=llama3-70b-8192
```

### Settings

All Groq-related settings are in `backend/src/utils/config.py`:
- `groq_api_key`: Required API key (uses GROQ_API_KEY env var)
- `groq_api_url`: API endpoint (default: https://api.groq.com/openai/v1)
- `llm_model`: Model name (default: "llama3-70b-8192")
- Note: Voice transcription uses client-side Web Speech API (recommended)

## Usage

### Grok API Client

**Location:** `backend/src/utils/grok_client.py`

**Basic Usage:**
```python
from src.utils.grok_client import get_grok_client

grok = get_grok_client()

# Generate text
response = grok.generate_text(
    prompt="Plan a 3-day trip to Jaipur",
    system_prompt="You are a travel planning assistant.",
    temperature=0.7
)

# Chat completion
messages = [
    {"role": "system", "content": "You are a travel assistant."},
    {"role": "user", "content": "Plan a trip to Mumbai"}
]
response = grok.chat_completion(messages=messages)

# Intent classification
intent = grok.classify_intent(
    user_input="Make Day 2 more relaxed",
    possible_intents=["PLAN_TRIP", "EDIT_ITINERARY", "EXPLAIN"]
)
```

### Grok Voice API Client

**Location:** `backend/src/utils/grok_voice_client.py`

**Basic Usage:**
```python
from src.utils.grok_voice_client import get_grok_voice_client

voice_client = get_grok_voice_client()

# Transcribe audio file
result = voice_client.transcribe_audio(
    audio_file_path="audio.mp3",
    language="en"
)
transcript = result["text"]

# Transcribe audio bytes
transcript = voice_client.transcribe_audio_bytes(
    audio_data=audio_bytes,
    filename="audio.mp3",
    language="en"
)
```

## API Endpoints

### Chat Completions
- **URL:** `POST https://api.groq.com/openai/v1/chat/completions`
- **Model:** `llama3-70b-8192` (best quality), `llama3-8b-8192` (faster), `mixtral-8x7b-32768`, `gemma-7b-it`
- **Format:** OpenAI-compatible chat completions API

### Audio Transcription
- **URL:** `POST https://api.groq.com/openai/v1/audio/transcriptions` (if supported)
- **Method:** Multipart form data
- **File:** Audio file (MP3, WAV, etc.)
- **Response:** JSON with transcribed text
- **Note:** Groq may not have a separate voice API. Use client-side Web Speech API for production.

## Differences from OpenAI

1. **API Endpoint:** Uses `api.groq.com/openai/v1` (OpenAI-compatible endpoint)
2. **Model Names:** Uses Groq models (`llama3-70b-8192`, `mixtral-8x7b-32768`, etc.) instead of GPT models
3. **Voice API:** May not be available - use client-side Web Speech API instead
4. **Authentication:** Uses `Authorization: Bearer {api_key}` header (same format as OpenAI)
5. **Speed:** Groq models are optimized for fast inference

## Integration Points

### Where Grok is Used:

1. **Orchestrator** (`src/orchestrator/orchestrator.py`)
   - Trip planning logic
   - Edit handling
   - Explanation generation

2. **Intent Classifier** (`src/orchestrator/intent_classifier.py`)
   - Intent classification
   - Entity extraction

3. **MCP Tools** (`mcp-tools/itinerary-builder/`)
   - Itinerary generation
   - POI ranking

4. **Voice Input** (Frontend → Backend)
   - Speech-to-text via Grok Voice API
   - Text-to-speech (if needed in future)

## Error Handling

The Grok clients handle errors gracefully:
- API failures are logged
- Exceptions are raised with descriptive messages
- Network timeouts are configured (60 seconds)

## Rate Limiting

Groq API has rate limits (check Groq documentation for current limits).
The application's rate limiting middleware (`rate_limiter.py`) helps manage this.

## Migration Notes

If you need to switch back to OpenAI or use both:

1. **Dual Support:** You can implement both clients and choose based on config
2. **Abstraction Layer:** Create an LLM client interface that both implement
3. **Environment Variable:** Use `LLM_PROVIDER=grok|openai` to switch

Example abstraction:
```python
class LLMClient(ABC):
    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        pass

class GrokLLMClient(LLMClient):
    # Implements using Grok

class OpenAILLMClient(LLMClient):
    # Implements using OpenAI
```

## Resources

- Groq API Documentation: https://console.groq.com/docs
- Groq Console: https://console.groq.com/
- API Keys: https://console.groq.com/keys
- API Status: Check Groq status page

## Troubleshooting

### Common Issues:

1. **"GROQ_API_KEY is required"**
   - Set `GROQ_API_KEY` in `.env` file
   - Get your key from: https://console.groq.com/keys

2. **"Groq API request failed"**
   - Check API key is valid
   - Check network connectivity
   - Verify API endpoint is accessible (https://api.groq.com/openai/v1)

3. **"GROQ_VOICE_API_KEY is required"**
   - Voice transcription is optional
   - Groq may not have a separate voice API
   - Use client-side Web Speech API in frontend as recommended

## Future Enhancements

- Support for streaming responses
- Fine-tuned Grok models (when available)
- Voice-to-voice capabilities
- Multi-language support
- Audio format conversion utilities
