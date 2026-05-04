import logging
import json
from typing import Dict, Any, List
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logging.warning("Ollama library not installed. Diet plans will use mock data.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DietService:
    def __init__(self, default_model="llama3.2"):
        self.model_name = default_model
        self._ensure_model_available()

    def _ensure_model_available(self):
        """Auto-detects available models and switches if default is missing."""
        if not OLLAMA_AVAILABLE:
            return

        try:
            models_info = ollama.list()
            available_models = []
            
             # Handle object-based response (newer ollama client)
            if hasattr(models_info, 'models'):
                # It's a Pydantic model or similar object
                for m in models_info.models:
                    # Try attribute access first, then dict access
                    name = getattr(m, 'model', None) or getattr(m, 'name', None)
                    if not name and isinstance(m, dict):
                        name = m.get('model') or m.get('name')
                    # Fallback to string representation if needed
                    if name:
                        available_models.append(name)
                    else:
                        available_models.append(str(m))
            
            # Handle dict-based response (older clients or raw API)
            elif isinstance(models_info, dict) and 'models' in models_info:
                 for m in models_info['models']:
                    if isinstance(m, dict):
                        name = m.get('model') or m.get('name')
                    else:
                        name = getattr(m, 'model', None) or getattr(m, 'name', None)
                    
                    if name:
                        available_models.append(name)
                    else:
                        available_models.append(str(m))
            else:
                # Fallback for unexpected structures
                available_models = [str(m) for m in models_info]


            logger.info(f"DietService found available Ollama models: {available_models}")

            if self.model_name not in available_models and f"{self.model_name}:latest" not in available_models:
                # Try to find a suitable fallback
                preferred = ['llama3.2', 'llama3', 'mistral', 'gemma', 'tinyllama']
                found = False
                for p in preferred:
                    for av in available_models:
                        if p in av:
                            self.model_name = av
                            logger.info(f"DietService switched to available model: {self.model_name}")
                            found = True
                            break
                    if found: break
                
                if not found and available_models:
                    self.model_name = available_models[0]

        except Exception as e:
            logger.warning(f"DietService failed to list Ollama models: {e}")

    def check_ollama_status(self) -> bool:
        if not OLLAMA_AVAILABLE: return False
        try:
            ollama.list()
            return True
        except Exception:
            return False

    def generate_diet_plan(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a 1-day meal plan using local LLM.
        Args:
            user_profile: Dict containing 'age', 'weight', 'goal', 'preference', 'allergies'
        """
        age = user_profile.get('age', 25)
        weight = user_profile.get('weight', 70)
        goal = user_profile.get('goal', 'maintain')
        diet_type = user_profile.get('preference', 'standard')
        allergies = user_profile.get('allergies', 'none')

        logger.info(f"Generating diet plan for: {diet_type}, {goal}, allergies: {allergies}")

        if not self.check_ollama_status():
            return self._get_fallback_plan(diet_type, goal)

        prompt = f"""
        You are an expert Nutritionist. Create a detailed 1-Day Meal Plan for a person with these details:
        - Diet Preference: {diet_type}
        - Fitness Goal: {goal}
        - Allergies/Restrictions: {allergies}
        - Weight: {weight}kg

        Your response must be a valid JSON object with the following structure:
        {{
            "summary": "Brief summary of why this plan works for the goal",
            "macros": {{ "protein": "150g", "carbs": "200g", "fats": "70g", "calories": "2200" }},
            "meals": [
                {{ "type": "Breakfast", "name": "Meal Name", "ingredients": "Key ingredients list", "calories": 500 }},
                {{ "type": "Lunch", "name": "Meal Name", "ingredients": "Key ingredients list", "calories": 700 }},
                {{ "type": "Snack", "name": "Snack Name", "ingredients": "Key ingredients list", "calories": 200 }},
                {{ "type": "Dinner", "name": "Meal Name", "ingredients": "Key ingredients list", "calories": 600 }}
            ]
        }}
        
        Ensure the meals STRICTLY respect the diet preference (e.g. if Vegan, NO animal products).
        Return ONLY valid JSON.
        """

        try:
            response = ollama.chat(model=self.model_name, messages=[
                {'role': 'system', 'content': 'You are a nutritionist assistant that outputs only JSON.'},
                {'role': 'user', 'content': prompt},
            ])
            
            content = response['message']['content']
            
            # JSON Cleanup
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            plan = json.loads(content)
            return {"success": True, "plan": plan}

        except Exception as e:
            logger.error(f"Error generating diet plan: {e}")
            return self._get_fallback_plan(diet_type, goal, error=str(e))

    def _get_fallback_plan(self, diet_type, goal, error=None) -> Dict[str, Any]:
        """Returns a static plan if AI is unavailable."""
        plan = {
            "summary": "Balanced fallback plan (AI Unavailable).",
            "macros": { "protein": "140g", "carbs": "180g", "fats": "65g", "calories": "2000" },
            "meals": [
                { "type": "Breakfast", "name": "Oatmeal & Berries", "ingredients": "Oats, Blueberries, Almonds, Honey", "calories": 450 },
                { "type": "Lunch", "name": "Grilled Chicken Salad", "ingredients": "Chicken Breast, Mixed Greens, Olive Oil", "calories": 650 },
                { "type": "Snack", "name": "Greek Yogurt", "ingredients": "Yogurt, Chia Seeds", "calories": 200 },
                { "type": "Dinner", "name": "Salmon & Asparagus", "ingredients": "Salmon Fillet, Asparagus, Quinoa", "calories": 600 }
            ]
        }
        
        result = {"success": True, "plan": plan, "is_fallback": True}
        if error: result["error"] = error
        return result
