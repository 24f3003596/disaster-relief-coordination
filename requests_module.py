from extensions import db
from models import ReliefRequest, User
from constants import REQUEST_CATEGORIES, URGENCY_LEVELS, REQUEST_STATUSES

def create_relief_request(user_id, category, quantity, urgency, latitude, longitude, incident_id=None):
    if db.session.get(User,user_id) is None: raise ValueError("Requester not found")
    if category not in REQUEST_CATEGORIES: raise ValueError("Invalid request category")
    if int(quantity)<=0: raise ValueError("Quantity must be positive")
    if urgency not in URGENCY_LEVELS: raise ValueError("Invalid urgency")
    if not (-90<=float(latitude)<=90) or not (-180<=float(longitude)<=180): raise ValueError("Invalid coordinates")
    r=ReliefRequest(user_id=user_id,category=category,quantity=int(quantity),urgency=urgency,latitude=float(latitude),longitude=float(longitude),incident_id=incident_id,status="Pending")
    db.session.add(r); db.session.commit(); return r

def list_relief_requests(status=None,user_id=None):
    q=ReliefRequest.query
    if status: q=q.filter_by(status=status)
    if user_id is not None: q=q.filter_by(user_id=user_id)
    return q.order_by(ReliefRequest.created_at.asc()).all()

def update_request_status(request_id,new_status,actor_id):
    actor=db.session.get(User,actor_id)
    if not actor or actor.role not in ("Coordinator","Admin"): raise PermissionError("Coordinator or Admin required")
    if new_status not in REQUEST_STATUSES: raise ValueError("Invalid request status")
    r=db.session.get(ReliefRequest,request_id)
    if not r: raise ValueError("Request not found")
    r.status=new_status; db.session.commit(); return r
