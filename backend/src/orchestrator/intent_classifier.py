"""
Intent Classifier
Classifies user input into intents and extracts entities.
"""

import re
import json
from typing import Dict, List, Optional, Any
import logging

try:
    from ..utils.grok_client import get_grok_client
except ImportError:
    from src.utils.grok_client import get_grok_client

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Classifies user input into intents and extracts entities.
    Uses Grok API for LLM-based classification.
    """
    
    # Intent types
    PLAN_TRIP = "PLAN_TRIP"
    EDIT_ITINERARY = "EDIT_ITINERARY"
    EXPLAIN = "EXPLAIN"
    CLARIFY = "CLARIFY"
    OTHER = "OTHER"
    
    INTENTS = [PLAN_TRIP, EDIT_ITINERARY, EXPLAIN, CLARIFY, OTHER]
    
    def __init__(self):
        """Initialize intent classifier."""
        self.groq_client = get_grok_client()
        logger.info("IntentClassifier initialized")
    
    def normalize_voice_input(self, text: str) -> str:
        """
        Normalize voice input text.
        Removes common voice transcription artifacts and fixes STT errors.
        
        Args:
            text: Raw voice input text
        
        Returns:
            Normalized text with corrections applied
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Dictionary of common Indian city names with their common mispronunciations
        city_corrections = {
            "jai poor": "Jaipur",
            "jai poore": "Jaipur",
            "jai pur": "Jaipur",
            "jay poor": "Jaipur",
            "mum bye": "Mumbai",
            "bom bay": "Mumbai",
            "del he": "Delhi",
            "ban ga lore": "Bangalore",
            "ban ga low": "Bangalore",
            "chen nai": "Chennai",
            "mad ras": "Chennai",
            "cal cut ta": "Kolkata",
            "cal cut": "Kolkata",
            "hya der a bad": "Hyderabad",
            "pune": "Pune",
            "ah med a bad": "Ahmedabad",
            "sur at": "Surat",
            "jaipur": "Jaipur",
            "mumbai": "Mumbai",
            "delhi": "Delhi",
            "bangalore": "Bangalore",
            "chennai": "Chennai",
            "kolkata": "Kolkata",
            "hyderabad": "Hyderabad"
        }
        
        # Fix city name mispronunciations (case-insensitive, whole word match)
        text_lower = text.lower()
        for wrong, correct in city_corrections.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(wrong.lower()) + r'\b'
            if re.search(pattern, text_lower):
                text = re.sub(pattern, correct, text, flags=re.IGNORECASE)
                logger.info(f"Corrected city name: '{wrong}' → '{correct}'")
        
        # Fix number word to digit conversions (one, two, three → 1, 2, 3)
        number_words = {
            "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
            "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
            "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
            "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
            "eighteen": "18", "nineteen": "19", "twenty": "20", "thirty": "30"
        }
        
        # Replace number words in context (e.g., "day one" → "day 1", "three days" → "3 days")
        for word, digit in number_words.items():
            # Match whole word only
            pattern = r'\b' + word + r'\b'
            text = re.sub(pattern, digit, text, flags=re.IGNORECASE)
        
        # Fix common STT errors for numbers and days
        stt_corrections = {
            # Number misrecognitions
            r'\btree\b': "three",  # "tree day" → "three day" → "3 day"
            r'\bfor\b(?!\s+(?:the|a|an|in|on|at|to))': "four",  # "for days" → "four days" (but not "for the trip")
            r'\bto\b(?!\s+(?:the|a|an|in|on|at|day|mumbai|chennai|jaipur|delhi|bangalore|hyderabad|kolkata|pune))': "two",  # "to days" → "two days" (but not "to Mumbai")
            # Day misrecognitions
            r'\bplay\s+one\b': "swap day 1",
            r'\bplay\s+day\s+(\d+)\b': r"swap day \1",
            r'\bplace\s+one\b': "swap day 1",
            r'\bplace\s+day\s+(\d+)\b': r"swap day \1",
            # Common voice command variations
            r'\bchange\s+day\s+(\d+)\s+to\s+day\s+(\d+)\b': r"swap day \1 with day \2",  # "change day 1 to day 2" → "swap day 1 with day 2"
            r'\bmake\s+day\s+(\d+)\s+more\s+relaxed\b': r"make day \1 more relaxed",  # Keep as is
            r'\bmake\s+day\s+(\d+)\s+faster\b': r"make day \1 faster",  # Keep as is
            r'\badd\s+activity\s+to\s+day\s+(\d+)\b': r"add activity to day \1",  # Keep as is
            r'\bremove\s+activity\s+from\s+day\s+(\d+)\b': r"remove activity from day \1",  # Keep as is
            # Voice transcription artifacts
            r'\bum\b': "",
            r'\buh\b': "",
            r'\blike\b(?!\s+(?:food|culture|shopping|nature|beaches))': "",  # Remove filler "like" but keep "like food"
            r'\byou know\b': "",
            r'\bwell\s+': "",  # Remove leading "well"
            r'\bso\s+': "",  # Remove leading "so"
            r'\bactually\s+': "",  # Remove "actually"
            r'\bbasically\s+': "",  # Remove "basically"
            r'\bkind of\b': "",  # Remove "kind of"
            r'\bsort of\b': "",  # Remove "sort of"
        }
        
        # Apply STT corrections
        for pattern, replacement in stt_corrections.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Fix "day to" → "day 2" (common voice error)
        text = re.sub(r'\bday\s+to\b(?!\s+(?:the|a|an|mumbai|chennai|jaipur|delhi|bangalore|hyderabad|kolkata|pune))', 'day 2', text, flags=re.IGNORECASE)
        
        # Fix "day too" → "day 2" (another common voice error)
        text = re.sub(r'\bday\s+too\b(?!\s+(?:the|a|an|mumbai|chennai|jaipur|delhi|bangalore|hyderabad|kolkata|pune))', 'day 2', text, flags=re.IGNORECASE)
        
        # Fix "day tu" → "day 2" (STT error)
        text = re.sub(r'\bday\s+tu\b(?!\s+(?:the|a|an|mumbai|chennai|jaipur|delhi|bangalore|hyderabad|kolkata|pune))', 'day 2', text, flags=re.IGNORECASE)
        
        # Additional Chennai-specific voice corrections
        chennai_variations = {
            r'\bchen\s+nai\b': "Chennai",
            r'\bchennai\b': "Chennai",  # Ensure proper capitalization
            r'\bmad\s+ras\b': "Chennai",
            r'\bmadras\b': "Chennai",
            r'\bshen\s+nai\b': "Chennai",  # Common mispronunciation
            r'\bshennai\b': "Chennai",
        }
        for pattern, replacement in chennai_variations.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Fix spacing issues after replacements
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove any remaining double spaces
        while '  ' in text:
            text = text.replace('  ', ' ')
        
        return text.strip()
    
    def classify_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Classify user input into an intent.
        
        Args:
            user_input: User input text
        
        Returns:
            Dictionary with intent, entities, and confidence
        """
        # Normalize input
        normalized_input = self.normalize_voice_input(user_input)
        
        # Use Grok API for classification
        prompt = f"""Classify this user input into one of these intents: {', '.join(self.INTENTS)}

