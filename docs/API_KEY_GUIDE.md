# Groq API Key Configuration Guide

## API Keys Required

### ✅ Required: GROQ_API_KEY
- **Purpose**: LLM text generation (itinerary building, explanations, intent classification, etc.)
- **Used in**: `backend/src/utils/grok_client.py`
- **Endpoints**: All chat completions, text generation
- **Token tracking**: Yes - counts toward your daily token limit

### ⚠️ Optional: GROQ_VOICE_API_KEY
- **Purpose**: Backend voice transcription (currently NOT USED)
- **Status**: **Optional** - The frontend uses **Web Speech API** (client-side) instead
- **Current Implementation**: Voice input uses browser's `SpeechRecognition` API (no backend API needed)
- **Note**: `GROQ_VOICE_API_KEY` is configured but not actively used in the current implementation

## Configuration

### Backend `.env` file:
```env
# Required - LLM text generation
GROQ_API_KEY=your_groq_api_key_here
GROQ_API_URL=https://api.groq.com/openai/v1

# Optional - Voice API (not currently used)
GROQ_VOICE_API_KEY=your_groq_voice_api_key_here  # Optional - can leave empty
GROQ_VOICE_API_URL=https://api.groq.com/openai/v1/audio  # Optional
```

## Answer: Do you need 2 API keys?

### ✅ **You only need 1 API key:**
- **`GROQ_API_KEY`** - Required for all LLM operations

### ❌ **`GROQ_VOICE_API_KEY` is optional:**
- Frontend uses **Web Speech API** (browser-based, no API key needed)
- Backend voice client exists but is not actively used
- You can leave `GROQ_VOICE_API_KEY` empty or omit it

## Voice Input Implementation

**Current Implementation:**
- **Frontend**: Uses `window.SpeechRecognition` (Web Speech API)
- **Backend**: Groq Voice API client exists but is NOT used
- **Result**: Voice transcription happens in the browser (no API calls)

**Why Web Speech API?**
- Free (no API key needed)
- Fast (client-side processing)
- Works in Chrome, Edge, Safari
- No token usage

## Token Optimization Status

✅ **Optimizations Active:**
- Model routing (fast model for simple tasks)
- Reduced max_tokens for classification
- Response caching
- Per-call model selection

## Recommended Setup

**Minimum (required):**
```env
GROQ_API_KEY=your_key_here
```

**Complete (includes optional):**
```env
GROQ_API_KEY=your_key_here
GROQ_VOICE_API_KEY=your_voice_key_here  # Optional - not used currently
```

---

**Summary**: You only need **1 API key** (`GROQ_API_KEY`) for the application to work. The voice API key is optional and not currently used.
