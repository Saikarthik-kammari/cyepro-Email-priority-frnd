from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Optional

from collections import defaultdict
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from gmail_helper import get_gmail_service, get_unread_emails, get_label_id, add_label
from decision_maker import classify_notification

app = FastAPI(title="Cyepro Priority Frnd – Notification Prioritization Engine")

# Global storage
user_history = defaultdict(list)          # list of (decision, timestamp, subject)
recent_subjects = defaultdict(list)       # list of (subject, timestamp)
audit_logs = []                           # list of scan summaries

# ------------------------------
# Deduplication
# ------------------------------
def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def is_duplicate(subject, user_id="manager", exact_window_sec=300, near_threshold=0.9):
    now = datetime.now()

    # Exact duplicate (same subject)
    recent_subjects[user_id] = [(s, t) for s, t in recent_subjects[user_id] if (now - t).seconds < exact_window_sec]
    for s, t in recent_subjects[user_id]:
        if s.lower() == subject.lower():
            return True, "Exact duplicate"

    # Near-duplicate (similar text)
    for s, t in recent_subjects[user_id]:
        if similarity(subject, s) > near_threshold:
            return True, "Near duplicate (>90% similarity)"

    recent_subjects[user_id].append((subject, now))
    return False, None

# ------------------------------
# Fatigue Control
# ------------------------------
def too_many_now(user_id="manager", threshold=5, window_sec=600):
    now = datetime.now()
    user_history[user_id] = [(d, t, subj) for d, t, subj in user_history[user_id] if (now - t).seconds < window_sec]
    count = sum(1 for d, t, subj in user_history[user_id] if d == "Now")
    return count >= threshold

def track_decision(user_id, decision, subject):
    user_history[user_id].append((decision, datetime.now(), subject))

# ------------------------------
# Scan & Classify Core Logic
# ------------------------------
def scan_and_classify():
    service = get_gmail_service()
    print("Connected to Gmail! Scanning recent unread emails...\n")

    emails = get_unread_emails(service, max_results=10)

    if not emails:
        print("No unread emails found.")
        return {"results": [], "summary": {"Now": 0, "Later": 0, "Never": 0}}

    results = []
    summary = {"Now": 0, "Later": 0, "Never": 0}

    for email in emails:
        subject = email['subject']
        snippet = email['snippet']
        sender = email['from']

        # Deduplication
        duplicate, dup_reason = is_duplicate(subject)
        if duplicate:
            decision = "Never"
            reason = dup_reason
        else:
            decision, reason = classify_notification(subject, snippet)

            # Fatigue
            if decision == "Now" and too_many_now():
                decision = "Later"
                reason += " | Fatigue control: too many urgent notifications recently"

        # Track
        track_decision("manager", decision, subject)

        # Labeling
        label = "Urgent-" + decision.capitalize()
        print(f"Attempting to add label: {label}")

        label_id = get_label_id(service, label)
        if label_id:
            add_label(service, email['id'], label_id)
        else:
            print("Label not found:", label)

        # Results
        results.append({
            "subject": subject,
            "from": sender,
            "decision": decision,
            "reason": reason
        })

        summary[decision] += 1

    print("\n=== Daily Summary ===")
    print(f"✅ Now (Very Important): {summary['Now']}")
    print(f"⏰ Later: {summary['Later']}")
    print(f"❌ Never: {summary['Never']}")

    # Audit log
    audit_logs.append({
        "timestamp": datetime.now().isoformat(),
        "processed": len(emails),
        "summary": summary.copy(),
        "results_count": len(results)
    })

    return {"results": results, "summary": summary}

# ------------------------------
# API Endpoints
# ------------------------------
@app.get("/")
def home():
    return {"message": "Cyepro Priority Frnd Engine Running 🚀"}

@app.get("/scan")
def scan():
    return scan_and_classify()

@app.get("/audit")
def get_audit():
    return {"logs": audit_logs}

@app.get("/stats")
def get_stats():
    total_scans = len(audit_logs)
    total_processed = sum(log["processed"] for log in audit_logs)
    total_now = sum(log["summary"].get("Now", 0) for log in audit_logs)
    return {
        "total_scans": total_scans,
        "total_emails_processed": total_processed,
        "total_now": total_now,
        "now_percentage": round((total_now / total_processed * 100), 1) if total_processed > 0 else 0
    }