User input (may contain voice transcription errors): "{normalized_input}"

CRITICAL: This input may come from voice recognition and could have transcription errors. Be flexible:
- Number words: "one"=1, "two"=2, "three"=3, etc.
- Common STT errors: "tree" may mean "three" or "3", "Jai poor" = "Jaipur", "play one" = "swap day 1"
- Short responses like "yes", "no", "3", "Jaipur", "road" are often answers to clarifying questions

INTENT PATTERNS:

PLAN_TRIP:
- "plan", "trip", "visit", "itinerary", "create", "make a plan"
- Includes city names, durations, interests
- Examples: "Plan a 3-day trip to Jaipur", "Visit Mumbai", "I want to go to Delhi"

EDIT_ITINERARY:
- "change", "modify", "edit", "update", "swap", "move", "add", "remove", "delete", "replace"
- Voice variations: "play one" = "swap day 1", "day to" = "day 2"
- Editing patterns:
  * "add a day", "add another day", "add extra day" → ADD_ACTIVITY
  * "swap day X with day Y", "swap day X and day Y", "play day X with day Y" → SWAP_DAYS
  * "move day X morning to day Y", "swap day X evening to day Y" → MOVE_TIME_BLOCK
  * "make day X more relaxed/faster" → CHANGE_PACE
  * "remove activity from day X" → REMOVE_ACTIVITY
  * "reduce travel time" → REDUCE_TRAVEL

