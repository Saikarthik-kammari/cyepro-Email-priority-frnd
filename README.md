\# Cyepro Priority Frnd – Notification Prioritization Engine



AI-powered Gmail assistant that classifies unread emails as \*\*Now / Later / Never\*\*, applies labels, prevents duplicates \& fatigue, and logs decisions.



Built for Cyepro – Notification Prioritization Engine.



\## Architecture

\- gmail\_helper.py → Gmail API (auth, fetch, labels)

\- decision\_maker.py → Rules + Groq LLM classification

\- app.py → FastAPI server + core engine

\- rules.json → Configurable keywords

\- .env → Groq key



Data flow:

Gmail → fetch unread → dedupe check → classify (rules → Groq) → fatigue check → label → summary + audit



\## How to Run

1\. `pip install fastapi uvicorn google-api-python-client google-auth-httplib2 google-auth-oauthlib groq python-dotenv`

2\. `credentials.json` from Google Cloud (Gmail API)

3\. `.env`: GROQ\_API\_KEY=...

4\. `uvicorn app:app --reload`

5\. Open http://127.0.0.1:8000/docs → Try /scan



\## Features Implemented

\- Real Gmail integration

\- Keyword rules + Groq fallback

\- Exact \& near-duplicate prevention

\- Fatigue control (downgrade after 5+ urgent in 10 min)

\- Auto-labeling (Urgent-Now etc.)

\- Audit logs \& stats endpoint



\## Video Demo

\[Insert YouTube link]



Sai – Feb 2026

