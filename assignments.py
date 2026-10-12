from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
from extensions import db
from models import Assignment, ReliefRequest, InventoryItem, User
from constants import ASSIGNMENT_STATUSES, REQUEST_STATUSES
from notifications import create_notification

def allocate_request(request_id, volunteer_id, item_id):
    """Allocate the full requested quantity atomically; rolls back on any failure."""
    try:
        request = db.session.get(ReliefRequest, request_id)
        volunteer = db.session.get(User, volunteer_id)
        item = db.session.get(InventoryItem, item_id)
        if request is None: raise ValueError("Relief request not found")
        if volunteer is None or volunteer.role != "Volunteer": raise ValueError("A valid Volunteer user is required")
        if item is None: raise ValueError("Inventory item not found")
        if request.status != "Pending": raise ValueError("Only pending requests can be allocated")
        if request.quantity <= 0: raise ValueError("Requested quantity must be positive")
        if item.category.lower() != request.category.lower(): raise ValueError("Inventory category must match request category")
        if item.quantity < request.quantity: raise ValueError("Insufficient inventory stock")
        if any(a.request_id == request_id for a in Assignment.query.all()): raise ValueError("Request already has an assignment")
        assignment = Assignment(request_id=request_id, volunteer_id=volunteer_id, item_id=item_id, quantity_assigned=request.quantity, status="Assigned")
        item.quantity -= request.quantity
        request.status = "Assigned"
        db.session.add(assignment)
        db.session.flush()
        create_notification(volunteer_id, f"You have been assigned request #{request_id}: {request.category}, quantity {request.quantity}.", "Assignment")
        db.session.commit()
        return assignment
    except Exception:
        db.session.rollback()
        raise

def list_assignments(status=None, volunteer_id=None):
    q = Assignment.query
    if status: q = q.filter_by(status=status)
    if volunteer_id is not None: q = q.filter_by(volunteer_id=volunteer_id)
    return q.order_by(Assignment.assigned_at.desc()).all()

def update_assignment_status(task_id, new_status):
    if new_status not in ASSIGNMENT_STATUSES: raise ValueError("Invalid assignment status")
    task = db.session.get(Assignment, task_id)
    if task is None: raise ValueError("Assignment not found")
    task.status = new_status
    if new_status == "Completed":
        task.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        task.relief_request.status = "Fulfilled"
    elif new_status in ("Accepted", "In Progress"):
        task.relief_request.status = "In Progress"
    db.session.commit()
    return task

def complete_assignment(task_id):
    return update_assignment_status(task_id, "Completed")
