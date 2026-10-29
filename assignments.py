from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, session, has_request_context

from extensions import db
from models import Assignment, ReliefRequest, InventoryItem, User, utc_now
from auth import login_required, roles_required
from audit import log_action
from notifications import create_notification
from constants import (
    ROLE_VOLUNTEER,
    ASSIGNMENT_STATUSES,
    VALID_ASSIGNMENT_STATUSES,
    STATUS_ASSIGNMENT_ASSIGNED,
    STATUS_ASSIGNMENT_COMPLETED,
    STATUS_REQUEST_PENDING,
    STATUS_REQUEST_ASSIGNED,
    STATUS_REQUEST_FULFILLED,
    ACTION_ALLOCATE_RESOURCE,
    ACTION_COMPLETE_ASSIGNMENT,
    NOTIFICATION_ASSIGNMENT,
    NOTIFICATION_STATUS_UPDATE,
)

assignments_bp = Blueprint("assignments", __name__)

def allocate_request(request_id, volunteer_id, item_id, quantity_assigned=None):
    """
    Allocate an inventory item to a relief request and assign a volunteer atomically.
    Validates request, volunteer role, inventory matching and sufficient stock.
    """
    try:
        req = db.session.get(ReliefRequest, request_id)
        if req is None:
            raise ValueError("Relief request not found")

        volunteer = db.session.get(User, volunteer_id)
        if volunteer is None or volunteer.role != ROLE_VOLUNTEER:
            raise ValueError("A valid Volunteer user is required")

        item = db.session.get(InventoryItem, item_id)
        if item is None:
            raise ValueError("Inventory item not found")

        if req.status != STATUS_REQUEST_PENDING:
            raise ValueError("Only pending requests can be allocated")

        if req.quantity <= 0:
            raise ValueError("Requested quantity must be positive")

        # Category compatibility check (exact or substring match)
        item_cat = (item.category or "").strip().lower()
        req_cat = (req.category or "").strip().lower()
        if item_cat != req_cat and item_cat not in req_cat and req_cat not in item_cat:
            raise ValueError("Inventory category must match request category")

        alloc_qty = quantity_assigned if quantity_assigned is not None else req.quantity
        try:
            alloc_qty = int(alloc_qty)
        except (TypeError, ValueError):
            raise ValueError("quantity_assigned must be an integer")
        if alloc_qty <= 0:
            raise ValueError("quantity_assigned must be positive")

        if item.quantity < alloc_qty:
            raise ValueError("Insufficient inventory stock")

        if Assignment.query.filter_by(request_id=request_id).first():
            raise ValueError("Request already has an assignment")

        # Atomic stock deduction and status transition
        item.quantity -= alloc_qty
        req.status = STATUS_REQUEST_ASSIGNED

        assignment = Assignment(
            request_id=request_id,
            volunteer_id=volunteer_id,
            item_id=item_id,
            quantity_assigned=alloc_qty,
            status=STATUS_ASSIGNMENT_ASSIGNED,
            assigned_at=utc_now(),
        )
        db.session.add(assignment)
        db.session.flush()

        # Dual notifications
        create_notification(
            user_id=volunteer_id,
            message=f"You have been assigned request #{request_id}: {req.category}, quantity {alloc_qty}.",
            notification_type=NOTIFICATION_ASSIGNMENT,
        )
        create_notification(
            user_id=req.user_id,
            message=f"Your request #{req.request_id} for {req.category} has been allocated to volunteer {volunteer.name}.",
            notification_type=NOTIFICATION_STATUS_UPDATE,
        )

        # Audit log
        actor_id = None
        if has_request_context() and "user_id" in session:
            actor_id = session.get("user_id")
        log_action(
            user_id=actor_id,
            action=ACTION_ALLOCATE_RESOURCE,
            entity_type="Assignment",
            entity_id=assignment.task_id,
        )

        db.session.commit()
        return assignment
    except Exception:
        db.session.rollback()
        raise

def list_assignments(status=None, volunteer_id=None):
    """Retrieve assignments with optional filters."""
    query = Assignment.query
    if status:
        query = query.filter_by(status=status)
    if volunteer_id is not None:
        query = query.filter_by(volunteer_id=volunteer_id)

    return query.order_by(Assignment.assigned_at.desc()).all()

