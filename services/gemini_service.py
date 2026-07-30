# backend/services/gemini_service.py
import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel

class ExtractedEntities(BaseModel):
    intent: str  # "price_query", "trend_query", "weather_query", or "unknown"
    crop: str | None  # Standardized English name: "Wheat", "Onion", "Potato", "Tomato", etc.
    location: str | None  # Extracted city/district/state or null if not mentioned

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else None

    def extract_intent_and_entities(self, text: str) -> dict | None:
        """Sends raw transcript to Gemini to extract intent, crop, and location."""
        if not self.client:
            return None

        prompt = f"""
        You are the Natural Language Understanding (NLU) engine for an Indian agricultural voice assistant.
        Analyze the farmer's query: "{text}"

        Tasks:
        1. Classify intent into EXACTLY one of: ["price_query", "trend_query", "weather_query", "unknown"].
        2. Extract the crop mentioned and translate it to English Title-Case (e.g., "गेहूं" -> "Wheat"; "प्याज"/"कांदा" -> "Onion"; "टमाटर" -> "Tomato"; "आलू" -> "Potato").
        3. Extract the location/city/district mentioned (e.g., "चेन्नई" -> "Chennai"; "इंदौर" -> "Indore"; "नाशिक" -> "Nashik"). If no location is mentioned, return null.
        """

        try:
            response = self.client.models.generate_content(
                model='gemini-3.5-flash-lite',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExtractedEntities,
                    temperature=0.1
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"[Gemini NLU Error]: {e}")
            return None

    def synthesize_response(self, lang: str, context_data: dict) -> str | None:
        """Sends raw factual database numbers to Gemini to compose a natural spoken response."""
        if not self.client:
            return None

        prompt = f"""
        You are a friendly AI Agricultural Voice Assistant speaking to a farmer in India.
        Language to speak in: '{lang}' ('hi' = Hindi, 'mr' = Marathi, 'en' = English).

        Factual Data to convey:
        {json.dumps(context_data, ensure_ascii=False)}

        CRITICAL INSTRUCTION:
        - Always address the price/weather specifically for the location requested by the user in context_data ('location').
        - Compose a warm, concise 1 to 2 sentence spoken response.
        - Do NOT use markdown symbols (*, **, #), bullet points, or special characters.
        """

        try:
            response = self.client.models.generate_content(
                model='gemini-3.5-flash-lite',
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            print(f"[Gemini Synthesis Error]: {e}")
            return None