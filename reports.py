from datetime import datetime
from flask import Blueprint, jsonify, request

from extensions import db
from models import ReliefRequest, Assignment, InventoryItem, Incident
from auth import login_required, roles_required
from constants import STATUS_REQUEST_COMPLETED, STATUS_REQUEST_PENDING, STATUS_REQUEST_ALLOCATED

reports_bp = Blueprint("reports", __name__)

def generate_relief_report(start_date=None, end_date=None):
    """
    Generate comprehensive relief report summarizing requests,
    assignments, inventory status, and incidents.
    """
    request_query = ReliefRequest.query
    if start_date:
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        request_query = request_query.filter(ReliefRequest.created_at >= start_date)
    if end_date:
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
        request_query = request_query.filter(ReliefRequest.created_at <= end_date)

    requests = request_query.all()
    total_requests = len(requests)
    completed_requests = sum(1 for r in requests if r.status == STATUS_REQUEST_COMPLETED)
    pending_requests = sum(1 for r in requests if r.status == STATUS_REQUEST_PENDING)
    allocated_requests = sum(1 for r in requests if r.status == STATUS_REQUEST_ALLOCATED)

    inventory_items = InventoryItem.query.all()
    total_stock_units = sum(item.quantity for item in inventory_items)
    low_stock_items = [item.to_dict() for item in inventory_items if item.is_low_stock()]

    incidents = Incident.query.all()

    return {
        "generated_at": datetime.now().isoformat() + "Z",
        "date_range": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        },
        "summary": {
            "total_requests": total_requests,
            "pending_requests": pending_requests,
            "allocated_requests": allocated_requests,
            "completed_requests": completed_requests,
            "total_inventory_items": len(inventory_items),
            "total_stock_units": total_stock_units,
            "low_stock_count": len(low_stock_items),
            "total_incidents": len(incidents),
        },
        "low_stock_alerts": low_stock_items,
    }

@reports_bp.get("/")
@login_required
@roles_required("Coordinator", "Admin")
def get_report_route():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    try:
        report = generate_relief_report(start_date=start_date, end_date=end_date)
        return jsonify({"report": report}), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
