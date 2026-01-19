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
        Removes common voice transcription artifacts.
        
        Args:
            text: Raw voice input text
        
        Returns:
            Normalized text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Fix common voice transcription issues
        replacements = {
            "um": "",
            "uh": "",
            "like": "",
            "you know": "",
            "  ": " "  # Double spaces
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
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

User input: "{normalized_input}"

IMPORTANT: Voice commands for editing include:
- "add a day", "add another day", "add extra day" → EDIT_ITINERARY with ADD_ACTIVITY
- "swap day X with day Y", "swap day X and day Y" → EDIT_ITINERARY with SWAP_ACTIVITY
- "move day X morning to day Y", "swap day X evening to day Y" → EDIT_ITINERARY with SWAP_ACTIVITY
- "change", "modify", "edit", "update" → EDIT_ITINERARY
- "remove", "delete" → EDIT_ITINERARY with REMOVE_ACTIVITY

Return a JSON object with this exact structure:
{{
    "intent": "PLAN_TRIP|EDIT_ITINERARY|EXPLAIN|CLARIFY|OTHER",
    "confidence": 0.0-1.0,
    "entities": {{
        "city": "city name or null",
        "duration": number or null,
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
        
        # Extract duration (e.g., "3 days", "2-day")
        duration_match = re.search(r'(\d+)[\s-]?day', user_input.lower())
        if duration_match:
            entities["duration"] = int(duration_match.group(1))
        
        # Extract day number (e.g., "day 2", "day two")
        day_match = re.search(r'day\s+(\d+)', user_input.lower())
        if day_match:
            entities["target_day"] = int(day_match.group(1))
        
        # Extract edit type with better voice command recognition
        user_lower = user_input.lower()
        if "relaxed" in user_lower or "slower" in user_lower or "faster" in user_lower:
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
        elif "add" in user_lower and ("day" in user_lower or "extra day" in user_lower):
            entities["edit_type"] = "ADD_ACTIVITY"  # Adding a day is handled as ADD_ACTIVITY
        elif "add" in user_lower:
            entities["edit_type"] = "ADD_ACTIVITY"
        elif "remove" in user_lower or "delete" in user_lower:
            entities["edit_type"] = "REMOVE_ACTIVITY"
        
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
