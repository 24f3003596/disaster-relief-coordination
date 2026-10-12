from flask import Blueprint, jsonify, render_template, request

from extensions import db
from models import ReliefRequest, InventoryItem, Incident, User, Assignment, AuditLog
from constants import (
    STATUS_REQUEST_PENDING,
    STATUS_REQUEST_ALLOCATED,
    STATUS_REQUEST_COMPLETED,
    STATUS_INCIDENT_OPEN,
    STATUS_INCIDENT_IN_PROGRESS,
    ROLE_VOLUNTEER,
    STATUS_ASSIGNMENT_ASSIGNED,
    STATUS_ASSIGNMENT_IN_PROGRESS,
)

dashboard_bp = Blueprint("dashboard", __name__)

def get_dashboard_summary():
    """
    Compile high-level operational metrics across requests,
    inventory, incidents, volunteers, and recent activity.
    """
    total_requests = ReliefRequest.query.count()
    pending_requests = ReliefRequest.query.filter_by(status=STATUS_REQUEST_PENDING).count()
    allocated_requests = ReliefRequest.query.filter_by(status=STATUS_REQUEST_ALLOCATED).count()
    completed_requests = ReliefRequest.query.filter_by(status=STATUS_REQUEST_COMPLETED).count()

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
        Assignment.status.in_([STATUS_ASSIGNMENT_ASSIGNED, STATUS_ASSIGNMENT_IN_PROGRESS])
    ).count()

    recent_requests = (
        ReliefRequest.query.order_by(ReliefRequest.created_at.desc()).limit(5).all()
    )
    recent_logs = (
        AuditLog.query.order_by(AuditLog.created_at.desc()).limit(5).all()
    )

    return {
        "requests": {
            "total": total_requests,
            "pending": pending_requests,
            "allocated": allocated_requests,
            "completed": completed_requests,
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
        "recent_requests": [r.to_dict() for r in recent_requests],
        "recent_activity": [log.to_dict() for log in recent_logs],
    }

@dashboard_bp.get("/summary")
def summary_api():
    summary = get_dashboard_summary()
    return jsonify(summary), 200

@dashboard_bp.get("/")
def dashboard_page():
    summary = get_dashboard_summary()
    if request.headers.get("Accept") == "application/json" or request.args.get("format") == "json":
        return jsonify(summary), 200
    from flask import current_app, session, redirect, url_for, flash
    user_id = session.get("user_id")
    user = db.session.get(User, user_id) if user_id else None
    if not current_app.config.get("TESTING"):
        if not user:
            flash("Please sign in to access the coordinator dashboard.", "warning")
            return redirect(url_for("root_login"))
        if user.role not in ["Coordinator", "Admin"]:
            flash("Access denied: Coordinator permissions required for the analytics dashboard.", "danger")
            if user.role == "Volunteer":
                return redirect(url_for("root_assignments"))
            return redirect("/requests")
    return render_template("dashboard.html", summary=summary)
