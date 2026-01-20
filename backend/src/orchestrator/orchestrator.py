"""
Main Orchestrator
Orchestrates the trip planning flow, editing, and explanations.
"""

import json
from typing import Dict, List, Optional, Any
import logging

try:
    from .conversation_manager import get_conversation_manager
    from .intent_classifier import IntentClassifier, get_intent_classifier
    from .edit_handler import get_edit_handler
    from .explanation_generator import get_explanation_generator
    from ..mcp.mcp_client import get_mcp_client
    from ..rag.retriever import retrieve_city_tips
    from ..evaluation.feasibility_eval import get_feasibility_evaluator
    from ..evaluation.grounding_eval import get_grounding_evaluator
    from ..evaluation.edit_correctness_eval import get_edit_correctness_evaluator
    from ..utils.grok_client import get_grok_client
    from ..utils.config import settings
except ImportError:
    from src.orchestrator.conversation_manager import get_conversation_manager
    from src.orchestrator.intent_classifier import IntentClassifier, get_intent_classifier
    from src.orchestrator.edit_handler import get_edit_handler
    from src.orchestrator.explanation_generator import get_explanation_generator
    from src.mcp.mcp_client import get_mcp_client
    from src.rag.retriever import retrieve_city_tips
    from src.evaluation.feasibility_eval import get_feasibility_evaluator
    from src.evaluation.grounding_eval import get_grounding_evaluator
    from src.evaluation.edit_correctness_eval import get_edit_correctness_evaluator
    from src.utils.grok_client import get_grok_client
    from src.utils.config import settings

logger = logging.getLogger(__name__)


