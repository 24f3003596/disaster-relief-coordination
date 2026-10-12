from sqlalchemy import func
from models import ReliefRequest, InventoryItem, Assignment

def get_dashboard_summary():
    total=ReliefRequest.query.count()
    pending=ReliefRequest.query.filter_by(status="Pending").count()
    fulfilled=ReliefRequest.query.filter_by(status="Fulfilled").count()
    stock=sum(i.quantity for i in InventoryItem.query.all())
    assigned=Assignment.query.count()
    return {"total_requests":total,"pending_requests":pending,"fulfilled_requests":fulfilled,"total_stock_units":stock,"total_assignments":assigned,"fulfilment_rate":round((fulfilled/total)*100,2) if total else 0.0}
