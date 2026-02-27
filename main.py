from datetime import datetime, timedelta
from collections import defaultdict

from gmail_helper import get_gmail_service, get_unread_emails, get_label_id, add_label
from decision_maker import classify_notification


# ------------------------------
# Context + Tracking
# ------------------------------
user_history = defaultdict(list)          # stores (decision, timestamp, subject)
recent_subjects = defaultdict(list)       # stores (subject, timestamp) for dedupe


def is_duplicate(user_id, subject):
    now = datetime.now()

    # Remove old entries (>5 min)
    recent_subjects[user_id] = [
        (s, t) for s, t in recent_subjects[user_id]
        if (now - t).seconds < 300
    ]

    for s, t in recent_subjects[user_id]:
        if s.lower() == subject.lower():
            return True, "Exact duplicate"

    # Optional: near-duplicate check (uncomment if you want)
    # for s, t in recent_subjects[user_id]:
    #     if similarity(subject, s) > 0.9:
    #         return True, "Near duplicate"

    recent_subjects[user_id].append((subject, now))
    return False, None


def too_many_now(user_id):
    now = datetime.now()

    user_history[user_id] = [
        (d, t, subj) for d, t, subj in user_history[user_id]
        if (now - t).seconds < 600
    ]

    count = sum(1 for d, t, subj in user_history[user_id] if d == "Now")
    return count >= 5


def track_decision(user_id, decision, subject):
    user_history[user_id].append((decision, datetime.now(), subject))


# ------------------------------
# Main Engine
# ------------------------------
def main():
    service = get_gmail_service()
    user_id = "manager"

    print("Connected to Gmail! Scanning recent unread emails...\n")

    emails = get_unread_emails(service, max_results=10)

    if not emails:
        print("No unread emails found.")
        return

    summary = {
        "Now": [],
        "Later": [],
        "Never": []
    }

    for email in emails:
        subject = email['subject']
        snippet = email['snippet']
        sender = email['from']

        # 1. Deduplication Check
        duplicate, dup_reason = is_duplicate(user_id, subject)
        if duplicate:
            decision = "Never"
            reason = dup_reason
        else:
            # 2. AI + Rule Classification
            decision, reason = classify_notification(subject, snippet)

            # 3. Fatigue Control
            if decision == "Now" and too_many_now(user_id):
                decision = "Later"
                reason += " | Fatigue: too many urgent notifications recently"

        # Track decision
        track_decision(user_id, decision, subject)

        # Labeling
        label = "Urgent-" + decision.capitalize()
        print(f"Attempting to add label: {label}")

        label_id = get_label_id(service, label)
        if label_id:
            add_label(service, email['id'], label_id)
        else:
            print("Label not found:", label)

        # Console Output
        print(f"Email: {subject}")
        print(f"From: {sender}")
        print(f"Decision: {decision}")
        print(f"Reason: {reason}")
        print("-" * 50)

        # Store in summary with sender
        summary[decision].append({
            "subject": subject,
            "from": sender
        })

    # ------------------------------
    # Summary with sender info
    # ------------------------------
    print("\n=== Daily Summary ===")

    print(f"✅ Now (Very Important): {len(summary['Now'])}")
    for item in summary['Now']:
        print(f"  - {item['subject']} (from {item['from']})")

    print(f"\n⏰ Later: {len(summary['Later'])}")
    for item in summary['Later']:
        print(f"  - {item['subject']} (from {item['from']})")

    print(f"\n❌ Never: {len(summary['Never'])}")
    for item in summary['Never']:
        print(f"  - {item['subject']} (from {item['from']})")


if __name__ == "__main__":
    main()