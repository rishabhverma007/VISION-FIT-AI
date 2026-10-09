"""
VisionFit AI - Pose Detection & Biomechanical Movement Analysis Module
Aligned with B.Tech Synopsis Specifications:
- MediaPipe 33-point body landmark processing
- Vector-based joint angle calculation: theta = arccos((v1 . v2) / (|v1| * |v2|))
- Machine Learning Exercise Classification (Pushups, Squats, Jumping Jacks, Idle)
- Form Validation, Movement Consistency Analysis, and Correct Repetition Recognition
- Voice Guidance & Visual Feedback generation
"""

import numpy as np
import logging
import time
from typing import Dict, List, Tuple, Optional, Any
from sklearn.ensemble import RandomForestClassifier

logger = logging.getLogger(__name__)


def calculate_vector_angle(p1: Any, p2: Any, p3: Any) -> float:
    """
    Biomechanical Joint Angle Analysis using Vector Mathematics:
    theta = arccos((v1 . v2) / (|v1| * |v2|))
    
    Parameters:
        p1: First point {'x': float, 'y': float} or [x, y]
        p2: Vertex joint (e.g. elbow, knee, hip) {'x': float, 'y': float} or [x, y]
        p3: Third point {'x': float, 'y': float} or [x, y]
    Returns:
        Angle in degrees [0.0, 180.0]
    """
    try:
        x1 = p1['x'] if isinstance(p1, dict) else p1[0]
        y1 = p1['y'] if isinstance(p1, dict) else p1[1]
        x2 = p2['x'] if isinstance(p2, dict) else p2[0]
        y2 = p2['y'] if isinstance(p2, dict) else p2[1]
        x3 = p3['x'] if isinstance(p3, dict) else p3[0]
        y3 = p3['y'] if isinstance(p3, dict) else p3[1]

        v1 = np.array([x1 - x2, y1 - y2], dtype=np.float64)
        v2 = np.array([x3 - x2, y3 - y2], dtype=np.float64)

        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 < 1e-6 or norm2 < 1e-6:
            return 180.0

        dot_product = np.dot(v1, v2)
        cosine = np.clip(dot_product / (norm1 * norm2), -1.0, 1.0)
        angle_rad = np.arccos(cosine)
        return float(np.degrees(angle_rad))
    except Exception as e:
        logger.error(f"Error calculating vector angle: {e}")
        return 180.0


