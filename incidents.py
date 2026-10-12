from extensions import db
from models import Incident, User
from constants import INCIDENT_SEVERITIES, INCIDENT_STATUSES

def create_incident(title, description, latitude, longitude, severity, reported_by):
    if not title or not title.strip(): raise ValueError("Incident title is required")
    if not (-90 <= float(latitude) <= 90) or not (-180 <= float(longitude) <= 180): raise ValueError("Invalid coordinates")
    if severity not in INCIDENT_SEVERITIES: raise ValueError("Invalid severity")
    if db.session.get(User, reported_by) is None: raise ValueError("Reporter not found")
    incident=Incident(title=title.strip(),description=description or "",latitude=float(latitude),longitude=float(longitude),severity=severity,reported_by=reported_by)
    db.session.add(incident); db.session.commit(); return incident

def list_incidents(status=None):
    q=Incident.query
    if status: q=q.filter_by(status=status)
    return q.order_by(Incident.created_at.desc()).all()

def list_affected_areas(incident_id=None):
    q=Incident.query
    if incident_id is not None: q=q.filter_by(incident_id=incident_id)
    return [{"incident_id":i.incident_id,"title":i.title,"latitude":i.latitude,"longitude":i.longitude,"severity":i.severity,"status":i.status} for i in q.all()]
