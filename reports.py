"""Coordinator/Admin reporting endpoints for disaster relief operations."""
from datetime import datetime, timezone
import io
import csv

from flask import Blueprint, jsonify, request, Response
from sqlalchemy import func

from auth import login_required, roles_required
from constants import ROLE_ADMIN
from extensions import db
from models import Assignment, Incident, InventoryItem, ReliefRequest
from csv_safety import safe_csv_text

reports_bp = Blueprint("reports", __name__)


def generate_relief_report(start_date=None, end_date=None):
    """Generate relief report dictionary."""
    request_total = ReliefRequest.query.count()
    incident_total = Incident.query.count()
    inventory_total = InventoryItem.query.count()
    inventory_quantity = db.session.query(
        func.coalesce(func.sum(InventoryItem.quantity), 0)
    ).scalar() or 0
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "requests_total": request_total,
        "incidents_total": incident_total,
        "inventory_total": inventory_total,
        "inventory_units": int(inventory_quantity),
    }


def generate_relief_requests_csv():
    """
    Generate CSV string for relief requests data (SRS FR 3.7.2).
    Includes appropriate column headers and correctly formatted values.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "request_id",
        "user_id",
        "category",
        "quantity",
        "urgency",
        "location",
        "latitude",
        "longitude",
        "incident_id",
        "status",
        "created_at",
    ])
    requests = ReliefRequest.query.order_by(ReliefRequest.request_id.asc()).all()
    for req in requests:
        writer.writerow([
            req.request_id,
            req.user_id,
            safe_csv_text(req.category),
            req.quantity,
            req.urgency,
            safe_csv_text(req.location),
            req.latitude if req.latitude is not None else "",
            req.longitude if req.longitude is not None else "",
            req.incident_id if req.incident_id is not None else "",
            req.status,
            req.created_at.isoformat() + "Z" if req.created_at else "",
        ])
    return output.getvalue()


def generate_inventory_csv():
    """
    Generate CSV string for inventory stock and threshold data (SRS FR 3.7.2).
    Includes appropriate column headers and correctly formatted values.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "item_id",
        "category",
        "quantity",
        "storage_location",
        "expiry_date",
        "threshold",
        "is_low_stock",
    ])
    items = InventoryItem.query.order_by(InventoryItem.item_id.asc()).all()
    for item in items:
        writer.writerow([
            item.item_id,
            safe_csv_text(item.category),
            item.quantity,
            safe_csv_text(item.storage_location),
            item.expiry_date.isoformat() if item.expiry_date else "",
            item.threshold,
            "Yes" if item.is_low_stock() else "No",
        ])
    return output.getvalue()


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


@reports_bp.get("/export/relief-requests")
@reports_bp.get("/export/requests")
@login_required
@roles_required(ROLE_ADMIN)
def export_relief_requests_csv_route():
    """Admin-only CSV export for relief requests (FR 3.7.2)."""
    csv_data = generate_relief_requests_csv()
    response = Response(csv_data, mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=relief_requests.csv"
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@reports_bp.get("/export/inventory")
@login_required
@roles_required(ROLE_ADMIN)
def export_inventory_csv_route():
    """Admin-only CSV export for warehouse inventory (FR 3.7.2)."""
    csv_data = generate_inventory_csv()
    response = Response(csv_data, mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=inventory.csv"
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