class MLExerciseClassifier:
    """
    Machine Learning Exercise Recognition Model.
    Learns movement patterns from 33 MediaPipe body landmarks.
    Performs multi-class exercise classification:
      - pushup
      - squat
      - jumping_jack
      - idle
    """

    def __init__(self):
        self.classes = ['pushup', 'squat', 'jumping_jack', 'idle']
        self.model = self._train_initial_model()
        self.is_trained = True

    def _extract_feature_vector(self, landmarks: List[Dict]) -> np.ndarray:
        """
        Extracts 12 biomechanical features from 33 MediaPipe landmarks:
        1. Left elbow angle
        2. Right elbow angle
        3. Left knee angle
        4. Right knee angle
        5. Left hip angle
        6. Right hip angle
        7. Torso inclination relative to horizontal (degrees)
        8. Ankle spread ratio (distance between ankles / shoulder width)
        9. Wrist spread ratio (distance between wrists / shoulder width)
        10. Wrist elevation ratio (avg wrist Y vs shoulder Y)
        11. Knee depth ratio (avg hip Y vs avg knee Y)
        12. Body bounding box aspect ratio (width / height)
        """
        # Key landmarks
        nose = landmarks[0]
        l_shoulder, r_shoulder = landmarks[11], landmarks[12]
        l_elbow, r_elbow = landmarks[13], landmarks[14]
        l_wrist, r_wrist = landmarks[15], landmarks[16]
        l_hip, r_hip = landmarks[23], landmarks[24]
        l_knee, r_knee = landmarks[25], landmarks[26]
        l_ankle, r_ankle = landmarks[27], landmarks[28]

        # 1-6 Joint Angles using vector dot product
        l_elbow_ang = calculate_vector_angle(l_shoulder, l_elbow, l_wrist)
        r_elbow_ang = calculate_vector_angle(r_shoulder, r_elbow, r_wrist)
        l_knee_ang = calculate_vector_angle(l_hip, l_knee, l_ankle)
        r_knee_ang = calculate_vector_angle(r_hip, r_knee, r_ankle)
        l_hip_ang = calculate_vector_angle(l_shoulder, l_hip, l_knee)
        r_hip_ang = calculate_vector_angle(r_shoulder, r_hip, r_knee)

        # Midpoints
        shoulder_mid = np.array([(l_shoulder['x'] + r_shoulder['x']) / 2, (l_shoulder['y'] + r_shoulder['y']) / 2])
        hip_mid = np.array([(l_hip['x'] + r_hip['x']) / 2, (l_hip['y'] + r_hip['y']) / 2])

        # 7. Torso inclination (0 = horizontal like pushup, 90 = vertical like squat/standing)
        torso_vec = shoulder_mid - hip_mid
        torso_len = np.linalg.norm(torso_vec)
        if torso_len > 1e-6:
            # Angle relative to horizontal axis [1, 0]
            cos_incl = np.clip(abs(torso_vec[0]) / torso_len, 0.0, 1.0)
            torso_inclination = 90.0 - float(np.degrees(np.arccos(cos_incl)))
        else:
            torso_inclination = 90.0

        # Shoulder width baseline
        shoulder_w = max(1e-4, abs(r_shoulder['x'] - l_shoulder['x']))

        # 8-9 Spreads
        ankle_spread = abs(r_ankle['x'] - l_ankle['x']) / shoulder_w
        wrist_spread = abs(r_wrist['x'] - l_wrist['x']) / shoulder_w

        # 10. Wrist elevation: in MediaPipe, lower Y is higher on screen
        avg_shoulder_y = (l_shoulder['y'] + r_shoulder['y']) / 2
        avg_wrist_y = (l_wrist['y'] + r_wrist['y']) / 2
        wrist_elevation = (avg_shoulder_y - avg_wrist_y) / (shoulder_w * 2.0)  # > 0 means hands above shoulders

        # 11. Knee depth: hip Y - knee Y
        avg_hip_y = (l_hip['y'] + r_hip['y']) / 2
        avg_knee_y = (l_knee['y'] + r_knee['y']) / 2
        knee_depth = (avg_knee_y - avg_hip_y)

        # 12. Bounding box aspect ratio
        xs = [pt['x'] for pt in landmarks if pt.get('visibility', 1.0) > 0.3]
        ys = [pt['y'] for pt in landmarks if pt.get('visibility', 1.0) > 0.3]
        if xs and ys:
            w = max(xs) - min(xs)
            h = max(ys) - min(ys)
            aspect = w / max(1e-4, h)
        else:
            aspect = 0.5

        return np.array([
            l_elbow_ang, r_elbow_ang,
            l_knee_ang, r_knee_ang,
            l_hip_ang, r_hip_ang,
            torso_inclination,
            ankle_spread,
            wrist_spread,
            wrist_elevation,
            knee_depth,
            aspect
        ], dtype=np.float32)

    def _train_initial_model(self) -> RandomForestClassifier:
        """
        Synthesizes a representative biomechanical training set based on
        exercise biomechanics and trains a Random Forest Classifier.
        """
        np.random.seed(42)
        n_per_class = 200
        X = []
        y = []

        # 1. PUSHUP (horizontal torso, arms flexing, legs straight)
        for _ in range(n_per_class):
            elbow = np.random.uniform(60, 175)
            knee = np.random.uniform(160, 180)
            hip = np.random.uniform(150, 180)
            torso_inc = np.random.uniform(5, 35)  # distinctly horizontal
            ankle_sp = np.random.uniform(0.5, 1.2)
            wrist_sp = np.random.uniform(1.2, 2.2)
            wrist_elev = np.random.uniform(-0.5, 0.2)
            knee_depth = np.random.uniform(-0.2, 0.2)
            aspect = np.random.uniform(1.2, 2.5)  # elongated horizontally
            X.append([elbow, elbow, knee, knee, hip, hip, torso_inc, ankle_sp, wrist_sp, wrist_elev, knee_depth, aspect])
            y.append('pushup')

        # 2. SQUAT (vertical torso, deep knee flexion, feet around shoulder width)
        for _ in range(n_per_class):
            elbow = np.random.uniform(120, 175)
            knee = np.random.uniform(70, 140)  # flexing knees
            hip = np.random.uniform(70, 130)
            torso_inc = np.random.uniform(50, 85)  # mostly upright
            ankle_sp = np.random.uniform(0.9, 1.6)
            wrist_sp = np.random.uniform(0.6, 1.5)
            wrist_elev = np.random.uniform(-0.4, 0.2)
            knee_depth = np.random.uniform(0.1, 0.4)
            aspect = np.random.uniform(0.4, 0.9)
            X.append([elbow, elbow, knee, knee, hip, hip, torso_inc, ankle_sp, wrist_sp, wrist_elev, knee_depth, aspect])
            y.append('squat')

        # 3. JUMPING JACK (vertical torso, wide arms/legs, hands overhead)
        for _ in range(n_per_class):
            elbow = np.random.uniform(140, 180)
            knee = np.random.uniform(155, 180)
            hip = np.random.uniform(150, 180)
            torso_inc = np.random.uniform(75, 90)
            ankle_sp = np.random.uniform(1.3, 2.8)  # wide feet
            wrist_sp = np.random.uniform(1.5, 3.5)  # wide or overhead hands
            wrist_elev = np.random.uniform(0.3, 1.2)  # hands raised high
            knee_depth = np.random.uniform(0.3, 0.6)
            aspect = np.random.uniform(0.7, 1.5)
            X.append([elbow, elbow, knee, knee, hip, hip, torso_inc, ankle_sp, wrist_sp, wrist_elev, knee_depth, aspect])
            y.append('jumping_jack')

        # 4. IDLE / STANDING (upright, arms by sides, legs straight, neutral)
        for _ in range(n_per_class):
            elbow = np.random.uniform(150, 180)
            knee = np.random.uniform(165, 180)
            hip = np.random.uniform(165, 180)
            torso_inc = np.random.uniform(80, 90)
            ankle_sp = np.random.uniform(0.5, 1.0)
            wrist_sp = np.random.uniform(0.6, 1.2)
            wrist_elev = np.random.uniform(-0.6, -0.2)
            knee_depth = np.random.uniform(0.4, 0.7)
            aspect = np.random.uniform(0.3, 0.6)
            X.append([elbow, elbow, knee, knee, hip, hip, torso_inc, ankle_sp, wrist_sp, wrist_elev, knee_depth, aspect])
            y.append('idle')

        clf = RandomForestClassifier(n_estimators=35, max_depth=8, random_state=42)
        clf.fit(np.array(X), np.array(y))
        return clf

    def predict(self, landmarks: List[Dict]) -> Dict[str, Any]:
        """
        Classify current exercise pose from landmarks.
        Returns predicted exercise, confidence score, and probability distribution.
        """
        try:
            feats = self._extract_feature_vector(landmarks).reshape(1, -1)
            probs = self.model.predict_proba(feats)[0]
            class_prob_map = {str(cls_name): round(float(prob), 3) for cls_name, prob in zip(self.model.classes_, probs)}
            best_idx = np.argmax(probs)
            pred_class = str(self.model.classes_[best_idx])
            confidence = round(float(probs[best_idx]), 2)

            return {
                "exercise": pred_class,
                "confidence": confidence,
                "probabilities": class_prob_map
            }
        except Exception as e:
            logger.error(f"ML classification error: {e}")
            return {
                "exercise": "squat",
                "confidence": 0.5,
                "probabilities": {}
            }


