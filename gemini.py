
import json
import logging
import os
import base64
import re
from typing import Dict, Any

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logging.warning("Google GenAI SDK not available. Using mock responses.")

from pydantic import BaseModel

from ollama_utils import list_models, pick_chat_model

class WorkoutPlan(BaseModel):
    plan_name: str
    duration_weeks: int
    workouts: list



from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Gemini AI client
client = None
GEMINI_CONFIGURED = False
DEFAULT_MODEL = 'gemini-2.0-flash'

if GENAI_AVAILABLE:
    try:
        # Use the provided API key directly
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
             logging.warning("GOOGLE_API_KEY not found in environment variables.")
             GEMINI_CONFIGURED = False
        else:
             client = genai.Client(api_key=api_key)
             GEMINI_CONFIGURED = True
             logging.info(f"Gemini AI configured successfully with Client (default model: {DEFAULT_MODEL})")
            
    except Exception as e:
        GEMINI_CONFIGURED = False
        client = None
def _query_local_ollama(prompt: str, system_prompt: str = "") -> str:
    """Fallback to local Ollama (Llama 3.2, Qwen 2.5, Mistral) if Gemini is unconfigured or fails (Module 4)"""
    try:
        import ollama
        available = list_models()
        chosen = pick_chat_model(available)
        if not chosen:
            logging.warning("No chat-capable Ollama model installed; skipping local fallback.")
            return ""

        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})

        res = ollama.chat(model=chosen, messages=messages)
        if res and 'message' in res and 'content' in res['message']:
            return res['message']['content']
    except Exception as e:
        logging.warning(f"Local Ollama fallback error: {e}")
    return ""

def generate_workout_plan(fitness_level: str, goals: str, equipment: str = "none", limitations: str = "none") -> Dict[str, Any]:
    """Generate a personalized workout plan using Gemini AI"""
    try:
        if GEMINI_CONFIGURED and client is not None:
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
                # Fall through to local Ollama or mock
                pass

        # Try local Ollama fallback (Module 4)
        ollama_response = _query_local_ollama(
            prompt=f"Create a personalized 4-week workout plan for a {fitness_level} level user with goals '{goals}', equipment '{equipment}', and physical limitations '{limitations}'. Structure clearly by weeks and days.",
            system_prompt="You are an expert fitness coach and exercise biomechanics specialist."
        )
        if ollama_response:
            return {"success": True, "plan": ollama_response}
        
        # Mock response when Gemini and Ollama are not configured or fail
        mock_plan = f"""
# {fitness_level.title()} Workout Plan - {goals}
## Limitations: {limitations.title()}

### Week 1-2: Foundation Building
**Monday - Adaptive Strength**
- Warm-up: 5-10 minutes gentle movement
- Pushups: 3 sets of 8-12 reps
- Squats: 3 sets of 12-15 reps
- Core Plank: 3 sets of 30-45 seconds
- Cool-down: 5 minutes gentle stretching

**Wednesday - Mobility & Conditioning**
- Jumping Jacks: 3 sets of 30 seconds
- Bodyweight Lunges: 3 sets of 10 reps each leg
- Glute Bridges: 3 sets of 12 reps
- Cat-Cow & Child's Pose: 5 minutes

**Friday - Strength Progression**
- Pushups (tempo controlled): 3 sets of 10-12 reps
- Squats (deep controlled): 3 sets of 12-15 reps
- Plank to Downward Dog: 3 sets of 8 reps
- Deep recovery breathing: 5 minutes

### Week 3-4: Intensity & Form Optimization
- Increase volume by 1 set per exercise or reduce rest times by 15 seconds.
- Focus on joint alignment and movement consistency (>85% form score).
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
        if GEMINI_CONFIGURED and client is not None:
            prompt = f"""
            You are a knowledgeable fitness coach. Answer this fitness question:

            Question: {question}

            User Context: {user_context}

            Provide helpful, accurate, and practical advice. Keep the response concise but informative.
            If the question is not fitness-related, politely redirect to fitness topics.
            """

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
                # Fall through to local Ollama or mock
                pass

        # Try local Ollama fallback (Module 4)
        ollama_response = _query_local_ollama(
            prompt=f"Question: {question}\n\nUser Context: {user_context}\n\nProvide practical, encouraging fitness and biomechanics advice tailored to this user.",
            system_prompt="You are a knowledgeable AI fitness coach and exercise biomechanics expert. Provide clear, direct, and actionable coaching advice."
        )
        if ollama_response:
            return ollama_response
        
        # Mock response when Gemini and Ollama are not configured or fail
        return f"""
Based on your question about "{question}", here are some general fitness tips:

• **Consistency is key** - Regular exercise, even in small amounts, is better than sporadic intense sessions
• **Progressive overload** - Gradually increase intensity, duration, or resistance over time
• **Recovery matters** - Allow adequate rest between workouts for muscle repair and growth
• **Nutrition support** - Proper nutrition fuels your workouts and aids recovery
• **Listen to your body** - Adjust intensity based on how you feel

For personalized advice, consider consulting with a certified fitness trainer or healthcare provider.
"""

    except Exception as e:
        logging.error(f"Failed to get fitness advice: {e}")
        return "I'm sorry, I'm having trouble processing your request right now. Please try again later."
