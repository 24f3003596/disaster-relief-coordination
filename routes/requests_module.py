from flask import Blueprint, jsonify, request, session, render_template

from extensions import db
from models import ReliefRequest, User, Incident
from audit import log_action
from constants import (
    VALID_CATEGORIES,
    VALID_URGENCIES,
    VALID_REQUEST_STATUSES,
    STATUS_REQUEST_PENDING,
    ACTION_CREATE_REQUEST,
    ACTION_UPDATE_REQUEST_STATUS,
)

requests_bp = Blueprint("requests_module", __name__)

def create_relief_request(user_id, category, quantity, urgency="Medium", latitude=None, longitude=None, incident_id=None, location=None):
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise ValueError("Invalid user_id")

    user = db.session.get(User, user_id)
    if not user:
        raise ValueError("User not found")

    category = (category or "").strip()
    if not category:
        raise ValueError("category is required")
    if category not in VALID_CATEGORIES:
        raise ValueError(f"invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}")

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        raise ValueError("quantity must be an integer")
    if quantity <= 0:
        raise ValueError("quantity must be greater than zero")

    urgency = (urgency or "Medium").strip()
    if urgency not in VALID_URGENCIES:
        raise ValueError(f"invalid urgency. Must be one of: {', '.join(VALID_URGENCIES)}")

    parsed_lat = None
    parsed_lon = None
    if latitude is not None and longitude is not None:
        try:
            parsed_lat = float(latitude)
            parsed_lon = float(longitude)
        except (TypeError, ValueError):
            raise ValueError("latitude and longitude must be numbers")
        if not -90 <= parsed_lat <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if not -180 <= parsed_lon <= 180:
            raise ValueError("longitude must be between -180 and 180")

    if not location:
        if parsed_lat is not None and parsed_lon is not None:
            location = f"{parsed_lat:.4f}, {parsed_lon:.4f}"
        else:
            location = "Location coordinates unspecified"

    if incident_id is not None:
        incident = db.session.get(Incident, incident_id)
        if not incident:
            raise ValueError(f"Incident with ID {incident_id} does not exist")

    req = ReliefRequest(
        user_id=user_id,
        category=category,
        quantity=quantity,
        urgency=urgency,
        location=location,
        latitude=parsed_lat,
        longitude=parsed_lon,
        incident_id=incident_id,
        status=STATUS_REQUEST_PENDING,
    )
    db.session.add(req)
    db.session.commit()

    log_action(
        user_id=user_id,
        action=ACTION_CREATE_REQUEST,
        entity_type="ReliefRequest",
        entity_id=req.request_id,
    )

    return req

def list_relief_requests(status=None, user_id=None):
    query = ReliefRequest.query
    if status:
        if status not in VALID_REQUEST_STATUSES:
            raise ValueError("invalid status filter")
        query = query.filter_by(status=status)
    if user_id:
        query = query.filter_by(user_id=user_id)

    return query.order_by(ReliefRequest.created_at.desc()).all()

def update_request_status(request_id, new_status, actor_id=None):
    if new_status not in VALID_REQUEST_STATUSES:
        raise ValueError(f"invalid status. Must be one of: {', '.join(VALID_REQUEST_STATUSES)}")

    req = db.session.get(ReliefRequest, request_id)
    if not req:
        raise ValueError("Relief request not found")

    req.status = new_status
    db.session.commit()

    log_action(
        user_id=actor_id,
        action=ACTION_UPDATE_REQUEST_STATUS,
        entity_type="ReliefRequest",
        entity_id=req.request_id,
    )

    return req

@requests_bp.post("/")
def create_request_route():
    data = request.get_json(silent=True) or request.form or {}
    try:
        user_id = data.get("user_id") or session.get("user_id")
        req = create_relief_request(
            user_id=user_id,
            category=data.get("category"),
            quantity=data.get("quantity"),
            urgency=data.get("urgency", "Medium"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            incident_id=data.get("incident_id"),
            location=data.get("location"),
        )
        if request.is_json or request.headers.get("Accept") == "application/json":
            return jsonify({"message": "Relief request submitted", "request": req.to_dict()}), 201
        requests_list = list_relief_requests()
        return render_template("requests.html", requests=[r.to_dict() for r in requests_list], users=User.query.all(), message="Relief request submitted"), 200
    except ValueError as exc:
        db.session.rollback()
        if request.is_json or request.headers.get("Accept") == "application/json":
            return jsonify({"error": str(exc)}), 400
        requests_list = list_relief_requests()
        return render_template("requests.html", requests=[r.to_dict() for r in requests_list], users=User.query.all(), error=str(exc)), 400

@requests_bp.get("/")
def list_requests_route():
    status = request.args.get("status")
    user_id = request.args.get("user_id", type=int)
    try:
        requests_list = list_relief_requests(status=status, user_id=user_id)
        requests_dict = [r.to_dict() for r in requests_list]
        if request.is_json or request.args.get("format") == "json" or request.headers.get("Accept") == "application/json":
            return jsonify({
                "requests": requests_dict,
                "total_requests": len(requests_list),
            }), 200
        users = User.query.all()
        return render_template("requests.html", requests=requests_dict, users=users), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

@requests_bp.get("/<int:request_id>")
def get_request_route(request_id):
    req = db.session.get(ReliefRequest, request_id)
    if not req:
        return jsonify({"error": "Relief request not found"}), 404
    return jsonify({"request": req.to_dict()}), 200

@requests_bp.patch("/<int:request_id>/status")
def update_request_status_route(request_id):
    data = request.get_json(silent=True) or request.form or {}
    new_status = data.get("status")
    try:
        req = update_request_status(
            request_id=request_id,
            new_status=new_status,
            actor_id=session.get("user_id"),
        )
        return jsonify({"message": "Request status updated", "request": req.to_dict()}), 200
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400
