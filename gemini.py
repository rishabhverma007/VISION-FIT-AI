
import json
import logging
import os
import base64
import re
from typing import Dict, Any, Optional

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logging.warning("Google GenAI SDK not available. Using mock responses.")

from pydantic import BaseModel

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logging.warning("Ollama library not installed. Gemini helpers will use fallback templates when Google Gemini is unavailable.")


class WorkoutPlan(BaseModel):
    plan_name: str
    duration_weeks: int
    workouts: list



# Initialize Gemini AI client
client = None
GEMINI_CONFIGURED = False

# Default Gemini model (fast, general-purpose).
# You can override this with the GEMINI_MODEL environment variable, e.g.:
#   GEMINI_MODEL=models/gemini-2.5-flash
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "models/gemini-2.0-flash")
OLLAMA_MODEL: Optional[str] = None

if GENAI_AVAILABLE:
    try:
        # Use the provided API key directly
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            logging.warning("GOOGLE_API_KEY not found in environment variables. Gemini will be disabled.")
            GEMINI_CONFIGURED = False
        else:
            client = genai.Client(api_key=api_key)
            GEMINI_CONFIGURED = True
            logging.info(
                "Gemini AI configured successfully with Client "
                f"(default model: {DEFAULT_MODEL})"
            )
    except Exception as e:
        GEMINI_CONFIGURED = False
        client = None
        logging.error(f"Failed to configure Gemini AI: {e}")
else:
    GEMINI_CONFIGURED = False


def _ensure_ollama_model() -> Optional[str]:
    """
    Pick a sensible local Ollama model if available.

    Mirrors the selection logic used in yoga_service / diet_service so that
    workout planner and fitness chat can also run fully locally when Gemini
    is not configured.
    """
    global OLLAMA_MODEL

    if not OLLAMA_AVAILABLE:
        return None

    if OLLAMA_MODEL:
        return OLLAMA_MODEL

    try:
        models_info = ollama.list()
        available_models = []

        # Object-style response (newer clients)
        if hasattr(models_info, "models"):
            for m in models_info.models:
                name = getattr(m, "model", None) or getattr(m, "name", None)
                if not name and isinstance(m, dict):
                    name = m.get("model") or m.get("name")
                available_models.append(name or str(m))
        # Dict-style response
        elif isinstance(models_info, dict) and "models" in models_info:
            for m in models_info["models"]:
                if isinstance(m, dict):
                    name = m.get("model") or m.get("name")
                else:
                    name = getattr(m, "model", None) or getattr(m, "name", None)
                available_models.append(name or str(m))
        else:
            # Fallback for legacy/unknown formats
            available_models = [str(m) for m in models_info]

        if not available_models:
            logging.warning("No Ollama models found for Gemini helpers.")
            return None

        preferred = ["llama3.2", "llama3", "gemma", "mistral", "tinyllama"]
        for p in preferred:
            for av in available_models:
                if p in av:
                    OLLAMA_MODEL = av
                    logging.info(f"Gemini helpers using local Ollama model: {OLLAMA_MODEL}")
                    return OLLAMA_MODEL

        OLLAMA_MODEL = available_models[0]
        logging.info(f"Gemini helpers defaulting to first Ollama model: {OLLAMA_MODEL}")
        return OLLAMA_MODEL
    except Exception as e:
        logging.warning(f"Gemini helpers failed to list Ollama models: {e}")
        return None


def _ollama_complete(prompt: str) -> Optional[str]:
    """Small helper to run a single-turn chat on the chosen local Ollama model."""
    model = _ensure_ollama_model()
    if not model:
        return None

    try:
        resp = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful fitness assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        content = (resp.get("message") or {}).get("content") or ""
        return content.strip() or None
    except Exception as e:
        logging.error(f"Ollama error in Gemini helpers: {e}")
        return None

