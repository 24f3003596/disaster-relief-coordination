from extensions import db
from models import User, Notification

def create_notification(user_id, message, notification_type="General"):
    if not message or not message.strip(): raise ValueError("Notification message is required")
    if db.session.get(User, user_id) is None: raise ValueError("User not found")
    notification = Notification(user_id=user_id, message=message.strip(), type=notification_type or "General")
    db.session.add(notification)
    # Caller may be inside a larger transaction; don't commit here.
    db.session.flush()
    return notification

def list_notifications(user_id, unread_only=False):
    q = Notification.query.filter_by(user_id=user_id)
    if unread_only: q = q.filter_by(is_read=False)
    return q.order_by(Notification.created_at.desc()).all()

def mark_notification_read(notification_id, user_id):
    notification = db.session.get(Notification, notification_id)
    if notification is None or notification.user_id != user_id: raise ValueError("Notification not found for this user")
    notification.is_read = True
    db.session.commit()
    return notification

def broadcast_emergency_alert(message, notification_type, recipient_user_ids=None):
    if not message or not message.strip(): raise ValueError("Alert message is required")
    q = User.query
    if recipient_user_ids is not None:
        ids = set(recipient_user_ids)
        recipients = q.filter(User.user_id.in_(ids)).all() if ids else []
    else:
        recipients = q.filter(User.role.in_(["Coordinator", "Admin", "Volunteer"])).all()
    created = [Notification(user_id=u.user_id, message=message.strip(), type=notification_type or "Emergency") for u in recipients]
    db.session.add_all(created); db.session.commit()
    return created
