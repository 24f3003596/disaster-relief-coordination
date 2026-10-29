from flask import Blueprint, jsonify, request, session

from extensions import db
from models import Incident
from auth import login_required, roles_required
from audit import log_action
from constants import (
    VALID_SEVERITIES,
    VALID_INCIDENT_STATUSES,
    STATUS_INCIDENT_OPEN,
    STATUS_INCIDENT_IN_PROGRESS,
    STATUS_INCIDENT_MONITORING,
    STATUS_INCIDENT_RESOLVED,
    STATUS_INCIDENT_CLOSED,
    ACTION_CREATE_INCIDENT,
    ACTION_UPDATE_INCIDENT,
    ACTION_UPDATE_INCIDENT_STATUS,
)

incidents_bp = Blueprint("incidents", __name__)

INCIDENT_STATUS_TRANSITIONS = {
    STATUS_INCIDENT_OPEN: {STATUS_INCIDENT_IN_PROGRESS, STATUS_INCIDENT_MONITORING},
    STATUS_INCIDENT_IN_PROGRESS: {STATUS_INCIDENT_MONITORING, STATUS_INCIDENT_RESOLVED},
    STATUS_INCIDENT_MONITORING: {STATUS_INCIDENT_IN_PROGRESS, STATUS_INCIDENT_RESOLVED},
    STATUS_INCIDENT_RESOLVED: {STATUS_INCIDENT_IN_PROGRESS, STATUS_INCIDENT_CLOSED},
    STATUS_INCIDENT_CLOSED: set(),
}


def _validated_coordinates(latitude, longitude):
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        raise ValueError("latitude and longitude must be numbers")
    if not -90 <= latitude <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= longitude <= 180:
        raise ValueError("longitude must be between -180 and 180")
    return latitude, longitude


def create_incident(title, description, latitude, longitude, severity, reported_by):
    if title is not None and not isinstance(title, str):
        raise ValueError("title must be a string")
    if description is not None and not isinstance(description, str):
        raise ValueError("description must be a string")
    if not isinstance(severity, str):
        raise ValueError("severity must be Low, Medium, High, or Critical")
    title = (title or "").strip()
    if not title:
        raise ValueError("title is required")
    if len(title) > 150:
        raise ValueError("title must be 150 characters or fewer")
    if severity not in VALID_SEVERITIES:
        raise ValueError("severity must be Low, Medium, High, or Critical")
    latitude, longitude = _validated_coordinates(latitude, longitude)

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
    log_action(
        user_id=reported_by,
        action=ACTION_CREATE_INCIDENT,
        entity_type="Incident",
        entity_id=incident.incident_id,
    )
    return incident


def list_incidents(status=None):
    """Retrieve incidents, optionally filtered by a valid status."""
    query = Incident.query
    if status:
        if status not in VALID_INCIDENT_STATUSES:
            raise ValueError("invalid status filter")
        query = query.filter_by(status=status)
    return query.order_by(Incident.created_at.desc()).all()


def update_incident(incident_id, updates, actor_id=None):
    """Update incident details without allowing status to bypass its workflow."""
    incident = db.session.get(Incident, incident_id)
    if incident is None:
        raise ValueError("Incident not found")
    if not isinstance(updates, dict):
        raise ValueError("incident updates must be an object")

    allowed_fields = {"title", "description", "latitude", "longitude", "severity"}
    unknown_fields = set(updates) - allowed_fields
    if unknown_fields:
        raise ValueError(f"unsupported incident fields: {', '.join(sorted(unknown_fields))}")
    if not updates:
        raise ValueError("at least one incident field must be provided")

    title = incident.title
    if "title" in updates:
        if not isinstance(updates.get("title"), str):
            raise ValueError("title must be a string")
        title = (updates.get("title") or "").strip()
        if not title:
            raise ValueError("title is required")
        if len(title) > 150:
            raise ValueError("title must be 150 characters or fewer")

    description = incident.description
    if "description" in updates:
        if updates.get("description") is not None and not isinstance(updates.get("description"), str):
            raise ValueError("description must be a string")
        description = (updates.get("description") or "").strip()

    severity = incident.severity
    if "severity" in updates:
        severity = updates.get("severity")
        if not isinstance(severity, str) or severity not in VALID_SEVERITIES:
            raise ValueError("severity must be Low, Medium, High, or Critical")

    latitude = updates.get("latitude", incident.latitude)
    longitude = updates.get("longitude", incident.longitude)
    latitude, longitude = _validated_coordinates(latitude, longitude)

    incident.title = title
    incident.description = description
    incident.severity = severity
    incident.latitude = latitude
    incident.longitude = longitude
    db.session.commit()
    log_action(
        user_id=actor_id,
        action=ACTION_UPDATE_INCIDENT,
        entity_type="Incident",
        entity_id=incident.incident_id,
    )
    return incident


