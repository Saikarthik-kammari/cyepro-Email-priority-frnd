# Cyepro Priority Frnd – Notification Prioritization Engine

AI-powered Gmail assistant that classifies emails as **Now / Later / Never**, auto-applies labels (Urgent-Now etc.), prevents duplicates & fatigue, and uses Groq LLM for smart fallback.

Built for Cyepro Solutions Round 1 hiring task.

## Features
- Real Gmail unread email scanning
- Keyword rules + Groq AI fallback
- Automatic labels in Gmail
- Deduplication (exact + near)
- Fatigue control
- Configurable rules (rules.json)
- Safe fallback if Groq fails

## How to Run
1. Install dependencies: `pip install fastapi uvicorn google-api-python-client google-auth-httplib2 google-auth-oauthlib groq python-dotenv`
2. Put `credentials.json` from Google Cloud
3. Add `GROQ_API_KEY` to `.env`
4. Run: `uvicorn app:app --reload`
5. Open http://127.0.0.1:8000/docs → Try /scan

## Demo Video
[To be added]

Sai Karthik – Feb 2026