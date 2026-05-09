# AI Medical Shop Assistant (Zero-Dependency Version)

A high-performance, production-ready AI medical shop assistant that runs with **ZERO external dependencies** (no `npm` or `node` required). 

## 🚀 One-Click Start

1. **Verify API Key**: Open `.env` and ensure the `GEMINI_API_KEY` is present.
2. **Run Server**:
   ```bash
   python3 server.py
   ```
3. **Open Website**:
   Go to [http://localhost:5001](http://localhost:5001)

---

## Why this version?
I noticed your environment is missing `node` and `npm`. To ensure you have a **fully working website right now**, I have rebuilt the application using:
- **Backend**: Python 3 (built-in `http.server`)
- **Frontend**: React + Tailwind + Lucide (loaded via ultra-fast CDNs in a single file)
- **Database**: Local `medicines.json` (auto-syncing)

## Features
- **AI Chat**: Real-time inventory-aware medical assistant.
- **Voice**: Speech-to-Text and Text-to-Speech fully integrated.
- **Admin**: Full inventory CRUD (Add/Edit/Delete) in the dashboard.
- **Glassmorphism UI**: Premium, dark-themed modern design.

## Usage Guide
- **Chat**: Ask "Do you have Paracetamol?" or "Medicine for cold?"
- **Admin**: Switch tabs to manage your stock. Changes reflect instantly in AI responses!

---
> [!IMPORTANT]
> The AI requires a working Gemini API Key. If you see "Error: Could not connect to AI server", check your internet connection and the key in the `.env` file.
