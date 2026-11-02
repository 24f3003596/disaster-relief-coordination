from flask import Blueprint, jsonify, request, session

from extensions import db
from models import (
    Notification, User, InventoryItem, ReliefRequest,
    InventoryShortageState,
)
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
    """Create one alert per active category-shortage episode.

    A shortage episode starts when category stock is at/below the configured
    threshold (or an individual storage record is at/below its own threshold)
    AND at least one matching relief request is pending. Repeated checks do
    not create duplicate alerts, even if an earlier alert has been read.
    A recovery above threshold or the absence of pending demand closes the
    episode; a later shortage can then generate a fresh alert.

    This function flushes changes but deliberately does not commit. Callers
    commit it together with the inventory/request operation that triggered it.
    """
    target_categories = set()
    if item_id is not None:
        item = db.session.get(InventoryItem, item_id)
        if item and item.category:
            target_categories.add(item.category.strip())
    elif category:
        normalized_category = str(category).strip()
        if normalized_category:
            target_categories.add(normalized_category)
    else:
        categories = db.session.query(InventoryItem.category).distinct().all()
        target_categories = {
            str(row[0]).strip() for row in categories if row[0] and str(row[0]).strip()
        }

    if not target_categories:
        return []

    created_alerts = []
    # Collapse case-only duplicates while preserving a readable category label.
    categories_by_key = {}
    for label in sorted(target_categories, key=str.casefold):
        categories_by_key.setdefault(label.casefold(), label)

    for category_key, category_label in categories_by_key.items():
        items = (
            InventoryItem.query
            .filter(InventoryItem.category.ilike(category_label))
            .order_by(InventoryItem.item_id.asc())
            .all()
        )
        state = db.session.get(InventoryShortageState, category_key)

        if not items:
            if state and state.is_active:
                state.is_active = False
                state.available_stock = 0
                state.configured_threshold = 0
                state.pending_request_count = 0
            continue

        total_stock = sum(max(0, int(item.quantity or 0)) for item in items)
        total_threshold = sum(max(0, int(item.threshold or 0)) for item in items)
        low_stock_item_count = sum(1 for item in items if item.is_low_stock())
        is_stock_shortage = (
            total_stock <= total_threshold or low_stock_item_count > 0
        )

        pending_count = ReliefRequest.query.filter(
            ReliefRequest.category.ilike(category_label),
            ReliefRequest.status == STATUS_REQUEST_PENDING,
        ).count()

        shortage_is_active = is_stock_shortage and pending_count > 0

        if not shortage_is_active:
            # Remember recovery so a future shortage becomes a new episode.
            if state and state.is_active:
                state.is_active = False
            if state:
                state.available_stock = total_stock
                state.configured_threshold = total_threshold
                state.pending_request_count = pending_count
            continue

        if state and state.is_active:
            # Same uninterrupted shortage: update diagnostic values, but do
            # not send another notification (even if the earlier one was read).
            state.available_stock = total_stock
            state.configured_threshold = total_threshold
            state.pending_request_count = pending_count
            continue

        recipients = (
            User.query
            .filter(
                User.role.in_([ROLE_COORDINATOR, ROLE_ADMIN]),
                User.is_active.is_(True),
                User.phone_verified.is_(True),
                User.approval_status == "approved",
            )
            .order_by(User.user_id.asc())
            .all()
        )
        if not recipients:
            # Do not mark the episode active until at least one eligible
            # recipient can actually receive the alert.
            continue

        if state is None:
            state = InventoryShortageState(category_key=category_key)
            db.session.add(state)

        reason = (
            f"{low_stock_item_count} inventory item(s) at/below their own "
            f"threshold; category total {total_stock} units, combined "
            f"threshold {total_threshold} units"
        )
        message = (
            f"CRITICAL SHORTAGE ALERT: Resource category '{category_label}' "
            f"requires attention ({reason}) with {pending_count} pending "
            f"request(s) awaiting fulfillment."
        )

        for recipient in recipients:
            notification = Notification(
                user_id=recipient.user_id,
                message=message,
                type=NOTIFICATION_CRITICAL_SHORTAGE,
                is_read=False,
            )
            db.session.add(notification)
            created_alerts.append(notification)

        state.is_active = True
        state.available_stock = total_stock
        state.configured_threshold = total_threshold
        state.pending_request_count = pending_count

    if created_alerts or target_categories:
        db.session.flush()

    return created_alerts


@notifications_bp.get("/")
def get_user_notifications():
    user_id = session.get("user_id")
    # Preserve an empty response for anonymous page loads, but never expose
    # system-wide or other users' private notifications.
    if not user_id:
        return jsonify({"notifications": []}), 200
    notifs = list_notifications(user_id)
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


@notifications_bp.post("/broadcast")
@login_required
@roles_required(ROLE_COORDINATOR, ROLE_ADMIN)
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