class PushupCounter:
    """Pushup form analysis, repetition counting, and consistency tracking."""

    def __init__(self):
        self.state = "up"
        self.rep_count = 0
        self.valid_reps = 0
        self.rep_history: List[Dict] = []
        self.rep_start_time = None
        self.min_arm_angle = 180.0

    def analyze(self, landmarks: List[Dict]) -> Dict:
        try:
            l_shoulder, r_shoulder = landmarks[11], landmarks[12]
            l_elbow, r_elbow = landmarks[13], landmarks[14]
            l_wrist, r_wrist = landmarks[15], landmarks[16]
            l_hip, r_hip = landmarks[23], landmarks[24]
            l_ankle, r_ankle = landmarks[27], landmarks[28]

            # Vector-based angles
            l_arm = calculate_vector_angle(l_shoulder, l_elbow, l_wrist)
            r_arm = calculate_vector_angle(r_shoulder, r_elbow, r_wrist)
            avg_arm_angle = (l_arm + r_arm) / 2.0

            # Body alignment: shoulder-hip-ankle line
            shoulder_mid = {'x': (l_shoulder['x'] + r_shoulder['x']) / 2, 'y': (l_shoulder['y'] + r_shoulder['y']) / 2}
            hip_mid = {'x': (l_hip['x'] + r_hip['x']) / 2, 'y': (l_hip['y'] + r_hip['y']) / 2}
            ankle_mid = {'x': (l_ankle['x'] + r_ankle['x']) / 2, 'y': (l_ankle['y'] + r_ankle['y']) / 2}
            spine_angle = calculate_vector_angle(shoulder_mid, hip_mid, ankle_mid)
            body_alignment_score = max(0.0, 100.0 - abs(spine_angle - 180.0) * 3.0)

            # Track range during repetition
            if self.state == "down":
                self.min_arm_angle = min(self.min_arm_angle, avg_arm_angle)

            voice_feedback = None

            # State transition
            if self.state == "up" and avg_arm_angle < 95:
                self.state = "down"
                self.min_arm_angle = avg_arm_angle
                self.rep_start_time = time.time()
                voice_feedback = "Down"

            elif self.state == "down" and avg_arm_angle > 155:
                self.state = "up"
                self.rep_count += 1
                duration = time.time() - (self.rep_start_time or time.time())
                is_valid = self.min_arm_angle <= 90.0 and body_alignment_score >= 65.0

                if is_valid:
                    self.valid_reps += 1
                    voice_feedback = f"Good rep {self.valid_reps}"
                else:
                    voice_feedback = "Go lower next time"

                self.rep_history.append({
                    "min_angle": self.min_arm_angle,
                    "alignment": body_alignment_score,
                    "duration": duration,
                    "is_valid": is_valid
                })

            # Calculate form score (0-100)
            form_score = self._calculate_form_score(avg_arm_angle, body_alignment_score)
            feedback = self._generate_feedback(avg_arm_angle, body_alignment_score)
            consistency = self._calculate_consistency()

            return {
                "reps": self.rep_count,
                "valid_reps": self.valid_reps,
                "form_score": round(form_score, 1),
                "movement_consistency": round(consistency, 1),
                "feedback": feedback,
                "voice_feedback": voice_feedback,
                "state": self.state,
                "joint_angles": {
                    "elbow_angle": round(avg_arm_angle, 1),
                    "spine_angle": round(spine_angle, 1)
                },
                "is_valid_form": body_alignment_score >= 70
            }
        except Exception as e:
            logger.error(f"Pushup analysis failed: {e}")
            return {"error": str(e), "reps": self.rep_count, "valid_reps": self.valid_reps, "form_score": 0, "feedback": ["Form check failed"]}

    def _calculate_form_score(self, arm_angle: float, body_alignment: float) -> float:
        if 65 <= arm_angle <= 90 or 155 <= arm_angle <= 180:
            angle_score = 100.0
        elif 90 < arm_angle < 155:
            angle_score = 75.0
        else:
            angle_score = max(0.0, 100.0 - abs(arm_angle - 85.0) * 2.0)
        return float(min(100.0, max(0.0, (angle_score * 0.65) + (body_alignment * 0.35))))

    def _calculate_consistency(self) -> float:
        if len(self.rep_history) < 2:
            return 95.0
        durations = [r["duration"] for r in self.rep_history[-5:]]
        mean_d = np.mean(durations)
        std_d = np.std(durations)
        if mean_d <= 0:
            return 90.0
        cv = std_d / mean_d
        return float(np.clip((1.0 - cv) * 100.0, 40.0, 100.0))

    def _generate_feedback(self, arm_angle: float, body_alignment: float) -> List[str]:
        feedback = []
        if arm_angle < 60:
            feedback.append("Don't over-dip shoulders")
        elif arm_angle < 90 and self.state == "down":
            feedback.append("Good depth! Push up now")
        elif 100 < arm_angle < 150:
            feedback.append("Complete the full extension")

        if body_alignment < 70:
            feedback.append("Keep your core tight and hips level")
        if not feedback:
            feedback.append("Excellent pushup posture!")
        return feedback


