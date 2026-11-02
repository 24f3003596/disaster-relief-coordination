import io
import csv
from flask import Blueprint, jsonify, render_template, request, Response

from sqlalchemy import func
from extensions import db
from models import ReliefRequest, InventoryItem, Incident, User, Assignment, AuditLog
from auth import login_required, roles_required
from csv_safety import safe_csv_text
from constants import (
    STATUS_REQUEST_PENDING,
    STATUS_REQUEST_ALLOCATED,
    STATUS_REQUEST_ASSIGNED,
    STATUS_REQUEST_FULFILLED,
    STATUS_REQUEST_COMPLETED,
    STATUS_INCIDENT_OPEN,
    STATUS_INCIDENT_IN_PROGRESS,
    ROLE_VOLUNTEER,
    ROLE_ADMIN,
    STATUS_ASSIGNMENT_ASSIGNED,
    STATUS_ASSIGNMENT_ACCEPTED,
    STATUS_ASSIGNMENT_IN_PROGRESS,
    STATUS_ASSIGNMENT_COMPLETED,
)

dashboard_bp = Blueprint("dashboard", __name__)


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


def get_dashboard_summary():
    """
    Compile high-level operational metrics across requests,
    inventory, incidents, volunteers, and recent activity.

    SRS FR 3.7.1 & FR 3.7.2 Analytics Specification:
    1. Total requests & breakdowns by status and by category.
    2. Average Response Time (seconds and minutes):
       Calculated as the elapsed time from request creation (ReliefRequest.created_at)
       to initial resource assignment (Assignment.assigned_at) across all assigned requests:
           Response Time = (assigned_at - created_at)
       Zero denominators and empty datasets return 0.0 safely without exception.
    3. Resource Utilization Rate (%):
       Calculated as total allocated units divided by total system capacity
       (on-hand warehouse inventory stock plus total units assigned to field tasks):
           Utilization Rate (%) = (Total Allocated Units / (Available Stock + Total Allocated Units)) * 100
       Empty datasets and zero total capacity safely evaluate to 0.0%.
    """
    total_requests = ReliefRequest.query.count()
    pending_requests = ReliefRequest.query.filter_by(status=STATUS_REQUEST_PENDING).count()
    allocated_requests = ReliefRequest.query.filter(
        ReliefRequest.status.in_([STATUS_REQUEST_ASSIGNED, STATUS_REQUEST_ALLOCATED])
    ).count()
    completed_requests = ReliefRequest.query.filter(
        ReliefRequest.status.in_([STATUS_REQUEST_FULFILLED, STATUS_REQUEST_COMPLETED])
    ).count()

    # Request breakdown by status (SRS FR 3.7.1)
    status_counts = (
        db.session.query(ReliefRequest.status, func.count(ReliefRequest.request_id))
        .group_by(ReliefRequest.status)
        .all()
    )
    requests_by_status = {str(st): int(cnt) for st, cnt in status_counts}

    # Request breakdown by category (SRS FR 3.7.1)
    cat_counts = (
        db.session.query(ReliefRequest.category, func.count(ReliefRequest.request_id))
        .group_by(ReliefRequest.category)
        .all()
    )
    requests_by_category = {str(cat): int(cnt) for cat, cnt in cat_counts}

    all_inventory = InventoryItem.query.all()
    total_inventory_items = len(all_inventory)
    total_units_in_stock = sum(item.quantity for item in all_inventory)
    low_stock_items = [item for item in all_inventory if item.is_low_stock()]
    out_of_stock_items = [item for item in all_inventory if item.quantity == 0]

    active_incidents = Incident.query.filter(
        Incident.status.in_([STATUS_INCIDENT_OPEN, STATUS_INCIDENT_IN_PROGRESS])
    ).all()

    total_volunteers = User.query.filter_by(role=ROLE_VOLUNTEER).count()

    active_assignments = Assignment.query.filter(
        Assignment.status.in_([
            STATUS_ASSIGNMENT_ASSIGNED,
            STATUS_ASSIGNMENT_ACCEPTED,
            STATUS_ASSIGNMENT_IN_PROGRESS,
        ])
    ).count()

    recent_requests = (
        ReliefRequest.query.order_by(ReliefRequest.created_at.desc()).limit(5).all()
    )
    recent_logs = (
        AuditLog.query.order_by(AuditLog.created_at.desc()).limit(5).all()
    )

    # -------------------------------------------------------------
    # FR 3.7.1: Average Response Time Calculation
    # -------------------------------------------------------------
    # Query timestamps for requests that have received an assignment
    assigned_query = (
        db.session.query(Assignment.assigned_at, ReliefRequest.created_at)
        .join(ReliefRequest, Assignment.request_id == ReliefRequest.request_id)
        .filter(Assignment.assigned_at.isnot(None), ReliefRequest.created_at.isnot(None))
        .all()
    )
    if assigned_query:
        response_durations = [
            max(0.0, (assigned_at - req_created).total_seconds())
            for assigned_at, req_created in assigned_query
        ]
        avg_response_time_seconds = round(sum(response_durations) / len(response_durations), 2)
    else:
        avg_response_time_seconds = 0.0

    # Fulfillment / completion duration
    completed_query = (
        db.session.query(Assignment.completed_at, ReliefRequest.created_at)
        .join(ReliefRequest, Assignment.request_id == ReliefRequest.request_id)
        .filter(Assignment.completed_at.isnot(None), ReliefRequest.created_at.isnot(None))
        .all()
    )
    if completed_query:
        fulfillment_durations = [
            max(0.0, (completed_at - req_created).total_seconds())
            for completed_at, req_created in completed_query
        ]
        avg_fulfillment_time_seconds = round(sum(fulfillment_durations) / len(fulfillment_durations), 2)
    else:
        avg_fulfillment_time_seconds = 0.0

    # -------------------------------------------------------------
    # FR 3.7.1: Resource Utilization Rate Calculation
    # -------------------------------------------------------------
    total_allocated_units = int(
        db.session.query(func.coalesce(func.sum(Assignment.quantity_assigned), 0))
        .filter(Assignment.status != "Cancelled")
        .scalar() or 0
    )
    total_system_capacity = total_units_in_stock + total_allocated_units
    if total_system_capacity > 0:
        resource_utilization_rate = round(
            (total_allocated_units / float(total_system_capacity)) * 100.0, 2
        )
    else:
        resource_utilization_rate = 0.0

    return {
        "requests": {
            "total": total_requests,
            "pending": pending_requests,
            "allocated": allocated_requests,
            "completed": completed_requests,
            "by_status": requests_by_status,
            "by_category": requests_by_category,
        },
        "inventory": {
            "total_items": total_inventory_items,
            "total_units": total_units_in_stock,
            "low_stock_count": len(low_stock_items),
            "out_of_stock_count": len(out_of_stock_items),
            "low_stock_items": [item.to_dict() for item in low_stock_items[:5]],
        },
        "incidents": {
            "active_count": len(active_incidents),
            "active_incidents": [i.to_dict() for i in active_incidents[:5]],
        },
        "volunteers": {
            "total_count": total_volunteers,
            "active_assignments": active_assignments,
        },
        "analytics": {
            "average_response_time_seconds": avg_response_time_seconds,
            "average_response_time_minutes": round(avg_response_time_seconds / 60.0, 2),
            "average_fulfillment_time_seconds": avg_fulfillment_time_seconds,
            "average_fulfillment_time_minutes": round(avg_fulfillment_time_seconds / 60.0, 2),
            "resource_utilization_rate": resource_utilization_rate,
            "resource_utilization_percent": resource_utilization_rate,
            "total_allocated_units": total_allocated_units,
            "total_available_stock": total_units_in_stock,
            "total_system_capacity": total_system_capacity,
        },
        "recent_requests": [r.to_dict() for r in recent_requests],
        "recent_activity": [log.to_dict() for log in recent_logs],
    }


@dashboard_bp.get("/summary")
@login_required
@roles_required("Coordinator", ROLE_ADMIN)
def summary_api():
    """Return operational analytics only to authorized operational roles."""
    summary = get_dashboard_summary()
    return jsonify(summary), 200


@dashboard_bp.get("/export/relief-requests")
@dashboard_bp.get("/export/requests")
@login_required
@roles_required(ROLE_ADMIN)
def export_requests_csv_route():
    """Admin-only CSV export for relief requests (FR 3.7.2)."""
    csv_data = generate_relief_requests_csv()
    response = Response(csv_data, mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=relief_requests.csv"
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@dashboard_bp.get("/export/inventory")
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


@dashboard_bp.get("/")
@login_required
@roles_required("Coordinator", ROLE_ADMIN)
def dashboard_page():
    """Render the analytics dashboard for Coordinators and Admins only."""
    summary = get_dashboard_summary()
    if request.headers.get("Accept") == "application/json" or request.args.get("format") == "json":
        return jsonify(summary), 200
    return render_template("dashboard.html", summary=summary)
