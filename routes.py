from flask import render_template, request, redirect, url_for, flash, jsonify, session, Response, stream_with_context
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
import base64
from PIL import Image
import io
import logging
from datetime import datetime, timedelta
import numpy as np

# Handle optional cv2 import
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("OpenCV (cv2) not available. Some pose detection features may be limited.")

# Import db from extensions to avoid circular imports
from extensions import db
from models import User, Workout
import gemini
from pose_detection import PoseAnalyzer
from yoga_service import YogaService

from yoga_service import YogaService
from diet_service import DietService
from google_fit_service import GoogleFitService
import voice_service as voice_svc

# Initialize services
yoga_service = YogaService()
diet_service = DietService()
google_fit_service = GoogleFitService()


# Global app variable that will be set by the main app
app = None

# Initialize pose analyzer
pose_analyzer = PoseAnalyzer()

def set_app(flask_app):
    """Set the Flask app instance for route registration"""
    global app
    app = flask_app

# Route definitions
def register_routes(flask_app):
    """Register all routes with the Flask app"""
    global app
    app = flask_app

    @app.route('/')
    def index():
        return render_template('index.html')


    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            fitness_level = request.form.get('fitness_level', 'beginner')
            fitness_goals = request.form.get('fitness_goals', '')

            # Check if user exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists')
                return render_template('register.html')

            if User.query.filter_by(email=email).first():
                flash('Email already registered')
                return render_template('register.html')

            # Create new user
            user = User(
                username=username, 
                email=email, 
                fitness_level=fitness_level,
                fitness_goals=fitness_goals
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            login_user(user)
            return redirect(url_for('dashboard'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password')

        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Recent food logs removed
        
        # Calculate workout statistics
        workouts = Workout.query.filter_by(user_id=current_user.id).all()
        total_workouts = len(workouts)
        
        # Calculate total calories burned
        total_calories_burned = sum(workout.calories_burned or 0 for workout in workouts)
        
        # Calculate average workout duration
        if total_workouts > 0:
            avg_duration = sum(workout.duration_minutes or 0 for workout in workouts) / total_workouts
            avg_duration = f"{int(avg_duration)} min"
        else:
            avg_duration = "0 min"
        
        # Calculate day streak (simplified version - consecutive days with workouts)
        streak = 0
        if workouts:
            # Sort workouts by completion date
            sorted_workouts = sorted(workouts, key=lambda w: w.completed_at, reverse=True)
            
            # Get unique dates of workouts
            workout_dates = set()
            for workout in sorted_workouts:
                workout_dates.add(workout.completed_at.date())
            
            # Count consecutive days
            streak = 0
            today = datetime.utcnow().date()
            
            for i in range(30):  # Check up to 30 days back
                check_date = today - timedelta(days=i)
                if check_date in workout_dates:
                    streak += 1
                else:
                    # Break streak if a day is missed
                    if i < streak:
                        break
        
        return render_template('dashboard.html',
                              total_workouts=total_workouts,
                              total_calories_burned=total_calories_burned,
                              avg_duration=avg_duration,
                              streak=streak)

    @app.route('/exercise-analysis')
    @app.route('/exercise_analysis')  # Adding alternative route with underscore
    @login_required
    def exercise_analysis():
        """Render the exercise analysis page"""
        return render_template('exercise_analysis.html')

    @app.route('/api/analyze-pose', methods=['POST'])
    @login_required
    def analyze_pose():
        """API endpoint for real-time pose analysis"""
        try:
            data = request.json
            landmarks = data.get('landmarks')
            exercise_type = data.get('exercise_type')

            if not landmarks or not exercise_type:
                return jsonify({'error': 'Missing landmarks or exercise type'}), 400

            # Analyze pose using the PoseAnalyzer
            result = pose_analyzer.analyze_pose(landmarks, exercise_type)
            return jsonify(result)

        except Exception as e:
            logging.error(f"Error in pose analysis: {e}")
            return jsonify({'error': 'Analysis failed'}), 500

    @app.route('/workout_planner', methods=['GET', 'POST'])
    @login_required
    def workout_planner():
        """Render the workout planner page and handle form submissions"""
        if request.method == 'POST':
            try:
                fitness_level = request.form.get('fitness_level')
                equipment = request.form.get('equipment')
                goals = request.form.get('goals')
                limitations = request.form.get('limitations')

                # Get user context
                user_context = f"Fitness level: {fitness_level}, Equipment: {equipment}, Goals: {goals}, Limitations: {limitations}"

                # Get AI response for workout plan
                plan = gemini.get_workout_plan(user_context)

                return render_template('workout_planner.html', plan=plan)

            except Exception as e:
                flash('Error generating workout plan. Please try again.', 'error')
                return render_template('workout_planner.html')

        return render_template('workout_planner.html')

    @app.route('/exercise_tracker')
    @login_required
    def exercise_tracker():
        """Render the exercise tracker page"""
        return render_template('exercise_tracker.html')









    @app.route('/api/fitness-chat', methods=['POST'])
    @login_required
    def fitness_chat():
        try:
            data = request.get_json()
            question = data.get('question', '')

            if not question:
                return jsonify({'success': False, 'error': 'No question provided'})

            # Get user context
            user_context = f"Fitness level: {current_user.fitness_level}, Goals: {current_user.fitness_goals}"

            # Get AI response
            response = gemini.get_fitness_advice(question, user_context)

            return jsonify({'success': True, 'response': response})

        except Exception as e:
            logging.error(f"Error in fitness chat: {e}")
            return jsonify({'success': False, 'error': 'Sorry, I had trouble processing your request.'})

    @app.route('/api/dashboard-stats')
    @login_required
    def dashboard_stats():
        """Get dashboard statistics for charts"""
        try:
            # Get workout history for last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)

            workouts = Workout.query.filter(
                Workout.user_id == current_user.id,
                Workout.completed_at >= thirty_days_ago
            ).all()

            # Prepare data for charts
            workout_dates = []
            calories_burned = []

            for workout in workouts:
                workout_dates.append(workout.completed_at.strftime('%Y-%m-%d'))
                calories_burned.append(workout.calories_burned or 0)

            return jsonify({
                'success': True,
                'data': {
                    'workout_dates': workout_dates,
                    'calories_burned': calories_burned,
                    'total_workouts': len(workouts),
                    'avg_calories': sum(calories_burned) / len(calories_burned) if calories_burned else 0
                }
            })

        except Exception as e:
            logging.error(f"Error getting dashboard stats: {e}")
            return jsonify({'success': False, 'error': str(e)})



            workout = Workout(
                user_id=current_user.id,
                name=data.get('name', 'Custom Workout'),
                exercises=json.dumps(data.get('exercises', [])),
                duration=data.get('duration', 0),
                calories_burned=data.get('calories_burned', 0),
                difficulty=data.get('difficulty', 'medium')
            )

            db.session.add(workout)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Workout recorded successfully!'})

        except Exception as e:
            logging.error(f"Error recording workout: {e}")
            return jsonify({'success': False, 'error': str(e)})

    # All workout-related code has been removed



    # All workout-related code has been removed



    @app.route('/api/update-profile', methods=['POST'])
    @login_required
    def update_profile():
        try:
            data = request.get_json()

            current_user.fitness_level = data.get('fitness_level', current_user.fitness_level)
            current_user.fitness_goals = data.get('fitness_goals', current_user.fitness_goals)

            db.session.commit()

            return jsonify({'success': True, 'message': 'Profile updated successfully!'})

        except Exception as e:
            logging.error(f"Error updating profile: {e}")
            return jsonify({'success': False, 'error': str(e)})





    @app.route('/api/export-data')
    @login_required
    def export_data():
        try:
            # Get user's data
            workouts = Workout.query.filter_by(user_id=current_user.id).all()


            # Prepare export data
            export_data = {
                'user_info': {
                    'username': current_user.username,
                    'email': current_user.email,
                    'fitness_level': current_user.fitness_level,
                    'fitness_goals': current_user.fitness_goals
                },
                'workouts': []
            }

            for workout in workouts:
                export_data['workouts'].append({
                    'name': workout.name,
                    'duration': workout.duration,
                    'calories_burned': workout.calories_burned,
                    'completed_at': workout.completed_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'difficulty': workout.difficulty
                })



            return jsonify({'success': True, 'data': export_data})

        except Exception as e:
            logging.error(f"Error exporting data: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/import-data', methods=['POST'])
    @login_required
    def import_data():
        try:
            data = request.get_json()

            # Import workouts
            for workout_data in data.get('workouts', []):
                workout = Workout(
                    user_id=current_user.id,
                    name=workout_data.get('name', 'Imported Workout'),
                    duration=workout_data.get('duration', 0),
                    calories_burned=workout_data.get('calories_burned', 0),
                    difficulty=workout_data.get('difficulty', 'medium')
                )
                db.session.add(workout)



            db.session.commit()

            return jsonify({'success': True, 'message': 'Data imported successfully!'})

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error importing data: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/backup-data')
    @login_required
    def backup_data():
        try:
            # Get user's data
            workouts = Workout.query.filter_by(user_id=current_user.id).all()


            # Create backup data
            backup_data = {
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': current_user.id,
                'workouts': []
            }

            for workout in workouts:
                backup_data['workouts'].append({
                    'name': workout.name,
                    'duration': workout.duration,
                    'calories_burned': workout.calories_burned,
                    'completed_at': workout.completed_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'difficulty': workout.difficulty
                })



            return jsonify({'success': True, 'data': backup_data})

        except Exception as e:
            logging.error(f"Error creating backup: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/restore-data', methods=['POST'])
    @login_required
    def restore_data():
        try:
            data = request.get_json()

            # Clear existing data
            Workout.query.filter_by(user_id=current_user.id).delete()


            # Restore workouts
            for workout_data in data.get('workouts', []):
                workout = Workout(
                    user_id=current_user.id,
                    name=workout_data.get('name', 'Restored Workout'),
                    duration=workout_data.get('duration', 0),
                    calories_burned=workout_data.get('calories_burned', 0),
                    difficulty=workout_data.get('difficulty', 'medium')
                )
                db.session.add(workout)



            db.session.commit()

            return jsonify({'success': True, 'message': 'Data restored successfully!'})

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error restoring data: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/clear-data', methods=['POST'])
    @login_required
    def clear_data():
        try:
            # Clear all user data
            Workout.query.filter_by(user_id=current_user.id).delete()


            db.session.commit()

            return jsonify({'success': True, 'message': 'All data cleared successfully!'})

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error clearing data: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/health-check')
    def health_check():
        return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')})

    @app.route('/api/version')
    def version():
        return jsonify({'version': '1.0.0', 'name': 'VisionFitAI'})

    @app.route('/api/pose-detection', methods=['POST'])
    @login_required
    def pose_detection_api():
        try:
            # Get image data from request
            if 'image' not in request.files and 'image_data' not in request.form:
                return jsonify({'success': False, 'error': 'No image provided'})

            # Process image data
            if 'image' in request.files:
                image_file = request.files['image']
                image_data = image_file.read()
            else:
                # Handle base64 encoded image
                image_data = base64.b64decode(request.form['image_data'].split(',')[1])

            # Get exercise type
            exercise_type = request.form.get('exercise_type', 'pushup')

            # Convert to OpenCV format
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Use PoseDetector to process the image
            detector = PoseDetector()
            result = detector.process_image(img)

            if result['success']:
                return jsonify({
                    'success': True,
                    'message': 'Pose detection successful',
                    'landmarks': result.get('landmarks', [])
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('message', 'Failed to detect pose')
                })

        except Exception as e:
            logging.error(f"Error in pose detection API: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/docs')
    def api_docs():
        return jsonify({
            'endpoints': [
                '/api/pose-detection',
                '/api/delete-workout/<id>',
                '/api/export-data',
                '/api/import-data',
                '/api/backup-data',
                '/api/restore-data',
                '/api/clear-data',
                '/api/health-check',
                '/api/version',
                '/api/docs'
            ]
        })

    @app.route('/yoga')
    @login_required
    def yoga_hub():
        return render_template('yoga.html')

    @app.route('/api/generate-yoga-plan', methods=['POST'])
    @login_required
    def generate_yoga_plan():
        try:
            data = request.json
            user_profile = {
                'feeling': data.get('feeling'),
                'goal': data.get('goal'),
                'duration': data.get('duration'),
                'mobility': data.get('mobility'),
                'level': current_user.fitness_level
            }
            
            result = yoga_service.generate_plan(user_profile)
            return jsonify(result)
        except Exception as e:
            logging.error(f"Yoga plan generation error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/diet')
    @login_required
    def diet_planner():
        return render_template('diet.html')

    @app.route('/voice-assistant')
    @login_required
    def voice_assistant():
        """Bilingual (Hindi/English) voice chatbot - in-app feature on same localhost."""
        if "voice_chat_history" not in session:
            session["voice_chat_history"] = []
        return render_template('voice_assistant.html')

    def _voice_process_stream_generator():
        """Stream: user_text -> tokens -> assistant_text -> audio -> done. Real-time feel."""
        try:
            audio_bytes = None
            if request.files and request.files.get("audio"):
                audio_bytes = request.files["audio"].read()
            elif request.is_json:
                data = request.get_json() or {}
                b64 = data.get("audio_base64")
                if b64:
                    audio_bytes = base64.b64decode(b64)
            if not audio_bytes:
                yield json.dumps({"type": "error", "error": "No audio provided"}) + "\n"
                return

            history = session.get("voice_chat_history") or []
            user_text, detected_lang = voice_svc.transcribe(audio_bytes)
            if not user_text or not user_text.strip():
                yield json.dumps({"type": "error", "error": "No speech detected"}) + "\n"
                return

            yield json.dumps({"type": "user_text", "text": user_text}) + "\n"

            messages = voice_svc.build_messages_for_ollama(history, user_text, detected_language=detected_lang)
            reply = ""
            for token, full in voice_svc.ollama_chat_stream(messages):
                reply = full
                yield json.dumps({"type": "token", "text": token}) + "\n"

            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": reply})
            session["voice_chat_history"] = history

            yield json.dumps({"type": "assistant_text", "text": reply}) + "\n"

            mp3_bytes = voice_svc.text_to_speech_mp3_bytes(reply)
            if mp3_bytes:
                audio_b64 = base64.b64encode(mp3_bytes).decode("utf-8")
                yield json.dumps({"type": "audio", "base64": audio_b64}) + "\n"
            yield json.dumps({"type": "done"}) + "\n"
        except Exception as e:
            logging.exception("Voice stream error: %s", e)
            yield json.dumps({"type": "error", "error": str(e)}) + "\n"

    @app.route('/api/voice/process', methods=['POST'])
    @login_required
    def api_voice_process():
        """Streaming: transcribe -> stream LLM tokens -> TTS. Real-time response."""
        return Response(
            stream_with_context(_voice_process_stream_generator()),
            mimetype="application/x-ndjson",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.route('/api/voice/process_legacy', methods=['POST'])
    @login_required
    def api_voice_process_legacy():
        """Non-streaming fallback: accept audio, return full JSON when done."""
        try:
            audio_bytes = None
            if request.files and request.files.get("audio"):
                audio_bytes = request.files["audio"].read()
            elif request.is_json:
                data = request.get_json() or {}
                b64 = data.get("audio_base64")
                if b64:
                    audio_bytes = base64.b64decode(b64)
            if not audio_bytes:
                return jsonify({"success": False, "error": "No audio provided"}), 400

            history = session.get("voice_chat_history") or []
            user_text, detected_lang = voice_svc.transcribe(audio_bytes)
            if not user_text or not user_text.strip():
                return jsonify({"success": False, "error": "No speech detected"}), 400

            messages = voice_svc.build_messages_for_ollama(history, user_text, detected_language=detected_lang)
            reply = voice_svc.ollama_chat(messages)
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": reply})
            session["voice_chat_history"] = history

            audio_b64 = None
            mp3_bytes = voice_svc.text_to_speech_mp3_bytes(reply)
            if mp3_bytes:
                audio_b64 = base64.b64encode(mp3_bytes).decode("utf-8")

            return jsonify({
                "success": True,
                "user_text": user_text,
                "assistant_text": reply,
                "audio_base64": audio_b64,
                "history": history,
            })
        except Exception as e:
            logging.exception("Voice process error: %s", e)
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/voice/process_text', methods=['POST'])
    @login_required
    def api_voice_process_text():
        """Accept text (no audio); run chat + TTS and return JSON. Use when mic is unavailable."""
        try:
            user_text = None
            if request.form and request.form.get("text"):
                user_text = request.form.get("text", "").strip()
            elif request.is_json:
                user_text = (request.get_json() or {}).get("text", "").strip()
            if not user_text:
                return jsonify({"success": False, "error": "No text provided"}), 400

            detected_lang = voice_svc.detect_response_language(user_text)
            history = session.get("voice_chat_history") or []
            messages = voice_svc.build_messages_for_ollama(history, user_text, detected_language=detected_lang)
            reply = voice_svc.ollama_chat(messages)
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": reply})
            session["voice_chat_history"] = history

            audio_b64 = None
            mp3_bytes = voice_svc.text_to_speech_mp3_bytes(reply)
            if mp3_bytes:
                audio_b64 = base64.b64encode(mp3_bytes).decode("utf-8")

            return jsonify({
                "success": True,
                "user_text": user_text,
                "assistant_text": reply,
                "audio_base64": audio_b64,
                "history": history,
            })
        except Exception as e:
            logging.exception("Voice process_text error: %s", e)
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/voice/clear', methods=['POST'])
    @login_required
    def api_voice_clear():
        """Clear voice chat history for current user."""
        session["voice_chat_history"] = []
        return jsonify({"success": True})

    @app.route('/api/generate-diet-plan', methods=['POST'])
    @login_required
    def generate_diet_plan():
        try:
            data = request.json
            user_profile = {
                'age': data.get('age'),
                'weight': data.get('weight'),
                'goal': data.get('goal'),
                'preference': data.get('preference'),
                'allergies': data.get('allergies')
            }
            
            result = diet_service.generate_diet_plan(user_profile)
            return jsonify(result)
        except Exception as e:
            logging.error(f"Diet plan generation error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/authorize/google-fit')
    @login_required
    def authorize_google_fit():
        # Auto-correct domain mismatch (e.g. 127.0.0.1 vs localhost)
        # This prevents the "Session expired" error by ensuring cookie domain matches redirect URI
        redirect_uri = google_fit_service.redirect_uri
        if redirect_uri:
            from urllib.parse import urlparse
            parsed_redirect = urlparse(redirect_uri)
            expected_host = parsed_redirect.netloc # e.g. localhost:5000
            
            # If user is on 127.0.0.1 but config expects localhost (or vice versa)
            if request.host != expected_host:
                logging.info(f"Redirecting from {request.host} to {expected_host} for OAuth consistency")
                # Reconstruct URL for the expected host
                new_url = f"{parsed_redirect.scheme}://{expected_host}{url_for('authorize_google_fit')}"
                return redirect(new_url)

        try:
            auth_url, state, _ = google_fit_service.get_auth_url()
            session['oauth_state'] = state
            return redirect(auth_url)
        except Exception as e:
            flash(f"Error initializing Google Fit auth: {e}", "error")
            return redirect(url_for('dashboard'))

    @app.route('/oauth2callback')
    def oauth2callback():
        # Handle errors from Google (e.g., access_denied)
        if 'error' in request.args:
            error_msg = request.args.get('error')
            flash(f"Google Fit connection failed: {error_msg}. (Did you add your email as a Test User in Google Cloud?)", "error")
            return redirect(url_for('dashboard'))

        try:
            if 'oauth_state' not in session:
                flash("Session expired or invalid state. Please try connecting again.", "error")
                return redirect(url_for('dashboard'))

            state = session['oauth_state']
            callback_state = request.args.get('state')

            if callback_state != state:
                flash("Invalid OAuth state. Please try connecting again.", "error")
                return redirect(url_for('dashboard'))

            flow_credentials = google_fit_service.get_credentials_from_code(
                request.url,
                state=state
            )

            # One-time OAuth artifacts are no longer needed after token exchange.
            session.pop('oauth_state', None)
            
            # Store credentials in session (in production, strictly encrypt or store in DB)
            creds_dict = google_fit_service.credentials_to_dict(flow_credentials)
            session['google_fit_credentials'] = creds_dict
            session['google_fit_token'] = True # Marker for UI
            
            flash("Successfully connected to Google Fit!", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            logging.error(f"OAuth callback error: {e}")
            flash(f"Failed to connect to Google Fit: {str(e)}", "error")
            return redirect(url_for('dashboard'))

    @app.route('/api/google-fit-data')
    @login_required
    def google_fit_data():
        if 'google_fit_credentials' not in session:
            return jsonify({'success': False, 'error': 'Not connected'})
            
        try:
            creds_dict = session['google_fit_credentials']
            credentials = google_fit_service.dict_to_credentials(creds_dict)
            
            data = google_fit_service.get_fitness_data(credentials)
            
            if data:
                return jsonify({'success': True, 'data': data})
            else:
                return jsonify({'success': False, 'error': 'Failed to fetch data'})
        except Exception as e:
             # Basic token refresh logic handling needed or re-auth prompt
            return jsonify({'success': False, 'error': str(e)})
