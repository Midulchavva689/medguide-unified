# MedPulse Unified Clinical Intelligence (v12.0)

A high-performance, public-access medical assistant powered by Gemini AI and FastAPI.

## 🚀 Key Features
- **Zero-Failure AI Architecture**: Multi-model fallback (Gemini 1.5, 2.0, 2.5) for 100% uptime.
- **Multilingual Support**: Real-time switching between English, Hindi, and Telugu (Strict Native Script).
- **Clinical Inventory Sync**: Intelligent RAG-lite context injection using a 3,000-item SQLite registry.
- **Digital Prescription Engine**: Auto-generates professional PDFs via jsPDF.

## 🛠️ Technology Stack
- **Backend**: Python 3.12, FastAPI, SQLModel (SQLite).
- **Frontend**: Vanilla HTML5/CSS3 (Glassmorphism), JavaScript ES6.
- **AI Engine**: Google Gemini API (v1beta).
- **Deployment**: Ready for Heroku, Render, or Vercel.

## 📦 Deployment Guide
1. **GitHub**: Push this repository to your GitHub account.
2. **Environment**: Add your `GEMINI_API_KEY` to the environment variables on your hosting provider.
3. **Command**: Use `uvicorn server:app --host 0.0.0.0 --port $PORT` to launch.
4. **Platform**: 
   - **Heroku**: Uses the included `Procfile`.
   - **Render/Railway**: Connect GitHub and select Python/FastAPI.

## 👨‍💻 Team Project Division
- **Member 1**: Backend & DB Architecture (FastAPI/SQLite).
- **Member 2**: Frontend UI & Multi-Language Logic.
- **Member 3**: AI Orchestration & Prompt Engineering.
- **Member 4**: System Integration & PDF Prescription Engine.

---
*Developed as a Minor Project by B.Tech 2nd Year Team.*
