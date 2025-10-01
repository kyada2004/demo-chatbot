import json
import re
from app.features.ai import get_ai_response
from app.features.weather import fetch_weather

def fix_json(bad_json: str) -> str:
    """
    Attempts to clean and fix JSON string returned by AI.
    Removes extra text, trailing commas, and ensures proper formatting.
    """
    # Remove Markdown fences if present
    bad_json = re.sub(r"```(?:json)?", "", bad_json)
    bad_json = bad_json.strip()

    # Remove trailing commas
    bad_json = re.sub(r",\s*}", "}", bad_json)
    bad_json = re.sub(r",\s*]", "]", bad_json)

    return bad_json

def plan_trip(destination, duration, interests, trip_type, search_results):
    """
    Plans a trip to a destination based on user interests and trip type.
    """
    if not all([destination, duration, interests, trip_type]):
        return {"error": "Please provide a destination, duration, interests, and trip type."}

    try:
        weather_report = fetch_weather(destination)

        if not search_results or not search_results.get('results'):
            return {"error": f"I couldn't find enough information to plan a trip to {destination}."}

        prompt = f"""
        You are a travel assistant. Your task is to create a structured trip itinerary.

        STRICT RULES:
        - Output ONLY valid JSON. No explanations, no text outside JSON.
        - JSON must have the following structure:
        {{
            "itinerary": [
                {{
                    "day": <number>,
                    "morning": "<activity>",
                    "afternoon": "<activity>",
                    "evening": "<activity>"
                }}
            ]
        }}

        User request:
        - Destination: {destination}
        - Duration: {duration} days
        - Interests: {', '.join(interests)}
        - Trip Type: {trip_type}

        Weather forecast:
        {weather_report}

        Search results:
        {search_results['results']}
        """

        response = get_ai_response(prompt, [], "")
        itinerary_text = response.get('text', '{}')

        # Clean up AI response
        cleaned_json = fix_json(itinerary_text)

        try:
            itinerary_json = json.loads(cleaned_json)
            return itinerary_json
        except json.JSONDecodeError as e:
            print(f"[JSON Decode Error] {e}\nRaw output: {cleaned_json}")
            return {"error": "Failed to parse the itinerary. The AI did not return valid JSON."}

    except Exception as e:
        print(f"[Trip Planner Error] {e}")
        return {"error": "I encountered an error while trying to plan your trip."}