EXPLAIN:
- "why", "explain", "reason", "how come", "what", "tell me about"
- Questions about POIs, timing, decisions
- Examples: "Why did you pick Hawa Mahal?", "Explain the itinerary", "What if it rains?"

CLARIFY:
- Short responses: "yes", "no", "sure", "okay", "ok", "correct", "right"
- Single word answers: city names, numbers, interests, pace preferences
- Responses to clarifying questions

Return a JSON object with this exact structure:
{{
    "intent": "PLAN_TRIP|EDIT_ITINERARY|EXPLAIN|CLARIFY|OTHER",
    "confidence": 0.0-1.0,
    "entities": {{
        "city": "city name (corrected if mispronounced) or null",
        "duration": number (convert words like 'three' to 3) or null,
        "target_day": number or null,
        "source_day": number or null,
        "edit_type": "CHANGE_PACE|SWAP_ACTIVITY|SWAP_DAYS|MOVE_TIME_BLOCK|ADD_ACTIVITY|REMOVE_ACTIVITY|REDUCE_TRAVEL or null",
        "poi_name": "POI name or null",
        "question_type": "WHY_POI|IS_FEASIBLE|WHAT_IF|TIMING or null"
    }}
}}

Only return the JSON, no other text."""
        
        try:
            # Intent classification now uses optimized classify_intent method
            # which uses fast model and reduced tokens automatically
            result = self.groq_client.classify_intent(user_input, self.INTENTS)
            
            # Validate intent
            if result.get("intent") not in self.INTENTS:
                logger.warning(f"Invalid intent returned: {result.get('intent')}, defaulting to OTHER")
                result["intent"] = self.OTHER
            
            logger.info(f"Classified intent: {result.get('intent')} (confidence: {result.get('confidence', 0)})")
            return result
        
        except Exception as e:
            logger.error(f"Intent classification failed: {e}", exc_info=True)
            # Fallback: simple rule-based classification
            # Use original input if normalized_input wasn't set
            fallback_input = normalized_input if 'normalized_input' in locals() else user_input
            return self._fallback_classify(fallback_input)
    
    def _fallback_classify(self, user_input: str) -> Dict[str, Any]:
        """
        Fallback rule-based classification if LLM fails.
        
        Args:
            user_input: Normalized user input
        
        Returns:
            Classification result
        """
        user_input_lower = user_input.lower()
        
        # Simple keyword-based classification
        if any(word in user_input_lower for word in ["plan", "trip", "itinerary", "visit", "travel to", "create"]):
            intent = self.PLAN_TRIP
        elif any(word in user_input_lower for word in ["edit", "change", "modify", "swap", "remove", "add", "move", "update", "replace"]):
            intent = self.EDIT_ITINERARY
        elif any(word in user_input_lower for word in ["why", "explain", "reason", "how come"]):
            intent = self.EXPLAIN
        elif any(word in user_input_lower for word in ["yes", "no", "sure", "okay", "ok", "correct", "right"]):
            intent = self.CLARIFY
        else:
            intent = self.OTHER
        
        # Extract basic entities
        entities = self._extract_entities_simple(user_input)
        
        return {
            "intent": intent,
            "confidence": 0.5,  # Lower confidence for fallback
            "entities": entities
        }
    
    def _extract_entities_simple(self, user_input: str) -> Dict[str, Any]:
        """
        Simple entity extraction using regex patterns.
        
        Args:
            user_input: User input text
        
        Returns:
            Entities dictionary
        """
        entities = {
            "city": None,
            "duration": None,
            "target_day": None,
            "edit_type": None,
            "poi_name": None,
            "question_type": None
        }
        
        # Extract duration (e.g., "3 days", "2-day", "three days", "tree days")
        # First try numeric patterns
        duration_match = re.search(r'(\d+)[\s-]?day', user_input.lower())
        if duration_match:
            entities["duration"] = int(duration_match.group(1))
        else:
            # Try word numbers (already converted to digits by normalize_voice_input, but handle edge cases)
            word_to_num = {
                "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
            }
            for word, num in word_to_num.items():
                if re.search(rf'\b{word}\s+days?\b', user_input.lower()):
                    entities["duration"] = num
                    break
        
        # Extract day number (e.g., "day 2", "day two", "day to" = day 2)
        # First try numeric patterns
        day_match = re.search(r'day\s+(\d+)', user_input.lower())
        if day_match:
            entities["target_day"] = int(day_match.group(1))
        else:
            # Try word numbers and voice errors
            word_to_num = {
                "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "to": 2  # "day to" = "day 2" (common voice error)
            }
            for word, num in word_to_num.items():
                if re.search(rf'day\s+{word}\b', user_input.lower()):
                    entities["target_day"] = num
                    break
        
        # Extract source_day for swaps (e.g., "swap day 1 with day 2")
        source_day_match = re.search(r'(?:swap|switch|move|play|place).*?day\s+(\d+)', user_input.lower())
        if source_day_match:
            entities["source_day"] = int(source_day_match.group(1))
        
        # Also check for word numbers in source day context
        if not entities.get("source_day"):
            for word, num in word_to_num.items():
                if re.search(rf'(?:swap|switch|move|play|place).*?day\s+{word}\b', user_input.lower()):
                    entities["source_day"] = num
                    break
        
        # Extract edit type with better voice command recognition
        user_lower = user_input.lower()
        
        # Handle voice transcription variations: "play" = "swap", "place" = "swap"
        if "play" in user_lower or "place" in user_lower:
            user_lower = user_lower.replace("play", "swap").replace("place", "swap")
        
        if "relaxed" in user_lower or "slower" in user_lower or "faster" in user_lower or "more relaxed" in user_lower or "packed" in user_lower:
            entities["edit_type"] = "CHANGE_PACE"
        elif "swap" in user_lower or "switch" in user_lower or "modify" in user_lower or "change" in user_lower or "update" in user_lower:
            # Check if it's a day swap or activity swap
            if "day" in user_lower and ("with day" in user_lower or "and day" in user_lower or "to day" in user_lower):
                entities["edit_type"] = "SWAP_DAYS"
            elif "day" in user_lower and any(tb in user_lower for tb in ["morning", "afternoon", "evening"]):
                # Time block swap
                entities["edit_type"] = "MOVE_TIME_BLOCK"
            else:
                entities["edit_type"] = "SWAP_ACTIVITY"
        elif "move" in user_lower and "day" in user_lower:
            entities["edit_type"] = "MOVE_TIME_BLOCK"
        elif "add" in user_lower and ("day" in user_lower or "extra day" in user_lower or "another day" in user_lower):
            entities["edit_type"] = "ADD_ACTIVITY"  # Adding a day is handled as ADD_ACTIVITY
        elif "add" in user_lower:
            entities["edit_type"] = "ADD_ACTIVITY"
        elif "remove" in user_lower or "delete" in user_lower:
            entities["edit_type"] = "REMOVE_ACTIVITY"
        elif "reduce" in user_lower and ("travel" in user_lower or "time" in user_lower):
            entities["edit_type"] = "REDUCE_TRAVEL"
        
        return entities
    
    def extract_entities(
        self,
        user_input: str,
        intent: str
    ) -> Dict[str, Any]:
        """
        Extract entities from user input based on intent.
        
        Args:
            user_input: User input text
            intent: Classified intent
        
        Returns:
            Entities dictionary
        """
        # Classification already includes entity extraction
        classification = self.classify_intent(user_input)
        return classification.get("entities", {})
    
    def is_clarifying_response(self, user_input: str, last_question: Optional[str] = None) -> bool:
        """
        Check if user input is a response to a clarifying question.
        
        Args:
            user_input: User input text
            last_question: Last clarifying question asked
        
        Returns:
            True if it's a clarifying response
        """
        classification = self.classify_intent(user_input)
        return classification["intent"] == self.CLARIFY


# Global intent classifier instance
_intent_classifier: Optional[IntentClassifier] = None


def get_intent_classifier() -> IntentClassifier:
    """
    Get or create global intent classifier instance.
    
    Returns:
        IntentClassifier instance
    """
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    return _intent_classifier