def update_assignment_status(task_id, new_status):
    """Update task assignment status and synchronize request status."""
    if new_status not in VALID_ASSIGNMENT_STATUSES:
        raise ValueError("Invalid assignment status")

    assignment = db.session.get(Assignment, task_id)
    if assignment is None:
        raise ValueError("Assignment not found")

    assignment.status = new_status
    if new_status == STATUS_ASSIGNMENT_COMPLETED:
        assignment.completed_at = utc_now()
        if assignment.relief_request:
            assignment.relief_request.status = STATUS_REQUEST_FULFILLED
    elif new_status in ("Accepted", "In Progress"):
        if assignment.relief_request:
            assignment.relief_request.status = "In Progress"

    actor_id = None
    if has_request_context() and "user_id" in session:
        actor_id = session.get("user_id")
    log_action(
        user_id=actor_id,
        action=ACTION_COMPLETE_ASSIGNMENT if new_status == STATUS_ASSIGNMENT_COMPLETED else "UPDATE_ASSIGNMENT_STATUS",
        entity_type="Assignment",
        entity_id=assignment.task_id,
    )

    db.session.commit()
    return assignment

def complete_assignment(task_id):
    """Mark an assignment as completed."""
    return update_assignment_status(task_id, STATUS_ASSIGNMENT_COMPLETED)

@assignments_bp.post("/allocate")
@login_required
@roles_required("Coordinator", "Admin")
def allocate_route():
    data = request.get_json(silent=True) or request.form or {}
    try:
        assignment = allocate_request(
            request_id=int(data.get("request_id")),
            volunteer_id=int(data.get("volunteer_id")),
            item_id=int(data.get("item_id")),
            quantity_assigned=data.get("quantity_assigned"),
        )
        return jsonify({"message": "Resource allocated successfully", "assignment": assignment.to_dict()}), 201
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400

@assignments_bp.get("/")
@login_required
def list_assignments_route():
    status = request.args.get("status")
    volunteer_id = request.args.get("volunteer_id", type=int)
    actor = db.session.get(User, session.get("user_id"))
    if actor is None:
        session.clear()
        return jsonify({"error": "Authentication required"}), 401
    if actor.role == ROLE_VOLUNTEER:
        volunteer_id = actor.user_id
    elif actor.role not in ("Coordinator", "Admin"):
        return jsonify({"error": "Insufficient permissions"}), 403
    tasks = list_assignments(status=status, volunteer_id=volunteer_id)
    return jsonify({"assignments": [t.to_dict() for t in tasks]}), 200

@assignments_bp.patch("/<int:task_id>/status")
@login_required
def update_status_route(task_id):
    actor = db.session.get(User, session.get("user_id"))
    assignment = db.session.get(Assignment, task_id)
    if assignment is None:
        return jsonify({"error": "Assignment not found"}), 404
    if actor is None:
        return jsonify({"error": "Authentication required"}), 401
    if actor.role == ROLE_VOLUNTEER:
        if assignment.volunteer_id != actor.user_id:
            return jsonify({"error": "Insufficient permissions"}), 403
    elif actor.role not in ("Coordinator", "Admin"):
        return jsonify({"error": "Insufficient permissions"}), 403
    data = request.get_json(silent=True) or request.form or {}
    new_status = data.get("status")
    try:
        task = update_assignment_status(task_id, new_status)
        return jsonify({"message": "Assignment status updated", "assignment": task.to_dict()}), 200
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400

@assignments_bp.post("/<int:task_id>/complete")
@login_required
def complete_route(task_id):
    actor = db.session.get(User, session.get("user_id"))
    assignment = db.session.get(Assignment, task_id)
    if assignment is None:
        return jsonify({"error": "Assignment not found"}), 404
    if actor is None:
        return jsonify({"error": "Authentication required"}), 401
    if actor.role == ROLE_VOLUNTEER:
        if assignment.volunteer_id != actor.user_id:
            return jsonify({"error": "Insufficient permissions"}), 403
    elif actor.role not in ("Coordinator", "Admin"):
        return jsonify({"error": "Insufficient permissions"}), 403
    try:
        task = complete_assignment(task_id)
        return jsonify({"message": "Assignment completed", "assignment": task.to_dict()}), 200
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400
