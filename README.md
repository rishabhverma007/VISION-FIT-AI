# VisionFit AI 🏋️‍♂️🥗🧘‍♀️

<div align="center">
  <p><strong>Your Personal, AI-Powered Digital Health & Fitness Coach.</strong></p>
  
  ![Python](https://img.shields.io/badge/python-3.11+-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
  ![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
  ![OpenCV](https://img.shields.io/badge/opencv-%23white.svg?style=for-the-badge&logo=opencv&logoColor=white)
  ![MediaPipe](https://img.shields.io/badge/mediapipe-009688?style=for-the-badge&logo=google&logoColor=white)
  ![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
  ![Google Gemini](https://img.shields.io/badge/google%20gemini-8E75B2?style=for-the-badge&logo=google%20gemini&logoColor=white)
  ![Ollama](https://img.shields.io/badge/ollama-000000?style=for-the-badge&logo=ollama&logoColor=white)
</div>

<br/>

**VisionFit AI** is a comprehensive health and fitness platform that bridges state-of-the-art computer vision with advanced AI (Google Gemini & Local LLMs via Ollama) to deliver a hyper-personalized fitness experience. Unlike standard fitness apps, VisionFit AI observes your form, plans your meals, curates your yoga flows, and coaches you locally in multiple languages.

---

## 📸 Project Showcase

| Landing Page | Dashboard | Voice Assistant |
| :---: | :---: | :---: |
| <img src="https://via.placeholder.com/400x250.png?text=Landing+Page" alt="Landing Page" width="100%"> | <img src="https://via.placeholder.com/400x250.png?text=Dashboard" alt="Dashboard" width="100%"> | <img src="https://via.placeholder.com/400x250.png?text=Voice+Assistant" alt="Voice Assistant" width="100%"> |

| Pose Detection | AI Workout Planner | Diet & Yoga |
| :---: | :---: | :---: |
| <img src="https://via.placeholder.com/400x250.png?text=Pose+Detection" alt="Pose Detection" width="100%"> | <img src="https://via.placeholder.com/400x250.png?text=Workout+Planner" alt="Workout Planner" width="100%"> | <img src="https://via.placeholder.com/400x250.png?text=Diet+and+Yoga" alt="Diet and Yoga" width="100%"> |

---

## 🚀 Key Features

### 1. 📹 Real-Time Pose Detection & Form Analysis
- **Powered by:** MediaPipe & OpenCV
- **Functionality:** Tracks 33 body landmarks in real-time via your webcam.
- **Capabilities:**
  - **Pushups:** Scrutinizes depth, arm angle, and back posture.
  - **Squats:** Monitors hip-knee alignment and squat depth.
  - **Jumping Jacks:** Inspects coordination and range of motion.
- **Feedback Loop:** Reps are only counted with correct form. Delivers instant visual and audio cues (e.g., "Keep your back straight").

### 2. 🤖 AI Workout Planner
- **Powered by:** Google Gemini (2.0 Flash)
- **Functionality:** Generates adaptive 4-week workout plans based on your fitness profile, equipment, goals, and physical limitations.

### 3. 🍎 AI Diet Planner (Privacy-First)
- **Powered by:** Local LLMs via **Ollama** (Llama 3.2, Qwen 2.5, Mistral) with cloud fallback.
- **Functionality:** Synthesizes personalized meal plans with caloric and macronutrient breakdowns. Supports dietary restrictions (Paleo, Vegan, Keto, etc.).
- **Privacy:** Data stays on your machine during inference.

### 4. 🧘 AI Yoga Instructor
- **Powered by:** Local LLMs via **Ollama**.
- **Functionality:** Creates custom yoga flows based on your emotional state, goals, and mobility level. Includes chair yoga, bed yoga, and other accessibility-focused routines with SVG pose graphics.

### 5. 🎤 Bilingual Voice Assistant
- **Powered by:** Google Gemini & Local LLMs with `langdetect`.
- **Functionality:** Real-time conversational fitness coach supporting both **Hindi** and **English**. Uses streaming responses for a natural feel.
- **Features:** Voice recording with real-time transcription, text input fallback, chat history, and clear/reset functionality.

### 6. 📊 Dashboard & Google Fit Sync
- **Capabilities:** Interactive Chart.js visualizations for workout streaks, calorie burns, and performance history.
- **Third-Party Sync:** Google Fit API integration for automated activity data ingestion.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| --- | --- |
| **Backend Framework** | Flask 2.3, Python 3.11+, Flask-Login, Flask-Session |
| **Database** | SQLite (Dev), PostgreSQL (Prod) via SQLAlchemy |
| **Frontend** | HTML5, CSS3 (Bootstrap 5), Vanilla JavaScript, Chart.js |
| **Computer Vision** | OpenCV, Google MediaPipe, Pillow, NumPy |
| **Cloud AI** | Google GenAI API (Gemini 2.0 Flash) |
| **Local AI** | Ollama (Llama 3.2, Qwen 2.5 VL, Nomic Embed) |
| **Integrations** | Google Auth OAuthlib, Google Fit REST API |

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.11+
- Webcam (for Pose Detection)
- [Ollama](https://ollama.com/) *(Optional: Required for local Diet, Yoga, and Voice features)*
- Google Cloud Project with Gemini API enabled *(Optional: For AI Workout Planner and Gemini-powered features)*

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/VisionFitAi.git
cd VisionFitAi
```

### 2. Set Up Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory by copying the example template:

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Edit `.env` with your settings:

```ini
# Flask Security
SESSION_SECRET=your_super_secret_key_here

# Database URI (SQLite for local dev)
DATABASE_URL=sqlite:///visionfit.db

# Google Gemini API Key (Required for AI features)
GOOGLE_API_KEY=your_google_gemini_api_key

# Google Fit Configuration (Optional)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:5000/oauth2callback

# Port Configuration
PORT=5000
```

### 5. Set Up Ollama (Optional - Recommended)

For local, privacy-first AI features (Diet, Yoga, Voice):

1. Download and install [Ollama](https://ollama.com/)
2. Pull the recommended models:

```bash
ollama pull llama3.2
ollama pull qwen2.5vl:7b
```

> The system is model-agnostic and will auto-detect available local models.

### 6. Run the Application

```bash
# Standard Flask Dev Server
python app.py

# Or using the orchestrator (auto-starts Ollama)
python start_app.py
```

Open your browser to:

- **Main Platform:** [http://localhost:5000](http://localhost:5000)
- **Voice Assistant:** [http://localhost:5000/voice-assistant](http://localhost:5000/voice-assistant)

---

## 📂 Project Structure

```
VisionFitAi/
├── app.py                  # Core Application Factory (auto-starts Ollama)
├── routes.py               # All route handlers & API endpoints
├── models.py               # SQLAlchemy database models (User, Workout)
├── extensions.py           # Flask extension instances (db, login_manager)
├── pose_detection.py       # OpenCV & MediaPipe pose analysis
├── gemini.py               # Google Gemini AI wrappers
├── diet_service.py         # Ollama-powered diet plan generation
├── yoga_service.py         # Ollama-powered yoga flow generation
├── voice_service.py        # Bilingual voice chatbot (STT/TTS/LLM)
├── google_fit_service.py   # Google Fit OAuth & data sync
├── start_app.py            # Orchestrator (Ollama + Flask launcher)
├── run.py                  # Production entry point (gunicorn-compatible)
├── templates/              # Jinja2 HTML templates
│   ├── base.html           #   Base layout with navigation
│   ├── index.html          #   Landing page
│   ├── login.html          #   User login
│   ├── register.html       #   User registration
│   ├── dashboard.html      #   User dashboard
│   ├── workout_planner.html#   AI workout plan generation
│   ├── exercise_analysis.html#  Real-time pose detection
│   ├── voice_assistant.html#   Bilingual voice chatbot
│   ├── yoga.html           #   AI yoga flow generator
│   └── diet.html           #   AI diet plan generator
├── static/
│   ├── css/style.css       # Global styles
│   ├── js/main.js          # Client-side JavaScript
│   └── yoga_images/        # Yoga pose reference images
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project metadata
├── .env.example            # Environment variable template
└── Procfile                # Deployment configuration
```

---

## 📊 System Architecture

```mermaid
graph TD
    classDef client fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef server fill:#efebe9,stroke:#5d4037,stroke-width:2px;
    classDef localAI fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef cloud fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef db fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;

    User([User / Athlete]) -->|Interacts| Browser[Web Browser]
    Browser -->|Webcam Video| MP[MediaPipe Pose JS]
    Browser -->|Visualizations| ChartJS[Chart.js Dashboard]

    Browser <-->|HTTP| Flask[Flask Backend]
    Flask -->|ORM| DB[(SQLite / PostgreSQL)]

    Flask <-->|Local AI| Ollama[Ollama Server]
    subgraph Local LLMs
        Ollama --> Diet[diet_service.py]
        Ollama --> Yoga[yoga_service.py]
        Ollama --> Voice[voice_service.py]
    end

    Flask <-->|Cloud AI| Gemini[Google Gemini Cloud]
    Flask <-->|OAuth + REST| GoogleFit[Google Fit]

    class Browser,MP,ChartJS client;
    class Flask server;
    class Ollama,Diet,Yoga,Voice localAI;
    class Gemini,GoogleFit cloud;
    class DB db;
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Landing page |
| `/register` | GET/POST | User registration |
| `/login` | GET/POST | User login |
| `/logout` | GET | User logout |
| `/dashboard` | GET | User dashboard |
| `/workout_planner` | GET/POST | AI workout planner |
| `/exercise-analysis` | GET | Real-time pose detection |
| `/yoga` | GET | AI yoga flow generator |
| `/diet` | GET | AI diet plan generator |
| `/voice-assistant` | GET | Bilingual voice chatbot |
| `/authorize/google-fit` | GET | Google Fit OAuth flow |
| `/oauth2callback` | GET | Google Fit OAuth callback |
| `/api/analyze-pose` | POST | Pose analysis API |
| `/api/voice/process` | POST | Voice processing (streaming) |
| `/api/voice/process_text` | POST | Text-based voice chat |
| `/api/generate-yoga-plan` | POST | Generate yoga plan |
| `/api/generate-diet-plan` | POST | Generate diet plan |
| `/api/fitness-chat` | POST | AI fitness Q&A |
| `/api/google-fit-data` | GET | Fetch Google Fit data |
| `/api/dashboard-stats` | GET | Dashboard statistics |
| `/api/health-check` | GET | Health check endpoint |

---

## 🌐 Deployment

### Heroku / Railway

The project includes a `Procfile` for Heroku-compatible deployments:

```
web: gunicorn run:app
```

For Railway, set the `DATABASE_URL` environment variable to your PostgreSQL connection string. The app automatically handles `postgres://` → `postgresql://` URL conversion.

### Environment Variables for Production

```ini
SESSION_SECRET=your_production_secret
DATABASE_URL=postgresql://user:pass@host:5432/dbname
GOOGLE_API_KEY=your_key
PORT=5000
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <p>Built with ❤️ using Flask, MediaPipe, Google Gemini, and Ollama</p>
</div>
