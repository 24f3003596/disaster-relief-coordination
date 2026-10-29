from flask import Blueprint, jsonify, request, session, render_template

from extensions import db
from models import Assignment, ReliefRequest, User, Incident
from auth import login_required, roles_required
from audit import log_action
from constants import (
    ROLE_ADMIN,
    ROLE_COORDINATOR,
    ROLE_VICTIM,
    ROLE_VOLUNTEER,
    VALID_CATEGORIES,
    VALID_URGENCIES,
    VALID_REQUEST_STATUSES,
    STATUS_REQUEST_PENDING,
    STATUS_REQUEST_ASSIGNED,
    STATUS_REQUEST_ALLOCATED,
    STATUS_REQUEST_IN_PROGRESS,
    STATUS_REQUEST_FULFILLED,
    STATUS_REQUEST_COMPLETED,
    STATUS_REQUEST_CANCELLED,
    ACTION_CREATE_REQUEST,
    ACTION_UPDATE_REQUEST_STATUS,
)

requests_bp = Blueprint("requests_module", __name__)

# A request can move forward through the relief workflow, or be cancelled
# before it reaches a terminal completion state. Allocation/assignment code
# also updates these statuses as part of its transaction.
REQUEST_STATUS_TRANSITIONS = {
    STATUS_REQUEST_PENDING: {
        STATUS_REQUEST_ASSIGNED,
        STATUS_REQUEST_ALLOCATED,
        STATUS_REQUEST_CANCELLED,
    },
    STATUS_REQUEST_ASSIGNED: {
        STATUS_REQUEST_ALLOCATED,
        STATUS_REQUEST_IN_PROGRESS,
        STATUS_REQUEST_FULFILLED,
        STATUS_REQUEST_COMPLETED,
        STATUS_REQUEST_CANCELLED,
    },
    STATUS_REQUEST_ALLOCATED: {
        STATUS_REQUEST_ASSIGNED,
        STATUS_REQUEST_IN_PROGRESS,
        STATUS_REQUEST_FULFILLED,
        STATUS_REQUEST_COMPLETED,
        STATUS_REQUEST_CANCELLED,
    },
    STATUS_REQUEST_IN_PROGRESS: {
        STATUS_REQUEST_FULFILLED,
        STATUS_REQUEST_COMPLETED,
        STATUS_REQUEST_CANCELLED,
    },
    STATUS_REQUEST_FULFILLED: {STATUS_REQUEST_COMPLETED},
    STATUS_REQUEST_COMPLETED: set(),
    STATUS_REQUEST_CANCELLED: set(),
}


def create_relief_request(
    user_id,
    category,
    quantity,
    urgency="Medium",
    latitude=None,
    longitude=None,
    incident_id=None,
    location=None,
):
    """Validate and persist a relief request for an existing user."""
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise ValueError("Invalid user_id")

    user = db.session.get(User, user_id)
    if not user:
        raise ValueError("User not found")

    if category is not None and not isinstance(category, str):
        raise ValueError("category must be a string")
    category = (category or "").strip()
    if not category:
        raise ValueError("category is required")
    if category not in VALID_CATEGORIES:
        raise ValueError(
            f"invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}"
        )

    if isinstance(quantity, bool) or (
        isinstance(quantity, float) and not quantity.is_integer()
    ):
        raise ValueError("quantity must be an integer")
    try:
        quantity = int(quantity)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("quantity must be an integer")
    if quantity <= 0:
        raise ValueError("quantity must be greater than zero")

    if urgency is not None and not isinstance(urgency, str):
        raise ValueError("urgency must be a string")
    urgency = (urgency or "Medium").strip()
    if urgency not in VALID_URGENCIES:
        raise ValueError(
            f"invalid urgency. Must be one of: {', '.join(VALID_URGENCIES)}"
        )

    if (latitude is None) != (longitude is None):
        raise ValueError("latitude and longitude must be provided together")

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
    else:
        location = str(location).strip()
        if not location:
            location = "Location coordinates unspecified"

    if incident_id in (None, ""):
        incident_id = None
    else:
        if isinstance(incident_id, bool) or (
            isinstance(incident_id, float) and not incident_id.is_integer()
        ):
            raise ValueError("incident_id must be an integer")
        try:
            incident_id = int(incident_id)
        except (TypeError, ValueError, OverflowError):
            raise ValueError("incident_id must be an integer")
        if not db.session.get(Incident, incident_id):
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
    """Return requests, optionally filtered by a valid status and owner."""
    query = ReliefRequest.query
    if status:
        if status not in VALID_REQUEST_STATUSES:
            raise ValueError("invalid status filter")
        query = query.filter_by(status=status)
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    return query.order_by(ReliefRequest.created_at.desc()).all()


