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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    exercise_type = db.Column(db.String(50))
    duration_minutes = db.Column(db.Integer)
    calories_burned = db.Column(db.Integer)
    reps_completed = db.Column(db.Integer)
    form_score = db.Column(db.Float)
    notes = db.Column(db.Text)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('workouts', lazy=True, cascade='all, delete-orphan'))