class SquatCounter:
    """Squat form analysis, depth validation, and consistency tracking."""

    def __init__(self):
        self.state = "up"
        self.rep_count = 0
        self.valid_reps = 0
        self.rep_history: List[Dict] = []
        self.rep_start_time = None
        self.min_knee_angle = 180.0

    def analyze(self, landmarks: List[Dict]) -> Dict:
        try:
            l_shoulder, r_shoulder = landmarks[11], landmarks[12]
            l_hip, r_hip = landmarks[23], landmarks[24]
            l_knee, r_knee = landmarks[25], landmarks[26]
            l_ankle, r_ankle = landmarks[27], landmarks[28]

            # Vector-based knee angles
            l_knee_angle = calculate_vector_angle(l_hip, l_knee, l_ankle)
            r_knee_angle = calculate_vector_angle(r_hip, r_knee, r_ankle)
            avg_knee_angle = (l_knee_angle + r_knee_angle) / 2.0

            # Vector-based hip angle (torso to thigh)
            l_hip_angle = calculate_vector_angle(l_shoulder, l_hip, l_knee)
            r_hip_angle = calculate_vector_angle(r_shoulder, r_hip, r_knee)
            avg_hip_angle = (l_hip_angle + r_hip_angle) / 2.0

            if self.state == "down":
                self.min_knee_angle = min(self.min_knee_angle, avg_knee_angle)

            voice_feedback = None

            # State transition
            if self.state == "up" and avg_knee_angle < 115:
                self.state = "down"
                self.min_knee_angle = avg_knee_angle
                self.rep_start_time = time.time()
                voice_feedback = "Squat down"

            elif self.state == "down" and avg_knee_angle > 155:
                self.state = "up"
                self.rep_count += 1
                duration = time.time() - (self.rep_start_time or time.time())
                is_valid = self.min_knee_angle <= 100.0 and avg_hip_angle >= 45.0

                if is_valid:
                    self.valid_reps += 1
                    voice_feedback = f"Great squat {self.valid_reps}"
                else:
                    voice_feedback = "Squat deeper to parallel"

                self.rep_history.append({
                    "min_angle": self.min_knee_angle,
                    "duration": duration,
                    "is_valid": is_valid
                })

            form_score = self._calculate_form_score(avg_knee_angle, avg_hip_angle)
            feedback = self._generate_feedback(avg_knee_angle, avg_hip_angle)
            consistency = self._calculate_consistency()

            return {
                "reps": self.rep_count,
                "valid_reps": self.valid_reps,
                "form_score": round(form_score, 1),
                "movement_consistency": round(consistency, 1),
                "feedback": feedback,
                "voice_feedback": voice_feedback,
                "state": self.state,
                "joint_angles": {
                    "knee_angle": round(avg_knee_angle, 1),
                    "hip_angle": round(avg_hip_angle, 1)
                },
                "is_valid_form": avg_hip_angle >= 50.0 and avg_knee_angle <= 140
            }
        except Exception as e:
            logger.error(f"Squat analysis failed: {e}")
            return {"error": str(e), "reps": self.rep_count, "valid_reps": self.valid_reps, "form_score": 0, "feedback": ["Form check failed"]}

    def _calculate_form_score(self, knee_angle: float, hip_angle: float) -> float:
        if 80 <= knee_angle <= 105 or 155 <= knee_angle <= 180:
            depth_score = 100.0
        elif 105 < knee_angle < 155:
            depth_score = 75.0
        else:
            depth_score = max(0.0, 100.0 - abs(knee_angle - 95.0) * 2.0)

        torso_score = 100.0 if hip_angle >= 60.0 else max(40.0, hip_angle * 1.5)
        return float(min(100.0, max(0.0, (depth_score * 0.7) + (torso_score * 0.3))))

    def _calculate_consistency(self) -> float:
        if len(self.rep_history) < 2:
            return 95.0
        durations = [r["duration"] for r in self.rep_history[-5:]]
        mean_d = np.mean(durations)
        std_d = np.std(durations)
        if mean_d <= 0:
            return 90.0
        cv = std_d / mean_d
        return float(np.clip((1.0 - cv) * 100.0, 40.0, 100.0))

    def _generate_feedback(self, knee_angle: float, hip_angle: float) -> List[str]:
        feedback = []
        if knee_angle < 75:
            feedback.append("Do not over-compress knees")
        elif knee_angle <= 100 and self.state == "down":
            feedback.append("Parallel depth reached! Drive up through heels")
        elif 110 < knee_angle < 150:
            feedback.append("Keep sinking hips down")

        if hip_angle < 50:
            feedback.append("Keep your chest lifted - avoid leaning forward")
        if not feedback:
            feedback.append("Flawless squat form!")
        return feedback


