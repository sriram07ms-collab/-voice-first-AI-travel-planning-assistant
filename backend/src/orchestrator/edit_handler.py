"""
Voice Edit Handler
Parses edit commands and applies edits to itineraries.
Only modifies affected sections, leaving others unchanged.
"""

import re
import json
from typing import Dict, List, Optional, Any
import logging

try:
    from .intent_classifier import get_intent_classifier
    from ..mcp.mcp_client import get_mcp_client
    from ..utils.grok_client import get_grok_client
except ImportError:
    from src.orchestrator.intent_classifier import get_intent_classifier
    from src.mcp.mcp_client import get_mcp_client
    from src.utils.grok_client import get_grok_client

logger = logging.getLogger(__name__)


class EditHandler:
    """
    Handles voice/text edit commands for itineraries.
    Ensures only affected sections are modified.
    """
    
    # Edit types
    CHANGE_PACE = "CHANGE_PACE"
    SWAP_ACTIVITY = "SWAP_ACTIVITY"
    SWAP_DAYS = "SWAP_DAYS"
    MOVE_TIME_BLOCK = "MOVE_TIME_BLOCK"
    ADD_ACTIVITY = "ADD_ACTIVITY"
    ADD_DAY = "ADD_DAY"
    REMOVE_ACTIVITY = "REMOVE_ACTIVITY"
    REDUCE_TRAVEL = "REDUCE_TRAVEL"
    
    def __init__(self):
        """Initialize edit handler."""
        self.intent_classifier = get_intent_classifier()
        self.mcp_client = get_mcp_client()
        self.groq_client = get_grok_client()
        logger.info("EditHandler initialized")
    
    def parse_edit_command(self, user_input: str) -> Dict[str, Any]:
        """
        Parse edit command from user input.
        
        Args:
            user_input: User edit command text
        
        Returns:
            Dictionary with edit_type, target_day, target_time_block, and other parameters
        """
        # Use intent classifier to get initial classification
        classification = self.intent_classifier.classify_intent(user_input)
        entities = classification.get("entities", {})
        
        edit_type = entities.get("edit_type")
        target_day = entities.get("target_day")
        
        # Use Grok to extract detailed edit parameters
        prompt = f"""Parse this edit command: "{user_input}"

Return JSON with:
{{
    "edit_type": "CHANGE_PACE|SWAP_ACTIVITY|SWAP_DAYS|MOVE_TIME_BLOCK|ADD_ACTIVITY|ADD_DAY|REMOVE_ACTIVITY|REDUCE_TRAVEL",
    "target_day": number or null,
    "source_day": number or null,
    "target_time_block": "morning|afternoon|evening or null",
    "source_time_block": "morning|afternoon|evening or null",
    "target_activity": "activity name or null",
    "new_pace": "relaxed|moderate|fast or null",
    "new_activity_name": "activity name or null",
    "activity_category": "category or null",
    "place_name": "specific place/neighborhood name or null (e.g., 'Anna Nagar west')",
    "regenerate_vacated": true or false,
    "description": "what user wants to change"
}}

CRITICAL: Identify these patterns correctly. Handle voice transcription variations (e.g., "play one" = "swap day 1"):

1. DAY SWAPS (entire day):
   - "swap Day X itinerary with Day Y" → edit_type: "SWAP_DAYS", source_day: X, target_day: Y
   - "swap Day X and Day Y" → edit_type: "SWAP_DAYS", source_day: X, target_day: Y
   - "swap Day X to Day Y" → edit_type: "SWAP_DAYS", source_day: X, target_day: Y
   - "swap day 1 itinerary with day 2" → edit_type: "SWAP_DAYS", source_day: 1, target_day: 2
   - "play one with day 2" (voice transcription) → edit_type: "SWAP_DAYS", source_day: 1, target_day: 2
   - "modify day X with day Y" → edit_type: "SWAP_DAYS", source_day: X, target_day: Y
   - "change day X to day Y" → edit_type: "SWAP_DAYS", source_day: X, target_day: Y
   - If user mentions swapping two days (even without "itinerary"), it's SWAP_DAYS

2. TIME BLOCK MOVES:
   - "move Day X [time_block] to Day Y [time_block]" → edit_type: "MOVE_TIME_BLOCK", source_day: X, target_day: Y, source_time_block: [time_block], target_time_block: [time_block], regenerate_vacated: true
   - "swap Day X [time_block] with Day Y [time_block]" → edit_type: "MOVE_TIME_BLOCK", source_day: X, target_day: Y, source_time_block: [time_block], target_time_block: [time_block], regenerate_vacated: true
   - "modify Day X [time_block] with Day Y [time_block]" → edit_type: "MOVE_TIME_BLOCK", source_day: X, target_day: Y, source_time_block: [time_block], target_time_block: [time_block], regenerate_vacated: true
   - "change Day X [time_block] to Day Y [time_block]" → edit_type: "MOVE_TIME_BLOCK", source_day: X, target_day: Y, source_time_block: [time_block], target_time_block: [time_block], regenerate_vacated: true
   - "update Day X [time_block] with Day Y [time_block]" → edit_type: "MOVE_TIME_BLOCK", source_day: X, target_day: Y, source_time_block: [time_block], target_time_block: [time_block], regenerate_vacated: true
   - "Day X [time_block] to Day Y [time_block]" (voice: "day one evening to day two evening") → edit_type: "MOVE_TIME_BLOCK", source_day: X, target_day: Y, source_time_block: [time_block], target_time_block: [time_block], regenerate_vacated: true

3. REGENERATE TIME BLOCK:
   - "plan something new for Day X [time_block]" → edit_type: "MOVE_TIME_BLOCK", target_day: X, target_time_block: [time_block], regenerate_vacated: true
   - "plan new Day X [time_block]" → edit_type: "MOVE_TIME_BLOCK", target_day: X, target_time_block: [time_block], regenerate_vacated: true

4. ADD NEW DAY:
   - "add one more day", "add another day", "add extra day" → edit_type: "ADD_DAY"
   - "add one more day to the itinerary" → edit_type: "ADD_DAY"
   - "add one more day specific to this place in [city], [place_name]" → edit_type: "ADD_DAY", place_name: [place_name]
   - "add day 3", "add day three" → edit_type: "ADD_DAY", target_day: 3
   - "extend itinerary" → edit_type: "ADD_DAY"
   - If user says "add [place_name]" after "add one more day", extract place_name (e.g., "Anna Nagar west")

5. COMPLEX MOVES:
   - "I need to Day X [time_block] in Day Y [time_block] and plan something new in Day X [time_block]"
   → edit_type: "MOVE_TIME_BLOCK", source_day: X, target_day: Y, source_time_block: [time_block], target_time_block: [time_block], regenerate_vacated: true

IMPORTANT RULES:
- If TWO day numbers are mentioned with "swap"/"modify"/"change", it's ALWAYS SWAP_DAYS (not SWAP_ACTIVITY)
- Extract BOTH source_day and target_day for swaps
- For day swaps, source_day and target_day are REQUIRED
- For time block moves, source_day, target_day, source_time_block, and target_time_block are REQUIRED
- Handle voice transcription: "play" = "swap", "day to" = "day 2", "day one" = "day 1"

Extract day numbers and time blocks (morning/afternoon/evening) carefully from the text.

Only return JSON, no other text."""
        
        try:
            # Use fast model for edit parsing (token optimization)
            from src.utils.grok_client import GROQ_FAST_MODEL
            response = self.groq_client.generate_text(
                prompt=prompt,
                temperature=0.3,
                max_tokens=150,  # Reduced from 200 (token optimization)
                model=GROQ_FAST_MODEL,  # Use fast model for structured extraction
                use_cache=True
            )
            
            # Parse JSON
            response_text = response.strip()
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            
            parsed = json.loads(response_text)
            
            # Merge with entities from intent classifier, but be smart about it
            # NEVER override SWAP_DAYS or MOVE_TIME_BLOCK from LLM with intent classifier
            llm_edit_type = parsed.get("edit_type")
            if edit_type and llm_edit_type not in [self.SWAP_DAYS, self.MOVE_TIME_BLOCK]:
                # Only override if LLM didn't detect a complex edit type
                parsed["edit_type"] = edit_type
            elif llm_edit_type in [self.SWAP_DAYS, self.MOVE_TIME_BLOCK]:
                # LLM detected a complex edit - trust it
                logger.info(f"LLM detected {llm_edit_type}, keeping it (not overriding with {edit_type})")
            
            # Only override target_day if LLM didn't extract it
            if target_day and not parsed.get("target_day"):
                parsed["target_day"] = target_day
            
            # Validate and fix swap commands
            if parsed.get("edit_type") == self.SWAP_DAYS:
                if not parsed.get("source_day") or not parsed.get("target_day"):
                    # Try to extract from description if missing
                    day_numbers = re.findall(r'day\s+(\d+)', user_input.lower())
                    if len(day_numbers) >= 2:
                        parsed["source_day"] = int(day_numbers[0])
                        parsed["target_day"] = int(day_numbers[1])
                        logger.info(f"Extracted day numbers from description: source_day={parsed['source_day']}, target_day={parsed['target_day']}")
                    else:
                        logger.warning(f"SWAP_DAYS detected but missing source_day or target_day. Day numbers found: {day_numbers}")
            
            # Validate time block moves
            if parsed.get("edit_type") == self.MOVE_TIME_BLOCK:
                if not parsed.get("target_day"):
                    logger.warning(f"MOVE_TIME_BLOCK detected but missing target_day")
                if parsed.get("source_day") and not parsed.get("source_time_block"):
                    logger.warning(f"MOVE_TIME_BLOCK with source_day but missing source_time_block")
            
            # Final validation and logging
            if parsed.get("edit_type") == self.SWAP_DAYS:
                if parsed.get("source_day") and parsed.get("target_day"):
                    logger.info(f"✅ Parsed SWAP_DAYS: Day {parsed['source_day']} ↔ Day {parsed['target_day']}")
                else:
                    logger.warning(f"⚠️ SWAP_DAYS detected but missing days: source_day={parsed.get('source_day')}, target_day={parsed.get('target_day')}")
            elif parsed.get("edit_type") == self.MOVE_TIME_BLOCK:
                logger.info(f"✅ Parsed MOVE_TIME_BLOCK: Day {parsed.get('source_day')} {parsed.get('source_time_block')} → Day {parsed.get('target_day')} {parsed.get('target_time_block')}")
            
            logger.info(f"Final parsed edit command: {parsed}")
            return parsed
        
        except Exception as e:
            logger.warning(f"Edit parsing failed: {e}, using fallback")
            return self._parse_edit_command_fallback(user_input, entities)
    
    def _parse_edit_command_fallback(
        self,
        user_input: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback edit parsing using simple patterns."""
        user_input_lower = user_input.lower()
        
        edit_type = entities.get("edit_type", "CHANGE_PACE")
        target_day = entities.get("target_day")
        
        # Check for day swaps: "swap day X with day Y", "swap day X itinerary with day Y"
        # Also handle voice transcription variations like "play one" (swap day 1)
        swap_day_patterns = [
            r'(?:want\s+to\s+)?swap\s+day\s+(\d+)\s+(?:itinerary\s+)?(?:with|and|to)\s+day\s+(\d+)',
            r'swap\s+day\s+(\d+)\s+and\s+day\s+(\d+)',
            r'swap\s+day\s+(\d+)\s+itinerary\s+with\s+day\s+(\d+)',
            r'swap\s+day\s+(\d+)\s+to\s+day\s+(\d+)',
            r'swap\s+day\s+(\d+)\s+with\s+day\s+(\d+)',
            r'swap\s+day\s+(\d+)\s+itinerary\s+and\s+day\s+(\d+)',
            r'(?:play|place)\s+(?:day\s+)?(\d+)\s+(?:with|and|to)\s+day\s+(\d+)',  # Voice: "play one with day 2"
            r'modify\s+day\s+(\d+)\s+(?:with|and|to)\s+day\s+(\d+)',  # "modify day 1 with day 2"
            r'change\s+day\s+(\d+)\s+(?:with|and|to)\s+day\s+(\d+)',  # "change day 1 with day 2"
        ]
        
        for pattern in swap_day_patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                source_day = int(match.group(1))
                target_day_val = int(match.group(2))
                return {
                    "edit_type": self.SWAP_DAYS,
                    "source_day": source_day,
                    "target_day": target_day_val,
                    "target_time_block": None,
                    "source_time_block": None,
                    "target_activity": None,
                    "new_pace": None,
                    "new_activity_name": None,
                    "regenerate_vacated": False,
                    "description": user_input
                }
        
        # Check for time block moves: "move day X evening to day Y evening"
        # Also handle "swap day X evening with day Y evening" and "modify" variations
        move_time_patterns = [
            r'move\s+day\s+(\d+)\s+(morning|afternoon|evening)\s+to\s+day\s+(\d+)\s+(morning|afternoon|evening)',
            r'day\s+(\d+)\s+(morning|afternoon|evening)\s+(?:to|in)\s+day\s+(\d+)\s+(morning|afternoon|evening)',
            r'swap\s+day\s+(\d+)\s+(morning|afternoon|evening)\s+with\s+day\s+(\d+)\s+(morning|afternoon|evening)',  # "swap day 1 evening with day 2 evening"
            r'swap\s+day\s+(\d+)\s+(morning|afternoon|evening)\s+to\s+day\s+(\d+)\s+(morning|afternoon|evening)',  # "swap day 1 evening to day 2 evening"
            r'modify\s+day\s+(\d+)\s+(morning|afternoon|evening)\s+(?:with|to)\s+day\s+(\d+)\s+(morning|afternoon|evening)',  # "modify day 1 evening with day 2 evening"
            r'change\s+day\s+(\d+)\s+(morning|afternoon|evening)\s+(?:with|to)\s+day\s+(\d+)\s+(morning|afternoon|evening)',  # "change day 1 evening with day 2 evening"
            r'update\s+day\s+(\d+)\s+(morning|afternoon|evening)\s+(?:with|to)\s+day\s+(\d+)\s+(morning|afternoon|evening)',  # "update day 1 evening with day 2 evening"
            r'day\s+(\d+)\s+(morning|afternoon|evening)\s+(?:with|to)\s+day\s+(\d+)\s+(morning|afternoon|evening)',  # "day 1 evening with day 2 evening"
        ]
        
        for pattern in move_time_patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                source_day = int(match.group(1))
                source_time_block = match.group(2)
                target_day_val = int(match.group(3))
                target_time_block = match.group(4)
                return {
                    "edit_type": self.MOVE_TIME_BLOCK,
                    "source_day": source_day,
                    "target_day": target_day_val,
                    "source_time_block": source_time_block,
                    "target_time_block": target_time_block,
                    "target_activity": None,
                    "new_pace": None,
                    "new_activity_name": None,
                    "regenerate_vacated": True,
                    "description": user_input
                }
        
        # Extract all day numbers mentioned
        day_numbers = re.findall(r'day\s+(\d+)', user_input_lower)
        # Also check for "day one", "day two" etc. (voice transcription)
        day_words = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }
        for word, num in day_words.items():
            if f'day {word}' in user_input_lower or f'day {word}' in user_input_lower:
                day_numbers.append(str(num))
        
        # Check for swap/modify/change with multiple days
        swap_keywords = ["swap", "modify", "change", "switch", "replace"]
        if len(day_numbers) >= 2 and any(kw in user_input_lower for kw in swap_keywords):
            # Multiple days mentioned with swap/modify - likely a day swap
            source_day = int(day_numbers[0])
            target_day_val = int(day_numbers[1])
            return {
                "edit_type": self.SWAP_DAYS,
                "source_day": source_day,
                "target_day": target_day_val,
                "target_time_block": None,
                "source_time_block": None,
                "target_activity": None,
                "new_pace": None,
                "new_activity_name": None,
                "regenerate_vacated": False,
                "description": user_input
            }
        
        # Check for time block swap with multiple days and time blocks
        if len(day_numbers) >= 2 and target_time_block:
            # Check if both days have time blocks mentioned
            time_block_keywords = ["morning", "afternoon", "evening"]
            mentioned_time_blocks = [tb for tb in time_block_keywords if tb in user_input_lower]
            if len(mentioned_time_blocks) >= 1 and any(kw in user_input_lower for kw in swap_keywords + ["move", "update"]):
                # Likely a time block move/swap
                source_day = int(day_numbers[0])
                target_day_val = int(day_numbers[1])
                source_time_block = mentioned_time_blocks[0] if len(mentioned_time_blocks) >= 1 else target_time_block
                target_time_block_val = mentioned_time_blocks[1] if len(mentioned_time_blocks) >= 2 else target_time_block
                return {
                    "edit_type": self.MOVE_TIME_BLOCK,
                    "source_day": source_day,
                    "target_day": target_day_val,
                    "source_time_block": source_time_block,
                    "target_time_block": target_time_block_val,
                    "target_activity": None,
                    "new_pace": None,
                    "new_activity_name": None,
                    "regenerate_vacated": True,
                    "description": user_input
                }
        
        # Check for "add one more day" / "add another day" / "extend itinerary" patterns
        add_day_patterns = [
            r'add\s+(?:one\s+more|another|extra)\s+day',
            r'add\s+day\s+(\d+)',
            r'extend\s+itinerary',
            r'add\s+one\s+more\s+day\s+(?:to\s+)?(?:the\s+)?itinerary',
            r'add\s+one\s+more\s+day\s+(?:specific\s+to\s+)?(?:this\s+)?place\s+(?:in\s+)?(?:.*?),\s*([^,]+)',
        ]
        
        for pattern in add_day_patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                place_name = match.group(1) if match.groups() else None
                # Try to extract place name from common patterns
                if not place_name:
                    # Pattern: "add one more day specific to this place in chennai, Anna Nagar west"
                    place_match = re.search(r'(?:place\s+in\s+[^,]+,\s*|in\s+[^,]+,\s*)([^,]+)', user_input)
                    if place_match:
                        place_name = place_match.group(1).strip()
                
                return {
                    "edit_type": self.ADD_DAY,
                    "target_day": None,
                    "source_day": None,
                    "target_time_block": None,
                    "source_time_block": None,
                    "target_activity": None,
                    "new_pace": None,
                    "new_activity_name": None,
                    "place_name": place_name,
                    "regenerate_vacated": False,
                    "description": user_input
                }
        
        # Extract time block
        target_time_block = None
        source_time_block = None
        if "morning" in user_input_lower:
            target_time_block = "morning"
        elif "afternoon" in user_input_lower:
            target_time_block = "afternoon"
        elif "evening" in user_input_lower:
            target_time_block = "evening"
        
        # Extract activity name (simple pattern)
        activity_match = re.search(r'(?:remove|delete|add|swap)\s+([^from]+?)(?:\s+from|\s+on|$)', user_input_lower)
        target_activity = activity_match.group(1).strip() if activity_match else None
        
        # If swap is mentioned but no day swap detected, check if it's a time block swap
        if "swap" in user_input_lower and target_time_block and target_day:
            # Might be swapping time blocks - but we need more context
            # For now, treat as SWAP_ACTIVITY
            pass
        
        return {
            "edit_type": edit_type,
            "target_day": target_day,
            "source_day": int(day_numbers[0]) if day_numbers and len(day_numbers) >= 1 else None,
            "target_time_block": target_time_block,
            "source_time_block": source_time_block,
            "target_activity": target_activity,
            "new_pace": None,
            "new_activity_name": None,
            "place_name": None,  # Will be extracted by LLM if provided
            "regenerate_vacated": False,
            "description": user_input
        }
    
    def identify_affected_section(
        self,
        edit_command: Dict[str, Any],
        itinerary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Identify which section of the itinerary is affected by the edit.
        
        Args:
            edit_command: Parsed edit command
            itinerary: Current itinerary
        
        Returns:
            Dictionary with affected_sections list and context
        """
        affected_sections = []
        target_day = edit_command.get("target_day")
        source_day = edit_command.get("source_day")
        target_time_block = edit_command.get("target_time_block")
        source_time_block = edit_command.get("source_time_block")
        edit_type = edit_command.get("edit_type")
        
        # Handle day swaps
        if edit_type == self.SWAP_DAYS:
            if source_day and target_day:
                source_key = f"day_{source_day}"
                target_key = f"day_{target_day}"
                if source_key in itinerary:
                    affected_sections.append(source_key)
                if target_key in itinerary:
                    affected_sections.append(target_key)
        # Handle time block moves
        elif edit_type == self.MOVE_TIME_BLOCK:
            if source_day and source_time_block:
                source_key = f"day_{source_day}"
                if source_key in itinerary:
                    affected_sections.append(f"{source_key}.{source_time_block}")
            if target_day and target_time_block:
                target_key = f"day_{target_day}"
                if target_key in itinerary:
                    affected_sections.append(f"{target_key}.{target_time_block}")
        # Handle regular edits
        elif target_day:
            day_key = f"day_{target_day}"
            if day_key in itinerary:
                if target_time_block:
                    # Specific time block
                    affected_sections.append(f"{day_key}.{target_time_block}")
                else:
                    # Entire day
                    affected_sections.append(day_key)
        else:
            # No specific day - might affect multiple days
            # For now, assume it affects the first day or all days
            if edit_type == self.CHANGE_PACE:
                # Pace change affects all days
                for i in range(1, itinerary.get("duration_days", 3) + 1):
                    affected_sections.append(f"day_{i}")
            else:
                # Default to first day
                affected_sections.append("day_1")
        
        return {
            "affected_sections": affected_sections,
            "target_day": target_day,
            "source_day": source_day,
            "target_time_block": target_time_block,
            "source_time_block": source_time_block,
            "edit_type": edit_type
        }
    
    def apply_edit(
        self,
        itinerary: Dict[str, Any],
        edit_command: Dict[str, Any],
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Apply edit to itinerary, modifying only affected sections.
        
        Args:
            itinerary: Current itinerary
            edit_command: Parsed edit command
            preferences: User preferences (for context)
        
        Returns:
            Updated itinerary with only affected sections changed
        """
        try:
            # Create a deep copy to avoid modifying original
            updated_itinerary = json.loads(json.dumps(itinerary))
            
            # Identify affected sections
            affected_info = self.identify_affected_section(edit_command, updated_itinerary)
            affected_sections = affected_info["affected_sections"]
            edit_type = edit_command.get("edit_type")
            
            logger.info(f"Applying {edit_type} edit to sections: {affected_sections}")
            
            # Apply edit based on type
            if edit_type == self.CHANGE_PACE:
                updated_itinerary = self._apply_pace_change(
                    updated_itinerary,
                    edit_command,
                    affected_sections
                )
            elif edit_type == self.SWAP_DAYS:
                updated_itinerary = self._apply_swap_days(
                    updated_itinerary,
                    edit_command,
                    affected_sections
                )
            elif edit_type == self.MOVE_TIME_BLOCK:
                updated_itinerary = self._apply_move_time_block(
                    updated_itinerary,
                    edit_command,
                    affected_sections,
                    preferences
                )
            elif edit_type == self.ADD_ACTIVITY:
                updated_itinerary = self._apply_add_activity(
                    updated_itinerary,
                    edit_command,
                    affected_sections,
                    preferences
                )
            elif edit_type == self.ADD_DAY:
                updated_itinerary = self._apply_add_day(
                    updated_itinerary,
                    edit_command,
                    affected_sections,
                    preferences
                )
            elif edit_type == self.REMOVE_ACTIVITY:
                updated_itinerary = self._apply_remove_activity(
                    updated_itinerary,
                    edit_command,
                    affected_sections
                )
            elif edit_type == self.SWAP_ACTIVITY:
                updated_itinerary = self._apply_swap_activity(
                    updated_itinerary,
                    edit_command,
                    affected_sections
                )
            elif edit_type == self.REDUCE_TRAVEL:
                updated_itinerary = self._apply_reduce_travel(
                    updated_itinerary,
                    edit_command,
                    affected_sections
                )
            else:
                logger.warning(f"Unknown edit type: {edit_type}")
            
            # Recalculate total travel time after any edit
            updated_itinerary = self._recalculate_total_travel_time(updated_itinerary)
            
            return updated_itinerary
        
        except Exception as e:
            logger.error(f"Failed to apply edit: {e}", exc_info=True)
            return itinerary  # Return original on error
    
    def _apply_pace_change(
        self,
        itinerary: Dict[str, Any],
        edit_command: Dict[str, Any],
        affected_sections: List[str]
    ) -> Dict[str, Any]:
        """Apply pace change to affected sections."""
        new_pace = edit_command.get("new_pace")
        if not new_pace:
            # Determine pace from description
            desc = edit_command.get("description", "").lower()
            if "relaxed" in desc or "slower" in desc:
                new_pace = "relaxed"
            elif "fast paced" in desc or "fast-paced" in desc or ("fast" in desc and "pace" in desc) or "packed" in desc or "fast" in desc:
                new_pace = "fast"
            else:
                new_pace = "moderate"
        
        # Update pace in itinerary
        itinerary["pace"] = new_pace
        
        # Adjust activities per day based on pace
        activities_per_day = {
            "relaxed": 2,
            "moderate": 3,
            "fast": 4
        }
        target_count = activities_per_day.get(new_pace, 3)
        
        # For each affected day, adjust activity count
        for section in affected_sections:
            if section.startswith("day_"):
                day_num = int(section.split("_")[1])
                day_key = f"day_{day_num}"
                if day_key in itinerary:
                    day_data = itinerary[day_key]
                    # Count current activities
                    total_activities = sum(
                        len(day_data.get(time_block, {}).get("activities", []))
                        for time_block in ["morning", "afternoon", "evening"]
                    )
                    
                    # Adjust if needed (simplified - would need more logic for full implementation)
                    if total_activities > target_count:
                        # Remove some activities (simplified)
                        pass
                    elif total_activities < target_count:
                        # Add activities (would need POI search)
                        pass
        
        return itinerary
    
    def _apply_add_activity(
        self,
        itinerary: Dict[str, Any],
        edit_command: Dict[str, Any],
        affected_sections: List[str],
        preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Add activity to affected section."""
        target_day = edit_command.get("target_day", 1)
        target_time_block = edit_command.get("target_time_block", "afternoon")
        new_activity_name = edit_command.get("new_activity_name")
        activity_category = edit_command.get("activity_category", "attraction")
        
        day_key = f"day_{target_day}"
        if day_key not in itinerary:
            return itinerary
        
        # Search for POI if activity name provided
        if new_activity_name and preferences:
            city = preferences.get("city")
            if city:
                interests = [activity_category] if activity_category else ["culture"]
                pois = self.mcp_client.search_pois(
                    city=city,
                    interests=interests,
                    limit=5
                )
                
                # Find matching POI
                matching_poi = None
                for poi in pois:
                    if new_activity_name.lower() in poi.get("name", "").lower():
                        matching_poi = poi
                        break
                
                if matching_poi:
                    # Add activity
                    activity = {
                        "activity": matching_poi["name"],
                        "time": "14:00 - 15:30",  # Default time
                        "duration_minutes": matching_poi.get("duration_minutes", 90),
                        "location": matching_poi["location"],
                        "category": matching_poi.get("category", activity_category),
                        "source_id": matching_poi.get("source_id"),
                        "description": matching_poi.get("description")
                    }
                    
                    day_data = itinerary[day_key]
                    if target_time_block in day_data:
                        if "activities" not in day_data[target_time_block]:
                            day_data[target_time_block]["activities"] = []
                        day_data[target_time_block]["activities"].append(activity)
        
        return itinerary
    
    def _apply_add_day(
        self,
        itinerary: Dict[str, Any],
        edit_command: Dict[str, Any],
        affected_sections: List[str],
        preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Add a new day to the itinerary, optionally for a specific place/neighborhood."""
        if not preferences:
            logger.warning("Cannot add day without preferences")
            return itinerary
        
        # Calculate new day number (max existing day + 1)
        existing_days = [int(k.split("_")[1]) for k in itinerary.keys() if k.startswith("day_")]
        new_day_num = max(existing_days) + 1 if existing_days else 1
        
        # Check if user specified a day number
        target_day = edit_command.get("target_day")
        if target_day:
            new_day_num = int(target_day)
            if new_day_num <= max(existing_days):
                logger.warning(f"Day {new_day_num} already exists. Adding as Day {max(existing_days) + 1} instead.")
                new_day_num = max(existing_days) + 1
        
        # Extract place name if provided (e.g., "Anna Nagar west")
        place_name = edit_command.get("place_name") or edit_command.get("new_activity_name")
        
        # Get city and interests from preferences
        city = preferences.get("city")
        if not city:
            logger.warning("Cannot add day without city")
            return itinerary
        
        interests = preferences.get("interests", ["culture", "food"])
        pace = preferences.get("pace", "moderate")
        
        # Determine search location: if place_name provided, search for "place_name, city"
        search_location = f"{place_name}, {city}" if place_name else city
        country = preferences.get("country") or ("India" if city.title() in [
            "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune", "Jaipur"
        ] else None)
        
        logger.info(f"Adding Day {new_day_num} for location: {search_location} (place: {place_name or 'entire city'})")
        
        # Search for POIs in the specified location
        try:
            pois = self.mcp_client.search_pois(
                city=search_location,  # Can be "Anna Nagar west, Chennai" or just "Chennai"
                interests=interests,
                country=country,
                limit=30
            )
            logger.info(f"Found {len(pois)} POIs for new day at {search_location}")
        except Exception as e:
            logger.error(f"POI search failed for {search_location}: {e}", exc_info=True)
            # Fallback to city search if place-specific search fails
            if place_name:
                logger.info(f"Falling back to city search for {city}")
                try:
                    pois = self.mcp_client.search_pois(
                        city=city,
                        interests=interests,
                        country=country,
                        limit=30
                    )
                except Exception as fallback_error:
                    logger.error(f"Fallback POI search also failed: {fallback_error}")
                    return itinerary
            else:
                return itinerary
        
        if not pois:
            logger.warning(f"No POIs found for {search_location}")
            return itinerary
        
        # Get existing day's time windows as reference (use Day 1 if available)
        reference_day = itinerary.get("day_1", {})
        morning_start = "09:00"
        morning_end = "12:00"
        afternoon_start = "12:00"
        afternoon_end = "17:00"
        evening_start = "17:00"
        evening_end = "22:00"
        
        # Build daily time windows for the new day (single day)
        daily_time_windows = [{
            "day": 1,  # Use 1 for MCP tool (it will return day_1, we'll rename it)
            "start": morning_start,
            "end": evening_end
        }]
        
        # Build itinerary for the new day using MCP tools
        try:
            new_day_itinerary_result = self.mcp_client.build_itinerary(
                pois=pois,
                daily_time_windows=daily_time_windows,
                pace=pace,
                preferences=preferences,
                starting_point_location=None  # No specific starting point for new day
            )
            
            new_day_itinerary = new_day_itinerary_result.get("itinerary", {})
            
            # Extract day_1 from result and rename to day_N
            if "day_1" in new_day_itinerary:
                new_day_key = f"day_{new_day_num}"
                itinerary[new_day_key] = new_day_itinerary["day_1"]
                logger.info(f"✅ Successfully added {new_day_key} to itinerary")
            else:
                logger.warning(f"MCP builder didn't return day_1 structure. Keys: {list(new_day_itinerary.keys())}")
                return itinerary
        
        except Exception as e:
            logger.error(f"Failed to build itinerary for new day: {e}", exc_info=True)
            return itinerary
        
        # Update duration_days
        itinerary["duration_days"] = new_day_num
        
        # Update travel_dates array if it exists
        if "travel_dates" in itinerary and isinstance(itinerary["travel_dates"], list):
            from datetime import datetime, timedelta
            try:
                # Get the last date from existing travel_dates
                last_date_str = itinerary["travel_dates"][-1]
                last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
                # Add one day
                new_date = last_date + timedelta(days=1)
                itinerary["travel_dates"].append(new_date.strftime("%Y-%m-%d"))
                logger.info(f"Updated travel_dates: Added {new_date.strftime('%Y-%m-%d')} for Day {new_day_num}")
            except Exception as e:
                logger.warning(f"Failed to update travel_dates: {e}")
        
        return itinerary
    
    def _apply_remove_activity(
        self,
        itinerary: Dict[str, Any],
        edit_command: Dict[str, Any],
        affected_sections: List[str]
    ) -> Dict[str, Any]:
        """Remove activity from affected section."""
        target_activity = edit_command.get("target_activity")
        target_day = edit_command.get("target_day", 1)
        
        if not target_activity:
            return itinerary
        
        day_key = f"day_{target_day}"
        if day_key not in itinerary:
            return itinerary
        
        day_data = itinerary[day_key]
        
        # Search for and remove activity
        for time_block in ["morning", "afternoon", "evening"]:
            if time_block in day_data and "activities" in day_data[time_block]:
                activities = day_data[time_block]["activities"]
                day_data[time_block]["activities"] = [
                    act for act in activities
                    if target_activity.lower() not in act.get("activity", "").lower()
                ]
        
        return itinerary
    
    def _apply_swap_days(
        self,
        itinerary: Dict[str, Any],
        edit_command: Dict[str, Any],
        affected_sections: List[str]
    ) -> Dict[str, Any]:
        """Swap entire days in itinerary."""
        source_day = edit_command.get("source_day")
        target_day = edit_command.get("target_day")
        
        if not source_day or not target_day:
            logger.warning(f"SWAP_DAYS requires both source_day and target_day. Got source_day={source_day}, target_day={target_day}")
            logger.warning(f"Edit command: {edit_command}")
            return itinerary
        
        # Ensure days are integers
        try:
            source_day = int(source_day)
            target_day = int(target_day)
        except (ValueError, TypeError):
            logger.error(f"Invalid day numbers: source_day={source_day} (type: {type(source_day)}), target_day={target_day} (type: {type(target_day)})")
            return itinerary
        
        source_key = f"day_{source_day}"
        target_key = f"day_{target_day}"
        
        if source_key not in itinerary:
            logger.warning(f"Source day not found: {source_key}. Available days: {[k for k in itinerary.keys() if k.startswith('day_')]}")
            return itinerary
        
        if target_key not in itinerary:
            logger.warning(f"Target day not found: {target_key}. Available days: {[k for k in itinerary.keys() if k.startswith('day_')]}")
            return itinerary
        
        # Store original for logging
        source_original = json.dumps(itinerary[source_key], sort_keys=True)
        target_original = json.dumps(itinerary[target_key], sort_keys=True)
        
        # Swap entire day data (deep copy)
        source_data = json.loads(json.dumps(itinerary[source_key]))
        target_data = json.loads(json.dumps(itinerary[target_key]))
        
        # Perform the swap
        itinerary[source_key] = target_data
        itinerary[target_key] = source_data
        
        # Verify swap was successful
        source_after = json.dumps(itinerary[source_key], sort_keys=True)
        target_after = json.dumps(itinerary[target_key], sort_keys=True)
        
        if source_after == target_original and target_after == source_original:
            logger.info(f"✅ Successfully swapped Day {source_day} with Day {target_day}")
        else:
            logger.error(f"❌ Swap verification failed!")
            logger.error(f"Expected Day {source_day} to have Day {target_day}'s data")
            logger.error(f"Expected Day {target_day} to have Day {source_day}'s data")
        
        return itinerary
    
    def _apply_move_time_block(
        self,
        itinerary: Dict[str, Any],
        edit_command: Dict[str, Any],
        affected_sections: List[str],
        preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Move a time block from one day to another, optionally regenerating vacated slot."""
        source_day = edit_command.get("source_day")
        target_day = edit_command.get("target_day")
        source_time_block = edit_command.get("source_time_block")
        target_time_block = edit_command.get("target_time_block")
        regenerate_vacated = edit_command.get("regenerate_vacated", False)
        
        if not target_day or not target_time_block:
            logger.warning("MOVE_TIME_BLOCK requires target_day and target_time_block")
            return itinerary
        
        # If source is not specified, we're just regenerating the target
        if not source_day or not source_time_block:
            # This is a "plan something new" request
            if regenerate_vacated and preferences:
                return self._regenerate_time_block(
                    itinerary,
                    target_day,
                    target_time_block,
                    preferences
                )
            return itinerary
        
        source_key = f"day_{source_day}"
        target_key = f"day_{target_day}"
        
        if source_key not in itinerary or target_key not in itinerary:
            logger.warning(f"One or both days not found: {source_key}, {target_key}")
            return itinerary
        
        source_day_data = itinerary[source_key]
        target_day_data = itinerary[target_key]
        
        # Get the source time block data
        if source_time_block not in source_day_data:
            logger.warning(f"Source time block {source_time_block} not found in Day {source_day}")
            return itinerary
        
        source_block_data = json.loads(json.dumps(source_day_data[source_time_block]))
        
        # Move the time block
        if target_time_block not in target_day_data:
            target_day_data[target_time_block] = {}
        
        # Replace target with source (or merge if needed)
        target_day_data[target_time_block] = source_block_data
        
        logger.info(f"Moved {source_time_block} from Day {source_day} to {target_time_block} of Day {target_day}")
        
        # Regenerate vacated source time block if requested
        if regenerate_vacated and preferences:
            logger.info(f"Regenerating vacated {source_time_block} for Day {source_day}")
            # Clear the source time block
            source_day_data[source_time_block] = {"activities": []}
            # Regenerate it
            itinerary = self._regenerate_time_block(
                itinerary,
                source_day,
                source_time_block,
                preferences
            )
        
        return itinerary
    
    def _regenerate_time_block(
        self,
        itinerary: Dict[str, Any],
        day: int,
        time_block: str,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Regenerate a time block using MCP tools."""
        try:
            city = preferences.get("city")
            if not city:
                logger.warning("Cannot regenerate time block without city")
                return itinerary
            
            # Get existing POIs from itinerary to avoid duplicates
            existing_pois = set()
            for day_key in itinerary.keys():
                if day_key.startswith("day_"):
                    day_data = itinerary[day_key]
                    for tb in ["morning", "afternoon", "evening"]:
                        if tb in day_data:
                            activities = day_data[tb].get("activities", [])
                            for act in activities:
                                if act.get("activity"):
                                    existing_pois.add(act["activity"].lower())
            
            # Search for new POIs
            interests = preferences.get("interests", ["culture", "food"])
            pois = self.mcp_client.search_pois(
                city=city,
                interests=interests,
                limit=20
            )
            
            # Filter out existing POIs
            new_pois = [
                poi for poi in pois
                if poi.get("name", "").lower() not in existing_pois
            ]
            
            if not new_pois:
                logger.warning(f"No new POIs found for regeneration")
                return itinerary
            
            # Build a mini itinerary for just this time block
            # Determine time window based on time block
            time_windows = {
                "morning": {"start": "09:00", "end": "12:00"},
                "afternoon": {"start": "12:00", "end": "17:00"},
                "evening": {"start": "17:00", "end": "22:00"}
            }
            
            time_window = time_windows.get(time_block, {"start": "09:00", "end": "22:00"})
            
            # Build itinerary for this time block
            mini_itinerary = self.mcp_client.build_itinerary(
                pois=new_pois[:10],  # Use top 10 new POIs
                daily_time_windows=[{"day": day, "start": time_window["start"], "end": time_window["end"]}],
                pace=preferences.get("pace", "moderate"),
                preferences={interest: True for interest in interests}
            )
            
            if "itinerary" in mini_itinerary:
                day_key = f"day_{day}"
                if day_key in itinerary:
                    # Extract the time block from mini itinerary
                    mini_day = mini_itinerary["itinerary"].get(day_key, {})
                    if time_block in mini_day:
                        itinerary[day_key][time_block] = mini_day[time_block]
                        logger.info(f"Regenerated {time_block} for Day {day}")
            
        except Exception as e:
            logger.error(f"Failed to regenerate time block: {e}", exc_info=True)
        
        return itinerary
    
    def _apply_swap_activity(
        self,
        itinerary: Dict[str, Any],
        edit_command: Dict[str, Any],
        affected_sections: List[str]
    ) -> Dict[str, Any]:
        """Swap activities within the same time block."""
        target_day = edit_command.get("target_day", 1)
        target_time_block = edit_command.get("target_time_block", "evening")
        
        day_key = f"day_{target_day}"
        if day_key not in itinerary:
            return itinerary
        
        day_data = itinerary[day_key]
        if target_time_block in day_data and "activities" in day_data[target_time_block]:
            activities = day_data[target_time_block]["activities"]
            if len(activities) >= 2:
                # Swap first two activities
                activities[0], activities[1] = activities[1], activities[0]
        
        return itinerary
    
    def _apply_reduce_travel(
        self,
        itinerary: Dict[str, Any],
        edit_command: Dict[str, Any],
        affected_sections: List[str]
    ) -> Dict[str, Any]:
        """Reduce travel time by grouping nearby activities."""
        # This would require recalculating travel times and reordering
        # For now, just return the itinerary
        logger.info("Reduce travel edit - would require itinerary regeneration")
        return itinerary
    
    def _recalculate_total_travel_time(self, itinerary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recalculate total travel time across all days and time blocks.
        
        Args:
            itinerary: Itinerary dictionary
            
        Returns:
            Itinerary with updated total_travel_time
        """
        total_travel_time = 0
        
        # Iterate through all days
        day_keys = sorted([k for k in itinerary.keys() if k.startswith("day_")])
        previous_poi = None
        
        for day_key in day_keys:
            day_data = itinerary[day_key]
            time_blocks = ["morning", "afternoon", "evening"]
            
            for time_block in time_blocks:
                if time_block in day_data and "activities" in day_data[time_block]:
                    activities = day_data[time_block]["activities"]
                    
                    for activity in activities:
                        travel_time = activity.get("travel_time_from_previous", 0)
                        if travel_time and travel_time > 0:
                            total_travel_time += travel_time
        
        itinerary["total_travel_time"] = total_travel_time
        logger.info(f"Recalculated total travel time: {total_travel_time} minutes")
        
        return itinerary


# Global edit handler instance
_edit_handler: Optional[EditHandler] = None


def get_edit_handler() -> EditHandler:
    """
    Get or create global edit handler instance.
    
    Returns:
        EditHandler instance
    """
    global _edit_handler
    if _edit_handler is None:
        _edit_handler = EditHandler()
    return _edit_handler
