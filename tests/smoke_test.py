"""End-to-end smoke test: exercises every major feature through the Flask test client.

Uses a throwaway SQLite database, so it never touches real data. If API keys are
set in .env, the AI checks exercise the real providers (Gemini/Ollama/Sarvam);
otherwise they verify the graceful-degradation fallbacks.

Run:  python tests/smoke_test.py
"""
import os
import sys
import tempfile

_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
_DB_PATH = os.path.join(tempfile.gettempdir(), 'visionfit_smoke_test.db')
if os.path.exists(_DB_PATH):
    os.remove(_DB_PATH)
os.environ['DATABASE_URL'] = 'sqlite:///' + _DB_PATH.replace('\\', '/')
sys.path.insert(0, _ROOT)

from app import app  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=''):
    if cond:
        PASS.append(name)
    else:
        FAIL.append(f'{name}  [{detail[:300]}]')


client = app.test_client()

# --- Auth & profile management ---
r = client.get('/')
check('GET / index', r.status_code == 200, str(r.status_code))

r = client.post('/register', data={
    'username': 'smoketest', 'email': 'smoke@test.com', 'password': 'pass1234',
    'fitness_level': 'beginner', 'age': '25', 'gender': 'male',
    'height': '175', 'weight': '70', 'fitness_goals': 'stay fit',
}, follow_redirects=False)
check('POST /register', r.status_code in (200, 302), str(r.status_code))

r = client.post('/register', data={
    'username': 'smoketest', 'email': 'smoke@test.com', 'password': 'pass1234',
}, follow_redirects=True)
check('duplicate register handled', b'already' in r.data.lower())

client.get('/logout')
r = client.post('/login', data={'username': 'smoketest', 'password': 'pass1234'},
                follow_redirects=False)
check('POST /login', r.status_code == 302, str(r.status_code))

# --- Pages ---
for page in ['/dashboard', '/exercise-analysis', '/workout_planner', '/fitness_chat',
             '/yoga', '/diet', '/voice-assistant']:
    r = client.get(page)
    check(f'GET {page}', r.status_code == 200, str(r.status_code))

# --- Real-time exercise analysis (MediaPipe landmarks -> analyzer) ---
landmarks = [{'x': 0.5, 'y': 0.5, 'z': 0.0, 'visibility': 0.9} for _ in range(33)]
r = client.post('/api/analyze-pose', json={'landmarks': landmarks, 'exercise_type': 'pushup'})
j = r.get_json(silent=True) or {}
check('POST /api/analyze-pose (pushup)', r.status_code == 200 and 'error' not in j,
      f'{r.status_code} {j}')

r = client.post('/api/analyze-pose', json={'landmarks': landmarks, 'exercise_type': 'auto'})
j = r.get_json(silent=True) or {}
check('POST /api/analyze-pose (auto ML)', r.status_code == 200 and 'error' not in j,
      f'{r.status_code} {j}')

r = client.post('/api/analyze-pose', json={'landmarks': [], 'exercise_type': 'pushup'})
check('analyze-pose empty landmarks -> 400', r.status_code == 400, str(r.status_code))

# --- Workout persistence & history ---
r = client.post('/api/save-workout', json={
    'exercise_type': 'pushup', 'reps_completed': 10, 'valid_reps': 9,
    'duration_seconds': 300, 'form_score': 82.5, 'movement_consistency': 88.0,
})
check('POST /api/save-workout', r.status_code == 200 and r.get_json().get('success'),
      str(r.get_json())[:200])

for ep in ['/api/dashboard-stats', '/api/workout-history', '/api/profile']:
    r = client.get(ep)
    check(f'GET {ep}', r.status_code == 200, f'{r.status_code} {str(r.get_json())[:150]}')

r = client.post('/api/update-profile', json={'age': 26, 'height': 176.0, 'weight': 71.0})
check('POST /api/update-profile', r.status_code == 200, str(r.get_json())[:150])

r = client.post('/api/reset-pose-session')
check('POST /api/reset-pose-session', r.status_code == 200)

# --- AI services ---
r = client.post('/api/fitness-chat', json={'question': 'Give me a beginner pushup routine.'})
j = r.get_json(silent=True) or {}
check('POST /api/fitness-chat (Gemini/Ollama)', r.status_code == 200 and j.get('success'),
      f'{r.status_code} {str(j)[:200]}')