def update_request_status(request_id, new_status, actor_id=None):
    """Apply a validated status transition to a relief request."""
    if new_status not in VALID_REQUEST_STATUSES:
        raise ValueError(
            f"invalid status. Must be one of: {', '.join(VALID_REQUEST_STATUSES)}"
        )

    req = db.session.get(ReliefRequest, request_id)
    if not req:
        raise ValueError("Relief request not found")

    if new_status == req.status:
        return req
    allowed = REQUEST_STATUS_TRANSITIONS.get(req.status, set())
    if new_status not in allowed:
        raise ValueError(
            f"Invalid request status transition: {req.status} -> {new_status}"
        )

    req.status = new_status
    db.session.commit()
    log_action(
        user_id=actor_id,
        action=ACTION_UPDATE_REQUEST_STATUS,
        entity_type="ReliefRequest",
        entity_id=req.request_id,
    )
    return req


def _requests_visible_to(user, status=None, requested_user_id=None):
    """Apply role-based visibility to relief request collections."""
    if user.role in (ROLE_ADMIN, ROLE_COORDINATOR):
        return list_relief_requests(status=status, user_id=requested_user_id)

    if user.role == ROLE_VICTIM:
        if requested_user_id is not None and requested_user_id != user.user_id:
            return []
        return list_relief_requests(status=status, user_id=user.user_id)

    if user.role == ROLE_VOLUNTEER:
        if requested_user_id is not None:
            raise PermissionError("Volunteers cannot filter requests by another user")
        if status and status not in VALID_REQUEST_STATUSES:
            raise ValueError("invalid status filter")
        query = ReliefRequest.query.join(Assignment).filter(
            Assignment.volunteer_id == user.user_id
        )
        if status:
            query = query.filter(ReliefRequest.status == status)
        return query.order_by(ReliefRequest.created_at.desc()).all()

    raise PermissionError("Insufficient permissions to view relief requests")


def _can_view_request(user, req):
    if user.role in (ROLE_ADMIN, ROLE_COORDINATOR):
        return True
    if user.role == ROLE_VICTIM:
        return req.user_id == user.user_id
    if user.role == ROLE_VOLUNTEER:
        return Assignment.query.filter_by(
            request_id=req.request_id, volunteer_id=user.user_id
        ).first() is not None
    return False


