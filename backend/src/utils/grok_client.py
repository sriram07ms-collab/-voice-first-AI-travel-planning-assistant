"""
Groq API client for LLM interactions.
Uses Groq API for text generation (OpenAI-compatible).
Optimized for token efficiency with model routing and caching.
"""

import requests
from typing import Optional, Dict, List, Any
import logging
import hashlib
from functools import lru_cache
from .config import settings

logger = logging.getLogger(__name__)

GROQ_API_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"  # Best model for quality and reasoning

# Model routing for token optimization
GROQ_FAST_MODEL = "llama-3.1-8b-instant"  # Fast, lower token cost for simple tasks
GROQ_QUALITY_MODEL = "llama-3.3-70b-versatile"  # High quality for complex tasks

# Response cache (in-memory)
_response_cache: Dict[str, Any] = {}
_cache_max_size = 200  # Maximum cache entries


class GrokClient:
    """Client for interacting with Groq API (OpenAI-compatible)."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize Groq client.
        
        Args:
            api_key: Groq API key (defaults to settings.groq_api_key)
            base_url: API base URL (defaults to settings.groq_api_url)
            model: Model name (defaults to settings.llm_model)
        """
        self.api_key = api_key or settings.groq_api_key
        self.base_url = base_url or getattr(settings, 'groq_api_url', GROQ_API_BASE_URL)
        self.model = model or settings.llm_model
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        model: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Generate chat completion using Groq API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            model: Model to use (overrides default, allows per-call model selection)
            use_cache: Whether to use response caching for identical requests
        
        Returns:
            API response dictionary
        """
        # Use provided model or default
        model_to_use = model or self.model
        
        # Check cache if enabled and not streaming
        if use_cache and not stream:
            cache_key = self._get_cache_key(messages, model_to_use, temperature, max_tokens)
            if cache_key in _response_cache:
                logger.debug(f"Cache hit for API call (model: {model_to_use})")
                return _response_cache[cache_key]
        
        url = f"{self.base_url}/chat/completions"
        
        # Build payload - Groq API may have restrictions on certain parameters
        import json as json_module
        
        payload = {
            "model": model_to_use,
            "messages": messages,
        }
        
        # Add optional parameters only if provided (Groq API may reject invalid values)
        temp_value = temperature if temperature is not None else settings.llm_temperature
        if temp_value is not None:
            payload["temperature"] = temp_value
        
        max_tokens_value = max_tokens if max_tokens is not None else settings.max_tokens
        # Groq has model-specific max token limits - ensure we don't exceed
        # llama-3.3-70b-versatile has 128k context window (both input + output)
        # We need to be conservative - if prompt is large, reduce max_tokens
        if max_tokens_value is not None:
            # Estimate input token count from messages
            messages_str = json_module.dumps(messages)
            estimated_input_tokens = len(messages_str.split()) * 1.3  # Rough estimate
            
            # Get model's total context window
            # Check both self.model and model_to_use for context window limits
            check_model = model_to_use.lower()
            if "128" in check_model or "128k" in check_model:
                model_max = 131072  # 128k tokens
            elif "32" in check_model or "32768" in check_model:
                model_max = 32768  # 32k tokens
            elif "8192" in check_model:
                model_max = 8192  # Legacy 8k tokens
            else:
                model_max = 131072  # Default to 128k for modern models
            
            # Reserve tokens for input (use actual estimate or minimum 1000)
            input_reserve = max(int(estimated_input_tokens), 1000)
            # Ensure output tokens don't exceed available space
            safe_max = min(max_tokens_value, model_max - input_reserve)
            
            # Ensure at least 100 tokens for output (minimum reasonable)
            if safe_max < 100:
                logger.warning(f"Large prompt detected (~{int(estimated_input_tokens)} input tokens). Reducing max_tokens to {safe_max}.")
            
            payload["max_tokens"] = max(100, safe_max)  # Minimum 100 tokens for output
        
        # Only include stream if True (Groq may reject explicit False)
        if stream:
            payload["stream"] = True
        
        try:
            logger.debug(f"Groq API request: model={model_to_use}, max_tokens={payload.get('max_tokens')}, temp={payload.get('temperature')}")
            
            # Log payload size for debugging
            payload_str = json_module.dumps(payload)
            prompt_tokens_estimate = len(payload_str.split()) * 1.3  # Rough estimate
            logger.debug(f"Request payload size: ~{len(payload_str)} chars, estimated input tokens: ~{int(prompt_tokens_estimate)}")
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            # Log error response details if request failed - BEFORE raise_for_status
            if response.status_code != 200:
                error_details = None
                try:
                    error_data = response.json()
                    error_details = error_data
                    logger.error(f"Groq API error ({response.status_code}): {json_module.dumps(error_data, indent=2)}")
                except Exception as parse_error:
                    error_text = response.text[:1000] if response.text else "No response text"
                    logger.error(f"Groq API error ({response.status_code}): {error_text}")
                    logger.error(f"Could not parse error response as JSON: {parse_error}")
                
                # Raise with detailed error message
                error_msg = f"Groq API returned {response.status_code}"
                if error_details:
                    if isinstance(error_details, dict):
                        api_error_msg = error_details.get('error', {}).get('message', 'Unknown error')
                        api_error_type = error_details.get('error', {}).get('type', 'Unknown type')
                        error_msg = f"{error_msg}: {api_error_type} - {api_error_msg}"
                    else:
                        error_msg = f"{error_msg}: {error_details}"
                raise requests.HTTPError(error_msg, response=response)
            
            response.raise_for_status()
            
            data = response.json()
            
            # Extract content from response
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                logger.debug(f"Groq API response received ({len(content)} chars)")
                
                result = {
                    "content": content,
                    "model": data.get("model"),
                    "usage": data.get("usage"),
                    "full_response": data
                }
                
                # Cache result if enabled and not streaming
                if use_cache and not stream:
                    cache_key = self._get_cache_key(messages, model_to_use, temperature, max_tokens)
                    self._cache_result(cache_key, result)
                
                return result
            else:
                raise ValueError("Invalid response format from Groq API")
        
        except requests.RequestException as e:
            # Include response details in error if available
            error_msg = str(e)
            if hasattr(e.response, 'text') and e.response.text:
                try:
                    error_data = e.response.json()
                    error_msg = f"{error_msg} - Response: {error_data}"
                except:
                    error_msg = f"{error_msg} - Response: {e.response.text[:500]}"
            logger.error(f"Groq API request failed: {error_msg}")
            raise Exception(f"Groq API request failed: {error_msg}")
    
    def _get_cache_key(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: Optional[float],
        max_tokens: Optional[int]
    ) -> str:
        """Generate cache key from request parameters."""
        import json as json_module
        key_data = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        key_str = json_module.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _cache_result(self, cache_key: str, result: Any):
        """Cache API result, evicting old entries if cache is full."""
        global _response_cache
        if len(_response_cache) >= _cache_max_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(_response_cache))
            del _response_cache[oldest_key]
            logger.debug(f"Cache evicted entry: {oldest_key[:8]}...")
        _response_cache[cache_key] = result
        logger.debug(f"Cached API response: {cache_key[:8]}... (cache size: {len(_response_cache)})")
    
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        use_cache: bool = True
    ) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            Generated text
        """
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        response = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
            use_cache=use_cache
        )
        
        return response["content"]
    
    def classify_intent(
        self,
        user_input: str,
        possible_intents: List[str]
    ) -> Dict[str, Any]:
        """
        Classify user intent using Groq (optimized with fast model and reduced tokens).
        
        Args:
            user_input: User input text
            possible_intents: List of possible intents
            
        Returns:
            Dictionary with intent and confidence
        """
        intent_list = ", ".join(possible_intents)
        
        prompt = f"""Classify this user input into one of these intents: {intent_list}

User input: "{user_input}"

Return JSON with this structure:
{{
    "intent": "one_of_the_intents",
    "confidence": 0.0-1.0,
    "entities": {{
        "city": "...",
        "duration": ...,
        "target_day": ...,
        "edit_type": "..."
    }}
}}

Only return the JSON, no other text."""
        
        try:
            # Use fast model for classification (token optimization)
            response_text = self.generate_text(
                prompt,
                temperature=0.3,
                max_tokens=100,  # Reduced from 200 (token optimization)
                model=GROQ_FAST_MODEL,  # Use fast model for simple classification
                use_cache=True
            )
            
            # Parse JSON from response
            import json
            # Remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            return result
        
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return {
                "intent": "OTHER",
                "confidence": 0.0,
                "entities": {}
            }


# Cache management
def clear_cache():
    """Clear the response cache."""
    global _response_cache
    _response_cache.clear()
    logger.info("Response cache cleared")


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    global _response_cache
    return {
        "size": len(_response_cache),
        "max_size": _cache_max_size,
        "hit_rate": "N/A"  # Would need hit tracking for accurate rate
    }


# Global Grok client instance
_grok_client: Optional[GrokClient] = None


def get_grok_client() -> GrokClient:
    """
    Get or create global Grok client instance.
    
    Returns:
        GrokClient instance
    """
    global _grok_client
    if _grok_client is None:
        _grok_client = GrokClient()
    return _grok_client