class TravelOrchestrator:
    """
    Main orchestrator for travel planning.
    Coordinates conversation management, intent classification, MCP tools, and RAG.
    """
    
    def __init__(self):
        """Initialize orchestrator."""
        self.conversation_manager = get_conversation_manager()
        self.intent_classifier = get_intent_classifier()
        self.edit_handler = get_edit_handler()
        self.explanation_generator = get_explanation_generator()
        self.feasibility_evaluator = get_feasibility_evaluator()
        self.grounding_evaluator = get_grounding_evaluator()
        self.edit_correctness_evaluator = get_edit_correctness_evaluator()
        self.mcp_client = get_mcp_client()
        self.groq_client = get_grok_client()
        self.max_clarifying_questions = getattr(settings, 'max_clarifying_questions', 6)
        logger.info("TravelOrchestrator initialized")
    
    def plan_trip(
        self,
        session_id: str,
        user_input: str
    ) -> Dict[str, Any]:
        """
        Plan a trip based on user input.
        
        Flow:
        1. Extract preferences from user_input
        2. Check if clarifying questions needed (max 6)
        3. If needed, generate clarifying question
        4. If complete, proceed:
           - Call POI Search MCP
           - Retrieve RAG context (Wikivoyage)
           - Call Itinerary Builder MCP
           - Run Feasibility Evaluator (placeholder)
           - Run Grounding Evaluator (placeholder)
           - Return itinerary + sources
        
        Args:
            session_id: Session ID
            user_input: User input text
        
        Returns:
            Dictionary with status, itinerary, or clarifying question
        """
        try:
            logger.info(f"Planning trip for session {session_id}")
            
            # Normalize voice input (handles STT errors, city corrections, number words, etc.)
            original_input = user_input
            normalized_input = self.intent_classifier.normalize_voice_input(user_input)
            
            # Log if corrections were made
            if original_input != normalized_input:
                logger.info(f"Voice input normalized: '{original_input}' → '{normalized_input}'")
                # Use normalized input for processing
                user_input = normalized_input
            
            # Get or create session
            session = self.conversation_manager.get_session(session_id)
            if not session:
                session_id = self.conversation_manager.create_session()
                session = self.conversation_manager.get_session(session_id)
            
            # Add user message to history (use normalized input if it was corrected)
            self.conversation_manager.add_message(session_id, "user", user_input)
            
            # Extract preferences from user input with conversation context
            preferences = self._extract_preferences(
                user_input, 
                session.preferences,
                session.conversation_history,
                session.clarifying_questions
            )
            
            # Normalize city name to proper title case (e.g., "jaipur" -> "Jaipur", "JAIPUR" -> "Jaipur")
            if preferences.get("city"):
                city = preferences["city"].strip()
                # Normalize to title case but preserve multi-word formats (e.g., "New York")
                preferences["city"] = city.title()
                logger.info(f"Normalized city name: '{city}' -> '{preferences['city']}'")
            
            # Update preferences
            self.conversation_manager.update_preferences(session_id, preferences)
            
            # Get updated session after preference update
            session = self.conversation_manager.get_session(session_id)
            
            # Check if we need clarifying questions
            missing_info = self._check_missing_info(preferences)
            
            # Filter out questions we've already asked
            missing_info = self._filter_already_asked_questions(missing_info, session.clarifying_questions)
            
            if missing_info and self.conversation_manager.can_ask_clarifying_question(session_id):
                # Generate clarifying question (ensuring we don't repeat)
                question = self._generate_clarifying_question(missing_info, preferences, session.clarifying_questions)
                
                # Double-check we haven't asked this exact question
                if question in session.clarifying_questions:
                    logger.warning(f"Question already asked, skipping: {question}")
                    # Try to find next missing info that hasn't been asked
                    missing_info = [m for m in missing_info if m not in [q.split()[0].lower() for q in session.clarifying_questions]]
                    if not missing_info:
                        # If we've asked all questions, proceed with what we have
                        missing_info = []
                    else:
                        question = self._generate_clarifying_question(missing_info, preferences, session.clarifying_questions)
                
                if question and question not in session.clarifying_questions:
                    self.conversation_manager.add_clarifying_question(session_id, question)
                    self.conversation_manager.add_message(session_id, "assistant", question)
                    
                    # Get updated session after adding question
                    session = self.conversation_manager.get_session(session_id)
                    
                    return {
                        "status": "clarifying",
                        "message": question,  # Use message field for consistency
                        "question": question,
                        "clarifying_questions_count": session.clarifying_questions_count,
                        "session_id": session_id,
                        "conversation_history": session.conversation_history
                    }
            
            # Check if we have minimum required info
            if not preferences.get("city") or not preferences.get("duration_days"):
                return {
                    "status": "error",
                    "message": "Please provide at least city and duration for trip planning.",
                    "session_id": session_id
                }
            
            # Check if user explicitly confirmed
            user_input_lower = user_input.lower()
            is_confirmation = any(word in user_input_lower for word in ["yes", "confirm", "proceed", "create", "generate", "plan", "go ahead", "sure", "okay", "ok"])
            
            # Check if we need confirmation (if preferences are complete including travel_mode and travel_dates, and no itinerary exists)
            has_all_required_info = (
                preferences.get("city") and 
                preferences.get("duration_days") and
                preferences.get("travel_mode") and
                preferences.get("travel_dates")
            )
            
            if not session.itinerary and has_all_required_info:
                # If not confirmed yet and not awaiting confirmation, ask for confirmation with concise summary
                if not is_confirmation and not session.preferences.get("confirmed", False) and not session.preferences.get("awaiting_confirmation", False):
                    # Format travel dates (max 3 lines total)
                    travel_dates_str = ""
                    if preferences.get("travel_dates") and len(preferences.get("travel_dates", [])) > 0:
                        dates = preferences.get("travel_dates", [])
                        if len(dates) == 1:
                            travel_dates_str = dates[0]
                        else:
                            travel_dates_str = f"{dates[0]} to {dates[-1]}"
                    
                    interests_str = ", ".join(preferences.get("interests", [])) if preferences.get("interests") else "general"
                    
                    # Concise 3-line summary
                    confirmation_message = f"Summary: {preferences.get('city')} • {preferences.get('duration_days')} days • {preferences.get('travel_mode')} • {travel_dates_str}\n"
                    confirmation_message += f"Interests: {interests_str} • Pace: {preferences.get('pace', 'moderate')}\n"
                    confirmation_message += "Create itinerary now? (Say 'yes' or 'confirm')"
                    
                    # Mark that we're asking for confirmation
                    preferences["awaiting_confirmation"] = True
                    self.conversation_manager.update_preferences(session_id, preferences)
                    
                    # Get updated session
                    session = self.conversation_manager.get_session(session_id)
                    
                    self.conversation_manager.add_message(session_id, "assistant", confirmation_message)
                    return {
                        "status": "confirmation_required",
                        "message": confirmation_message,
                        "preferences": preferences,
                        "session_id": session_id,
                        "conversation_history": session.conversation_history
                    }
            
            # If confirmed, proceed with planning
            if is_confirmation:
                preferences["confirmed"] = True
                preferences["awaiting_confirmation"] = False
                self.conversation_manager.update_preferences(session_id, preferences)
            
            # Proceed with trip planning
            logger.info(f"Planning trip: {preferences.get('city')}, {preferences.get('duration_days')} days")
            
            # 1. Search POIs
            # Normalize city name one more time before POI search to handle any variations
            city_name = preferences["city"].strip().title()
            
            # Handle common city name variations for better geocoding
            city_name_mappings = {
                "Delhi": "New Delhi",  # Delhi is often referred to as New Delhi for geocoding
            }
            if city_name in city_name_mappings:
                city_name = city_name_mappings[city_name]
            
            # Detect Indian cities and add country parameter for better geocoding
            # List of major Indian cities that might need country specification
            indian_cities = {
                "Chennai", "Mumbai", "Delhi", "New Delhi", "Kolkata", "Hyderabad", 
                "Bangalore", "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Kanpur",
                "Nagpur", "Indore", "Thane", "Bhopal", "Visakhapatnam", "Patna",
                "Vadodara", "Ghaziabad", "Ludhiana", "Agra", "Nashik", "Faridabad",
                "Meerut", "Rajkot", "Varanasi", "Srinagar", "Amritsar", "Chandigarh"
            }
            
            # Normalize city name for comparison (case-insensitive)
            country = None
            if city_name.title() in indian_cities or preferences.get("city", "").title() in indian_cities:
                country = "India"
                logger.info(f"Detected Indian city '{city_name}', adding country='India' for better geocoding")
            
            logger.info(f"Searching POIs for city: '{city_name}' (original: '{preferences['city']}'), country={country}")
            
            interests = preferences.get("interests", ["culture", "food"])  # Default interests
            logger.info(f"POI search parameters: city='{city_name}', country={country}, interests={interests}, limit=30")
            
            # Try POI search - if it fails, we'll get better error info now
            try:
                pois = self.mcp_client.search_pois(
                    city=city_name,
                    interests=interests,
                    country=country,  # Pass country parameter for better geocoding
                    constraints={
                        "budget": preferences.get("budget"),
                        "accessibility": None,
                        "time_of_day": None
                    },
                    limit=30
                )
                logger.info(f"POI search completed: found {len(pois)} POIs")
            except Exception as e:
                logger.error(f"POI search raised exception: {e}", exc_info=True)
                pois = []
            
            if not pois:
                # Verify geocoding worked (get coordinates to check)
                try:
                    from src.data_sources.geocoding import get_city_coordinates
                    coords = get_city_coordinates(city_name, country)
                    logger.info(f"Geocoding verified for '{city_name}': {coords}")
                except Exception as geocoding_error:
                    logger.error(f"Geocoding verification failed for '{city_name}': {geocoding_error}")
                
                # Try to get more details from the MCP result if available
                logger.warning(f"No POIs found for '{city_name}'. This could be due to:")
                logger.warning(f"  - City name not recognized by OpenStreetMap")
                logger.warning(f"  - No POIs matching interests: {interests}")
                logger.warning(f"  - OpenStreetMap API issue or timeout")
                logger.warning(f"  - All POIs filtered out (no names in OSM data)")
                
                # Provide a more helpful error message with suggestions
                error_msg = f"Could not find any points of interest for {city_name}."
                if interests:
                    error_msg += f" Searched for interests: {', '.join(interests)}."
                
                # Add Chennai-specific help
                if city_name.lower() in ["chennai", "madras"]:
                    error_msg += f" For Chennai, please try: 'Chennai, Tamil Nadu' or 'Chennai, India'."
                else:
                    error_msg += f" Please verify the city name is correct."
                
                error_msg += " The OpenStreetMap API may be temporarily unavailable. Please try again in a few moments."
                
                return {
                    "status": "error",
                    "message": error_msg,
                    "session_id": session_id
                }
            
            # 2. Retrieve RAG context (Wikivoyage tips) - increase to ensure we get enough sources
            # Get more RAG results to ensure we can reach 10 total sources
            city = preferences["city"]
            rag_context = retrieve_city_tips(city, query="travel tips and recommendations", top_k=10)
            
            # 3. Get starting point location - always use city center
            starting_point_location = None
            travel_mode = preferences.get("travel_mode")
            
            # Default to "driving" (car) mode for all travel time calculations
            if not travel_mode:
                travel_mode = "road"  # Default to road/car travel
                logger.info("No travel_mode specified, defaulting to 'road' (driving/car)")
            
            if pois:
                try:
                    # Always use city center as starting point
                    from src.data_sources.geocoding import get_city_coordinates
                    city_coords = get_city_coordinates(city_name, country=country if country else None)
                    starting_point_location = {
                        "lat": city_coords["lat"],
                        "lon": city_coords["lon"]
                    }
                    logger.info(f"Using city center as starting point: {city_name} at {starting_point_location}")
                except Exception as e:
                    logger.warning(f"Could not get city center coordinates: {e}, using first POI location")
                    # Fallback: use first POI location as starting point
                    if pois:
                        starting_point_location = pois[0].get("location")
            
            # 4. Build itinerary using MCP
            duration_days = preferences["duration_days"]
            time_windows = [
                {"day": day, "start": "09:00", "end": "22:00"}
                for day in range(1, duration_days + 1)
            ]
            
            # Ensure travel_mode defaults to "road" (driving/car) if not specified
            travel_mode_for_itinerary = preferences.get("travel_mode") or "road"
            logger.info(f"Building itinerary with travel_mode: {travel_mode_for_itinerary} (defaults to 'road' for driving/car)")
            
            itinerary_result = self.mcp_client.build_itinerary(
                pois=pois,
                daily_time_windows=time_windows,
                pace=preferences.get("pace", "moderate"),
                preferences={interest: True for interest in interests},
                starting_point_location=starting_point_location,
                travel_mode=travel_mode_for_itinerary
            )
            
            if "error" in itinerary_result:
                logger.error(f"Itinerary building failed: {itinerary_result.get('error')}")
                return {
                    "status": "error",
                    "message": f"Failed to build itinerary: {itinerary_result.get('error')}",
                    "session_id": session_id
                }
            
            # 5. Determine starting point name - always use city center
            starting_point = f"{city_name} City Center"
            logger.info(f"Starting point set to: {starting_point}")
            
            # 6. Ensure travel_dates array has dates for all days
            travel_dates = preferences.get("travel_dates")
            
            # If travel_dates exists but doesn't have enough dates, generate missing dates
            if travel_dates and isinstance(travel_dates, list) and len(travel_dates) > 0:
                if len(travel_dates) < duration_days:
                    # Generate missing dates from the last known date
                    from datetime import datetime, timedelta
                    try:
                        last_date = datetime.strptime(travel_dates[-1], "%Y-%m-%d")
                        # Add missing dates
                        for i in range(len(travel_dates), duration_days):
                            next_date = last_date + timedelta(days=i - len(travel_dates) + 1)
                            travel_dates.append(next_date.strftime("%Y-%m-%d"))
                        logger.info(f"Extended travel_dates array to {len(travel_dates)} dates for {duration_days}-day trip")
                    except Exception as e:
                        logger.warning(f"Failed to extend travel_dates: {e}")
            
            # If travel_dates doesn't exist or is empty, but we have start_date, generate it
            if (not travel_dates or len(travel_dates) == 0) and preferences.get("start_date"):
                from datetime import datetime, timedelta
                try:
                    start_date = datetime.strptime(preferences.get("start_date"), "%Y-%m-%d")
                    travel_dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(duration_days)]
                    logger.info(f"Generated travel_dates from start_date: {travel_dates}")
                except Exception as e:
                    logger.warning(f"Failed to generate travel_dates from start_date: {e}")
                    travel_dates = None
            
            # 7. Format itinerary (use normalized city name)
            itinerary = {
                "city": city_name,  # Use normalized city name
                "duration_days": duration_days,
                "pace": preferences.get("pace", "moderate"),
                "interests": interests,
                "travel_mode": travel_mode,
                "travel_dates": travel_dates,  # Use validated/generated travel_dates
                "starting_point": starting_point,
                **itinerary_result.get("itinerary", {})
            }
            
            logger.info(f"Itinerary created with travel_dates: {travel_dates} (length: {len(travel_dates) if travel_dates else 0}, duration_days: {duration_days})")
            
            # 7.5. Fetch weather data if travel_dates are available
            weather_by_date = {}
            if travel_dates and isinstance(travel_dates, list) and len(travel_dates) > 0:
                try:
                    from src.data_sources.weather import get_weather_for_dates
                    weather_by_date = get_weather_for_dates(
                        city=city_name,
                        travel_dates=travel_dates,
                        country=country if country else None
                    )
                    if weather_by_date:
                        logger.info(f"Fetched weather data for {len(weather_by_date)} dates")
                        # Add weather data to itinerary
                        itinerary["weather"] = weather_by_date
                    else:
                        logger.warning("Weather data fetch returned empty results")
                except Exception as e:
                    logger.warning(f"Failed to fetch weather data: {e}")
                    # Don't fail itinerary creation if weather fetch fails
            
            # 8. Prepare sources - Build from activities in itinerary (which have data_source preserved)
            # Goal: Collect up to 10 sources total (prioritize activities, then POIs, then RAG)
            sources = []
            sources_seen = set()  # Track sources to avoid duplicates
            MAX_TARGET_SOURCES = 10  # Target maximum of 10 sources
            
            # First, add sources from activities in the itinerary (these have data_source preserved)
            # Collect ALL activity sources (no limit here - we want all activities to have sources)
            if itinerary:
                for day_key in sorted([k for k in itinerary.keys() if k.startswith("day_")]):
                    day_data = itinerary.get(day_key, {})
                    for time_block in ["morning", "afternoon", "evening"]:
                        activities = day_data.get(time_block, {}).get("activities", [])
                        for activity in activities:
                            activity_name = activity.get("activity")
                            source_id = activity.get("source_id")
                            data_source = activity.get("data_source", "openstreetmap")  # Get from activity
                            
                            # Create unique key to avoid duplicates
                            source_key = f"{data_source}:{source_id}" if source_id else f"{data_source}:{activity_name}"
                            
                            if activity_name and source_key not in sources_seen:
                                sources_seen.add(source_key)
                                source_url = None
                                if source_id:
                                    # Format URL based on data source
                                    if data_source == "google_places":
                                        # Google Places uses place_id format
                                        if source_id.startswith("place_id:"):
                                            place_id = source_id.replace("place_id:", "")
                                            source_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
                                        else:
                                            source_url = f"https://www.google.com/maps/search/?api=1&query={activity_name}"
                                    else:
                                        # OpenStreetMap format
                                        if ":" in source_id:
                                            osm_type, osm_id = source_id.split(":", 1)
                                            source_url = f"https://www.openstreetmap.org/{osm_type}/{osm_id}"
                                        else:
                                            source_url = f"https://www.openstreetmap.org/node/{source_id}"
                                
                                sources.append({
                                    "type": data_source,  # Use actual data source from activity
                                    "poi": activity_name,
                                    "source_id": source_id,
                                    "url": source_url
                                })
                
                google_sources = len([s for s in sources if s.get('type') == 'google_places'])
                osm_sources = len([s for s in sources if s.get('type') == 'openstreetmap'])
                logger.info(f"✅ Added {len(sources)} sources from itinerary activities: {google_sources} Google Places, {osm_sources} OpenStreetMap")
            
            # Supplement with POIs if we don't have enough sources from activities
            # Add POIs up to MAX_TARGET_SOURCES total (don't duplicate what we already have)
            if pois and len(sources) < MAX_TARGET_SOURCES:
                remaining_slots = MAX_TARGET_SOURCES - len(sources)
                logger.info(f"Supplementing with POIs: {len(sources)} sources so far, need {remaining_slots} more to reach {MAX_TARGET_SOURCES}")
                
                added_pois = 0
                for poi in pois:
                    if added_pois >= remaining_slots:
                        break
                    
                    poi_name = poi.get("name")
                    source_id = poi.get("source_id")
                    data_source = poi.get("data_source", "openstreetmap")
                    
                    # Create unique key to avoid duplicates
                    source_key = f"{data_source}:{source_id}" if source_id else f"{data_source}:{poi_name}"
                    
                    # Skip if we already have this source
                    if source_key in sources_seen or not poi_name:
                        continue
                    
                    sources_seen.add(source_key)
                    source_url = None
                    if source_id:
                        # Format URL based on data source
                        if data_source == "google_places":
                            if source_id.startswith("place_id:"):
                                place_id = source_id.replace("place_id:", "")
                                source_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
                            else:
                                source_url = f"https://www.google.com/maps/search/?api=1&query={poi_name}"
                        else:
                            # OpenStreetMap format
                            if ":" in source_id:
                                osm_type, osm_id = source_id.split(":", 1)
                                source_url = f"https://www.openstreetmap.org/{osm_type}/{osm_id}"
                            else:
                                source_url = f"https://www.openstreetmap.org/node/{source_id}"
                    
                    sources.append({
                        "type": data_source,
                        "poi": poi_name,
                        "source_id": source_id,
                        "url": source_url
                    })
                    added_pois += 1
                
                if added_pois > 0:
                    logger.info(f"Added {added_pois} POI sources to supplement activities (total now: {len(sources)})")
            
            # Fallback: If no sources from activities at all, add from POIs (up to 10)
            if not sources and pois:
                logger.warning("⚠️ No sources from activities, falling back to POI sources")
                for poi in pois[:MAX_TARGET_SOURCES]:  # Top 10 POIs
                    poi_name = poi.get("name")
                    source_id = poi.get("source_id")
                    data_source = poi.get("data_source", "openstreetmap")
                    
                    if poi_name:  # Only add if POI has a name
                        source_url = None
                        if source_id:
                            # Format URL based on data source
                            if data_source == "google_places":
                                if source_id.startswith("place_id:"):
                                    place_id = source_id.replace("place_id:", "")
                                    source_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
                                else:
                                    source_url = f"https://www.google.com/maps/search/?api=1&query={poi_name}"
                            else:
                                # OpenStreetMap format
                                if ":" in source_id:
                                    osm_type, osm_id = source_id.split(":", 1)
                                    source_url = f"https://www.openstreetmap.org/{osm_type}/{osm_id}"
                                else:
                                    source_url = f"https://www.openstreetmap.org/node/{source_id}"
                        
                        sources.append({
                            "type": data_source,
                            "poi": poi_name,
                            "source_id": source_id,
                            "url": source_url
                        })
                
                google_sources = len([s for s in sources if s.get('type') == 'google_places'])
                osm_sources = len([s for s in sources if s.get('type') == 'openstreetmap'])
                logger.info(f"Added {google_sources} Google Places sources and {osm_sources} OpenStreetMap sources from POIs")
            
            # Add RAG/Wikivoyage sources (add all unique ones, but prioritize reaching 10 total)
            # Limit Wikivoyage to fill remaining slots up to MAX_TARGET_SOURCES
            if rag_context:
                wikivoyage_added = 0
                remaining_for_wikivoyage = max(0, MAX_TARGET_SOURCES - len(sources))
                
                for rag_item in rag_context:
                    # If we already have 10+ sources, stop adding Wikivoyage
                    if len(sources) >= MAX_TARGET_SOURCES:
                        break
                    
                    topic = rag_item.get("topic")
                    url = rag_item.get("url")
                    
                    # Create unique key to avoid duplicate Wikivoyage sources
                    wikivoyage_key = f"wikivoyage:{url}" if url else f"wikivoyage:{topic}"
                    
                    if (topic or url) and wikivoyage_key not in sources_seen:
                        sources_seen.add(wikivoyage_key)
                        sources.append({
                            "type": "wikivoyage",
                            "topic": topic,
                            "url": url,
                            "snippet": rag_item.get("snippet", "")[:200] if rag_item.get("snippet") else None
                        })
                        wikivoyage_added += 1
                
                if wikivoyage_added > 0:
                    logger.info(f"Added {wikivoyage_added} Wikivoyage sources (total now: {len(sources)})")
            
            logger.info(f"Total sources prepared: {len(sources)} (target: {MAX_TARGET_SOURCES})")
            
            # 9. Run evaluations
            constraints = {
                "daily_time_windows": time_windows
            }
            
            feasibility_result = self.feasibility_evaluator.evaluate_feasibility(
                itinerary=itinerary,
                constraints=constraints
            )
            
            grounding_result = self.grounding_evaluator.evaluate_grounding(
                itinerary=itinerary,
                sources=sources
            )
            
            evaluation = {
                "feasibility": feasibility_result,
                "grounding": grounding_result
            }
            
            # 10. Store in session
            self.conversation_manager.set_itinerary(session_id, itinerary)
            self.conversation_manager.set_sources(session_id, sources)
            self.conversation_manager.set_evaluation(session_id, evaluation)
            
            # 11. Generate explanation
            explanation = itinerary_result.get("explanation", f"Created a {duration_days}-day itinerary for {city}.")
            
            # Add assistant response
            response_message = f"I've created a {duration_days}-day itinerary for {city}. {explanation}"
            self.conversation_manager.add_message(session_id, "assistant", response_message)
            
            return {
                "status": "success",
                "message": response_message,
                "itinerary": itinerary,
                "sources": sources,
                "evaluation": evaluation,
                "explanation": explanation,
                "conversation_history": self.conversation_manager.get_context(session_id)["conversation_history"],
                "session_id": session_id
            }
        
        except Exception as e:
            logger.error(f"Trip planning failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"An error occurred while planning your trip: {str(e)}",
                "session_id": session_id
            }
    
    def edit_itinerary(
        self,
        session_id: str,
        user_input: str
    ) -> Dict[str, Any]:
        """
        Edit an existing itinerary.
        
        Flow:
        1. Parse edit intent (target_day, edit_type)
        2. Extract current itinerary section
        3. Call POI Search MCP (if needed)
        4. Call Itinerary Builder MCP (for affected day only)
        5. Run Edit Correctness Evaluator (placeholder)
        6. Return updated itinerary
        
        Args:
            session_id: Session ID
            user_input: Edit command text
        
        Returns:
            Dictionary with updated itinerary
        """
        try:
            logger.info(f"Editing itinerary for session {session_id}")
            
            # Normalize voice input (handles STT errors, voice patterns like "play one" = "swap day 1")
            original_input = user_input
            normalized_input = self.intent_classifier.normalize_voice_input(user_input)
            
            # Log if corrections were made
            if original_input != normalized_input:
                logger.info(f"Voice input normalized for edit: '{original_input}' → '{normalized_input}'")
                # Use normalized input for processing
                user_input = normalized_input
            
            session = self.conversation_manager.get_session(session_id)
            if not session or not session.itinerary:
                return {
                    "status": "error",
                    "message": "No itinerary found. Please plan a trip first.",
                    "session_id": session_id
                }
            
            # Parse edit command
            edit_command = self.edit_handler.parse_edit_command(user_input)
            
            # Add user message (use normalized input if corrected)
            self.conversation_manager.add_message(session_id, "user", user_input)
            
            # Store old itinerary for comparison
            old_itinerary = json.loads(json.dumps(session.itinerary))
            
            # Apply edit
            logger.info(f"Applying edit: {edit_command}")
            updated_itinerary = self.edit_handler.apply_edit(
                itinerary=session.itinerary,
                edit_command=edit_command,
                preferences=session.preferences
            )
            
            # Log the changes for debugging
            logger.info(f"Edit applied. Checking if itinerary changed...")
            logger.info(f"Old itinerary has {len([k for k in old_itinerary.keys() if k.startswith('day_')])} days")
            logger.info(f"New itinerary has {len([k for k in updated_itinerary.keys() if k.startswith('day_')])} days")
            
            # Evaluate edit correctness
            edit_correctness = self.edit_correctness_evaluator.evaluate_edit_correctness(
                old_itinerary=old_itinerary,
                new_itinerary=updated_itinerary,
                edit_intent=edit_command
            )
            
            # Update session with the modified itinerary
            logger.info(f"Updating session with modified itinerary...")
            self.conversation_manager.set_itinerary(session_id, updated_itinerary)
            
            # Verify the update
            updated_session = self.conversation_manager.get_session(session_id)
            if updated_session and updated_session.itinerary:
                logger.info(f"✅ Session updated successfully. Itinerary has {len([k for k in updated_session.itinerary.keys() if k.startswith('day_')])} days")
            else:
                logger.error(f"❌ Session update failed! Itinerary is None or missing")
            
            # Update evaluation
            current_eval = session.evaluation or {}
            current_eval["edit_correctness"] = edit_correctness
            self.conversation_manager.set_evaluation(session_id, current_eval)
            
            # Generate response
            edit_type = edit_command.get("edit_type", "EDIT")
            target_day = edit_command.get("target_day")
            source_day = edit_command.get("source_day")
            target_time_block = edit_command.get("target_time_block")
            source_time_block = edit_command.get("source_time_block")
            
            # Generate specific response based on edit type
            if edit_type == self.edit_handler.ADD_DAY:
                new_day_num = max([int(k.split("_")[1]) for k in updated_itinerary.keys() if k.startswith("day_")])
                place_name = edit_command.get("place_name")
                if place_name:
                    response_message = f"I've added Day {new_day_num} to your itinerary for {place_name}."
                else:
                    response_message = f"I've added Day {new_day_num} to your itinerary."
            elif edit_type == self.edit_handler.SWAP_DAYS:
                if source_day and target_day:
                    response_message = f"I've swapped Day {source_day} and Day {target_day} of your itinerary."
                else:
                    response_message = f"I've swapped the days in your itinerary."
            elif edit_type == self.edit_handler.MOVE_TIME_BLOCK:
                if source_day and target_day and source_time_block and target_time_block:
                    # Check if this is a swap (both blocks are being exchanged)
                    description = edit_command.get("description", "").lower()
                    is_swap = "swap" in description or "switch" in description
                    
                    if is_swap:
                        response_message = f"I've swapped Day {source_day} {source_time_block} with Day {target_day} {target_time_block}."
                    else:
                        response_message = f"I've moved Day {source_day} {source_time_block} to Day {target_day} {target_time_block}."
                        if edit_command.get("regenerate_vacated"):
                            response_message += f" I've also planned new activities for Day {source_day} {source_time_block}."
                elif target_day and target_time_block:
                    response_message = f"I've updated Day {target_day} {target_time_block} with new activities."
                else:
                    response_message = f"I've updated your itinerary based on your request."
            elif target_day:
                if target_time_block:
                    response_message = f"I've updated Day {target_day} {target_time_block} of your itinerary."
                else:
                    response_message = f"I've updated Day {target_day} of your itinerary."
            else:
                response_message = f"I've updated your itinerary based on your request."
            
            # Add warning if edit correctness issues
            if not edit_correctness.get("is_correct"):
                response_message += " Note: Some unexpected sections may have been modified."
            
            self.conversation_manager.add_message(session_id, "assistant", response_message)
            
            return {
                "status": "success",
                "message": response_message,
                "itinerary": updated_itinerary,
                "edit_type": edit_type,
                "target_day": target_day,
                "modified_section": edit_command.get("description", ""),
                "evaluation": {"edit_correctness": edit_correctness},
                "session_id": session_id,
                "conversation_history": session.conversation_history
            }
        
        except Exception as e:
            logger.error(f"Itinerary editing failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"An error occurred while editing the itinerary: {str(e)}",
                "session_id": session_id
            }
    
    def explain_decision(
        self,
        session_id: str,
        user_input: str
    ) -> Dict[str, Any]:
        """
        Explain a decision or answer a question.
        
        Flow:
        1. Identify what to explain (POI, timing, etc.)
        2. Retrieve relevant RAG context
        3. Retrieve original reasoning
        4. Generate explanation with citations
        5. Return explanation + sources
        
        Args:
            session_id: Session ID
            user_input: Question text
        
        Returns:
            Dictionary with explanation and sources
        """
        try:
            logger.info(f"Explaining decision for session {session_id}")
            
            # Normalize voice input (handles STT errors and voice patterns)
            original_question = user_input
            normalized_question = self.intent_classifier.normalize_voice_input(user_input)
            
            # Log if corrections were made
            if original_question != normalized_question:
                logger.info(f"Voice input normalized for explain: '{original_question}' → '{normalized_question}'")
                # Use normalized question for processing
                user_input = normalized_question
            
            session = self.conversation_manager.get_session(session_id)
            if not session:
                return {
                    "status": "error",
                    "message": "No active session found.",
                    "session_id": session_id
                }
            
            # Classify question
            classification = self.intent_classifier.classify_intent(user_input)
            entities = classification.get("entities", {})
            
            # Add user message (use normalized question if corrected)
            self.conversation_manager.add_message(session_id, "user", user_input)
            
            # Determine question type
            question_type = entities.get("question_type", "GENERAL")
            poi_name = entities.get("poi_name")
            
            # If POI name is not extracted but we have an itinerary, try to extract from question
            if not poi_name and session.itinerary:
                poi_name = self._extract_poi_from_question(user_input, session.itinerary)
            
            # Prepare context
            city = session.preferences.get("city", "unknown")
            context = {
                "city": city,
                "itinerary": session.itinerary,
                "poi_name": poi_name,
                "evaluation": session.evaluation,
                "scenario": user_input
            }
            
            # If we have a POI name, set question type to WHY_POI
            if poi_name and not question_type or question_type == "GENERAL":
                question_type = self.explanation_generator.WHY_POI
            
            # Generate explanation using explanation generator
            explanation_result = self.explanation_generator.generate_explanation(
                question=user_input,
                question_type=question_type,
                context=context
            )
            
            explanation = explanation_result.get("explanation", "")
            sources = explanation_result.get("sources", [])
            
            # Add assistant message
            self.conversation_manager.add_message(session_id, "assistant", explanation)
            
            return {
                "status": "success",
                "message": explanation,
                "explanation": explanation,
                "sources": sources,
                "question_type": explanation_result.get("question_type", question_type),
                "session_id": session_id,
                "conversation_history": session.conversation_history
            }
        
        except Exception as e:
            logger.error(f"Explanation failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"An error occurred while generating explanation: {str(e)}",
                "session_id": session_id
            }
    
    def _extract_preferences(
        self,
        user_input: str,
        existing_preferences: Dict[str, Any],
        conversation_history: List[Dict[str, str]] = None,
        clarifying_questions: List[str] = None
    ) -> Dict[str, Any]:
        """
        Extract preferences from user input with conversation context.
        
        Args:
            user_input: User input text
            existing_preferences: Existing preferences to merge with
            conversation_history: Previous conversation messages for context
            clarifying_questions: Previously asked clarifying questions
        
        Returns:
            Extracted preferences dictionary
        """
        preferences = existing_preferences.copy()
        
        # Build context from conversation history
        context_parts = []
        if conversation_history:
            # Get last few messages for context
            recent_messages = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
            context_parts.append("Recent conversation:")
            for msg in recent_messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                context_parts.append(f"{role}: {content}")
        
        if clarifying_questions:
            context_parts.append(f"\nPreviously asked questions: {', '.join(clarifying_questions[-3:])}")
        
        context_text = "\n".join(context_parts) if context_parts else ""
        
        # Check if this looks like a response to a clarifying question (short answer)
        is_short_response = len(user_input.split()) <= 5 and not any(char in user_input for char in ['?', '!', '.'])
        last_question = clarifying_questions[-1] if clarifying_questions else None
        
        # If it's a short response and we have a recent question, provide context-aware extraction
        if is_short_response and last_question:
            if "city" in last_question.lower():
                # This is likely a city name - normalize to title case
                city_name = user_input.strip().title()
                preferences["city"] = city_name
                logger.info(f"Extracted city from short response: '{user_input.strip()}' -> '{city_name}'")
            elif "day" in last_question.lower() or "duration" in last_question.lower():
                # This is likely a duration
                import re
                duration_match = re.search(r'(\d+)', user_input)
                if duration_match:
                    preferences["duration_days"] = int(duration_match.group(1))
                    logger.info(f"Extracted duration from short response: {preferences['duration_days']}")
            elif "interest" in last_question.lower():
                # This might be interests
                interests = [i.strip() for i in user_input.split(',')]
                existing = preferences.get("interests", [])
                preferences["interests"] = list(set(existing + interests))
                logger.info(f"Extracted interests from short response: {interests}")
            elif "pace" in last_question.lower():
                # This might be pace
                user_lower = user_input.lower()
                if "relaxed" in user_lower or "slow" in user_lower:
                    preferences["pace"] = "relaxed"
                elif "fast" in user_lower or "packed" in user_lower or "fast paced" in user_lower or "fast-paced" in user_lower:
                    preferences["pace"] = "fast"
                elif "moderate" in user_lower or "medium" in user_lower:
                    preferences["pace"] = "moderate"
                logger.info(f"Extracted pace from short response: {preferences.get('pace')}")
            elif "travel" in last_question.lower() and "how" in last_question.lower():
                # This is likely travel mode (road/airplane/railway)
                user_lower = user_input.lower()
                if "road" in user_lower or "car" in user_lower or "bus" in user_lower or "drive" in user_lower:
                    preferences["travel_mode"] = "road"
                elif "airplane" in user_lower or "plane" in user_lower or "air" in user_lower or "flight" in user_lower:
                    preferences["travel_mode"] = "airplane"
                elif "railway" in user_lower or "train" in user_lower or "rail" in user_lower:
                    preferences["travel_mode"] = "railway"
                logger.info(f"Extracted travel_mode from short response: {preferences.get('travel_mode')}")
            elif "date" in last_question.lower() or "when" in last_question.lower():
                # This might be travel dates - try to parse date
                import re
                from datetime import datetime
                # Try to parse date from input (e.g., "January 25, 2026" or "Jan 25 2026")
                date_patterns = [
                    r'(\w+)\s+(\d+),?\s+(\d{4})',  # "January 25, 2026"
                    r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # "01/25/2026" or "1-25-2026"
                    r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # "2026/01/25" or "2026-1-25"
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, user_input, re.IGNORECASE)
                    if match:
                        try:
                            if '/' in match.group(0) or '-' in match.group(0):
                                # Numeric date format
                                parts = re.split(r'[/-]', match.group(0))
                                if len(parts[0]) == 4:  # YYYY-MM-DD format
                                    date_str = '-'.join(parts)
                                else:  # MM-DD-YYYY format
                                    date_str = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                            else:
                                # Text date format - try to parse
                                date_str = match.group(0)
                                dt = datetime.strptime(date_str, "%B %d, %Y")
                                date_str = dt.strftime("%Y-%m-%d")
                            
                            # If we have duration_days, generate all dates
                            duration = preferences.get("duration_days", 1)
                            from datetime import datetime, timedelta
                            start_date = datetime.strptime(date_str, "%Y-%m-%d")
                            travel_dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(duration)]
                            preferences["travel_dates"] = travel_dates
                            logger.info(f"Extracted travel_dates from short response: {travel_dates} (generated {len(travel_dates)} dates for {duration}-day trip)")
                            break
                        except Exception as e:
                            logger.warning(f"Failed to parse date from '{user_input}': {e}")
                            continue
        
        # Use LLM to extract preferences with context
        prompt = f"""Extract travel preferences from this user input: "{user_input}"

{context_text}

Current known preferences: {json.dumps(existing_preferences, indent=2)}

Return JSON with:
{{
    "city": "city name or null",
    "duration_days": number or null,
    "interests": ["interest1", "interest2"] or [],
    "pace": "relaxed|moderate|fast or null",
    "budget": "low|moderate|high or null",
    "travel_mode": "road|airplane|railway or null",
    "travel_dates": ["YYYY-MM-DD"] or null,
    "start_date": "YYYY-MM-DD or null",
    "end_date": "YYYY-MM-DD or null"
}}

CRITICAL RULES:
- If the user input is a short response (like "Jaipur" or "3"), consider it as an answer to the most recent clarifying question.
- ONLY return fields that are explicitly mentioned or can be inferred from the context.
- DO NOT return null or empty arrays for fields that already have values in existing preferences UNLESS the user explicitly changes them.
- For interests: If user mentions "shopping", "food", "culture", etc., ADD them to existing interests (don't replace).
- If existing preferences already have a city, duration, or interests, DO NOT return null for those fields unless user explicitly changes them.
- Preserve ALL existing preferences that are not mentioned in the current input.

Only return JSON, no other text."""
        
        try:
            # Use fast model for preference extraction (token optimization)
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
            
            extracted = json.loads(response_text)
            
            # Convert start_date/end_date to travel_dates if needed
            if extracted.get("start_date") and not extracted.get("travel_dates"):
                from datetime import datetime, timedelta
                try:
                    start_date = datetime.strptime(extracted["start_date"], "%Y-%m-%d")
                    duration = existing_preferences.get("duration_days") or preferences.get("duration_days") or extracted.get("duration_days") or 1
                    travel_dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(duration)]
                    extracted["travel_dates"] = travel_dates
                    logger.info(f"Converted start_date to travel_dates: {travel_dates} (generated {len(travel_dates)} dates for {duration}-day trip)")
                except Exception as e:
                    logger.warning(f"Failed to convert start_date to travel_dates: {e}")
            
            # Merge with existing (only update non-None values, preserve existing)
            for key, value in extracted.items():
                if value is not None:
                    if key == "interests" and isinstance(value, list):
                        # Merge interests lists - always preserve existing interests
                        existing = preferences.get("interests", [])
                        # Normalize interest names (lowercase for comparison)
                        existing_normalized = [i.lower() for i in existing]
                        new_interests = []
                        for interest in value:
                            interest_lower = interest.lower()
                            if interest_lower not in existing_normalized:
                                new_interests.append(interest)
                        # Combine existing and new, preserving original case from existing
                        preferences[key] = existing + new_interests
                        logger.info(f"Merged interests: existing={existing}, new={new_interests}, final={preferences[key]}")
                    elif key == "city" and preferences.get("city"):
                        # Only update city if explicitly mentioned (don't overwrite existing)
                        if value and value.lower() != preferences.get("city", "").lower():
                            preferences[key] = value
                            logger.info(f"Updated city: {preferences.get('city')} -> {value}")
                    elif key == "duration_days" and preferences.get("duration_days"):
                        # Only update duration if explicitly mentioned
                        if value and value != preferences.get("duration_days"):
                            preferences[key] = value
                            logger.info(f"Updated duration: {preferences.get('duration_days')} -> {value}")
                    else:
                        preferences[key] = value
            
            return preferences
        
        except Exception as e:
            logger.warning(f"Preference extraction failed: {e}, using fallback")
            return self._extract_preferences_fallback(user_input, existing_preferences, conversation_history, clarifying_questions)
    
    def _extract_preferences_fallback(
        self,
        user_input: str,
        existing_preferences: Dict[str, Any],
        conversation_history: List[Dict[str, str]] = None,
        clarifying_questions: List[str] = None
    ) -> Dict[str, Any]:
        """
        Fallback preference extraction using simple patterns.
        Enhanced with context awareness.
        """
        preferences = existing_preferences.copy()
        user_input_lower = user_input.lower()
        user_input_stripped = user_input.strip()
        
        # Check if this looks like a response to a clarifying question
        is_short_response = len(user_input.split()) <= 5 and not any(char in user_input for char in ['?', '!', '.'])
        last_question = clarifying_questions[-1] if clarifying_questions else None
        
        # Context-aware extraction for short responses
        if is_short_response and last_question:
            question_lower = last_question.lower()
            if "city" in question_lower:
                # If it's a short response and we asked about city, treat it as a city name
                if len(user_input_stripped) > 1 and not user_input_stripped.isdigit():
                    preferences["city"] = user_input_stripped.title()  # Capitalize properly
                    logger.info(f"Fallback: Extracted city '{preferences['city']}' from short response")
                    return preferences
            elif "day" in question_lower or "duration" in question_lower:
                # Extract number from response
                import re
                numbers = re.findall(r'\d+', user_input)
                if numbers:
                    preferences["duration_days"] = int(numbers[0])
                    logger.info(f"Fallback: Extracted duration '{preferences['duration_days']}' from short response")
                    return preferences
        
        # Standard extraction patterns
        import re
        
        # Extract duration
        duration_match = re.search(r'(\d+)[\s-]?day', user_input_lower)
        if duration_match:
            preferences["duration_days"] = int(duration_match.group(1))
        
        # Extract city (look for city names in various patterns)
        if not preferences.get("city"):
            # Pattern 1: "trip to [city]", "visit [city]", "go to [city]", "in [city]"
            import re
            city_patterns = [
                r'\b(?:to|in|visit|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',  # "to Jaipur", "visit New York"
                r'\b([A-Z][a-z]{2,})',  # Standalone capitalized words (3+ chars, likely city names)
            ]
            
            for pattern in city_patterns:
                matches = re.finditer(pattern, user_input)
                for match in matches:
                    potential_city = match.group(1).strip()
                    # Skip common words that might match
                    skip_words = {'I', 'The', 'This', 'That', 'What', 'When', 'Where', 'How', 'Why', 
                                  'Want', 'Plan', 'Trip', 'Days', 'Day', 'Week', 'Weeks'}
                    if potential_city not in skip_words and len(potential_city) >= 3:
                        # Normalize to title case
                        preferences["city"] = potential_city.title()
                        logger.info(f"Fallback: Extracted city '{preferences['city']}' from pattern: {pattern}")
                        break
                if preferences.get("city"):
                    break
            
            # Pattern 2: If input is just a city name (1-3 words, capitalized)
            if not preferences.get("city"):
                words = user_input_stripped.split()
                if 1 <= len(words) <= 3:
                    # Check if it looks like a city name (not containing common travel words)
                    travel_words = {'i', 'want', 'to', 'plan', 'trip', 'go', 'visit', 'days', 'day', 'week'}
                    if not any(word.lower() in travel_words for word in words):
                        # If first word is capitalized, treat as city
                        if words[0] and words[0][0].isupper():
                            preferences["city"] = user_input_stripped.title()
                            logger.info(f"Fallback: Extracted city '{preferences['city']}' from standalone input")
        
        # Extract pace (including "fast paced" phrase)
        if "relaxed" in user_input_lower or "slow" in user_input_lower:
            preferences["pace"] = "relaxed"
        elif "fast paced" in user_input_lower or "fast-paced" in user_input_lower or ("fast" in user_input_lower and "pace" in user_input_lower) or "packed" in user_input_lower:
            preferences["pace"] = "fast"
        elif "moderate" in user_input_lower or "medium" in user_input_lower:
            preferences["pace"] = "moderate"
        
        # Extract interests (simple keywords)
        interests = []
        if any(word in user_input_lower for word in ["food", "restaurant", "dining", "eat", "cuisine"]):
            interests.append("food")
        if any(word in user_input_lower for word in ["culture", "museum", "history", "art", "heritage"]):
            interests.append("culture")
        if any(word in user_input_lower for word in ["shopping", "shop", "market", "bazaar"]):
            interests.append("shopping")
        if any(word in user_input_lower for word in ["nature", "park", "garden", "outdoor"]):
            interests.append("nature")
        
        if interests:
            existing_interests = preferences.get("interests", [])
            preferences["interests"] = list(set(existing_interests + interests))
        
        return preferences
    
    def _check_missing_info(self, preferences: Dict[str, Any]) -> List[str]:
        """
        Check what information is missing.
        
        Args:
            preferences: Current preferences
        
        Returns:
            List of missing information fields
        """
        missing = []
        
        if not preferences.get("city"):
            missing.append("city")
        if not preferences.get("duration_days"):
            missing.append("duration_days")
        
        # Travel-related questions (ask after city and duration are known)
        if preferences.get("city") and preferences.get("duration_days"):
            if not preferences.get("travel_mode"):
                missing.append("travel_mode")
            if not preferences.get("travel_dates"):
                missing.append("travel_dates")
        
        # Optional but nice to have
        if not preferences.get("interests"):
            missing.append("interests")
        if not preferences.get("pace"):
            missing.append("pace")
        
        return missing
    
    def _generate_clarifying_question(
        self,
        missing_info: List[str],
        current_preferences: Dict[str, Any],
        already_asked_questions: List[str] = None
    ) -> str:
        """
        Generate a clarifying question.
        
        Args:
            missing_info: List of missing information fields
            current_preferences: Current preferences
            already_asked_questions: Questions already asked in this session
        
        Returns:
            Clarifying question text
        """
        already_asked_questions = already_asked_questions or []
        
        # Map of field to question
        question_map = {
            "city": "Which city would you like to visit?",
            "duration_days": "How many days would you like to spend on this trip?",
            "travel_mode": "How are you traveling to the destination? (road/airplane/railway)",
            "travel_dates": "What are your travel dates? (Please provide start date, e.g., January 25, 2026)",
            "interests": "What are your main interests? (e.g., culture, food, shopping, nature)",
            "pace": "What pace would you prefer? (relaxed, moderate, or fast)"
        }
        
        # Prioritize questions (city and duration first, then travel mode/dates, then optional)
        priority_order = ["city", "duration_days", "travel_mode", "travel_dates", "interests", "pace"]
        
        for field in priority_order:
            if field in missing_info:
                question = question_map.get(field)
                # Check if we've already asked this exact question
                if question not in already_asked_questions:
                    return question
        
        # If all priority questions were asked, return generic question if needed
        if missing_info:
            return "Is there anything else you'd like me to know about your trip preferences?"
        
        return None
    
    def _filter_already_asked_questions(
        self,
        missing_info: List[str],
        already_asked_questions: List[str]
    ) -> List[str]:
        """
        Filter out fields for which we've already asked questions.
        
        Args:
            missing_info: List of missing information fields
            already_asked_questions: Questions already asked
        
        Returns:
            Filtered list of missing info fields
        """
        if not already_asked_questions:
            return missing_info
        
        # Map questions to fields
        question_to_field = {
            "Which city would you like to visit?": "city",
            "How many days would you like to spend on this trip?": "duration_days",
            "What are your main interests? (e.g., culture, food, shopping, nature)": "interests",
            "What pace would you prefer? (relaxed, moderate, or fast)": "pace"
        }
        
        # Find fields we've already asked about
        asked_fields = set()
        for question in already_asked_questions:
            # Try exact match first
            if question in question_to_field:
                asked_fields.add(question_to_field[question])
            else:
                # Try partial match
                question_lower = question.lower()
                if "city" in question_lower:
                    asked_fields.add("city")
                elif "day" in question_lower or "duration" in question_lower:
                    asked_fields.add("duration_days")
                elif "interest" in question_lower:
                    asked_fields.add("interests")
                elif "pace" in question_lower:
                    asked_fields.add("pace")
        
        # Return only fields we haven't asked about yet
        # BUT: if we asked about a field and it's still missing, we might need to ask again
        # (in case the answer wasn't clear). However, we should only re-ask if enough time has passed
        # For now, let's filter out fields we've asked about to prevent loops
        
        filtered = [field for field in missing_info if field not in asked_fields]
        
        # However, if city or duration_days are missing and we've asked about them,
        # we might want to re-ask (user might not have understood or answered incorrectly)
        # Let's be more lenient: only filter out if we asked recently and have no answer
        # For simplicity, we'll keep the filtered list but log a warning
        
        if asked_fields and filtered != missing_info:
            logger.info(f"Filtered already-asked questions. Asked fields: {asked_fields}, Filtered missing: {filtered}")
        
        return filtered
    
    def _extract_poi_from_question(
        self,
        question: str,
        itinerary: Dict[str, Any]
    ) -> Optional[str]:
        """
        Extract POI name from question by matching against itinerary activities.
        
        Args:
            question: User question
            itinerary: Current itinerary
            
        Returns:
            POI name if found, None otherwise
        """
        if not itinerary:
            return None
        
        question_lower = question.lower()
        
        # Collect all activity names from itinerary
        all_activities = []
        for day_key in sorted([k for k in itinerary.keys() if k.startswith("day_")]):
            day_data = itinerary.get(day_key, {})
            for time_block in ["morning", "afternoon", "evening"]:
                activities = day_data.get(time_block, {}).get("activities", [])
                for activity in activities:
                    activity_name = activity.get("activity", "")
                    if activity_name:
                        all_activities.append(activity_name)
        
        # Try to match question with activity names
        for activity_name in all_activities:
            activity_lower = activity_name.lower()
            # Check if activity name appears in question
            if activity_lower in question_lower or any(word in question_lower for word in activity_lower.split() if len(word) > 3):
                logger.info(f"Matched POI from question: '{activity_name}'")
                return activity_name
        
        # Try to extract using LLM if direct match fails
        try:
            prompt = f"""Extract the name of a place or activity mentioned in this question: "{question}"

Available activities in the itinerary:
{chr(10).join([f"- {act}" for act in all_activities[:10]])}

Return only the activity name if found, or "None" if not found. Do not include any other text."""
            
            # Use fast model for simple POI extraction (token optimization)
            from src.utils.grok_client import GROQ_FAST_MODEL
            response = self.groq_client.generate_text(
                prompt=prompt,
                temperature=0.3,
                max_tokens=50,  # Already optimized
                model=GROQ_FAST_MODEL,  # Use fast model for simple extraction
                use_cache=True
            )
            
            extracted_name = response.strip().strip('"').strip("'")
            
            # Verify it's in our activities list
            for activity_name in all_activities:
                if extracted_name.lower() == activity_name.lower() or extracted_name.lower() in activity_name.lower():
                    logger.info(f"Extracted POI via LLM: '{activity_name}'")
                    return activity_name
            
            if extracted_name.lower() != "none" and len(extracted_name) > 2:
                logger.info(f"LLM extracted POI (not verified): '{extracted_name}'")
                return extracted_name
        except Exception as e:
            logger.warning(f"POI extraction via LLM failed: {e}")
        
        return None


# Global orchestrator instance
_orchestrator: Optional[TravelOrchestrator] = None


def get_orchestrator() -> TravelOrchestrator:
    """
    Get or create global orchestrator instance.
    
    Returns:
        TravelOrchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TravelOrchestrator()
    return _orchestrator