class JumpingJackCounter:
    """Jumping Jack form analysis, coordination, and repetition counting."""

    def __init__(self):
        self.state = "closed"
        self.rep_count = 0
        self.valid_reps = 0
        self.rep_history: List[Dict] = []
        self.rep_start_time = None
        self.max_arm_spread = 0.0

    def analyze(self, landmarks: List[Dict]) -> Dict:
        try:
            nose = landmarks[0]
            l_shoulder, r_shoulder = landmarks[11], landmarks[12]
            l_wrist, r_wrist = landmarks[15], landmarks[16]
            l_ankle, r_ankle = landmarks[27], landmarks[28]

            shoulder_w = max(1e-4, abs(r_shoulder['x'] - l_shoulder['x']))
            arm_spread = abs(r_wrist['x'] - l_wrist['x']) / shoulder_w
            leg_spread = abs(r_ankle['x'] - l_ankle['x']) / shoulder_w

            # Arm elevation
            avg_wrist_y = (l_wrist['y'] + r_wrist['y']) / 2.0
            avg_shoulder_y = (l_shoulder['y'] + r_shoulder['y']) / 2.0
            overhead = avg_wrist_y < avg_shoulder_y  # Hands above shoulders

            is_open = (arm_spread > 1.8 or overhead) and leg_spread > 1.3
            voice_feedback = None

            if self.state == "closed" and is_open:
                self.state = "open"
                self.rep_start_time = time.time()
                self.max_arm_spread = arm_spread

            elif self.state == "open" and not is_open:
                self.state = "closed"
                self.rep_count += 1
                duration = time.time() - (self.rep_start_time or time.time())
                is_valid = self.max_arm_spread >= 1.6
                if is_valid:
                    self.valid_reps += 1
                    voice_feedback = f"{self.valid_reps}"

                self.rep_history.append({"duration": duration, "is_valid": is_valid})

            form_score = self._calculate_form_score(arm_spread, leg_spread)
            feedback = self._generate_feedback(arm_spread, leg_spread)
            consistency = self._calculate_consistency()

            return {
                "reps": self.rep_count,
                "valid_reps": self.valid_reps,
                "form_score": round(form_score, 1),
                "movement_consistency": round(consistency, 1),
                "feedback": feedback,
                "voice_feedback": voice_feedback,
                "state": self.state,
                "joint_angles": {
                    "arm_spread_ratio": round(arm_spread, 2),
                    "leg_spread_ratio": round(leg_spread, 2)
                },
                "is_valid_form": arm_spread > 1.2
            }
        except Exception as e:
            logger.error(f"Jumping jack analysis failed: {e}")
            return {"error": str(e), "reps": self.rep_count, "valid_reps": self.valid_reps, "form_score": 0, "feedback": ["Form check failed"]}

    def _calculate_form_score(self, arm_spread: float, leg_spread: float) -> float:
        coord = max(0.0, 100.0 - abs(arm_spread - leg_spread * 1.2) * 30.0)
        return float(min(100.0, coord))

    def _calculate_consistency(self) -> float:
        if len(self.rep_history) < 2:
            return 95.0
        durations = [r["duration"] for r in self.rep_history[-5:]]
        mean_d = np.mean(durations)
        std_d = np.std(durations)
        if mean_d <= 0:
            return 90.0
        cv = std_d / mean_d
        return float(np.clip((1.0 - cv) * 100.0, 40.0, 100.0))

    def _generate_feedback(self, arm_spread: float, leg_spread: float) -> List[str]:
        feedback = []
        if arm_spread < 1.4:
            feedback.append("Reach arms all the way overhead")
        if leg_spread < 1.2:
            feedback.append("Jump wider with feet")
        if not feedback:
            feedback.append("Good explosive rhythm!")
        return feedback


