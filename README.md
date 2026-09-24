<div align="center">
  <img src="docs/assets/banner.svg" alt="VisionFit AI — your personal, AI-powered digital health and fitness coach" width="100%">
</div>

<div align="center">

![Python](https://img.shields.io/badge/python-3.11+-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![MediaPipe](https://img.shields.io/badge/mediapipe-009688?style=for-the-badge&logo=google&logoColor=white)
![OpenCV](https://img.shields.io/badge/opencv-%23white.svg?style=for-the-badge&logo=opencv&logoColor=white)
![Google Gemini](https://img.shields.io/badge/google%20gemini-8E75B2?style=for-the-badge&logo=google%20gemini&logoColor=white)
![Ollama](https://img.shields.io/badge/ollama-000000?style=for-the-badge&logo=ollama&logoColor=white)
![Sarvam AI](https://img.shields.io/badge/sarvam%20ai-EA5454?style=for-the-badge&logo=voiceover&logoColor=white)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)

**A Flask monolith that watches your form, plans your training, cooks your macros, guides your yoga and talks to you in Hindi and English.**

</div>

---

**VisionFit AI** is a full-stack health platform that combines browser-side computer vision with cloud and on-device LLMs. It runs as a single Flask app on one port, keeps a per-user workout history in SQLAlchemy, and degrades gracefully: every AI feature has a deterministic fallback, so the app is fully usable even with no API key and no Ollama daemon running.

| | |
| :--- | :--- |
| **Architecture** | Single Flask monolith (`app.py` factory + `routes.py`) with server-side sessions |
| **Vision** | MediaPipe Pose in the browser (33 landmarks) → Flask rep counters + form scoring |
| **Cloud AI** | Google Gemini `models/gemini-2.0-flash` for training plans and fitness Q&A |
| **Local AI** | Ollama for diet and yoga generation (privacy-first, offline capable) |
| **Voice AI** | Sarvam AI — `saaras:v3` STT · `sarvam-30b` chat · `bulbul:v3` TTS (Hindi/English/Hinglish) |
| **Database** | SQLite in development, PostgreSQL in production, via SQLAlchemy 2.0 |

## 📑 Table of Contents

- [Project showcase](#-project-showcase)
- [Feature tour](#-feature-tour)
- [How it works](#-how-it-works)
- [System architecture](#-system-architecture)
- [Project structure](#-project-structure)
- [API reference](#-api-reference)
- [Data model](#-data-model)
- [Getting started](#-getting-started)
- [Deployment](#-deployment)
- [Tech stack](#-tech-stack)
- [Known gaps & roadmap](#-known-gaps--roadmap)
- [Contributing](#-contributing)

---

## 📸 Project Showcase

Every screenshot below was captured from the running application.

<table>
  <tr>
    <td width="50%">
      <img src="docs/screenshots/landing.png" alt="VisionFit AI landing page" width="100%"><br>
      <sub><b>Landing page</b> — neon hero with floating 3D elements.</sub>
    </td>
    <td width="50%">
      <img src="docs/screenshots/dashboard.png" alt="User dashboard" width="100%"><br>
      <sub><b>Dashboard</b> — streaks, calories and Google Fit health sync.</sub>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <img src="docs/screenshots/workout-planner.png" alt="AI workout planner" width="100%"><br>
      <sub><b>AI workout planner</b> — Gemini-generated 4-week programmes.</sub>
    </td>
    <td width="50%">
      <img src="docs/screenshots/exercise-analysis.png" alt="Real-time form analysis" width="100%"><br>
      <sub><b>Form analysis</b> — live pose detection with rep and form scoring.</sub>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <img src="docs/screenshots/yoga-hub.png" alt="AI yoga hub" width="100%"><br>
      <sub><b>Yoga hub</b> — mood-based flows built by a local LLM.</sub>
    </td>
    <td width="50%">
      <img src="docs/screenshots/diet-planner.png" alt="AI diet planner" width="100%"><br>
      <sub><b>Diet planner</b> — calorie and macro targets from private local inference.</sub>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <img src="docs/screenshots/voice-assistant.png" alt="Bilingual voice assistant" width="100%"><br>
      <sub><b>Voice assistant</b> — streaming, bilingual, TTS-optimised replies.</sub>
    </td>
    <td width="50%">
      <img src="docs/screenshots/register.png" alt="Registration" width="100%"><br>
      <sub><b>Onboarding</b> — goals, fitness level and constraints feed every AI prompt.</sub>
    </td>
  </tr>
</table>

---

## ✨ Feature Tour

### 1. 📹 Real-time Form Analysis

- **Stack:** MediaPipe Pose (browser) + OpenCV/NumPy tooling + `pose_detection.py` on the server.
- Tracks **33 body landmarks** per frame and draws a live skeleton overlay over the webcam feed.
- Landmarks are POSTed to `/api/analyze-pose`, where a dedicated counter scores each rep:
  - **Push-ups** — elbow depth, hip travel, body alignment.
  - **Squats** — knee angle, hip–knee tracking, squat depth.
  - **Jumping jacks** — arm/leg spread ratios and coordination.
- Feedback is only emitted when the joint angles are actually measured, so a rep counts only when the form is credible.

### 2. 🤖 AI Workout Planner

- **Stack:** Google Gemini (`models/gemini-2.0-flash`, override with `GEMINI_MODEL`).
- Builds 4-week programmes from fitness level, equipment, goals and physical limitations.
- Falls back to a local Ollama completion (and then a static template) when no Gemini key is configured, so the page never dead-ends.

### 3. 🍎 AI Diet Planner (privacy-first)

- **Stack:** Ollama with automatic local model detection (default `llama3.2`).
- Produces a 1-day meal plan with calorie and macronutrient breakdowns for the goal and preference you pick (standard, vegan, keto, paleo, high-protein…).
- All inference happens on your machine — nothing leaves the device.

### 4. 🧘 AI Yoga Coach

- **Stack:** Ollama + a hand-curated 25-pose knowledge base (`YOGA_POSES_DB`).
- Generates flows from how you feel today, your goal, available time and mobility level (chair, bed and other accessible variants included).
- LLM pose names are normalised against 26 alias groups (`"Tree Pose"` → `tree_pose`), so the right pose artwork is always shown; the page falls back to inline SVG pose guides whenever a PNG is missing.

### 5. 🎤 Bilingual Voice Assistant

- **Stack:** Sarvam AI — `saaras:v3` (speech-to-text), `sarvam-30b` (chat), `bulbul:v3` (text-to-speech).
- Understands and replies in **Hindi, English and Hinglish**, with Devanagari output tuned for TTS.
- `/api/voice/process` streams **NDJSON events** (`user_text → token → assistant_text → audio → done`), so text appears token-by-token and audio follows immediately.
- Text-only mode (`/api/voice/process_text`) covers mic-less environments; history lives in the server-side session and can be cleared from the UI.

### 6. 📊 Dashboard & Google Fit Sync

- Chart.js visualisations for a 30-day window: calories burned, workout cadence and exercise mix, plus streak, total workout and average duration cards.
- Google Fit OAuth 2.0 flow with state verification and a host-mismatch guard (`127.0.0.1` vs `localhost`), returning steps, calories and heart rate for today.

---

## 🧭 How it works

```mermaid
flowchart TD
    A([Visitor]) --> B{Has an account?}
    B -- No --> C[Register<br/>level + goals + constraints]
    B -- Yes --> D[Log in]
    C --> E[Dashboard]
    D --> E
    E --> F[AI Workout Planner]
    E --> G[Form Analysis]
    E --> H[Yoga Coach]
    E --> I[Diet Planner]
    E --> J[Voice Assistant]
    E --> K[Google Fit Sync]

    F --> F1[Gemini 2.0 Flash<br/>4-week programme]
    G --> G1[MediaPipe 33 landmarks]
    G1 --> G2[POST /api/analyze-pose]
    G2 --> G3[Rep counters +<br/>form score + cues]
    H --> H1[Ollama local LLM<br/>26-pose library]
    I --> I1[Ollama local LLM<br/>macros and meals]
    J --> J1[Sarvam STT]
    J1 --> J2[Sarvam 30B chat]
    J2 --> J3[Sarvam TTS audio]
    K --> K1[Google Fit REST<br/>steps, calories, HR]

    F1 --> L[(User and Workout tables)]
    G3 --> L
    H1 --> L
    I1 --> L
    J3 --> L
    L --> E

    classDef store fill:#f3e5f5,stroke:#7b1fa2,stroke-width:1px;
    class L store;
```

## 🏗 System architecture

```mermaid
graph LR
    classDef client fill:#e1f5fe,stroke:#0288d1,stroke-width:1px;
    classDef server fill:#efebe9,stroke:#5d4037,stroke-width:1px;
    classDef local fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px;
    classDef cloud fill:#fff3e0,stroke:#f57c00,stroke-width:1px;
    classDef data fill:#f3e5f5,stroke:#7b1fa2,stroke-width:1px;

    subgraph Browser
        UI[Jinja2 pages + neon CSS]:::client
        MP[MediaPipe Pose<br/>33 landmarks]:::client
        CH[Chart.js dashboards]:::client
    end

    subgraph "Flask app (single port)"
        APP[app.py — app factory<br/>ProxyFix, Flask-Session]:::server
        RT[routes.py — 33 endpoints]:::server
        MOD[models.py — User, Workout]:::server
        AUTH[flask-login]:::server
    end

    subgraph "AI services"
        GEM[gemini.py<br/>Google Gemini 2.0 Flash]:::cloud
        POSE[pose_detection.py<br/>rep + form scoring]:::local
        DIET[diet_service.py]:::local
        YOGA[yoga_service.py]:::local
        VOICE[voice_service.py<br/>Sarvam AI]:::cloud
    end

    OLL[(Ollama daemon)]:::local
    DB[(SQLite / PostgreSQL)]:::data
    FIT[Google Fit API]:::cloud

    UI --> RT
    MP --> RT
    RT --> APP
    APP --> MOD --> DB
    APP --> AUTH
    RT --> GEM
    RT --> POSE
    RT --> DIET --> OLL
    RT --> YOGA --> OLL
    RT --> VOICE
    GEM -. fallback .-> OLL
    RT --> FIT
    DB --> CH
```

A rendered, high-resolution version of this diagram lives at [`docs/assets/architecture.svg`](docs/assets/architecture.svg).

**Voice turn, in detail:**

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser MediaRecorder
    participant F as Flask /api/voice/process
    participant S as Sarvam AI
    participant H as Session history

    B->>F: POST audio (webm/opus)
    F->>S: saaras:v3 speech-to-text
    S-->>F: transcript + language
    F-->>B: {type: "user_text"}
    F->>S: sarvam-30b chat completions (streaming)
    loop tokens
        S-->>F: token
        F-->>B: {type: "token"}
    end
    F->>S: bulbul:v3 text-to-speech
    S-->>F: base64 MP3
    F-->>B: {type: "assistant_text"} then {type: "audio"}
    F->>H: append user + assistant turn
    F-->>B: {type: "done"}
```

---

## 📂 Project Structure

```text
VISION-FIT-AI/
├── app.py                        # Application factory: sessions, SQLAlchemy, Ollama bootstrap
├── run.py                        # WSGI entry point used by gunicorn (run:app)
├── start_app.py                  # Local orchestrator: starts Ollama, then Flask, logs to file
├── routes.py                     # Every page, JSON API, OAuth flow and pose endpoint
├── models.py                     # SQLAlchemy models: User, Workout
├── extensions.py                 # Shared db + login_manager instances (no circular imports)
├── gemini.py                     # Google Gemini client, workout plans, fitness Q&A, Ollama fallback
├── pose_detection.py             # PoseAnalyzer + Pushup/Squat/JumpingJack counters and scoring
├── diet_service.py               # Ollama-backed meal plans + fallback plans
├── yoga_service.py               # Ollama-backed yoga flows, 26-pose DB, pose-name normalisation
├── voice_service.py              # Sarvam AI STT + chat + TTS, bilingual prompt routing
├── google_fit_service.py         # Google Fit OAuth 2.0 and fitness data aggregation
├── voice_chatbot_app.py          # Standalone Streamlit voice chatbot (developer tool)
├── check_models.py               # Lists Gemini models available to your GOOGLE_API_KEY
├── debug_ollama.py               # Prints Ollama reachability and installed models
├── download_yoga_images.py       # Yoga artwork fetcher (v1, kept for reference)
├── download_yoga_images_v2.py    # Yoga artwork fetcher (v2)
├── download_unique_yoga_images.py# De-duplicating artwork fetcher
├── test_auth_url.py              # Google Fit consent-URL smoke test
├── test_oauth.py                 # Google Fit token-exchange smoke test
├── templates/                    # Jinja2 templates (10 pages)
│   ├── base.html                 #   Layout, nav, Chart.js + Bootstrap/Font Awesome CDN imports
│   ├── index.html                #   Landing page (hero, features, social proof, CTA)
│   ├── login.html / register.html#   Auth pages with goal/level onboarding
│   ├── dashboard.html            #   Stats, charts, Google Fit panel, AI companion
│   ├── workout_planner.html      #   Workout form + rendered Gemini programme
│   ├── exercise_analysis.html    #   Webcam studio: MediaPipe Pose, counters, live canvas
│   ├── yoga.html                 #   Mood/goal/mobility inputs + generated flow
│   ├── diet.html                 #   Body metrics + preference inputs + meal plan
│   └── voice_assistant.html      #   Mic capture, streaming transcript, audio playback
├── static/
│   ├── css/style.css             # Deep-neon design system (CSS variables, glass panels)
│   ├── js/main.js                # Global UI behaviour
│   ├── js/pose-detection.js      # Landmark helpers for the analysis page
│   ├── js/exercise_analysis.js   # Camera lifecycle and in-page rep state machine
│   ├── js/dashboard.js           # Chart.js setup, stat cards, AI companion widget
│   ├── yoga_images/              # Pose illustrations (9 images; the yoga page falls back to SVG guides)
│   └── h1.jpg … h4.jpg           # Hero/marketing artwork (currently unused by templates)
├── docs/
│   ├── assets/banner.svg         # README banner
│   ├── assets/architecture.svg   # High-resolution architecture poster
│   └── screenshots/              # Screenshots of every main screen
├── requirements.txt              # Pinned dependency list
├── requirements-voice-chatbot.txt# Extra deps for the standalone Streamlit chatbot
├── pyproject.toml                # Project metadata (requires Python >= 3.11)
├── Procfile                      # web: gunicorn run:app
├── runtime.txt                   # Platform Python version hint
├── .env.example                  # Environment variable template
└── .gitignore                    # Secrets, venvs, logs and session files stay out of git
```

---

## 🔌 API Reference

**Pages** (all rendered with Jinja2; every page except the three public ones requires a login):

| Route | Methods | Auth | Description |
| :--- | :--- | :--- | :--- |
| `/` | GET | — | Landing page |
| `/register` | GET, POST | — | Create an account, then auto-login |
| `/login` | GET, POST | — | Session login, honours `?next=` |
| `/logout` | GET | ✅ | Ends the session |
| `/dashboard` | GET | ✅ | Stats: workouts, calories, average duration, streak |
| `/workout_planner` | GET, POST | ✅ | Renders the planner or a Gemini-generated plan |
| `/exercise-analysis` · `/exercise_analysis` | GET | ✅ | Webcam form-analysis studio |
| `/exercise_tracker` | GET | ✅ | ⚠️ Renders a template that is not in the repo (see [known gaps](#-known-gaps--roadmap)) |
| `/yoga` | GET | ✅ | Yoga hub |
| `/diet` | GET | ✅ | Diet planner |
| `/voice-assistant` | GET | ✅ | Bilingual voice chat |
| `/authorize/google-fit` | GET | ✅ | Starts the Google Fit consent flow |
| `/oauth2callback` | GET | — | Google Fit redirect target (state verified against the session) |

**JSON APIs:**

| Endpoint | Method | Auth | Description |
| :--- | :--- | :--- | :--- |
| `/api/analyze-pose` | POST | ✅ | `{landmarks, exercise_type}` → `{reps, form_score, feedback}` |
| `/api/fitness-chat` | POST | ✅ | `{question}` → Gemini answer with user context |
| `/api/dashboard-stats` | GET | ✅ | 30-day workout dates, calories, totals |
| `/api/update-profile` | POST | ✅ | Updates fitness level and goals |
| `/api/generate-yoga-plan` | POST | ✅ | `{feeling, goal, duration, mobility}` → flow |
| `/api/generate-diet-plan` | POST | ✅ | `{age, weight, goal, preference, allergies}` → meal plan |
| `/api/voice/process` | POST | ✅ | Audio → **NDJSON stream**: `user_text`/`token`/`assistant_text`/`audio`/`done` |
| `/api/voice/process_legacy` | POST | ✅ | Audio → single JSON response with transcript, reply and MP3 |
| `/api/voice/process_text` | POST | ✅ | Text → reply + MP3 (no microphone required) |
| `/api/voice/clear` | POST | ✅ | Clears the session's voice history |
| `/api/google-fit-data` | GET | ✅ | Today's steps, calories and heart rate |
| `/api/health-check` | GET | — | Liveness probe |
| `/api/version` | GET | — | App name and version |
| `/api/docs` | GET | — | Self-describing endpoint index |
| `/api/clear-data` | POST | ✅ | Deletes the current user's workout history |
| `/api/pose-detection` | POST | ✅ | ⚠️ Image-upload variant; expects an unbound `PoseDetector` class |
| `/api/export-data` · `/api/backup-data` | GET | ✅ | ⚠️ References columns that no longer exist on `Workout` |
| `/api/import-data` · `/api/restore-data` | POST | ✅ | ⚠️ Same stale schema as above |

---

## 🗄 Data Model

```mermaid
erDiagram
    USER ||--o{ WORKOUT : logs
    USER {
        int id PK
        string username "unique, 64"
        string email "unique, 120"
        string password_hash "werkzeug hashing"
        string fitness_level "beginner | intermediate | advanced"
        text fitness_goals
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
        float form_score
        text notes
        datetime completed_at
    }
```

Passwords are hashed with `werkzeug.security`; deleting a user cascades to their workouts. Sessions are stored **server-side** (filesystem backend) because Google OAuth tokens are too large for a cookie.

---

## ⚙️ Getting Started

### Prerequisites

| Requirement | Needed for | Notes |
| :--- | :--- | :--- |
| Python **3.11+** | Everything | `pyproject.toml` requires `>=3.11` |
| A webcam | Form analysis | Chrome or Edge recommended for MediaPipe |
| [Ollama](https://ollama.com/) | Diet + yoga | Optional — fallback plans kick in without it |
| Google AI Studio key | Workout planner, fitness chat | Optional — Ollama fallback |
| Sarvam AI key | Voice assistant | Optional — the rest of the app works without it |
| Google Cloud OAuth client | Google Fit sync | Optional |

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/rishabhverma007/VISION-FIT-AI.git
cd VISION-FIT-AI

# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Then fill in `.env`:

| Variable | Required | Default | Purpose |
| :--- | :--- | :--- | :--- |
| `SESSION_SECRET` | ✅ prod | `dev-secret-key-change-in-production` | Signs session cookies — set a long random value |
| `DATABASE_URL` | — | `sqlite:///visionfit.db` | `postgres://` URLs are rewritten to `postgresql://` automatically |
| `GOOGLE_API_KEY` | — | *unset* | Enables Gemini workout plans and fitness Q&A |
| `GEMINI_MODEL` | — | `models/gemini-2.0-flash` | Override the Gemini model |
| `SARVAM_API_KEY` | — | *unset* | Enables the bilingual voice assistant |
| `GOOGLE_CLIENT_ID` | — | *unset* | Google Fit OAuth client |
| `GOOGLE_CLIENT_SECRET` | — | *unset* | Google Fit OAuth secret |
| `GOOGLE_REDIRECT_URI` | — | `http://localhost:5000/oauth2callback` | Must match the URI registered in Google Cloud |
| `PORT` | — | `5000` | HTTP port |

> 🔐 **Never commit `.env`.** It is already covered by `.gitignore`; rotate any key that has ever been pushed.

### 4. Prepare Ollama (optional, recommended for diet + yoga)

```bash
ollama pull llama3.2        # default model for diet and yoga
ollama list                 # both services auto-detect whatever you have installed
```

Gemini features can also fall back to Ollama, so a local model makes the whole app usable offline.

### 5. Run it

```bash
python app.py          # plain Flask server (auto-starts Ollama on Windows)
python start_app.py    # orchestrator: starts Ollama, waits for it, then Flask
gunicorn run:app       # production-style WSGI server
```

Open **http://localhost:5000**, register an account and you are on the dashboard. The voice assistant lives at **http://localhost:5000/voice-assistant** on the same port.

### 6. Troubleshooting

| Symptom | Fix |
| :--- | :--- |
| `Ollama executable ('ollama') was not found` | Install Ollama or ignore it — fallback plans are served |
| "Session expired or invalid state" on Google Fit | Re-run the consent flow in one browser tab; use `localhost` **and** `GOOGLE_REDIRECT_URI` consistently |
| "Google Fit connection failed: access_denied" | Add your Google account as a **Test user** in the OAuth consent screen |
| Camera never starts | Grant camera permission, use `localhost` (not an IP) and HTTPS or `http://localhost` |
| Models missing from `/workout_planner` | Run `python check_models.py` to list the models your key can access |
| Ollama questions | Run `python debug_ollama.py` for daemon status and installed models |

---

## 🚀 Deployment

The repo ships a `Procfile` (`web: gunicorn run:app`) and is Railway/Heroku-friendly.

1. Set the production environment variables:

   ```ini
   SESSION_SECRET=<long-random-value>
   DATABASE_URL=postgresql://user:password@host:5432/dbname
   GOOGLE_API_KEY=<gemini-key>
   SARVAM_API_KEY=<sarvam-key>
   GOOGLE_CLIENT_ID=<id>
   GOOGLE_CLIENT_SECRET=<secret>
   GOOGLE_REDIRECT_URI=https://<your-domain>/oauth2callback
   PORT=5000
   ```

2. Make sure `GOOGLE_REDIRECT_URI` matches the production URL registered in Google Cloud — the OAuth callback compares the incoming host against it.
3. Deploy: `web: gunicorn run:app`. `app.py` calls `ProxyFix` so the app works behind a proxy, and rewrites `postgres://` to `postgresql://` for managed Postgres providers.
4. `runtime.txt` pins Python 3.10 but the project requires 3.11+; point it at `python-3.11.x` (or delete it and let the buildpack decide).

> Voice, Gemini and Google Fit are cloud-dependent features. Ollama is not available on most PaaS platforms, so diet and yoga will serve their fallback plans there unless you host an Ollama endpoint separately.

---

## 🛠 Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Flask, Flask-Login, Flask-Session (filesystem), Gunicorn, ProxyFix |
| **Database** | SQLAlchemy 2.0 — SQLite (dev) / PostgreSQL (prod) |
| **Frontend** | Jinja2, Bootstrap 5, vanilla JS, Chart.js, Font Awesome, custom neon CSS design system |
| **Computer vision** | MediaPipe Pose (browser), OpenCV, NumPy, Pillow |
| **Cloud AI** | Google GenAI SDK (`google-genai`) — Gemini 2.0 Flash |
| **Local AI** | Ollama (Llama 3.2 by default, model-agnostic detection) |
| **Voice AI** | Sarvam AI — `saaras:v3` STT, `sarvam-30b` chat, `bulbul:v3` TTS |
| **Integrations** | Google OAuth 2.0 (`google-auth-oauthlib`), Google Fit REST API |
| **Config & tooling** | `python-dotenv`, Pydantic, `langdetect`, Streamlit (standalone voice chatbot) |

---

## 🗺 Known Gaps & Roadmap

Contributions that close any of these gaps are very welcome.

- [ ] `/exercise_tracker` and `/api/pose-detection` reference a template and a `PoseDetector` class that no longer exist.
- [ ] `/api/export-data`, `/api/backup-data`, `/api/import-data` and `/api/restore-data` still read `Workout.duration`, `.difficulty` and `.exercises`, which were removed from the model.
- [ ] `/api/docs` lists `/api/delete-workout/<id>`, which is not registered anywhere.
- [ ] Workout results from the analysis page are not yet persisted to the `Workout` table — only login and profile data are written today.
- [ ] `routes.py` has accumulated dead code and a duplicated import; it deserves a blueprint-per-feature split.
- [ ] `static/h1.jpg … h4.jpg` are unused marketing assets.
- [ ] The pose alias table maps `plank_pose`, but that pose is missing from `YOGA_POSES_DB`, so plank requests resolve to no artwork.
- [ ] No automated test suite yet — `check_models.py`, `debug_ollama.py` and the two `test_*.py` scripts are manual smoke tests.
- [ ] `runtime.txt` pins Python 3.10 while the project requires 3.11+.

Planned next: persistent workout logging, nutrition history, offline PWA shell, per-exercise rep targets, and streaming Gemini responses on the planner page.

---

## 🤝 Contributing

1. Fork the repository.
2. Create a branch: `git checkout -b feature/amazing-feature`.
3. Keep the environment contract intact — no secrets in code, no new dependency without a line in `requirements.txt`.
4. Commit with a clear message and open a Pull Request describing the change and how you verified it.

## 📄 License

Released under the MIT License. See [`LICENSE`](LICENSE) for details.

---

<div align="center">
  <sub>Built with ❤️ using Flask, MediaPipe, Google Gemini, Ollama and Sarvam AI</sub>
</div>