@requests_bp.post("/")
@login_required
def create_request_route():
    data = request.get_json(silent=True)
    if data is None:
        data = request.form
    if not hasattr(data, "get"):
        return jsonify({"error": "Request body must be a JSON object or form data"}), 400
    current_user = db.session.get(User, session.get("user_id"))
    if current_user is None:
        session.clear()
        return jsonify({"error": "Authentication required"}), 401

    # A Victim or other ordinary user cannot submit a request on behalf of
    # another account by forging user_id in the request body. Coordinators
    # and Admins may use the existing requester selector in the HTML workflow.
    target_user_id = current_user.user_id
    supplied_user_id = data.get("user_id")
    if current_user.role in (ROLE_ADMIN, ROLE_COORDINATOR) and supplied_user_id:
        target_user_id = supplied_user_id

    try:
        if current_user.role not in (ROLE_VICTIM, ROLE_COORDINATOR, ROLE_ADMIN):
            return jsonify({"error": "Insufficient permissions"}), 403
        req = create_relief_request(
            user_id=target_user_id,
            category=data.get("category"),
            quantity=data.get("quantity"),
            urgency=data.get("urgency", "Medium"),
            latitude=(data.get("latitude") if data.get("latitude") not in (None, "") else None),
            longitude=(data.get("longitude") if data.get("longitude") not in (None, "") else None),
            incident_id=data.get("incident_id") or None,
            location=data.get("location"),
        )
        if request.is_json or request.headers.get("Accept") == "application/json":
            return jsonify({"message": "Relief request submitted", "request": req.to_dict()}), 201
        visible_requests = _requests_visible_to(current_user)
        users = User.query.all() if current_user.role in (ROLE_ADMIN, ROLE_COORDINATOR) else [current_user]
        return render_template(
            "requests.html",
            requests=[item.to_dict() for item in visible_requests],
            users=users,
            message="Relief request submitted",
        ), 200
    except ValueError as exc:
        db.session.rollback()
        if request.is_json or request.headers.get("Accept") == "application/json":
            return jsonify({"error": str(exc)}), 400
        visible_requests = _requests_visible_to(current_user)
        users = User.query.all() if current_user.role in (ROLE_ADMIN, ROLE_COORDINATOR) else [current_user]
        return render_template(
            "requests.html",
            requests=[item.to_dict() for item in visible_requests],
            users=users,
            error=str(exc),
        ), 400
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403


@requests_bp.get("/")
@login_required
def list_requests_route():
    status = request.args.get("status")
    user_id = request.args.get("user_id", type=int)
    current_user = db.session.get(User, session.get("user_id"))
    if current_user is None:
        session.clear()
        return jsonify({"error": "Authentication required"}), 401
    if current_user.role not in (ROLE_VICTIM, ROLE_VOLUNTEER, ROLE_COORDINATOR, ROLE_ADMIN):
        return jsonify({"error": "Insufficient permissions"}), 403
    try:
        requests_list = _requests_visible_to(
            current_user, status=status, requested_user_id=user_id
        )
        requests_dict = [item.to_dict() for item in requests_list]
        if request.is_json or request.args.get("format") == "json" or request.headers.get("Accept") == "application/json":
            return jsonify({"requests": requests_dict, "total_requests": len(requests_list)}), 200
        users = User.query.all() if current_user.role in (ROLE_ADMIN, ROLE_COORDINATOR) else [current_user]
        return render_template("requests.html", requests=requests_dict, users=users), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403


@requests_bp.get("/<int:request_id>")
@login_required
def get_request_route(request_id):
    current_user = db.session.get(User, session.get("user_id"))
    req = db.session.get(ReliefRequest, request_id)
    if current_user is None:
        session.clear()
        return jsonify({"error": "Authentication required"}), 401
    if not req:
        return jsonify({"error": "Relief request not found"}), 404
    if not _can_view_request(current_user, req):
        return jsonify({"error": "Insufficient permissions"}), 403
    return jsonify({"request": req.to_dict()}), 200


@requests_bp.patch("/<int:request_id>/status")
@login_required
@roles_required("Coordinator", "Admin")
def update_request_status_route(request_id):
    current_user = db.session.get(User, session.get("user_id"))
    if current_user is None:
        session.clear()
        return jsonify({"error": "Authentication required"}), 401
    if current_user.role not in (ROLE_ADMIN, ROLE_COORDINATOR):
        return jsonify({"error": "Insufficient permissions"}), 403

    data = request.get_json(silent=True)
    if data is None:
        data = request.form
    if not hasattr(data, "get"):
        return jsonify({"error": "Request body must be a JSON object or form data"}), 400
    new_status = data.get("status")
    try:
        req = update_request_status(
            request_id=request_id,
            new_status=new_status,
            actor_id=current_user.user_id,
        )
        return jsonify({"message": "Request status updated", "request": req.to_dict()}), 200
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400
