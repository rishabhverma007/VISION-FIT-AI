from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Import db from extensions to avoid circular imports
from extensions import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    fitness_level = db.Column(db.String(20), default='beginner')
    fitness_goals = db.Column(db.Text)
    
    # Profile & Bio-metric parameters (Module 1: Data Collection)
    age = db.Column(db.Integer, default=25)
    gender = db.Column(db.String(20), default='other')
    height = db.Column(db.Float, default=170.0)  # in cm
    weight = db.Column(db.Float, default=70.0)   # in kg
    physical_limitations = db.Column(db.Text, default='none')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def bmi(self) -> float:
        """Calculate Body Mass Index (BMI)"""
        try:
            if self.height and self.weight and self.height > 0:
                h_m = self.height / 100.0
                return round(float(self.weight) / (h_m * h_m), 1)
        except Exception:
            pass
        return 22.0

    @property
    def bmi_category(self) -> str:
        """Return clinical BMI category"""
        b = self.bmi
        if b < 18.5:
            return "Underweight"
        elif b < 25.0:
            return "Normal weight"
        elif b < 30.0:
            return "Overweight"
        else:
            return "Obese"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    exercise_type = db.Column(db.String(50))  # pushup, squat, jumping_jack, etc.
    duration_minutes = db.Column(db.Integer, default=0)
    calories_burned = db.Column(db.Integer, default=0)
    reps_completed = db.Column(db.Integer, default=0)
    valid_reps = db.Column(db.Integer, default=0)
    form_score = db.Column(db.Float, default=0.0)
    movement_consistency = db.Column(db.Float, default=0.0)
    feedback_summary = db.Column(db.Text)
    notes = db.Column(db.Text)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('workouts', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'exercise_type': self.exercise_type,
            'duration_minutes': self.duration_minutes,
            'calories_burned': self.calories_burned,
            'reps_completed': self.reps_completed,
            'valid_reps': self.valid_reps,
            'form_score': round(self.form_score or 0.0, 1),
            'movement_consistency': round(self.movement_consistency or 0.0, 1),
            'feedback_summary': self.feedback_summary or '',
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M') if self.completed_at else ''
        }