r = client.post('/api/generate-diet-plan', json={'goal': 'maintain weight'})
j = r.get_json(silent=True) or {}
check('POST /api/generate-diet-plan (Ollama/local)', r.status_code == 200,
      f'{r.status_code} {str(j)[:200]}')

r = client.post('/api/generate-yoga-plan', json={'feeling': 'tired', 'duration': 15})
j = r.get_json(silent=True) or {}
check('POST /api/generate-yoga-plan (Ollama/local)', r.status_code == 200,
      f'{r.status_code} {str(j)[:200]}')

# --- Workout planner page POST (form -> Gemini plan) ---
r = client.post('/workout_planner', data={
    'fitness_level': 'beginner', 'equipment': 'none', 'goals': 'lose weight',
    'limitations': 'none',
})
check('POST /workout_planner (Gemini plan)', r.status_code == 200, str(r.status_code))

# --- Voice assistant (text path; audio path needs mic) ---
r = client.post('/api/voice/process_text', json={'text': 'Hello! How are you?'})
j = r.get_json(silent=True) or {}
check('POST /api/voice/process_text (Sarvam chat)', r.status_code == 200 and j.get('success'),
      f'{r.status_code} {str(j)[:200]}')
check('voice reply non-empty', bool((j.get('assistant_text') or '').strip()),
      str(j)[:200])
check('voice TTS audio returned', bool(j.get('audio_base64')),
      'audio_base64 missing/empty')

r = client.post('/api/voice/clear')
check('POST /api/voice/clear', r.status_code == 200)

# --- Google Fit (no creds configured -> graceful handling) ---
r = client.get('/authorize/google-fit', follow_redirects=False)
check('GET /authorize/google-fit graceful', r.status_code in (200, 302, 500), str(r.status_code))
r = client.get('/api/google-fit-data')
check('GET /api/google-fit-data graceful', r.status_code == 200, str(r.get_json())[:150])

# --- Meta & data portability ---
for ep in ['/api/health-check', '/api/version', '/api/docs',
           '/api/export-data', '/api/backup-data']:
    r = client.get(ep)
    check(f'GET {ep}', r.status_code == 200, f'{r.status_code}')

r = client.post('/api/pose-detection')  # no image attached
check('pose-detection no image -> 400', r.status_code == 400, str(r.status_code))

# Export -> import round-trip (import appends)
r = client.get('/api/export-data')
export_j = r.get_json(silent=True) or {}
exported = (export_j.get('data') or {}).get('workouts') or []
check('export-data returns workout list', r.status_code == 200 and isinstance(exported, list),
      f'{r.status_code} {str(export_j)[:200]}')

before = len(exported)
r = client.post('/api/import-data', json=export_j)
import_j = r.get_json(silent=True) or {}
check('import-data round-trip', r.status_code == 200 and import_j.get('success'),
      f'{r.status_code} {str(import_j)[:200]}')

r = client.get('/api/workout-history')
hist_j = r.get_json(silent=True) or {}
after = len(hist_j.get('workouts') or hist_j.get('history') or [])
check('import appended workouts', after == before * 2, f'before={before} after={after}')

# Backup -> restore round-trip (restore replaces)
r = client.get('/api/backup-data')
backup_j = r.get_json(silent=True) or {}
backed_up = (backup_j.get('data') or {}).get('workouts') or []
check('backup-data returns workout list', r.status_code == 200 and isinstance(backed_up, list),
      f'{r.status_code} {str(backup_j)[:200]}')

r = client.post('/api/restore-data', json=backup_j)
restore_j = r.get_json(silent=True) or {}
check('restore-data round-trip', r.status_code == 200 and restore_j.get('success'),
      f'{r.status_code} {str(restore_j)[:200]}')

r = client.get('/api/workout-history')
hist_j = r.get_json(silent=True) or {}
final = len(hist_j.get('workouts') or hist_j.get('history') or [])
check('restore replaced workouts', final == len(backed_up), f'expected={len(backed_up)} final={final}')

# --- Report ---
print(f'\n===== SMOKE TEST: {len(PASS)} passed, {len(FAIL)} failed =====')
for f in FAIL:
    print('FAIL:', f)
if not FAIL:
    print('ALL PASS')
sys.exit(1 if FAIL else 0)
