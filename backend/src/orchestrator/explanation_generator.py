"""
Explanation Generator
Generates detailed explanations for POI selections, timing, feasibility, and alternatives.
"""

from typing import Dict, List, Optional, Any
import logging

try:
    from ..rag.retriever import retrieve_city_tips, retrieve_safety_info, retrieve_indoor_alternatives
    from ..utils.grok_client import get_grok_client
    from ..data_sources.weather import get_weather_summary_for_day
except ImportError:
    from src.rag.retriever import retrieve_city_tips, retrieve_safety_info, retrieve_indoor_alternatives
    from src.utils.grok_client import get_grok_client
    from src.data_sources.weather import get_weather_summary_for_day

logger = logging.getLogger(__name__)


class ExplanationGenerator:
    """
    Generates explanations for various question types.
    Uses RAG context and LLM to create grounded explanations with citations.
    """
    
    # Question types
    WHY_POI = "WHY_POI"
    TIMING = "TIMING"
    IS_FEASIBLE = "IS_FEASIBLE"
    WHAT_IF = "WHAT_IF"
    GENERAL = "GENERAL"
    
    def __init__(self):
        """Initialize explanation generator."""
        self.groq_client = get_grok_client()
        logger.info("ExplanationGenerator initialized")
    
    def explain_poi_selection(
        self,
        poi_name: str,
        city: str,
        itinerary: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Explain why a specific POI was selected.
        
        Args:
            poi_name: Name of the POI
            city: City name
            itinerary: Optional itinerary context
        
        Returns:
            Dictionary with explanation and sources
        """
        try:
            # Retrieve RAG context about the POI
            rag_context = retrieve_city_tips(
                city=city,
                query=f"{poi_name} {city} why visit",
                top_k=5
            )
            
            # Build explanation prompt
            context_text = "\n".join([
                f"- {item.get('snippet', '')[:200]}"
                for item in rag_context[:3]
            ])
            
            prompt = f"""Explain why {poi_name} in {city} is a good choice for a travel itinerary.

Context from travel guides:
{context_text}

Provide a clear explanation with specific reasons. Cite sources when referencing facts."""
            
            explanation = self.groq_client.generate_text(
                prompt=prompt,
                temperature=0.7,
                max_tokens=300
            )
            
            # Prepare sources
            sources = []
            for item in rag_context:
                sources.append({
                    "type": "wikivoyage",
                    "topic": item.get("topic", poi_name),
                    "url": item.get("url"),
                    "snippet": item.get("snippet", "")[:200]
                })
            
            return {
                "explanation": explanation,
                "sources": sources,
                "poi_name": poi_name,
                "question_type": self.WHY_POI
            }
        
        except Exception as e:
            logger.error(f"POI explanation failed: {e}", exc_info=True)
            return {
                "explanation": f"{poi_name} is a popular attraction in {city} based on travel guides.",
                "sources": [],
                "poi_name": poi_name,
                "question_type": self.WHY_POI
            }
    
    def explain_timing(
        self,
        activity: Dict[str, Any],
        day: int,
        itinerary: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Explain why an activity is scheduled at a specific time.
        
        Args:
            activity: Activity dictionary
            day: Day number
            itinerary: Optional itinerary context
        
        Returns:
            Dictionary with explanation
        """
        try:
            activity_name = activity.get("activity", "activity")
            time_slot = activity.get("time", "unknown time")
            duration = activity.get("duration_minutes", 0)
            
            # Check for opening hours or other timing constraints
            opening_hours = activity.get("opening_hours")
            location = activity.get("location")
            
            prompt = f"""Explain why {activity_name} is scheduled at {time_slot} on Day {day}.

Activity details:
- Duration: {duration} minutes
- Opening hours: {opening_hours or 'Not specified'}
- Location: {location or 'Not specified'}

Consider factors like:
- Opening hours
- Best time to visit (avoiding crowds, weather)
- Logical flow from previous activities
- Travel time considerations

Provide a clear, practical explanation."""
            
            explanation = self.groq_client.generate_text(
                prompt=prompt,
                temperature=0.7,
                max_tokens=250
            )
            
            sources = []
            if opening_hours:
                sources.append({
                    "type": "opening_hours",
                    "info": opening_hours
                })
            
            return {
                "explanation": explanation,
                "sources": sources,
                "activity": activity_name,
                "day": day,
                "question_type": self.TIMING
            }
        
        except Exception as e:
            logger.error(f"Timing explanation failed: {e}", exc_info=True)
            return {
                "explanation": f"The timing for {activity.get('activity', 'this activity')} was chosen to fit the day's schedule and ensure a logical flow.",
                "sources": [],
                "activity": activity.get("activity", "activity"),
                "day": day,
                "question_type": self.TIMING
            }
    
    def explain_feasibility(
        self,
        itinerary: Dict[str, Any],
        evaluation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Explain whether the itinerary is feasible.
        
        Args:
            itinerary: Itinerary dictionary
            evaluation: Optional feasibility evaluation results
        
        Returns:
            Dictionary with explanation
        """
        try:
            city = itinerary.get("city", "the city")
            duration_days = itinerary.get("duration_days", 0)
            pace = itinerary.get("pace", "moderate")
            
            # Get evaluation results if available
            is_feasible = True
            violations = []
            warnings = []
            
            if evaluation and "feasibility" in evaluation:
                feas_eval = evaluation["feasibility"]
                is_feasible = feas_eval.get("is_feasible", True)
                violations = feas_eval.get("violations", [])
                warnings = feas_eval.get("warnings", [])
            
            prompt = f"""Evaluate the feasibility of this {duration_days}-day {pace} pace itinerary for {city}.

Evaluation results:
- Feasible: {is_feasible}
- Violations: {violations or 'None'}
- Warnings: {warnings or 'None'}

Provide a clear explanation of whether this itinerary is realistic and doable, considering:
- Time constraints
- Travel times between activities
- Pace consistency
- Physical feasibility

Be honest about any concerns."""
            
            explanation = self.groq_client.generate_text(
                prompt=prompt,
                temperature=0.7,
                max_tokens=300
            )
            
            return {
                "explanation": explanation,
                "sources": [],
                "is_feasible": is_feasible,
                "violations": violations,
                "warnings": warnings,
                "question_type": self.IS_FEASIBLE
            }
        
        except Exception as e:
            logger.error(f"Feasibility explanation failed: {e}", exc_info=True)
            return {
                "explanation": "The itinerary has been designed to be feasible, considering travel times and activity durations.",
                "sources": [],
                "is_feasible": True,
                "question_type": self.IS_FEASIBLE
            }
    
    def explain_weather(
        self,
        question: str,
        city: str,
        itinerary: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Explain weather forecast using actual weather data from itinerary.
        
        Args:
            question: Weather-related question (e.g., "Will it be sunny?", "What's the weather?")
            city: City name
            itinerary: Optional itinerary context with weather data
        
        Returns:
            Dictionary with weather explanation and forecast data
        """
        try:
            weather_data = itinerary.get("weather", {}) if itinerary else {}
            travel_dates = itinerary.get("travel_dates", []) if itinerary else []
            
            if not weather_data or not travel_dates:
                # No weather data available - fetch it or provide generic answer
                logger.info(f"No weather data in itinerary for {city}, providing generic weather guidance")
                return self._explain_weather_generic(question, city, itinerary)
            
            # Format weather forecast for each day
            weather_summaries = []
            rainy_days = []
            sunny_days = []
            
            for i, date in enumerate(travel_dates, 1):
                day_weather = weather_data.get(date)
                if day_weather:
                    summary = get_weather_summary_for_day(day_weather)
                    weather_summaries.append(f"Day {i} ({date}): {summary}")
                    
                    # Check for rain
                    condition = day_weather.get("condition", "").lower()
                    precip_prob = day_weather.get("precipitation_probability", 0)
                    if "rain" in condition or "drizzle" in condition or precip_prob > 50:
                        rainy_days.append((i, date, summary))
                    
                    # Check for sunny/clear
                    if "clear" in condition or "mostly_clear" in condition:
                        sunny_days.append((i, date, summary))
            
            # Build explanation based on question
            question_lower = question.lower()
            
            if "rain" in question_lower or "rainy" in question_lower:
                if rainy_days:
                    rain_info = "\n".join([f"- {summary}" for _, _, summary in rainy_days])
                    explanation = f"Based on the weather forecast for your trip to {city}:\n\n{rain_info}\n\n"
                    if len(rainy_days) == len(travel_dates):
                        explanation += "All days show rain. I recommend focusing on indoor activities like museums, galleries, shopping centers, or covered markets."
                    else:
                        explanation += f"{len(rainy_days)} out of {len(travel_dates)} days show rain. Consider indoor alternatives for those days."
                else:
                    explanation = f"Good news! The forecast shows no rain during your trip to {city}. All days look clear for outdoor activities."
            elif "sunny" in question_lower or "sun" in question_lower:
                if sunny_days:
                    sun_info = "\n".join([f"- {summary}" for _, _, summary in sunny_days])
                    explanation = f"Based on the weather forecast for your trip to {city}:\n\n{sun_info}\n\n"
                    explanation += "Perfect weather for outdoor activities! Make sure to stay hydrated and use sunscreen."
                else:
                    explanation = f"The forecast for {city} shows mostly cloudy or overcast conditions. Still good for most activities, but keep an eye on the weather."
            else:
                # General weather question
                all_forecasts = "\n".join(weather_summaries)
                explanation = f"Weather forecast for your trip to {city}:\n\n{all_forecasts}\n\n"
                
                if rainy_days:
                    explanation += f"Note: {len(rainy_days)} day(s) show rain. Consider indoor alternatives for those days."
                else:
                    explanation += "All days look good for outdoor activities!"
            
            # Add indoor alternatives if there are rainy days
            alternatives = []
            sources = []
            if rainy_days:
                try:
                    indoor_alternatives = retrieve_indoor_alternatives(city)
                    alternatives = indoor_alternatives[:5]
                    for item in indoor_alternatives[:3]:
                        sources.append({
                            "type": "wikivoyage",
                            "topic": item.get("name", "indoor alternative"),
                            "url": item.get("url"),
                            "snippet": item.get("description", "")[:200]
                        })
                except Exception as e:
                    logger.warning(f"Failed to retrieve indoor alternatives: {e}")
            
            # Add weather data source
            sources.append({
                "type": "weather",
                "source": "open-meteo",
                "data": "Weather forecast data"
            })
            
            return {
                "explanation": explanation,
                "sources": sources,
                "weather_forecast": weather_summaries,
                "rainy_days": [day for day, _, _ in rainy_days],
                "sunny_days": [day for day, _, _ in sunny_days],
                "alternatives": alternatives,
                "question_type": self.WHAT_IF
            }
        
        except Exception as e:
            logger.error(f"Weather explanation failed: {e}", exc_info=True)
            return self._explain_weather_generic(question, city, itinerary)
    
    def _explain_weather_generic(
        self,
        question: str,
        city: str,
        itinerary: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fallback weather explanation when no forecast data is available."""
        try:
            # Retrieve indoor alternatives
            indoor_alternatives = retrieve_indoor_alternatives(city)
            
            explanation = f"I don't have the current weather forecast for {city} in your itinerary. "
            explanation += "For weather-related questions, please make sure your itinerary includes travel dates. "
            explanation += "In general, if it rains, consider indoor activities like museums, galleries, or shopping centers."
            
            sources = []
            for item in indoor_alternatives[:3]:
                sources.append({
                    "type": "wikivoyage",
                    "topic": item.get("name", "indoor alternative"),
                    "url": item.get("url"),
                    "snippet": item.get("description", "")[:200]
                })
            
            return {
                "explanation": explanation,
                "sources": sources,
                "alternatives": indoor_alternatives[:5],
                "question_type": self.WHAT_IF
            }
        except Exception as e:
            logger.error(f"Generic weather explanation failed: {e}", exc_info=True)
            return {
                "explanation": f"For weather information about {city}, please ensure your itinerary includes travel dates. The system will then fetch the actual weather forecast.",
                "sources": [],
                "alternatives": [],
                "question_type": self.WHAT_IF
            }
    
    def explain_alternatives(
        self,
        scenario: str,
        city: str,
        itinerary: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Explain alternatives for a given scenario (e.g., "What if it rains?").
        Now checks for actual weather data first.
        
        Args:
            scenario: Scenario description (e.g., "it rains", "museum is closed")
            city: City name
            itinerary: Optional itinerary context
        
        Returns:
            Dictionary with explanation and alternatives
        """
        try:
            # Check if this is a weather-related question
            scenario_lower = scenario.lower()
            weather_keywords = ["rain", "rainy", "weather", "sunny", "sun", "cloudy", "storm", "snow"]
            is_weather_question = any(keyword in scenario_lower for keyword in weather_keywords)
            
            # If weather question and we have weather data, use it
            if is_weather_question and itinerary and itinerary.get("weather"):
                logger.info(f"Detected weather question, using actual forecast data")
                return self.explain_weather(scenario, city, itinerary)
            
            # Otherwise, use generic alternatives approach
            # Retrieve indoor alternatives
            indoor_alternatives = retrieve_indoor_alternatives(city)
            
            # Retrieve safety/weather info
            safety_info = retrieve_safety_info(city)
            
            # Check if we have weather data to include in context
            weather_context = ""
            if itinerary and itinerary.get("weather"):
                weather_data = itinerary.get("weather", {})
                travel_dates = itinerary.get("travel_dates", [])
                weather_summaries = []
                for date in travel_dates:
                    day_weather = weather_data.get(date)
                    if day_weather:
                        summary = get_weather_summary_for_day(day_weather)
                        weather_summaries.append(f"{date}: {summary}")
                if weather_summaries:
                    weather_context = f"\n\nCurrent weather forecast:\n" + "\n".join(weather_summaries)
            
            prompt = f"""User scenario: "{scenario}" in {city}

Available indoor alternatives:
{chr(10).join([f"- {item.get('name', 'N/A')}: {item.get('description', '')[:100]}" for item in indoor_alternatives[:5]])}
{weather_context}

Provide practical alternatives and suggestions for this scenario. Include:
- Indoor activities if weather-related
- Backup options
- How to adjust the itinerary

Be specific and helpful."""
            
            explanation = self.groq_client.generate_text(
                prompt=prompt,
                temperature=0.7,
                max_tokens=400
            )
            
            # Prepare sources
            sources = []
            for item in indoor_alternatives[:3]:
                sources.append({
                    "type": "wikivoyage",
                    "topic": item.get("name", "indoor alternative"),
                    "url": item.get("url"),
                    "snippet": item.get("description", "")[:200]
                })
            
            # Add weather source if available
            if itinerary and itinerary.get("weather"):
                sources.append({
                    "type": "weather",
                    "source": "open-meteo",
                    "data": "Weather forecast data"
                })
            
            return {
                "explanation": explanation,
                "sources": sources,
                "scenario": scenario,
                "alternatives": indoor_alternatives[:5],
                "question_type": self.WHAT_IF
            }
        
        except Exception as e:
            logger.error(f"Alternatives explanation failed: {e}", exc_info=True)
            return {
                "explanation": f"For the scenario '{scenario}' in {city}, consider indoor activities like museums, galleries, or shopping centers as alternatives.",
                "sources": [],
                "scenario": scenario,
                "alternatives": [],
                "question_type": self.WHAT_IF
            }
    
    def generate_explanation(
        self,
        question: str,
        question_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate explanation based on question type.
        
        Args:
            question: User question
            question_type: Type of question (WHY_POI, TIMING, etc.)
            context: Context dictionary with relevant information
        
        Returns:
            Dictionary with explanation and sources
        """
        city = context.get("city", "unknown")
        itinerary = context.get("itinerary")
        
        if question_type == self.WHY_POI:
            poi_name = context.get("poi_name", "")
            # If poi_name is None or empty, try to extract from question
            if not poi_name or poi_name.lower() == "none":
                # Try to extract from question text
                question = context.get("scenario", question)
                poi_name = self._extract_poi_from_text(question, itinerary)
            
            if poi_name and poi_name.lower() != "none":
                return self.explain_poi_selection(poi_name, city, itinerary)
            else:
                # Fallback to general explanation if POI not found
                logger.warning(f"POI name not found for explanation, using general explanation")
                return self._generate_general_explanation(question, city, itinerary)
        
        elif question_type == self.TIMING:
            activity = context.get("activity", {})
            day = context.get("day", 1)
            return self.explain_timing(activity, day, itinerary)
        
        elif question_type == self.IS_FEASIBLE:
            evaluation = context.get("evaluation")
            return self.explain_feasibility(itinerary, evaluation)
        
        elif question_type == self.WHAT_IF:
            scenario = context.get("scenario", question)
            return self.explain_alternatives(scenario, city, itinerary)
        
        else:
            # Check if it's a weather question even if not classified as WHAT_IF
            question_lower = question.lower()
            weather_keywords = ["weather", "rain", "rainy", "sunny", "sun", "cloudy", "forecast", "temperature", "precipitation", "will it be"]
            is_weather_question = any(keyword in question_lower for keyword in weather_keywords)
            
            if is_weather_question and itinerary and itinerary.get("weather"):
                return self.explain_weather(question, city, itinerary)
            else:
                # General explanation
                return self._generate_general_explanation(question, city, itinerary)
    
    def _generate_general_explanation(
        self,
        question: str,
        city: str,
        itinerary: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate general explanation for any question."""
        try:
            rag_context = retrieve_city_tips(city, query=question, top_k=3)
            
            context_text = "\n".join([
                item.get('snippet', '')[:200]
                for item in rag_context
            ])
            
            prompt = f"""User question: "{question}"

Context about {city}:
{context_text}

Provide a helpful, accurate answer with citations."""
            
            explanation = self.groq_client.generate_text(
                prompt=prompt,
                temperature=0.7,
                max_tokens=400
            )
            
            sources = []
            for item in rag_context:
                sources.append({
                    "type": "wikivoyage",
                    "topic": item.get("topic"),
                    "url": item.get("url"),
                    "snippet": item.get("snippet", "")[:200]
                })
            
            return {
                "explanation": explanation,
                "sources": sources,
                "question_type": self.GENERAL
            }
        
        except Exception as e:
            logger.error(f"General explanation failed: {e}", exc_info=True)
            return {
                "explanation": f"I'll help answer your question about {city}. Please provide more specific details if needed.",
                "sources": [],
                "question_type": self.GENERAL
            }
    
    def _extract_poi_from_text(
        self,
        text: str,
        itinerary: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Extract POI name from text by matching against itinerary.
        
        Args:
            text: Text to search
            itinerary: Itinerary to match against
        
        Returns:
            POI name if found, None otherwise
        """
        if not itinerary:
            return None
        
        text_lower = text.lower()
        
        # Collect all activity names
        all_activities = []
        for day_key in sorted([k for k in itinerary.keys() if k.startswith("day_")]):
            day_data = itinerary.get(day_key, {})
            for time_block in ["morning", "afternoon", "evening"]:
                activities = day_data.get(time_block, {}).get("activities", [])
                for activity in activities:
                    activity_name = activity.get("activity", "")
                    if activity_name:
                        all_activities.append(activity_name)
        
        # Try to match
        for activity_name in all_activities:
            activity_lower = activity_name.lower()
            # Check if activity name or significant words appear in text
            if activity_lower in text_lower:
                return activity_name
            # Check for significant word matches (words > 3 chars)
            activity_words = [w for w in activity_lower.split() if len(w) > 3]
            text_words = set(text_lower.split())
            if any(word in text_words for word in activity_words):
                return activity_name
        
        return None


# Global explanation generator instance
_explanation_generator: Optional[ExplanationGenerator] = None


def get_explanation_generator() -> ExplanationGenerator:
    """
    Get or create global explanation generator instance.
    
    Returns:
        ExplanationGenerator instance
    """
    global _explanation_generator
    if _explanation_generator is None:
        _explanation_generator = ExplanationGenerator()
    return _explanation_generator
