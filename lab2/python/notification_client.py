"""
Notification client for Lab 2.

Stores all notifications in MongoDB `notifications` collection (always).
Optionally sends real emails via SMTP if SMTP_HOST is configured.
Optionally posts to a webhook URL if NOTIFICATION_WEBHOOK_URL is set.

Environment variables:
  SMTP_HOST          — e.g. smtp.gmail.com
  SMTP_PORT          — default 587
  SMTP_USER          — sender email address
  SMTP_PASSWORD      — sender password / app password
  SMTP_FROM          — From: address (defaults to SMTP_USER)
  NOTIFICATION_WEBHOOK_URL — HTTP endpoint to POST notification JSON to
"""
from __future__ import annotations

import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

_SMTP_HOST = os.getenv("SMTP_HOST", "")
_SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
_SMTP_USER = os.getenv("SMTP_USER", "")
_SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
_SMTP_FROM = os.getenv("SMTP_FROM", _SMTP_USER)
_WEBHOOK_URL = os.getenv("NOTIFICATION_WEBHOOK_URL", "")


def _get_db():
    from mongo_client import get_db
    return get_db()


def _store_notification(db, recipient_user_id: int, subject: str, body: str,
                        notification_type: str, metadata: dict) -> str:
    from mongo_client import get_next_id
    nid = get_next_id("notifications")
    doc = {
        "_id": nid,
        "user_id": recipient_user_id,
        "type": notification_type,
        "subject": subject,
        "body": body,
        "metadata": metadata,
        "read": False,
        "created_at": datetime.now(timezone.utc),
    }
    db.notifications.insert_one(doc)
    return str(nid)


def _send_email(to_email: str, subject: str, body: str) -> bool:
    if not _SMTP_HOST or not _SMTP_USER:
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = _SMTP_FROM
        msg["To"] = to_email
        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(f"<pre>{body}</pre>", "html"))
        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as server:
            server.starttls()
            server.login(_SMTP_USER, _SMTP_PASSWORD)
            server.sendmail(_SMTP_FROM, [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"[notification_client] SMTP error: {e}", flush=True)
        return False


def _send_webhook(payload: dict) -> bool:
    if not _WEBHOOK_URL:
        return False
    try:
        import httpx
        httpx.post(_WEBHOOK_URL, json=payload, timeout=5.0)
        return True
    except Exception as e:
        print(f"[notification_client] Webhook error: {e}", flush=True)
        return False


def send_notification(
    recipient_user_id: int,
    subject: str,
    body: str,
    notification_type: str = "general",
    metadata: Optional[dict] = None,
    to_email: Optional[str] = None,
) -> str:
    """
    Persist notification + optionally send email/webhook.
    Returns the notification ID.
    """
    db = _get_db()
    meta = metadata or {}
    nid = _store_notification(db, recipient_user_id, subject, body, notification_type, meta)

    if to_email:
        _send_email(to_email, subject, body)

    _send_webhook({
        "notification_id": nid,
        "user_id": recipient_user_id,
        "type": notification_type,
        "subject": subject,
        "body": body,
        **meta,
    })
    return nid


def notify_owner_new_review(
    restaurant_id: int,
    restaurant_name: str,
    reviewer_name: str,
    rating: int,
    comment: Optional[str],
    review_id: int,
) -> None:
    """Called by review_worker after a review is created."""
    db = _get_db()
    rest = db.restaurants.find_one({"_id": restaurant_id}, {"owner_id": 1}) or {}
    owner_id = rest.get("owner_id")
    if not owner_id:
        return

    owner = db.users.find_one({"_id": owner_id}, {"email": 1, "name": 1}) or {}
    owner_email = owner.get("email")

    subject = f"New {rating}★ review on {restaurant_name}"
    body = (
        f"Hi {owner.get('name', 'there')},\n\n"
        f"{reviewer_name} just left a {rating}-star review on {restaurant_name}.\n\n"
        f"Comment: {comment or '(no comment)'}\n\n"
        f"Log in to your owner dashboard to respond.\n"
    )
    send_notification(
        recipient_user_id=owner_id,
        subject=subject,
        body=body,
        notification_type="new_review",
        metadata={
            "restaurant_id": restaurant_id,
            "review_id": review_id,
            "rating": rating,
        },
        to_email=owner_email,
    )


def notify_owner_reply_posted(
    review_id: int,
    reviewer_user_id: int,
    restaurant_name: str,
    reply_text: str,
) -> None:
    """Notify the reviewer that the owner replied to their review."""
    db = _get_db()
    reviewer = db.users.find_one({"_id": reviewer_user_id}, {"email": 1, "name": 1}) or {}
    reviewer_email = reviewer.get("email")

    subject = f"The owner of {restaurant_name} replied to your review"
    body = (
        f"Hi {reviewer.get('name', 'there')},\n\n"
        f"The owner of {restaurant_name} responded to your review:\n\n"
        f"\"{reply_text}\"\n\n"
        f"Visit the app to see the full conversation.\n"
    )
    send_notification(
        recipient_user_id=reviewer_user_id,
        subject=subject,
        body=body,
        notification_type="owner_reply",
        metadata={"review_id": review_id},
        to_email=reviewer_email,
    )


def notify_waitlist_position(
    user_id: int,
    restaurant_name: str,
    position: int,
    restaurant_id: int,
) -> None:
    """Notify a user of their waitlist position."""
    db = _get_db()
    user = db.users.find_one({"_id": user_id}, {"email": 1, "name": 1}) or {}

    subject = f"You're #{position} on the waitlist at {restaurant_name}"
    body = (
        f"Hi {user.get('name', 'there')},\n\n"
        f"You've been added to the waitlist at {restaurant_name}.\n"
        f"Your current position: #{position}\n\n"
        f"We'll notify you when it's your turn!\n"
    )
    send_notification(
        recipient_user_id=user_id,
        subject=subject,
        body=body,
        notification_type="waitlist_joined",
        metadata={"restaurant_id": restaurant_id, "position": position},
        to_email=user.get("email"),
    )
