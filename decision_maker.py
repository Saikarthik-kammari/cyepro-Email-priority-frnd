import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def load_rules():
    with open('rules.json', 'r') as f:
        return json.load(f)

rules = load_rules()   # <--- this line MUST be here, outside any function

def classify_notification(subject, body):
    text = (subject + " " + body).lower()

    # 🔴 1️⃣ NEVER / Promotion filter FIRST (highest priority block)
    for kw in rules['never_keywords']:
        if kw.lower() in text:
            return "Never", f"Keyword '{kw}' matched low-value/ignore rules"

    # 🟡 2️⃣ Later rules
    for kw in rules['later_keywords']:
        if kw.lower() in text:
            return "Later", f"Keyword '{kw}' matched medium-priority rules (can wait)"

    # 🟢 3️⃣ Now rules LAST
    for kw in rules['now_keywords']:
        if kw.lower() in text:
            return "Now", f"Keyword '{kw}' matched high-priority rules (urgent/time-sensitive)"

    # If no clear match → ask Groq
    try:
        prompt = f"""
You are a STRICT assistant for a busy automotive dealership manager. ONLY use 'Now' for truly urgent/time-critical items (OTP, emergencies, deadlines today, urgent meetings today).

Be very conservative — promotional emails, setup reminders, or anything not requiring immediate action = 'Never' or 'Later'.

Subject: {subject}
Body snippet: {body[:500]}

Decision: Now / Later / Never
Reason: [one short sentence]
"""

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.3
        )

        response = completion.choices[0].message.content.strip()
        lines = response.split('\n')

        decision = lines[0].replace("Decision:", "").strip() if lines else "Later"
        reason = lines[1].replace("Reason:", "").strip() if len(lines) > 1 else "AI classified"

        return decision, reason

    except Exception as e:
        print(f"Groq error: {e}")
        return "Later", "Fallback: Groq unavailable, treated as medium priority"