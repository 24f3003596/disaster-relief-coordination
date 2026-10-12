import csv, io
from models import ReliefRequest

def generate_relief_report(start_date=None,end_date=None):
    q=ReliefRequest.query
    if start_date: q=q.filter(ReliefRequest.created_at>=start_date)
    if end_date: q=q.filter(ReliefRequest.created_at<=end_date)
    rows=q.order_by(ReliefRequest.created_at.asc()).all()
    return [{"request_id":r.request_id,"user_id":r.user_id,"category":r.category,"quantity":r.quantity,"urgency":r.urgency,"status":r.status,"created_at":r.created_at.isoformat()+"Z"} for r in rows]
