from flask import Blueprint, jsonify, request, session

from extensions import db
from models import Notification, User, InventoryItem, ReliefRequest
from auth import login_required, roles_required
from constants import (
    VALID_NOTIFICATION_TYPES,
    NOTIFICATION_GENERAL,
    NOTIFICATION_EMERGENCY,
    NOTIFICATION_CRITICAL_SHORTAGE,
    STATUS_REQUEST_PENDING,
    ROLE_COORDINATOR,
    ROLE_ADMIN,
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


def check_and_notify_critical_shortage(category=None, item_id=None):
    """
    Automate critical-shortage notifications (SRS FR 3.6.2).
    
    When inventory for a resource category falls below or at its configured
    threshold while pending requests for that category exist, notify the
    relevant Coordinators and Admins through the in-app notification system.

    Acceptance Criteria Enforced:
    1. Threshold Checks: Checked on inventory creation, manual stock adjustments,
       request allocations, and new pending request creation.
    2. Shortage Notification: Triggered when category stock <= threshold AND pending requests > 0.
    3. No Unmatched Alerts: Shortages without matching pending requests do NOT generate request alerts.
    4. Access Control / Authorized Recipients: Only Coordinators and Admins receive alerts (Victims/Volunteers excluded).
    5. Deduplication: Repeated operations do not generate duplicate unread alerts for the same shortage condition.
    """
    target_categories = set()
    if item_id is not None:
        item = db.session.get(InventoryItem, item_id)
        if item and item.category:
            target_categories.add(item.category)
    elif category:
        target_categories.add(category.strip())
    else:
        # Check all categories present in warehouse inventory
        cats = db.session.query(InventoryItem.category).distinct().all()
        target_categories = {c[0] for c in cats if c[0]}

    if not target_categories:
        return []

    created_alerts = []

    for cat in target_categories:
        items = InventoryItem.query.filter(InventoryItem.category.ilike(cat)).all()
        if not items:
            continue

        total_stock = sum(i.quantity for i in items)
        total_threshold = sum(i.threshold for i in items)

        # Category is in shortage if total available stock <= total threshold
        # or any item in the category has reached low stock
        is_shortage = (total_stock <= total_threshold) or any(i.is_low_stock() for i in items)
        if not is_shortage:
            # Stock is strictly above threshold; no shortage condition
            continue

        # Check for matching pending relief requests (AC3)
        pending_requests = ReliefRequest.query.filter(
            ReliefRequest.category.ilike(cat),
            ReliefRequest.status == STATUS_REQUEST_PENDING,
        ).all()
        pending_count = len(pending_requests)
        if pending_count == 0:
            # AC3: Shortages without matching pending requests do not generate request-related alerts
            continue

        # Recipients: Coordinators and Admins only (AC4)
        recipients = User.query.filter(
            User.role.in_([ROLE_COORDINATOR, ROLE_ADMIN])
        ).all()
        if not recipients:
            continue

        # Deduplication (AC5): Do not send duplicate alert if an unread alert for this category already exists
        for recipient in recipients:
            existing = Notification.query.filter(
                Notification.user_id == recipient.user_id,
                Notification.type == NOTIFICATION_CRITICAL_SHORTAGE,
                Notification.is_read.is_(False),
                Notification.message.like(f"%'{cat}'%"),
            ).first()
            if existing:
                continue

            alert_msg = (
                f"CRITICAL SHORTAGE ALERT: Resource category '{cat}' stock is at or below threshold "
                f"({total_stock} units available, threshold {total_threshold}) "
                f"with {pending_count} pending request(s) awaiting fulfillment."
            )
            notif = Notification(
                user_id=recipient.user_id,
                message=alert_msg,
                type=NOTIFICATION_CRITICAL_SHORTAGE,
                is_read=False,
            )
            db.session.add(notif)
            created_alerts.append(notif)

    if created_alerts:
        db.session.flush()

    return created_alerts


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


@notifications_bp.post("/check-shortages")
@login_required
@roles_required(ROLE_COORDINATOR, ROLE_ADMIN)
def check_shortages_route():
    """Manual trigger / check for critical inventory shortages (FR 3.6.2)."""
    alerts = check_and_notify_critical_shortage()
    db.session.commit()
    return jsonify({
        "message": f"Critical shortage check complete. Generated {len(alerts)} alert(s).",
        "alerts": [a.to_dict() for a in alerts],
    }), 200