def generate_workout_plan(fitness_level: str, goals: str, equipment: str = "none", limitations: str = "none") -> Dict[str, Any]:
    """Generate a personalized workout plan using Gemini AI"""
    try:
        constraint_text = ""
        if limitations and limitations.lower() != 'none':
            constraint_text = f"CRITICAL: The user has the following physical limitations: {limitations}. The workout MUST accommodate these specific limitations (e.g. if 'seated', all exercises must be done in a chair)."

        prompt = f"""
        Create a personalized workout plan for someone with:
        - Fitness Level: {fitness_level}
        - Goals: {goals}
        - Available Equipment: {equipment}
        - Physical Limitations: {limitations}
        
        {constraint_text}

        Generate a detailed 4-week workout plan including:
        - Weekly workout schedule (3-5 days per week)
        - Specific exercises with sets/reps (adapted for limitations)
        - Progressive difficulty increase each week
        - Rest days and recovery advice

        Format the response as a structured workout plan with clear sections for each week.
        Make it practical and achievable for the specified fitness level.
        """

        if GEMINI_CONFIGURED and client is not None:
            try:
                # Using the new SDK call structure
                response = client.models.generate_content(
                    model=DEFAULT_MODEL,
                    contents=prompt
                )
                if response and hasattr(response, 'text'):
                    return {"success": True, "plan": response.text}
                else:
                    raise Exception("Invalid response from model")
            except Exception as api_error:
                logging.error(f"Gemini API error in generate_workout_plan: {api_error}")
                # Fall through to Ollama / mock response
                pass

        # Local Ollama fallback when Gemini is not configured/available
        ollama_text = _ollama_complete(prompt)
        if ollama_text:
            return {"success": True, "plan": ollama_text}
        
        # Mock response when Gemini is not configured or API call fails
        mock_plan = f"""
# {fitness_level.title()} Workout Plan - {goals}
## Limitations: {limitations.title()}

(Note: This is a fallback template. Configure Gemini API for fully adaptive plans.)

### Week 1-2: Foundation Building
**Monday - Adaptive Strength**
- Warm-up: 5-10 minutes gentle movement
- Exercise A: 3 sets of 8-12 reps
- Exercise B: 3 sets of 12-15 reps
...
"""
        return {"success": True, "plan": mock_plan}

    except Exception as e:
        logging.error(f"Failed to generate workout plan: {e}")
        return {"success": False, "error": str(e)}



def get_workout_plan(user_context: str) -> str:
    """Get personalized workout plan using Gemini AI"""
    # Extract information from user context
    try:
        fitness_level = re.search(r'Fitness level: ([^,]+)', user_context).group(1)
        equipment = re.search(r'Equipment: ([^,]+)', user_context).group(1)
        # Handle goals which might contain commas or other chars
        goals_match = re.search(r'Goals: ([^,]+)', user_context)
        goals = goals_match.group(1) if goals_match else "General Fitness"
        
        limitations_match = re.search(r'Limitations: (.+)$', user_context)
        limitations = limitations_match.group(1) if limitations_match else "none"
    except Exception as e:
        logging.error(f"Regex parsing error in get_workout_plan: {e}")
        # Fallback
        fitness_level = "beginner"
        equipment = "none"
        goals = "general fitness"
        limitations = "none"

    # Generate the workout plan
    result = generate_workout_plan(fitness_level, goals, equipment, limitations)
    return result['plan'] if result['success'] else 'Failed to generate workout plan. Please try again.'

def get_fitness_advice(question: str, user_context: str = "") -> str:
    """Get fitness advice using Gemini AI"""
    try:
        prompt = f"""
        You are a knowledgeable fitness coach. Answer this fitness question:
        
        Question: {question}
        
        User Context: {user_context}
        
        Provide helpful, accurate, and practical advice. Keep the response concise but informative.
        If the question is not fitness-related, politely redirect to fitness topics.
        """

        if GEMINI_CONFIGURED and client is not None:
            try:
                response = client.models.generate_content(
                    model=DEFAULT_MODEL,
                    contents=prompt
                )
                if response and hasattr(response, 'text'):
                    return response.text
                else:
                    raise Exception("Invalid response from model")
            except Exception as api_error:
                logging.error(f"Gemini API error in get_fitness_advice: {api_error}")
                # Fall through to Ollama / mock response
                pass

        # Local Ollama fallback for fitness chat
        ollama_reply = _ollama_complete(prompt)
        if ollama_reply:
            return ollama_reply
        
        # Mock response when Gemini is not configured or API call fails
        return f"""
Based on your question about "{question}", here are some general fitness tips:

• **Consistency is key** - Regular exercise, even in small amounts, is better than sporadic intense sessions
• **Progressive overload** - Gradually increase intensity, duration, or resistance over time
• **Recovery matters** - Allow adequate rest between workouts for muscle repair and growth
• **Nutrition support** - Proper nutrition fuels your workouts and aids recovery
• **Listen to your body** - Adjust intensity based on how you feel

For personalized advice, consider consulting with a certified fitness trainer or healthcare provider.

*Note: AI fitness advice is currently in demo mode. For full AI-powered responses, configure your Gemini API key.*
"""

    except Exception as e:
        logging.error(f"Failed to get fitness advice: {e}")
        return "I'm sorry, I'm having trouble processing your request right now. Please try again later."
