from flask import Blueprint, jsonify, request, session

from extensions import db
from models import Notification, User
from auth import login_required, roles_required
from constants import (
    VALID_NOTIFICATION_TYPES,
    NOTIFICATION_GENERAL,
    NOTIFICATION_EMERGENCY,
)

notifications_bp = Blueprint("notifications", __name__)

def create_notification(user_id, message, notification_type=NOTIFICATION_GENERAL):
    """
    Create and record a notification for a specific user.
    """
    if not message or not str(message).strip():
        raise ValueError("Notification message is required")

    user = db.session.get(User, user_id)
    if user is None:
        raise ValueError("User not found")

    notification = Notification(
        user_id=user_id,
        message=str(message).strip(),
        type=notification_type or NOTIFICATION_GENERAL,
        is_read=False,
    )
    db.session.add(notification)
    db.session.flush()
    return notification

def list_notifications(user_id, unread_only=False):
    """Retrieve notifications for a user."""
    query = Notification.query.filter_by(user_id=user_id)
    if unread_only:
        query = query.filter_by(is_read=False)
    return query.order_by(Notification.created_at.desc()).all()

def mark_notification_read(notification_id, user_id):
    """Mark notification read, enforcing user ownership."""
    notification = db.session.get(Notification, notification_id)
    if notification is None or notification.user_id != user_id:
        raise ValueError("Notification not found for this user")

    notification.is_read = True
    db.session.commit()
    return notification

def broadcast_emergency_alert(message, notification_type=NOTIFICATION_EMERGENCY, recipient_user_ids=None):
    """
    Broadcast notification to specified users or default to operational roles
    (Volunteer, Coordinator, Admin).
    """
    if not message or not str(message).strip():
        raise ValueError("Alert message is required")

    if recipient_user_ids is not None:
        ids = set(recipient_user_ids)
        recipients = User.query.filter(User.user_id.in_(ids)).all() if ids else []
    else:
        recipients = User.query.filter(User.role.in_(["Coordinator", "Admin", "Volunteer"])).all()

    created = [
        Notification(
            user_id=u.user_id,
            message=str(message).strip(),
            type=notification_type or NOTIFICATION_EMERGENCY,
            is_read=False,
        )
        for u in recipients
    ]
    db.session.add_all(created)
    db.session.commit()
    return created

@notifications_bp.get("/")
def get_user_notifications():
    user_id = session.get("user_id")
    if not user_id:
        notifs = Notification.query.order_by(Notification.created_at.desc()).all()
    else:
        notifs = list_notifications(user_id)
    return jsonify({"notifications": [n.to_dict() for n in notifs]}), 200

@notifications_bp.patch("/<int:notification_id>/read")
def read_notification_route(notification_id):
    user_id = session.get("user_id")
    try:
        notif = mark_notification_read(notification_id, user_id)
        return jsonify({"message": "Notification marked as read", "notification": notif.to_dict()}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404

@notifications_bp.post("/broadcast")
def broadcast_route():
    data = request.get_json(silent=True) or request.form or {}
    message = data.get("message")
    recipients = data.get("recipient_user_ids")
    try:
        alerts = broadcast_emergency_alert(message=message, recipient_user_ids=recipients)
        return jsonify({"message": f"Broadcast sent to {len(alerts)} users"}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
