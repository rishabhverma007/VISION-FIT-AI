# VisionFit AI 🏋️‍♂️🥗🧘‍♀️

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.3-000000?logo=flask&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10-00897B?logo=google&logoColor=white)
![Gemini](https://img.shields.io/badge/Google%20Gemini-2.0%20Flash-4285F4?logo=google&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-000000)
![License](https://img.shields.io/badge/License-MIT-green)

**VisionFit AI** is a comprehensive, AI-powered health and fitness platform that acts as your personal digital coach. It combines **real-time computer vision** for exercise form analysis with **Generative AI** (Google Gemini, local LLMs via Ollama, and Sarvam AI) to deliver personalized workout, diet, and yoga plans — plus a bilingual voice assistant.

> Built as a B.Tech project: MediaPipe 33-point pose tracking, vector-based biomechanics, ML exercise recognition, and multi-provider LLM orchestration.

---

## ✨ Key Features

| Module | Powered By | What It Does |
|---|---|---|
| 🤖 **AI Workout Planner** | Gemini 2.0 Flash → Ollama fallback | Generates 4-week plans from fitness level, goals, equipment & physical limitations |
| 📹 **Real-Time Exercise Analysis** | MediaPipe + OpenCV + scikit-learn | Live webcam form tracking for **Pushups, Squats, Jumping Jacks** with rep counting, form score & voice cues |
| 🍎 **AI Diet Planner** | Ollama (`llama3.2`, auto-detects models) | 1-day meal plans with macros (protein / carbs / fats / calories), respects preferences & allergies |
| 🧘 **AI Yoga Instructor** | Ollama | Custom yoga flows by mood, goal & duration — includes Chair/Bed yoga for limited mobility, with 26 pose illustrations |
| 💬 **AI Fitness Chat** | Gemini 2.0 Flash → Ollama fallback | Context-aware Q&A assistant that knows your profile |
| 🎙️ **Bilingual Voice Assistant** | Sarvam AI (`saaras:v3` STT · `sarvam-m` chat · `bulbul:v3` TTS) | Hands-free Hindi / English / Hinglish conversation, streaming responses |
| 📊 **Dashboard & Google Fit** | Chart.js + Google Fit API | Workout stats, calories, streaks, progress charts, and OAuth2-based Google Fit sync |

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Client["Browser Client"]
        UI["Jinja2 Templates<br/>Bootstrap 5 + Glassmorphic CSS"]
        MP["MediaPipe Pose JS<br/>33-point landmark extraction"]
        JS["Chart.js + Dashboard JS"]
        MIC["Microphone / Web Audio"]
    end

    subgraph Server["Flask Application"]
        RT["routes.py<br/>40+ endpoints"]
        AUTH["Flask-Login<br/>User sessions"]
        SS["Flask-Session<br/>server-side session store"]
        EXT["extensions.py<br/>SQLAlchemy + LoginManager"]
    end

    subgraph Services["Service Layer"]
        POSE["pose_detection.py<br/>RandomForest classifier + rep counters"]
        GEM["gemini.py<br/>Workout & chatbot engine"]
        DIET["diet_service.py<br/>Nutrition planner"]
        YOGA["yoga_service.py<br/>Yoga sequence generator"]
        VOICE["voice_service.py<br/>Bilingual voice engine"]
        GFIT["google_fit_service.py<br/>OAuth2 + telemetry"]
    end

    subgraph Providers["External AI Providers"]
        GAPI["Google Gemini API<br/>gemini-2.0-flash"]
        OLL["Ollama (local)<br/>llama3.2 / qwen2.5 / mistral"]
        SAR["Sarvam AI<br/>STT + Chat + TTS"]
        GFAPI["Google Fit REST API"]
    end

    DB[("Database<br/>SQLite dev / PostgreSQL prod")]

    MP -->|landmarks JSON| RT
    MIC -->|audio| RT
    JS -->|fetch stats| RT
    RT --> AUTH
    RT --> SS
    RT --> EXT
    RT --> POSE
    RT --> GEM
    RT --> DIET
    RT --> YOGA
    RT --> VOICE
    RT --> GFIT
    RT --> DB
    GEM --> GAPI
    GEM -. "fallback" .-> OLL
    DIET --> OLL
    YOGA --> OLL
    VOICE --> SAR
    GFIT --> GFAPI
```

---

## 🔬 Real-Time Exercise Analysis Pipeline

The browser extracts 33 body landmarks with MediaPipe, then the server performs biomechanical analysis — no video ever leaves the machine, only landmark coordinates.

```mermaid
flowchart LR
    CAM["Webcam feed"] --> MP["MediaPipe Pose<br/>33 landmarks"]
    MP --> SKEL["Skeleton overlay<br/>drawn on canvas"]
    MP -->|"POST /api/analyze-pose"| CLF{"Exercise selected?"}

    CLF -->|auto| RFC["MLExerciseClassifier<br/>RandomForest, 12 features"]
    CLF -->|explicit| CNT
    RFC -->|pushup / squat / jumping_jack| CNT["Rep Counter<br/>state machine + rep history"]

    CNT --> ANG["Vector biomechanics<br/>theta = arccos v1·v2 / |v1||v2|"]
    ANG --> VAL{"Rep valid?<br/>depth + alignment thresholds"}
    VAL -->|"yes"| VR["valid_reps++<br/>voice: 'Good rep N'"]
    VAL -->|"no"| IR["voice: 'Go lower next time'"]

    ANG --> FORM["Form score<br/>joint angle 65% + alignment 35%"]
    CNT --> CONS["Movement consistency<br/>CV of last 5 rep durations"]

    VR & IR --> HUD["Live HUD<br/>reps, form score, cues"]
    FORM --> HUD
    CONS --> HUD
    HUD -->|"POST /api/save-workout"| DBW[("Workout session<br/>persisted to DB")]
```

### 🔁 Pushup Rep-Counting State Machine

```mermaid
stateDiagram-v2
    [*] --> UP
    UP --> DOWN : elbow angle < 95 deg
    DOWN --> UP : elbow angle > 155 deg — rep counted

    note right of DOWN
        A rep is VALID only if:
        - min elbow angle <= 90 deg (full depth)
        - body alignment score >= 65
        (spine angle within 180 deg tolerance)
    end note
```

---

## 🧠 AI Plan Generation — Graceful Fallback Chain

Every LLM feature degrades gracefully: cloud model first, local model second, deterministic plan last.

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant W as Web UI
    participant F as Flask routes.py
    participant S as Service Layer
    participant G as Gemini API
    participant O as Ollama

    U->>W: Submit goals, level, equipment
    W->>F: POST form / AJAX request
    F->>S: generate plan
    S->>G: prompt with user context
    alt Gemini configured & reachable
        G-->>S: structured plan
    else Gemini unavailable
        S->>O: fallback prompt (llama3.2 et al.)
        alt Ollama running
            O-->>S: locally generated plan
        else no LLM available
            S-->>S: deterministic fallback plan
        end
    end
    S-->>F: plan text / JSON
    F-->>W: render template
    W-->>U: display plan
```

---

## 🎙️ Bilingual Voice Assistant (Sarvam AI)

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant W as Voice UI
    participant F as Flask /api/voice/process
    participant SV as Sarvam AI

    U->>W: Speaks (Hindi / English / Hinglish)
    W->>F: audio blob
    F->>SV: Speech-to-Text (saaras:v3)
    SV-->>F: transcript + detected language
    F->>SV: Chat completion (sarvam-m)
    SV-->>F: reply text (TTS-optimized, no markdown)
    F-->>W: stream tokens (NDJSON, word by word)
    F->>SV: Text-to-Speech (bulbul:v3)
    SV-->>F: MP3 audio
    F-->>W: reply + audio_base64
    W-->>U: playback + on-screen transcript
```

---

## 🔗 Google Fit Sync (OAuth 2.0)

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant F as Flask
    participant G as Google OAuth / Fit API

    U->>F: GET /authorize/google-fit
    F->>G: OAuth2 consent redirect
    G-->>F: /oauth2callback?code=...
    F->>G: exchange code for tokens
    Note over F: tokens stored in server-side session<br/>(filesystem backend handles large tokens)
    U->>F: GET /api/google-fit-data
    F->>G: Fitness REST query
    G-->>F: activity aggregates
    F-->>U: JSON metrics for dashboard
```

---

## 🗄️ Data Model

```mermaid
erDiagram
    USER ||--o{ WORKOUT : performs

    USER {
        int id PK
        string username UK
        string email UK
        string password_hash
        string fitness_level
        text fitness_goals
        int age
        string gender
        float height_cm
        float weight_kg
        text physical_limitations
        datetime created_at
    }

    WORKOUT {
        int id PK
        int user_id FK
        string name
        string exercise_type
        int duration_minutes
        int calories_burned
        int reps_completed
        int valid_reps
        float form_score
        float movement_consistency
        text feedback_summary
        text notes
        datetime completed_at
    }
```

---

## 📊 Project Analytics

**Form score composition** (real scoring weights from `pose_detection.py`):

```mermaid
pie showData title Pushup Form Score — weighted components
    "Joint angle quality" : 65
    "Body alignment" : 35
```

**Backend composition** (lines of Python per module):

```mermaid
pie showData title Python backend — lines of code by module
    "routes.py" : 1001
    "pose_detection.py" : 668
    "yoga_service.py" : 636
    "voice_service.py" : 294
    "gemini.py" : 249
    "diet_service.py" : 172
    "google_fit_service.py" : 160
    "app / models / infra" : 312
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.11, Flask 2.3, Flask-Login, Flask-Session (filesystem), SQLAlchemy, Werkzeug |
| **Frontend** | Jinja2, Bootstrap 5, Vanilla JS, Chart.js, dark neon glassmorphic theme |
| **Computer Vision** | MediaPipe Pose (client-side), OpenCV, NumPy, scikit-learn (RandomForest) |
| **Cloud AI** | Google Gemini (`gemini-2.0-flash`) via `google-genai` |
| **Local AI** | Ollama — `llama3.2` default, auto-detects `qwen2.5`, `mistral`, `llama3`, `gemma`, `tinyllama` |
| **Voice AI** | Sarvam AI — `saaras:v3` (STT), `sarvam-m` (chat), `bulbul:v3` (TTS) |
| **Integrations** | Google Fit REST API, OAuth 2.0 (`google-auth-oauthlib`) |
| **Database** | SQLite (dev) · PostgreSQL via `psycopg2-binary` (prod) |
| **Deployment** | Gunicorn, Procfile, Railway / Render / Heroku ready |

---

## 📂 Project Structure

```text
VISION-FIT-AI/
├── app.py                  # Application factory, DB + session config
├── run.py                  # WSGI entrypoint (gunicorn run:app)
├── start_app.py            # Local launcher (auto-starts Ollama + Flask)
├── run_visionfit.bat       # One-click Windows launcher
├── routes.py               # 40+ routes: pages + JSON APIs
├── models.py               # User (biometrics + BMI) & Workout models
├── extensions.py           # SQLAlchemy + LoginManager singletons
├── gemini.py               # Gemini engine with Ollama fallback
├── pose_detection.py       # Landmarks, RF classifier, rep counters, feedback
├── diet_service.py         # Ollama nutrition planner
├── yoga_service.py         # Ollama yoga sequence generator
├── voice_service.py        # Sarvam STT + chat + TTS (Hindi/English/Hinglish)
├── google_fit_service.py   # OAuth2 flow + fitness data fetch
├── requirements.txt        # Pinned dependencies
├── runtime.txt             # python-3.11.9
├── Procfile                # web: gunicorn run:app
├── .env.example            # Environment template (placeholders only)
├── static/
│   ├── css/style.css       # Glassmorphic neon theme
│   ├── js/                 # dashboard.js, exercise_analysis.js, pose-detection.js
│   ├── dist/               # Bundled assets
│   ├── yoga_images/        # 26 pose illustrations
│   └── favicon.ico, h1-h4.jpg
├── templates/              # 11 Jinja2 pages (base, dashboard, exercise_analysis,
│                           #  workout_planner, diet, yoga, fitness_chat, voice_assistant …)
└── frontend/               # Optional JS tooling scaffold (package.json only)
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com/) *(optional — required only for local Diet/Yoga generation)*
- A Google AI Studio key for Gemini *(required for Workout Planner & Chat)*
- A Sarvam AI key *(required for the Voice Assistant)*

### 1. Clone & create a virtual environment
```bash
git clone https://github.com/rishabhverma007/VISION-FIT-AI.git
cd VISION-FIT-AI

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
copy .env.example .env    # Windows  (cp on macOS/Linux)
```
Fill in your own keys in `.env` (never commit this file):

```ini
SESSION_SECRET=change-me-to-a-random-string
DATABASE_URL=sqlite:///visionfit.db
GOOGLE_API_KEY=your-gemini-api-key
SARVAM_API_KEY=your-sarvam-api-key
GOOGLE_CLIENT_ID=your_client_id_here          # optional, Google Fit
GOOGLE_CLIENT_SECRET=your_client_secret_here  # optional, Google Fit
GOOGLE_REDIRECT_URI=http://localhost:5000/oauth2callback
PORT=5000
```

### 4. Set up local AI (optional)
```bash
ollama pull llama3.2        # or qwen2.5 / mistral / llama3
```
The services auto-detect whichever preferred model is installed.

### 5. Run

```bash
# Windows one-click (starts Ollama if installed, then Flask):
run_visionfit.bat

# Or directly:
python start_app.py
```

Open **http://localhost:5000** 🎉

---

## 🧭 Usage Guide

1. **Register / Login** — create an account; biometrics (age, height, weight) power BMI and calorie math.
2. **Dashboard** — view streaks, calories, form-score trends; connect Google Fit for extra telemetry.
3. **Workout Planner** — enter goals, equipment, limitations → get a 4-week plan.
4. **Exercise Analysis** — pick Pushup / Squat / Jumping Jack (or *auto* for ML detection), grant camera access, stand back so your full body is visible, and train with live rep counting, form score and voice cues.
5. **Diet / Yoga** — generate instant plans locally via Ollama (yoga ships with 26 pose illustrations).
6. **Fitness Chat** — ask anything; the assistant has your profile context.
7. **Voice Assistant** — talk in Hindi, English or Hinglish and get spoken replies.

---

## 🌐 API Reference

| Group | Endpoint | Method | Purpose |
|---|---|---|---|
| Auth | `/register`, `/login`, `/logout` | GET/POST | Account management |
| Pages | `/dashboard`, `/exercise-analysis`, `/workout_planner`, `/diet`, `/yoga`, `/fitness_chat`, `/voice-assistant` | GET | Rendered pages (login required) |
| Pose | `/api/analyze-pose` | POST | Landmarks → reps, form score, feedback |
| Pose | `/api/pose-detection` · `/api/reset-pose-session` | POST | Alternate detector / reset counters |
| Workouts | `/api/save-workout` · `/api/workout-history` · `/api/dashboard-stats` | GET/POST | Persist & aggregate sessions |
| AI | `/api/fitness-chat` · `/api/generate-diet-plan` · `/api/generate-yoga-plan` | POST | LLM-generated content |
| Voice | `/api/voice/process` (streaming) · `/api/voice/process_legacy` · `/api/voice/process_text` · `/api/voice/clear` | POST | STT → chat → TTS pipeline |
| Google Fit | `/authorize/google-fit` · `/oauth2callback` · `/api/google-fit-data` | GET | OAuth2 + telemetry |
| Data | `/api/export-data` · `/api/import-data` · `/api/backup-data` · `/api/restore-data` · `/api/clear-data` | GET/POST | Backup & portability |
| Meta | `/api/health-check` · `/api/version` · `/api/docs` | GET | Ops endpoints |

---

## ☁️ Deployment

Production-ready for **Railway**, **Render**, or **Heroku**:

- **Entrypoint:** `Procfile` → `web: gunicorn run:app`
- **Runtime:** `runtime.txt` → `python-3.11.9`
- **Port:** binds to `0.0.0.0:$PORT` automatically
- **Proxy:** `ProxyFix` enabled for correct scheme/host behind load balancers

**Steps (Railway/Render):**
1. Connect this GitHub repository.
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn run:app`
4. Set environment variables: `SESSION_SECRET`, `GOOGLE_API_KEY`, `SARVAM_API_KEY`, and optionally `DATABASE_URL` (PostgreSQL URI — the app auto-normalizes Railway's `postgres://` scheme).

---

## 🔐 Security Notes

- **Never commit `.env`** — it is git-ignored; `.env.example` contains placeholders only.
- If API keys were ever shared or committed accidentally, **rotate them** in Google AI Studio / Sarvam dashboard immediately.
- Sessions are server-side (filesystem) with signed cookies — OAuth tokens never live in the browser.
- Passwords are hashed with Werkzeug PBKDF2.

---

## 🤝 Contributing

Contributions are welcome! Fork the repository, create a feature branch, and open a pull request.

## 📄 License

[MIT License](LICENSE)
