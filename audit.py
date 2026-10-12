from extensions import db
from models import AuditLog

def log_action(user_id, action, entity_type=None, entity_id=None):
    if not action or not action.strip(): raise ValueError("Action is required")
    log=AuditLog(user_id=user_id,action=action.strip(),entity_type=entity_type,entity_id=entity_id)
    db.session.add(log); db.session.commit(); return log

def list_audit_logs(start_date=None,end_date=None):
    q=AuditLog.query
    if start_date: q=q.filter(AuditLog.created_at>=start_date)
    if end_date: q=q.filter(AuditLog.created_at<=end_date)
    return q.order_by(AuditLog.created_at.desc()).all()
