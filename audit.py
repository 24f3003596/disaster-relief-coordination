from datetime import datetime
from flask import Blueprint, jsonify, request

from extensions import db
from models import AuditLog
from auth import login_required, roles_required

audit_bp = Blueprint("audit", __name__)

def log_action(user_id, action, entity_type=None, entity_id=None):
    """
    Record an action in the system audit log.
    user_id can be None for system-level actions.
    """
    action = (action or "").strip()
    if not action:
        raise ValueError("action is required")
    if len(action) > 120:
        action = action[:117] + "..."

    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    db.session.add(log_entry)
    db.session.commit()
    return log_entry

def list_entity_activity(entity_type, entity_id):
    """Return an entity's activity in chronological order, including actor names.

    The existing AuditLog table is reused so existing installations do not need
    a schema migration. New events put concise, human-readable change details
    into the existing action field.
    """
    entity_type = (entity_type or "").strip()
    if not entity_type:
        raise ValueError("entity_type is required")
    try:
        entity_id = int(entity_id)
    except (TypeError, ValueError):
        raise ValueError("entity_id must be an integer")

    entries = (
        AuditLog.query
        .filter_by(entity_type=entity_type, entity_id=entity_id)
        .order_by(AuditLog.created_at.asc(), AuditLog.log_id.asc())
        .all()
    )
    activity = []
    for entry in entries:
        item = entry.to_dict()
        item["actor_name"] = entry.user.name if entry.user else "System"
        activity.append(item)
    return activity


def list_audit_logs(start_date=None, end_date=None):
    """Retrieve audit logs ordered by date descending."""
    query = AuditLog.query
    if start_date:
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
        query = query.filter(AuditLog.created_at <= end_date)

    return query.order_by(AuditLog.created_at.desc()).all()

@audit_bp.get("/")
@login_required
@roles_required("Coordinator", "Admin")
def list_audit_logs_route():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    try:
        logs = list_audit_logs(start_date=start_date, end_date=end_date)
        return jsonify({"audit_logs": [entry.to_dict() for entry in logs]}), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
