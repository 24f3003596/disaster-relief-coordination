"""Coordinator map view and filtered geospatial data API."""
from datetime import datetime, timezone
import math

from flask import Blueprint, jsonify, render_template, request
from sqlalchemy import or_

from auth import login_required, roles_required
from constants import (
    ROLE_ADMIN,
    ROLE_COORDINATOR,
    STATUS_REQUEST_CANCELLED,
    STATUS_REQUEST_COMPLETED,
    STATUS_INCIDENT_CLOSED,
    STATUS_INCIDENT_RESOLVED,
    VALID_CATEGORIES,
    VALID_INCIDENT_STATUSES,
    VALID_REQUEST_STATUSES,
)
from models import Incident, InventoryItem, ReliefRequest, User

map_bp = Blueprint("map_view", __name__)


def _parse_viewport(args):
    """Parse and validate optional Leaflet map bounds."""
    if args.get("viewport") not in ("1", "true", "yes"):
        return None

    names = ("south", "west", "north", "east")
    try:
        bounds = {name: float(args[name]) for name in names}
    except (KeyError, TypeError, ValueError):
        raise ValueError("viewport requires south, west, north and east bounds")

    if not all(math.isfinite(value) for value in bounds.values()):
        raise ValueError("viewport bounds must be finite numbers")
    if not (-90 <= bounds["south"] <= 90 and -90 <= bounds["north"] <= 90):
        raise ValueError("viewport latitude bounds must be between -90 and 90")
    if not (-180 <= bounds["west"] <= 180 and -180 <= bounds["east"] <= 180):
        raise ValueError("viewport longitude bounds must be between -180 and 180")
    if bounds["south"] > bounds["north"]:
        raise ValueError("viewport south bound cannot exceed north bound")
    return bounds


def _case_insensitive_contains(column, value):
    """Build a literal, case-insensitive substring predicate."""
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return column.ilike(f"%{escaped}%", escape="\\")


def _apply_viewport(query, model, bounds):
    if bounds is None:
        return query

    query = query.filter(
        model.latitude >= bounds["south"],
        model.latitude <= bounds["north"],
    )
    west = bounds["west"]
    east = bounds["east"]
    if west <= east:
        return query.filter(model.longitude >= west, model.longitude <= east)
    # A Leaflet viewport can cross the anti-meridian.
    return query.filter(or_(model.longitude >= west, model.longitude <= east))


@map_bp.get("/")
@login_required
@roles_required(ROLE_COORDINATOR, ROLE_ADMIN)
def map_page():
    """Render the operational map for coordinators and administrators."""
    statuses = list(dict.fromkeys(VALID_REQUEST_STATUSES + VALID_INCIDENT_STATUSES))
    return render_template(
        "map.html",
        refresh_interval_seconds=30,
        categories=VALID_CATEGORIES,
        statuses=statuses,
    ), 200


@map_bp.get("/data")
@login_required
@roles_required(ROLE_COORDINATOR, ROLE_ADMIN)
def map_data():
    """Return map markers with category, status, region and viewport filters."""
    category = (request.args.get("category") or "").strip()
    status = (request.args.get("status") or "").strip()
    region = (request.args.get("region") or "").strip()

    if len(region) > 100:
        return jsonify({"error": "region filter must be 100 characters or fewer"}), 400
    if category and category not in VALID_CATEGORIES:
        return jsonify({"error": "Invalid category filter"}), 400
    valid_statuses = set(VALID_REQUEST_STATUSES) | set(VALID_INCIDENT_STATUSES)
    if status and status not in valid_statuses:
        return jsonify({"error": "Invalid status filter"}), 400

    try:
        bounds = _parse_viewport(request.args)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    request_query = ReliefRequest.query
    if not status:
        request_query = request_query.filter(
            ReliefRequest.status.notin_([STATUS_REQUEST_COMPLETED, STATUS_REQUEST_CANCELLED])
        )
    if category:
        request_query = request_query.filter(ReliefRequest.category == category)
    if status:
        request_query = request_query.filter(ReliefRequest.status == status)
    if region:
        request_query = request_query.filter(
            _case_insensitive_contains(ReliefRequest.location, region)
        )
    request_query = _apply_viewport(request_query, ReliefRequest, bounds)
    request_records = request_query.order_by(ReliefRequest.created_at.desc()).all()

    # Incidents have no category column, so request-category filtering does not
    # remove incident markers; the remaining filters still apply to incidents.
    incident_query = Incident.query
    if not status:
        incident_query = incident_query.filter(
            Incident.status.notin_([STATUS_INCIDENT_RESOLVED, STATUS_INCIDENT_CLOSED])
        )
    if status:
        incident_query = incident_query.filter(Incident.status == status)
    if region:
        incident_query = incident_query.filter(
            or_(
                _case_insensitive_contains(Incident.title, region),
                _case_insensitive_contains(Incident.description, region),
            )
        )
    incident_query = _apply_viewport(incident_query, Incident, bounds)
    incident_records = incident_query.order_by(Incident.created_at.desc()).all()

    # Requests with incomplete coordinate pairs remain valid application data,
    # but cannot be plotted until a location is supplied.
    requests_without_coordinates = ReliefRequest.query.filter(
        or_(ReliefRequest.latitude.is_(None), ReliefRequest.longitude.is_(None))
    ).count()
    storage_locations_without_coordinates = (
        db_query_storage_locations_count()
    )
    volunteers_without_coordinates = User.query.filter_by(role="Volunteer").count()

    response = jsonify({
        "requests": [
            {
                "request_id": item.request_id,
                "category": item.category,
                "quantity": item.quantity,
                "urgency": item.urgency,
                "status": item.status,
                "location": item.location,
                "latitude": item.latitude,
                "longitude": item.longitude,
                "created_at": item.created_at.isoformat() + "Z" if item.created_at else None,
            }
            for item in request_records
            if item.latitude is not None and item.longitude is not None
        ],
        "incidents": [
            {
                "incident_id": item.incident_id,
                "title": item.title,
                "description": item.description,
                "severity": item.severity,
                "status": item.status,
                "latitude": item.latitude,
                "longitude": item.longitude,
                "created_at": item.created_at.isoformat() + "Z" if item.created_at else None,
            }
            for item in incident_records
            if item.latitude is not None and item.longitude is not None
        ],
        "unmapped": {
            "requests_without_coordinates": requests_without_coordinates,
            "storage_locations_without_coordinates": storage_locations_without_coordinates,
            "volunteers_without_coordinates": volunteers_without_coordinates,
        },
        "filters": {"category": category, "status": status, "region": region,
                    "viewport": bounds is not None},
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
    })
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response, 200


def db_query_storage_locations_count():
    """Count distinct inventory storage labels; they have no coordinates yet."""
    return InventoryItem.query.with_entities(
        InventoryItem.storage_location
    ).filter(InventoryItem.storage_location.isnot(None)).distinct().count()
