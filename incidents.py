from flask import Blueprint, jsonify, request

from extensions import db
from models import Incident
from auth import login_required, roles_required

incidents_bp = Blueprint("incidents", __name__)
VALID_SEVERITIES = {"Low", "Medium", "High", "Critical"}
VALID_STATUSES = {"Open", "In Progress", "Resolved", "Closed"}

def create_incident(title, description, latitude, longitude, severity, reported_by):
    title = (title or "").strip()
    if not title:
        raise ValueError("title is required")
    if severity not in VALID_SEVERITIES:
        raise ValueError("severity must be Low, Medium, High, or Critical")
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        raise ValueError("latitude and longitude must be numbers")
    if not -90 <= latitude <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= longitude <= 180:
        raise ValueError("longitude must be between -180 and 180")
    incident = Incident(
        title=title,
        description=(description or "").strip(),
        latitude=latitude,
        longitude=longitude,
        severity=severity,
        reported_by=reported_by,
    )
    db.session.add(incident)
    db.session.commit()
    return incident

@incidents_bp.post("/")
@login_required
@roles_required("Coordinator", "Admin")
def create_incident_route():
    from flask import session
    data = request.get_json(silent=True) or {}
    try:
        incident = create_incident(
            data.get("title"), data.get("description", ""),
            data.get("latitude"), data.get("longitude"),
            data.get("severity"), session["user_id"],
        )
        return jsonify({"message": "Incident registered", "incident": incident.to_dict()}), 201
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400

@incidents_bp.get("/")
def list_incidents_route():
    status = request.args.get("status")
    query = Incident.query
    if status:
        if status not in VALID_STATUSES:
            return jsonify({"error": "invalid status filter"}), 400
        query = query.filter_by(status=status)
    incidents = query.order_by(Incident.created_at.desc()).all()
    return jsonify({"incidents": [incident.to_dict() for incident in incidents]}), 200

@incidents_bp.get("/affected-areas")
def affected_areas_route():
    incidents = Incident.query.filter(Incident.status.in_(["Open", "In Progress"])).order_by(Incident.severity.desc()).all()
    areas = [{
        "incident_id": item.incident_id,
        "title": item.title,
        "latitude": item.latitude,
        "longitude": item.longitude,
        "severity": item.severity,
        "status": item.status,
    } for item in incidents]
    return jsonify({"affected_areas": areas}), 200
