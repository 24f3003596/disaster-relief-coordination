from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, session, has_request_context

from extensions import db
from models import Assignment, ReliefRequest, InventoryItem, User, utc_now
from auth import login_required, roles_required
from audit import log_action
from notifications import create_notification
from constants import (
    ROLE_VOLUNTEER,
    STATUS_REQUEST_PENDING,
    STATUS_REQUEST_ALLOCATED,
    STATUS_REQUEST_COMPLETED,
    STATUS_ASSIGNMENT_ASSIGNED,
    STATUS_ASSIGNMENT_COMPLETED,
    VALID_ASSIGNMENT_STATUSES,
    ACTION_ALLOCATE_RESOURCE,
    ACTION_COMPLETE_ASSIGNMENT,
    NOTIFICATION_ASSIGNMENT,
    NOTIFICATION_STATUS_UPDATE,
)

assignments_bp = Blueprint("assignments", __name__)

def allocate_request(request_id, volunteer_id, item_id, quantity_assigned=None):
    """
    Allocate an inventory item to a relief request and assign a volunteer.
    Executed in a single atomic database transaction:
    - Verifies request is Pending
    - Verifies volunteer exists and has Volunteer role
    - Verifies sufficient inventory exists
    - Deducts inventory, creates Assignment, updates request status to Allocated
    - Generates notifications for volunteer and request owner
    - Logs audit action
    """
    req = db.session.get(ReliefRequest, request_id)
    if not req:
        raise ValueError("Relief request not found")
    if req.status != STATUS_REQUEST_PENDING:
        raise ValueError(f"Request is not pending (current status: {req.status})")

    volunteer = db.session.get(User, volunteer_id)
    if not volunteer:
        raise ValueError("Volunteer not found")
    if volunteer.role != ROLE_VOLUNTEER:
        raise ValueError("Selected user is not a registered Volunteer")

    item = db.session.get(InventoryItem, item_id)
    if not item:
        raise ValueError("Inventory item not found")

    alloc_qty = quantity_assigned if quantity_assigned is not None else req.quantity
    try:
        alloc_qty = int(alloc_qty)
    except (TypeError, ValueError):
        raise ValueError("quantity_assigned must be an integer")
    if alloc_qty <= 0:
        raise ValueError("quantity_assigned must be positive")

    if item.quantity < alloc_qty:
        raise ValueError(
            f"Insufficient stock for {item.category}. Available: {item.quantity}, Requested: {alloc_qty}"
        )

    # Atomic operations within transaction
    item.quantity -= alloc_qty
    req.status = STATUS_REQUEST_ALLOCATED

    assignment = Assignment(
        request_id=request_id,
        volunteer_id=volunteer_id,
        item_id=item_id,
        quantity_assigned=alloc_qty,
        status=STATUS_ASSIGNMENT_ASSIGNED,
        assigned_at=utc_now(),
    )
    db.session.add(assignment)

    # Flush to generate assignment.task_id if needed
    db.session.flush()

    # Notifications
    create_notification(
        user_id=volunteer_id,
        message=f"New task assigned: Deliver {alloc_qty} {item.category} to {req.location}.",
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

def list_assignments(status=None, volunteer_id=None):
    """Retrieve assignments with optional filters."""
    query = Assignment.query
    if status:
        if status not in VALID_ASSIGNMENT_STATUSES:
            raise ValueError("invalid status filter")
        query = query.filter_by(status=status)
    if volunteer_id:
        query = query.filter_by(volunteer_id=volunteer_id)

    return query.order_by(Assignment.assigned_at.desc()).all()

def update_assignment_status(task_id, new_status):
    """Update task assignment status."""
    if new_status not in VALID_ASSIGNMENT_STATUSES:
        raise ValueError(f"invalid status. Must be one of: {', '.join(VALID_ASSIGNMENT_STATUSES)}")

    assignment = db.session.get(Assignment, task_id)
    if not assignment:
        raise ValueError("Assignment not found")

    assignment.status = new_status
    if new_status == STATUS_ASSIGNMENT_COMPLETED:
        assignment.completed_at = utc_now()
        if assignment.request:
            assignment.request.status = STATUS_REQUEST_COMPLETED

    db.session.commit()
    return assignment

def complete_assignment(task_id):
    """Mark an assignment as completed and resolve request."""
    return update_assignment_status(task_id, STATUS_ASSIGNMENT_COMPLETED)

@assignments_bp.post("/allocate")
@login_required
@roles_required("Coordinator", "Admin")
def allocate_route():
    data = request.get_json(silent=True) or {}
    try:
        assignment = allocate_request(
            request_id=data.get("request_id"),
            volunteer_id=data.get("volunteer_id"),
            item_id=data.get("item_id"),
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
    try:
        tasks = list_assignments(status=status, volunteer_id=volunteer_id)
        return jsonify({"assignments": [t.to_dict() for t in tasks]}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

@assignments_bp.patch("/<int:task_id>/status")
@login_required
def update_status_route(task_id):
    data = request.get_json(silent=True) or {}
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
    try:
        task = complete_assignment(task_id)
        return jsonify({"message": "Assignment completed", "assignment": task.to_dict()}), 200
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 400
