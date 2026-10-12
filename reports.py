"""Coordinator/Admin reporting endpoints for disaster relief operations."""
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from auth import roles_required
from extensions import db
from models import Assignment, Incident, InventoryItem, ReliefRequest

reports_bp = Blueprint("reports", __name__)


@reports_bp.get("/summary")
@roles_required("Coordinator", "Admin")
def summary_report():
    """Return summary counts for requests, incidents, inventory and assignments."""
    request_total = ReliefRequest.query.count()
    request_by_status = db.session.query(
        ReliefRequest.status, func.count(ReliefRequest.request_id)
    ).group_by(ReliefRequest.status).all()
    request_by_category = db.session.query(
        ReliefRequest.category, func.count(ReliefRequest.request_id)
    ).group_by(ReliefRequest.category).all()

    incident_total = Incident.query.count()
    incident_by_status = db.session.query(
        Incident.status, func.count(Incident.incident_id)
    ).group_by(Incident.status).all()
    incident_by_severity = db.session.query(
        Incident.severity, func.count(Incident.incident_id)
    ).group_by(Incident.severity).all()

    inventory_total = InventoryItem.query.count()
    inventory_quantity = db.session.query(
        func.coalesce(func.sum(InventoryItem.quantity), 0)
    ).scalar()
    low_stock_count = InventoryItem.query.filter(
        InventoryItem.quantity <= InventoryItem.threshold
    ).count()

    assignment_total = Assignment.query.count()
    assignment_by_status = db.session.query(
        Assignment.status, func.count(Assignment.task_id)
    ).group_by(Assignment.status).all()

    return jsonify({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "relief_requests": {
            "total": request_total,
            "by_status": {str(key): count for key, count in request_by_status},
            "by_category": {str(key): count for key, count in request_by_category},
        },
        "incidents": {
            "total": incident_total,
            "by_status": {str(key): count for key, count in incident_by_status},
            "by_severity": {str(key): count for key, count in incident_by_severity},
        },
        "inventory": {
            "item_types": inventory_total,
            "total_quantity": int(inventory_quantity or 0),
            "low_stock_item_types": low_stock_count,
        },
        "assignments": {
            "total": assignment_total,
            "by_status": {str(key): count for key, count in assignment_by_status},
        },
    }), 200


@reports_bp.get("/relief-requests")
@roles_required("Coordinator", "Admin")
def relief_request_report():
    """List relief requests, optionally filtered by exact status/category."""
    query = ReliefRequest.query
    status = request.args.get("status", type=str)
    category = request.args.get("category", type=str)

    if status:
        query = query.filter(ReliefRequest.status == status.strip())
    if category:
        query = query.filter(ReliefRequest.category.ilike(category.strip()))

    rows = query.order_by(ReliefRequest.created_at.desc(), ReliefRequest.request_id.desc()).all()
    return jsonify({
        "count": len(rows),
        "filters": {"status": status, "category": category},
        "relief_requests": [
            {
                "request_id": row.request_id,
                "user_id": row.user_id,
                "category": row.category,
                "quantity": row.quantity,
                "urgency": row.urgency,
                "location": row.location,
                "status": row.status,
                "created_at": row.created_at.isoformat() + "Z",
            }
            for row in rows
        ],
    }), 200
