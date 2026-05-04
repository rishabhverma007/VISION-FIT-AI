import logging
import json
from typing import Dict, Any, List
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logging.warning("Ollama library not installed. Yoga plans will use mock data.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Map common LLM pose ID variations to exact database keys (for correct image lookup)
# LLMs often return "Tree Pose", "warrior_1", "Warrior I" etc. instead of exact keys.
POSE_ID_ALIASES = {
    "mountain_pose": ["mountain", "mountain pose", "tadasana", "tada"],
    "downward_dog": ["downward dog", "downward-facing dog", "downward facing dog", "adho mukha svanasana", "downward_dog"],
    "warrior_i": ["warrior i", "warrior 1", "warrior one", "warrior_i", "virabhadrasana i", "warrior1"],
    "warrior_ii": ["warrior ii", "warrior 2", "warrior two", "warrior_ii", "virabhadrasana ii", "warrior2"],
    "tree_pose": ["tree", "tree pose", "vrksasana", "tree_pose"],
    "child_pose": ["child", "child's pose", "childs pose", "child pose", "balasana", "child_pose"],
    "cobra_pose": ["cobra", "cobra pose", "bhujangasana", "cobra_pose"],
    "plank_pose": ["plank", "plank pose", "plank_pose"],
    "cat_cow": ["cat cow", "cat-cow", "cat_cow", "marjaryasana bitilasana"],
    "pigeon_pose": ["pigeon", "pigeon pose", "eka pada rajakapotasana", "one legged king pigeon"],
    "bridge_pose": ["bridge", "bridge pose", "setu bandhasana", "setu bandha"],
    "corpse_pose": ["corpse", "corpse pose", "savasana", "final relaxation", "resting pose"],
    "happy_baby": ["happy baby", "happy baby pose", "ananda balasana", "dead bug"],
    "triangle_pose": ["triangle", "triangle pose", "trikonasana", "utthita trikonasana"],
    "chair_pose": ["chair", "chair pose", "utkatasana", "fierce pose", "yoga squat"],
    "eagle_pose": ["eagle", "eagle pose", "garudasana"],
    "supine_twist": ["supine twist", "reclining twist", "spinal twist", "jathara parivartanasana"],
    "legs_up_wall": ["legs up wall", "legs up the wall", "viparita karani", "inverted pose"],
    "butterfly_pose": ["butterfly", "butterfly pose", "baddha konasana", "bound angle"],
    "standing_forward_bend": ["standing forward bend", "forward fold", "uttanasana", "standing forward fold"],
    "low_lunge": ["low lunge", "lunge", "anjaneyasana", "half kneeling"],
    "boat_pose": ["boat", "boat pose", "navasana", "paripurna navasana"],
    "reclined_butterfly": ["reclined butterfly", "supta baddha konasana", "reclined bound angle"],
    "seated_forward_bend": ["seated forward bend", "paschimottanasana", "seated forward fold"],
    "side_plank": ["side plank", "vasisthasana", "side plank pose"],
    "seated_twist": ["seated twist", "seated spinal twist", "ardha matsyendrasana", "half lord of the fishes"],
}

def _normalize_pose_id(pose_id: str, db_keys: set) -> str:
    """
    Maps LLM-returned pose id (e.g. 'Tree Pose', 'warrior_1') to exact YOGA_POSES_DB key
    so the correct image is always shown for the suggested pose.
    """
    if not pose_id:
        return ""
    raw = str(pose_id).strip().lower().replace("-", "_").replace(" ", "_")
    # Remove apostrophes for "child's pose" -> childs_pose
    raw = raw.replace("'", "")
    # Exact match
    if raw in db_keys:
        return raw
    # Alias lookup: match raw against each canonical's aliases
    for canonical, aliases in POSE_ID_ALIASES.items():
        if canonical not in db_keys:
            continue
        norm_canonical = canonical.replace("-", "_")
        if raw == norm_canonical:
            return canonical
        for a in aliases:
            norm_alias = a.strip().lower().replace("-", "_").replace(" ", "_").replace("'", "")
            if raw == norm_alias:
                return canonical
    # Fuzzy: same letters (e.g. warrior1 vs warrior_i)
    for key in db_keys:
        key_compact = key.replace("_", "")
        raw_compact = raw.replace("_", "")
        if key_compact == raw_compact:
            return key
    return ""


def _match_pose_by_name(pose_name: str, db: Dict[str, Any]) -> str:
    """
    When the LLM returns an id we don't recognize, match by the pose's display name
    so we still show the correct image for that yoga.
    """
    if not pose_name or not db:
        return ""
    raw = str(pose_name).strip().lower()
    raw = raw.replace("-", " ").replace("'", "").replace("(", " ").replace(")", " ")
    # 1) Exact or substring match against each pose's canonical name
    for pose_id, data in db.items():
        name = (data.get("name") or "").lower()
        name_clean = name.replace("-", " ").replace("(", " ").replace(")", " ")
        if raw in name_clean or name_clean in raw:
            return pose_id
    # 2) Distinctive keywords / Sanskrit -> pose_id (order matters: more specific first)
    name_to_id = [
        ("savasana", "corpse_pose"), ("corpse pose", "corpse_pose"), ("final relaxation", "corpse_pose"),
        ("tadasana", "mountain_pose"), ("mountain pose", "mountain_pose"),
        ("vrksasana", "tree_pose"), ("tree pose", "tree_pose"),
        ("balasana", "child_pose"), ("childs pose", "child_pose"), ("child pose", "child_pose"),
        ("adho mukha", "downward_dog"), ("downward dog", "downward_dog"), ("downward-facing dog", "downward_dog"),
        ("virabhadrasana i", "warrior_i"), ("warrior i", "warrior_i"), ("warrior 1", "warrior_i"),
        ("virabhadrasana ii", "warrior_ii"), ("warrior ii", "warrior_ii"), ("warrior 2", "warrior_ii"),
        ("bhujangasana", "cobra_pose"), ("cobra pose", "cobra_pose"),
        ("utkatasana", "chair_pose"), ("chair pose", "chair_pose"), ("fierce pose", "chair_pose"),
        ("trikonasana", "triangle_pose"), ("triangle pose", "triangle_pose"),
        ("garudasana", "eagle_pose"), ("eagle pose", "eagle_pose"),
        ("navasana", "boat_pose"), ("boat pose", "boat_pose"),
        ("uttanasana", "standing_forward_bend"), ("standing forward", "standing_forward_bend"), ("forward fold", "standing_forward_bend"),
        ("paschimottanasana", "seated_forward_bend"), ("seated forward", "seated_forward_bend"),
        ("rajakapotasana", "pigeon_pose"), ("pigeon pose", "pigeon_pose"),
        ("setu bandha", "bridge_pose"), ("bridge pose", "bridge_pose"),
        ("ananda balasana", "happy_baby"), ("happy baby", "happy_baby"),
        ("viparita karani", "legs_up_wall"), ("legs up", "legs_up_wall"),
        ("baddha konasana", "butterfly_pose"), ("butterfly pose", "butterfly_pose"), ("bound angle", "butterfly_pose"),
        ("supta baddha", "reclined_butterfly"), ("reclined butterfly", "reclined_butterfly"),
        ("anjaneyasana", "low_lunge"), ("low lunge", "low_lunge"),
        ("vasisthasana", "side_plank"), ("side plank", "side_plank"),
        ("ardha matsyendrasana", "seated_twist"), ("seated twist", "seated_twist"), ("spinal twist", "seated_twist"),
        ("marjaryasana", "cat_cow"), ("cat cow", "cat_cow"), ("cat-cow", "cat_cow"),
        ("plank pose", "plank_pose"),
        ("jathara parivartanasana", "supine_twist"), ("supine twist", "supine_twist"), ("reclining twist", "supine_twist"),
    ]
    for keyword, pose_id in name_to_id:
        if keyword in raw and pose_id in db:
            return pose_id
    return ""


# Local Database of Yoga Poses (The "Library")
# Esto prevents hallucination by grounding the AI's suggestions in known data.
YOGA_POSES_DB = {
    "mountain_pose": {
        "name": "Mountain Pose (Tadasana)",
        "difficulty": "Beginner",
        "benefits": "Improves posture, strengthens thighs, knees, and ankles.",
        "instructions": "Stand tall with feet together, shoulders relaxed, weight evenly distributed.",
        "image": "mountain_pose.png" 
    },
    "downward_dog": {
        "name": "Downward-Facing Dog (Adho Mukha Svanasana)",
        "difficulty": "Beginner",
        "benefits": "Stretches the shoulders, hamstrings, calves, arches, and hands.",
        "instructions": "From hands and knees, lift knees away from the floor. Lift tailbone toward ceiling.",
        "image": "downward_dog.png"
    },
    "warrior_i": {
        "name": "Warrior I (Virabhadrasana I)",
        "difficulty": "Intermediate",
        "benefits": "Stretches the chest and lungs, shoulders and neck, belly, groins (psoas).",
        "instructions": "Step feet apart. Turn right foot out 90 degrees. Bend right knee over right ankle.",
        "image": "warrior_i.png"
    },
    "warrior_ii": {
        "name": "Warrior II (Virabhadrasana II)",
        "difficulty": "Intermediate",
        "benefits": "Strengthens and stretches the legs and ankles. stretches the groins, chest and lungs, shoulders.",
        "instructions": "From standing, step feet wide apart. Turn right foot out. Bend right knee to 90 degrees, arms out to sides.",
        "image": "warrior_ii.png"
    },
    "tree_pose": {
        "name": "Tree Pose (Vrksasana)",
        "difficulty": "Beginner",
        "benefits": "Strengthens thighs, calves, ankles, and spine. Stretches the groins and inner thighs.",
        "instructions": "Stand on one leg. Place the sole of the other foot on your inner thigh or calf (avoid the knee). Hands in prayer.",
        "image": "tree_pose.png"
    },
    "child_pose": {
        "name": "Child's Pose (Balasana)",
        "difficulty": "Beginner",
        "benefits": "Gently stretches the hips, thighs, and ankles. Calms the brain and helps relieve stress.",
        "instructions": "Kneel on the floor. Touch big toes together and sit on your heels, then separate your knees about as wide as your hips.",
        "image": "child_pose.png"
    },
    "cobra_pose": {
        "name": "Cobra Pose (Bhujangasana)",
        "difficulty": "Beginner",
        "benefits": "Strengthens the spine. Stretches chest and lungs, shoulders, and abdomen.",
        "instructions": "Lie prone on the floor. Stretch legs back, tops of feet on floor. Hands under shoulders. Lift chest.",
        "image": "cobra_pose.png"
    },
     "plank_pose": {
        "name": "Plank Pose",
        "difficulty": "Intermediate",
        "benefits": "Strengthens the arms, wrists, and spine. Tones the abdomen.",
        "instructions": "Start in pushup position. Keep body in a straight line from head to heels. Engage core.",
        "image": "plank_pose.png"
    },
    "cat_cow": {
        "name": "Cat-Cow Pose (Marjaryasana-Bitilasana)",
        "difficulty": "Beginner",
        "benefits": "Warms the spine, stretches neck and torso. Improves coordination.",
        "instructions": "On hands and knees, alternate between rounding spine (cat) and arching spine (cow) with breath.",
        "image": "cat_cow.png",
        "goals": ["flexibility", "back_pain"],
        "feelings": ["sore", "stressed"],
    },
    "pigeon_pose": {
        "name": "Pigeon Pose (Eka Pada Rajakapotasana)",
        "difficulty": "Intermediate",
        "benefits": "Deep hip opener, stretches glutes and psoas. Relieves tension.",
        "instructions": "From downward dog, bring one knee forward between hands. Extend back leg. Keep hips square.",
        "image": "pigeon_pose.png",
        "goals": ["flexibility", "back_pain"],
        "feelings": ["sore", "stressed"],
    },
    "bridge_pose": {
        "name": "Bridge Pose (Setu Bandhasana)",
        "difficulty": "Beginner",
        "benefits": "Strengthens back, glutes, and legs. Opens chest. Calming.",
        "instructions": "Lie on back, knees bent, feet flat. Lift hips toward ceiling. Roll shoulders under.",
        "image": "bridge_pose.png",
        "goals": ["strength", "back_pain", "relaxation"],
        "feelings": ["tired", "stressed", "sore"],
    },
    "corpse_pose": {
        "name": "Corpse Pose / Savasana",
        "difficulty": "Beginner",
        "benefits": "Full relaxation, integrates practice. Reduces stress and fatigue.",
        "instructions": "Lie flat on back, arms slightly away from body, palms up. Close eyes and breathe naturally.",
        "image": "corpse_pose.png",
        "goals": ["relaxation"],
        "feelings": ["tired", "stressed", "sore"],
    },
    "happy_baby": {
        "name": "Happy Baby (Ananda Balasana)",
        "difficulty": "Beginner",
        "benefits": "Releases lower back and hips. Calms the mind.",
        "instructions": "Lie on back. Draw knees toward armpits. Hold feet or shins. Rock gently side to side.",
        "image": "happy_baby.png",
        "goals": ["flexibility", "relaxation", "back_pain"],
        "feelings": ["sore", "stressed", "tired"],
    },
    "triangle_pose": {
        "name": "Triangle Pose (Trikonasana)",
        "difficulty": "Intermediate",
        "benefits": "Stretches sides, hamstrings, and hips. Builds stability.",
        "instructions": "Wide stance. Turn one foot out 90°. Reach forward then down to shin or floor. Other arm up.",
        "image": "triangle_pose.png",
        "goals": ["flexibility", "balance"],
        "feelings": ["energetic"],
    },
    "chair_pose": {
        "name": "Chair Pose (Utkatasana)",
        "difficulty": "Beginner",
        "benefits": "Strengthens legs and core. Builds heat and stamina.",
        "instructions": "Stand with feet together. Sit back as if into a chair. Arms overhead or in prayer.",
        "image": "chair_pose.png",
        "goals": ["strength", "balance"],
        "feelings": ["energetic"],
    },
    "eagle_pose": {
        "name": "Eagle Pose (Garudasana)",
        "difficulty": "Intermediate",
        "benefits": "Improves balance and focus. Stretches shoulders and hips.",
        "instructions": "Stand on one leg. Wrap other leg and arm around. Sink into standing leg.",
        "image": "eagle_pose.png",
        "goals": ["balance", "flexibility"],
        "feelings": ["energetic"],
    },
    "supine_twist": {
        "name": "Supine Spinal Twist",
        "difficulty": "Beginner",
        "benefits": "Releases spine and lower back. Aids digestion.",
        "instructions": "Lie on back. Drop both knees to one side. Turn gaze opposite. Breathe and switch sides.",
        "image": "supine_twist.png",
        "goals": ["back_pain", "relaxation", "flexibility"],
        "feelings": ["sore", "tired", "stressed"],
    },
    "legs_up_wall": {
        "name": "Legs Up the Wall (Viparita Karani)",
        "difficulty": "Beginner",
        "benefits": "Restorative. Reduces swelling, calms nervous system.",
        "instructions": "Sit close to wall, swing legs up. Rest with legs vertical. Optional blanket under hips.",
        "image": "legs_up_wall.png",
        "goals": ["relaxation"],
        "feelings": ["tired", "stressed", "sore"],
    },
    "butterfly_pose": {
        "name": "Butterfly / Bound Angle (Baddha Konasana)",
        "difficulty": "Beginner",
        "benefits": "Opens hips and groins. Can be done seated in a chair.",
        "instructions": "Sit with soles of feet together. Let knees fall out. Sit tall or fold forward.",
        "image": "butterfly_pose.png",
        "goals": ["flexibility", "relaxation"],
        "feelings": ["stressed", "tired"],
    },
    "standing_forward_bend": {
        "name": "Standing Forward Bend (Uttanasana)",
        "difficulty": "Beginner",
        "benefits": "Stretches hamstrings and spine. Calms the mind.",
        "instructions": "Stand with feet hip-width. Hinge at hips and fold forward. Let head hang.",
        "image": "standing_forward_bend.png",
        "goals": ["flexibility", "back_pain"],
        "feelings": ["stressed", "sore"],
    },
    "low_lunge": {
        "name": "Low Lunge (Anjaneyasana)",
        "difficulty": "Beginner",
        "benefits": "Hip flexor and psoas stretch. Opens chest.",
        "instructions": "From kneeling, step one foot forward. Lower back knee. Lift chest, arms overhead or hands on thigh.",
        "image": "low_lunge.png",
        "goals": ["flexibility", "back_pain"],
        "feelings": ["sore", "energetic"],
    },
    "boat_pose": {
        "name": "Boat Pose (Navasana)",
        "difficulty": "Intermediate",
        "benefits": "Core strength and balance.",
        "instructions": "Sit with knees bent. Lean back, lift feet. Extend legs if possible. Arms parallel to floor.",
        "image": "boat_pose.png",
        "goals": ["strength", "balance"],
        "feelings": ["energetic"],
    },
    "reclined_butterfly": {
        "name": "Reclined Butterfly (Supta Baddha Konasana)",
        "difficulty": "Beginner",
        "benefits": "Restorative hip opener. Deep relaxation.",
        "instructions": "Lie on back. Bring soles of feet together, knees out. Arms at sides or on belly.",
        "image": "reclined_butterfly.png",
        "goals": ["relaxation", "flexibility"],
        "feelings": ["tired", "stressed"],
    },
    "seated_forward_bend": {
        "name": "Seated Forward Bend (Paschimottanasana)",
        "difficulty": "Beginner",
        "benefits": "Stretches entire back and hamstrings. Calming.",
        "instructions": "Sit with legs extended. Inhale tall, exhale fold forward. Hold feet or shins.",
        "image": "seated_forward_bend.png",
        "goals": ["flexibility", "relaxation", "back_pain"],
        "feelings": ["stressed", "tired", "sore"],
    },
    "side_plank": {
        "name": "Side Plank (Vasisthasana)",
        "difficulty": "Intermediate",
        "benefits": "Core and arm strength. Balance.",
        "instructions": "From plank, shift weight to one hand. Stack feet or knee down. Other arm up or on hip.",
        "image": "side_plank.png",
        "goals": ["strength", "balance"],
        "feelings": ["energetic"],
    },
    "seated_twist": {
        "name": "Seated Spinal Twist (Ardha Matsyendrasana)",
        "difficulty": "Intermediate",
        "benefits": "Twists spine, aids digestion. Can be adapted for chair.",
        "instructions": "Sit with one leg extended. Cross other foot over. Twist toward bent knee. Use arm for leverage.",
        "image": "seated_twist.png",
        "goals": ["flexibility", "back_pain"],
        "feelings": ["sore", "stressed"],
    },
}

class YogaService:
    def __init__(self, default_model="llama3.2"):
        self.model_name = default_model
        self.db = YOGA_POSES_DB
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
                    # Try attribute access first, then dict access (just in case), try 'model' then 'name'
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

            
            # Strip ':latest' for easier matching
            available_base_names = [m.split(':')[0] for m in available_models]

            logger.info(f"Available Ollama models: {available_models}")

            if self.model_name not in available_models and f"{self.model_name}:latest" not in available_models:
                # Try to find a suitable fallback
                preferred = ['llama3.2', 'llama3', 'mistral', 'gemma', 'tinyllama']
                found = False
                
                # Check preferred list
                for p in preferred:
                    for av in available_models:
                        if p in av:
                            self.model_name = av
                            logger.info(f"Default model not found. Switched to available model: {self.model_name}")
                            found = True
                            break
                    if found: break
                
                # If still not found, just take the first one
                if not found and available_models:
                    self.model_name = available_models[0]
                    logger.warning(f"No preferred model found. Using first available: {self.model_name}")

        except Exception as e:
            logger.warning(f"Failed to list Ollama models: {e}")

    def check_ollama_status(self) -> bool:
        """Checks if Ollama is running and accessible."""
        if not OLLAMA_AVAILABLE:
            return False
        try:
            ollama.list()
            return True
        except Exception as e:
            logger.warning(f"Ollama connection failed: {e}")
            return False

    def get_all_poses(self):
        return self.db

    def generate_plan(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a yoga plan using local LLM based on user profile.
        
        Args:
            user_profile: Dict containing 'feeling', 'goals', 'duration', 'level', 'mobility'
        """
        mood = user_profile.get('feeling', 'neutral')
        goal = user_profile.get('goal', 'general fitness')
        duration = user_profile.get('duration', 20)
        level = user_profile.get('level', 'Beginner')
        mobility = user_profile.get('mobility', 'standard')

        logger.info(f"Generating yoga plan for: {mood}, {goal}, {duration} mins, {level}, mobility: {mobility}")

        if not self.check_ollama_status():
            logger.info("Ollama not available, returning fallback plan.")
            return self._get_fallback_plan(mood, duration, goal=goal, mobility=mobility)

        # Prompt engineering: constraints and need-based guidance
        constraint_text = ""
        if mobility == 'chair':
            constraint_text = "CRITICAL CONSTRAINT: All poses MUST be performed while seated on a chair. Prefer: seated_forward_bend, seated_twist, butterfly_pose, cat_cow (seated version), corpse_pose. No standing or floor poses."
        elif mobility == 'bed':
            constraint_text = "CRITICAL CONSTRAINT: All poses must be gentle and lying down or seated on a bed. Prefer: corpse_pose, legs_up_wall, happy_baby, supine_twist, reclined_butterfly, bridge_pose."
        elif mobility == 'limited_mobility':
            constraint_text = "CRITICAL CONSTRAINT: Avoid deep lunges or heavy balance poses. Prefer: cat_cow, child_pose, seated_forward_bend, supine_twist, butterfly_pose, legs_up_wall, reclined_butterfly."

        # Build goal-based and mood-based hints so different inputs get different routines
        goal_hints = {
            "flexibility": "Focus on: pigeon_pose, triangle_pose, butterfly_pose, standing_forward_bend, low_lunge, seated_forward_bend, happy_baby.",
            "strength": "Focus on: plank_pose, boat_pose, side_plank, chair_pose, warrior_i, warrior_ii, bridge_pose.",
            "balance": "Focus on: tree_pose, eagle_pose, warrior_i, warrior_ii, chair_pose, boat_pose, side_plank.",
            "relaxation": "Focus on: child_pose, corpse_pose, legs_up_wall, reclined_butterfly, supine_twist, happy_baby, bridge_pose, seated_forward_bend.",
            "back_pain": "Focus on: cat_cow, child_pose, supine_twist, pigeon_pose, happy_baby, bridge_pose, seated_forward_bend, legs_up_wall.",
        }
        mood_hints = {
            "energetic": "Include dynamic poses: warrior_i, warrior_ii, chair_pose, plank_pose, boat_pose, triangle_pose, sun salutation-style flow.",
            "stressed": "Include calming poses: child_pose, legs_up_wall, corpse_pose, reclined_butterfly, seated_forward_bend, supine_twist.",
            "tired": "Keep it gentle and restorative: legs_up_wall, corpse_pose, reclined_butterfly, child_pose, supine_twist, bridge_pose.",
            "sore": "Focus on gentle stretches and releases: cat_cow, child_pose, happy_baby, supine_twist, pigeon_pose, legs_up_wall, seated_forward_bend.",
        }
        goal_guidance = goal_hints.get(goal, "Choose a mix of poses that suit the goal.")
        mood_guidance = mood_hints.get(str(mood).lower(), "Choose poses that match the user's energy.")

        prompt = f"""
        You are an expert Yoga Instructor. Create a UNIQUE {duration}-minute yoga routine for a {level} student who is feeling "{mood}" and wants to achieve "{goal}".
        {constraint_text}

        NEED-BASED SELECTION (follow this so each user gets a relevant routine):
        - Goal "{goal}": {goal_guidance}
        - Feeling "{mood}": {mood_guidance}

        VARIETY RULE: Different inputs must get different routines. Do NOT always pick the same 5–6 poses. Vary the sequence, order, and which poses you include. For example: if they ask for "relaxation" one time, use child_pose, legs_up_wall, corpse_pose; another time use supine_twist, reclined_butterfly, bridge_pose. Match the routine to THIS user's specific goal and feeling.

        Your response must be a valid JSON object with this structure:
        {{
            "title": "Creative routine name matching the focus",
            "description": "1–2 sentences on how this routine addresses their goal and feeling.",
            "poses": [
                {{
                    "id": "exact_pose_id_from_list",
                    "name": "Display Name of Pose",
                    "duration_seconds": 45 or 60 or 90,
                    "instruction": "Short instruction"
                }}
            ]
        }}

        CRITICAL - Correct image for each pose: Each pose must have "id" set to EXACTLY one of these (copy exactly).
        The app displays the image for that id - wrong id = wrong image. Use ONLY these ids:
        {', '.join(self.db.keys())}
        Example: for Mountain Pose use "mountain_pose", for Child's Pose use "child_pose", for Legs Up the Wall use "legs_up_wall".

        Return ONLY valid JSON, no markdown.
        """

        try:
            response = ollama.chat(model=self.model_name, messages=[
                {'role': 'system', 'content': 'You are a helpful yoga assistant that outputs only JSON.'},
                {'role': 'user', 'content': prompt},
            ])
            
            content = response['message']['content']
            
            # Basic cleanup to ensure JSON parsing if model adds markdown blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            plan = json.loads(content)
            db_keys = set(self.db.keys())

            # Enrich every pose with the CORRECT image for that specific yoga (id + name fallback)
            for pose in plan.get('poses', []):
                raw_id = pose.get('id') or ""
                pose_id = _normalize_pose_id(raw_id, db_keys)
                if not pose_id:
                    # Fallback: match by display name so we still show the right image
                    pose_id = _match_pose_by_name(pose.get('name') or "", self.db)
                if pose_id and pose_id in self.db:
                    pose['image'] = self.db[pose_id]['image']
                    pose['instruction'] = pose.get('instruction') or self.db[pose_id]['instructions']
                else:
                    # Only when we truly can't identify the pose
                    pose['image'] = 'mountain_pose.png'
                    logger.warning(f"Could not match pose id='{raw_id}' name='{pose.get('name')}' to DB; using default image.")
            
            return {"success": True, "plan": plan}

        except Exception as e:
            logger.error(f"Error generating plan with Ollama: {e}")
            return self._get_fallback_plan(mood, duration, goal=goal, mobility=mobility, error=str(e))

    def _get_fallback_plan(self, mood, duration, goal=None, mobility=None, error=None) -> Dict[str, Any]:
        """Returns a need-based static plan if AI is unavailable. Varies by goal and mood."""
        mood = (mood or "").lower()
        goal = (goal or "flexibility").lower()

        if goal == "relaxation" or mood in ("stressed", "tired"):
            plan = {
                "title": "Rest & Restore (Offline)",
                "description": "Gentle, calming sequence for stress and fatigue.",
                "poses": [
                    {"id": "child_pose", "name": "Child's Pose", "duration_seconds": 90},
                    {"id": "cat_cow", "name": "Cat-Cow", "duration_seconds": 60},
                    {"id": "seated_forward_bend", "name": "Seated Forward Bend", "duration_seconds": 60},
                    {"id": "supine_twist", "name": "Supine Twist", "duration_seconds": 60},
                    {"id": "legs_up_wall", "name": "Legs Up the Wall", "duration_seconds": 120},
                    {"id": "corpse_pose", "name": "Corpse Pose", "duration_seconds": 120},
                ]
            }
        elif goal == "back_pain" or mood == "sore":
            plan = {
                "title": "Lower Back Relief (Offline)",
                "description": "Poses to release tension in the back and hips.",
                "poses": [
                    {"id": "cat_cow", "name": "Cat-Cow", "duration_seconds": 60},
                    {"id": "child_pose", "name": "Child's Pose", "duration_seconds": 60},
                    {"id": "happy_baby", "name": "Happy Baby", "duration_seconds": 60},
                    {"id": "supine_twist", "name": "Supine Twist", "duration_seconds": 60},
                    {"id": "bridge_pose", "name": "Bridge Pose", "duration_seconds": 45},
                    {"id": "legs_up_wall", "name": "Legs Up the Wall", "duration_seconds": 90},
                ]
            }
        elif goal == "strength" or mood == "energetic":
            plan = {
                "title": "Strength & Flow (Offline)",
                "description": "Building strength and stability.",
                "poses": [
                    {"id": "mountain_pose", "name": "Mountain Pose", "duration_seconds": 45},
                    {"id": "chair_pose", "name": "Chair Pose", "duration_seconds": 45},
                    {"id": "warrior_i", "name": "Warrior I", "duration_seconds": 45},
                    {"id": "warrior_ii", "name": "Warrior II", "duration_seconds": 45},
                    {"id": "plank_pose", "name": "Plank Pose", "duration_seconds": 45},
                    {"id": "boat_pose", "name": "Boat Pose", "duration_seconds": 45},
                    {"id": "child_pose", "name": "Child's Pose", "duration_seconds": 60},
                ]
            }
        elif goal == "balance":
            plan = {
                "title": "Balance & Focus (Offline)",
                "description": "Improve balance and concentration.",
                "poses": [
                    {"id": "mountain_pose", "name": "Mountain Pose", "duration_seconds": 45},
                    {"id": "tree_pose", "name": "Tree Pose", "duration_seconds": 60},
                    {"id": "eagle_pose", "name": "Eagle Pose", "duration_seconds": 45},
                    {"id": "warrior_ii", "name": "Warrior II", "duration_seconds": 45},
                    {"id": "side_plank", "name": "Side Plank", "duration_seconds": 30},
                    {"id": "child_pose", "name": "Child's Pose", "duration_seconds": 60},
                ]
            }
        else:
            plan = {
                "title": "Flexibility Flow (Offline)",
                "description": "Stretch and open the body.",
                "poses": [
                    {"id": "mountain_pose", "name": "Mountain Pose", "duration_seconds": 45},
                    {"id": "standing_forward_bend", "name": "Standing Forward Bend", "duration_seconds": 60},
                    {"id": "low_lunge", "name": "Low Lunge", "duration_seconds": 45},
                    {"id": "triangle_pose", "name": "Triangle Pose", "duration_seconds": 45},
                    {"id": "butterfly_pose", "name": "Butterfly Pose", "duration_seconds": 60},
                    {"id": "seated_forward_bend", "name": "Seated Forward Bend", "duration_seconds": 60},
                    {"id": "child_pose", "name": "Child's Pose", "duration_seconds": 60},
                ]
            }

        for pose in plan["poses"]:
            if pose["id"] in self.db:
                pose["image"] = self.db[pose["id"]]["image"]
                pose["instruction"] = self.db[pose["id"]].get("instructions", "")

        result = {"success": True, "plan": plan, "is_fallback": True}
        if error:
            result["error"] = str(error)
        return result