def update_incident_status(incident_id, new_status, actor_id=None):
    """Apply a valid incident status transition."""
    if new_status not in VALID_INCIDENT_STATUSES:
        raise ValueError(f"invalid status. Must be one of: {', '.join(VALID_INCIDENT_STATUSES)}")
    incident = db.session.get(Incident, incident_id)
    if incident is None:
        raise ValueError("Incident not found")
    if new_status == incident.status:
        return incident
    allowed = INCIDENT_STATUS_TRANSITIONS.get(incident.status, set())
    if new_status not in allowed:
        raise ValueError(
            f"Invalid incident status transition: {incident.status} -> {new_status}"
        )
    incident.status = new_status
    db.session.commit()
    log_action(
        user_id=actor_id,
        action=ACTION_UPDATE_INCIDENT_STATUS,
        entity_type="Incident",
        entity_id=incident.incident_id,
    )
    return incident


def list_affected_areas(incident_id=None):
    """Return active incidents that identify affected areas."""
    active_statuses = [
        STATUS_INCIDENT_OPEN,
        STATUS_INCIDENT_IN_PROGRESS,
        STATUS_INCIDENT_MONITORING,
    ]
    query = Incident.query.filter(Incident.status.in_(active_statuses))
    if incident_id is not None:
        query = query.filter_by(incident_id=incident_id)
    incidents = query.order_by(Incident.severity.desc()).all()
    return [
        {
            "incident_id": item.incident_id,
            "title": item.title,
            "latitude": item.latitude,
            "longitude": item.longitude,
            "severity": item.severity,
            "status": item.status,
        }
        for item in incidents
    ]


@incidents_bp.post("/")
@login_required
@roles_required("Coordinator", "Admin")
def create_incident_route():
    data = request.get_json(silent=True)
    if data is None:
        data = request.form
    if not hasattr(data, "get"):
        return jsonify({"error": "Request body must be a JSON object or form data"}), 400
    try:
        incident = create_incident(
            data.get("title"),
            data.get("description", ""),
            data.get("latitude"),
            data.get("longitude"),
            data.get("severity"),
            session["user_id"],
        )
        return jsonify({"message": "Incident registered", "incident": incident.to_dict()}), 201
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400


@incidents_bp.get("/")
def list_incidents_route():
    status = request.args.get("status")
    try:
        incidents = list_incidents(status=status)
        return jsonify({"incidents": [incident.to_dict() for incident in incidents]}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@incidents_bp.get("/<int:incident_id>")
def get_incident_route(incident_id):
    incident = db.session.get(Incident, incident_id)
    if incident is None:
        return jsonify({"error": "Incident not found"}), 404
    return jsonify({"incident": incident.to_dict()}), 200


@incidents_bp.patch("/<int:incident_id>")
@login_required
@roles_required("Coordinator", "Admin")
def update_incident_route(incident_id):
    data = request.get_json(silent=True)
    if data is None:
        data = request.form
    if not hasattr(data, "get"):
        return jsonify({"error": "Request body must be a JSON object or form data"}), 400
    try:
        incident = update_incident(incident_id, dict(data), actor_id=session["user_id"])
        return jsonify({"message": "Incident updated", "incident": incident.to_dict()}), 200
    except ValueError as exc:
        db.session.rollback()
        status_code = 404 if str(exc) == "Incident not found" else 400
        return jsonify({"error": str(exc)}), status_code


@incidents_bp.patch("/<int:incident_id>/status")
@login_required
@roles_required("Coordinator", "Admin")
def update_incident_status_route(incident_id):
    data = request.get_json(silent=True)
    if data is None:
        data = request.form
    if not hasattr(data, "get"):
        return jsonify({"error": "Request body must be a JSON object or form data"}), 400
    try:
        incident = update_incident_status(
            incident_id,
            data.get("status"),
            actor_id=session["user_id"],
        )
        return jsonify({"message": "Incident status updated", "incident": incident.to_dict()}), 200
    except ValueError as exc:
        db.session.rollback()
        status_code = 404 if str(exc) == "Incident not found" else 400
        return jsonify({"error": str(exc)}), status_code


@incidents_bp.get("/affected-areas")
def affected_areas_route():
    incident_id = request.args.get("incident_id", type=int)
    areas = list_affected_areas(incident_id=incident_id)
    return jsonify({"affected_areas": areas}), 200