class PoseAnalyzer:
    """
    Unified Computer Vision & ML Exercise Analysis Coordinator.
    Integrates MediaPipe landmarks, ML classifier, vector biomechanics, and feedback.
    """

    def __init__(self):
        self.classifier = MLExerciseClassifier()
        self.exercise_counters = {
            'pushup': PushupCounter(),
            'squat': SquatCounter(),
            'jumping_jack': JumpingJackCounter()
        }

    def reset(self):
        """Reset all counters for a new workout session."""
        self.exercise_counters = {
            'pushup': PushupCounter(),
            'squat': SquatCounter(),
            'jumping_jack': JumpingJackCounter()
        }

    def analyze_pose(self, landmarks: List[Dict], exercise_type: str = 'auto') -> Dict[str, Any]:
        """
        Main entry point for pose analysis.
        Supports both specified exercise and automatic ML detection.
        """
        try:
            if not landmarks or len(landmarks) < 33:
                return {
                    "error": "Insufficient landmarks detected. Please step back into full frame.",
                    "success": False
                }

            # 1. Run Machine Learning Exercise Recognition
            ml_result = self.classifier.predict(landmarks)
            detected_exercise = ml_result["exercise"]
            confidence = ml_result["confidence"]

            # 2. Determine which exercise to evaluate
            active_exercise = exercise_type if exercise_type and exercise_type != 'auto' else detected_exercise

            # Fallback to squat if idle or unsupported
            if active_exercise not in self.exercise_counters:
                active_exercise = 'squat'

            counter = self.exercise_counters[active_exercise]
            analysis_result = counter.analyze(landmarks)

            return {
                "success": True,
                "exercise_type": active_exercise,
                "reps": analysis_result.get("reps", 0),
                "valid_reps": analysis_result.get("valid_reps", 0),
                "form_score": analysis_result.get("form_score", 0),
                "movement_consistency": analysis_result.get("movement_consistency", 0),
                "feedback": analysis_result.get("feedback", []),
                "voice_feedback": analysis_result.get("voice_feedback"),
                "joint_angles": analysis_result.get("joint_angles", {}),
                "is_valid_form": analysis_result.get("is_valid_form", True),
                "state": analysis_result.get("state", ""),
                "ml_classification": {
                    "predicted_exercise": detected_exercise,
                    "confidence": confidence,
                    "probabilities": ml_result.get("probabilities", {})
                }
            }
        except Exception as e:
            logger.error(f"Error in pose analysis: {e}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "reps": 0,
                "valid_reps": 0,
                "form_score": 0,
                "movement_consistency": 0,
                "feedback": ["Analysis error occurred"],
                "success": False
            }
