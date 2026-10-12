from flask import Blueprint, jsonify, request, session

from extensions import db
from models import Notification, User
from auth import login_required, roles_required
from constants import (
    VALID_NOTIFICATION_TYPES,
    NOTIFICATION_GENERAL,
    NOTIFICATION_EMERGENCY,
    ROLE_VOLUNTEER,
    ROLE_COORDINATOR,
)

notifications_bp = Blueprint("notifications", __name__)

def create_notification(user_id, message, notification_type=NOTIFICATION_GENERAL):
    """
    Create a notification for a specific user.
    """
    message = (message or "").strip()
    if not message:
        raise ValueError("message is required")

    user = db.session.get(User, user_id)
    if not user:
        raise ValueError("User not found")

    if notification_type not in VALID_NOTIFICATION_TYPES:
        notification_type = NOTIFICATION_GENERAL

    notif = Notification(
        user_id=user_id,
        message=message,
        type=notification_type,
        is_read=False,
    )
    db.session.add(notif)
    db.session.commit()
    return notif

def mark_notification_read(notification_id, user_id):
    """
    Mark a notification as read for a specific user.
    """
    notif = db.session.get(Notification, notification_id)
    if not notif:
        raise ValueError("Notification not found")
    if notif.user_id != user_id:
        raise PermissionError("Notification does not belong to this user")

    notif.is_read = True
    db.session.commit()
    return notif

def broadcast_emergency_alert(message, notification_type=NOTIFICATION_EMERGENCY, recipient_user_ids=None):
    """
    Broadcast an emergency notification to a group of users or all active users.
    """
    message = (message or "").strip()
    if not message:
        raise ValueError("message is required")

    if recipient_user_ids:
        users = User.query.filter(User.user_id.in_(recipient_user_ids)).all()
    else:
        # Broadcast to all users
        users = User.query.all()

    created_notifications = []
    for u in users:
        notif = Notification(
            user_id=u.user_id,
            message=message,
            type=notification_type,
            is_read=False,
        )
        db.session.add(notif)
        created_notifications.append(notif)

    db.session.commit()
    return created_notifications

@notifications_bp.get("/")
@login_required
def get_user_notifications():
    user_id = session.get("user_id")
    notifs = (
        Notification.query.filter_by(user_id=user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return jsonify({"notifications": [n.to_dict() for n in notifs]}), 200

@notifications_bp.patch("/<int:notification_id>/read")
@login_required
def read_notification_route(notification_id):
    user_id = session.get("user_id")
    try:
        notif = mark_notification_read(notification_id, user_id)
        return jsonify({"message": "Notification marked as read", "notification": notif.to_dict()}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403

@notifications_bp.post("/broadcast")
@login_required
@roles_required("Coordinator", "Admin")
def broadcast_route():
    data = request.get_json(silent=True) or {}
    message = data.get("message")
    recipients = data.get("recipient_user_ids")
    try:
        alerts = broadcast_emergency_alert(message=message, recipient_user_ids=recipients)
        return jsonify({"message": f"Broadcast sent to {len(alerts)} users"}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
