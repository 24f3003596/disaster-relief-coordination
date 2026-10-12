"""Routes package: modular blueprints for all system features."""
from routes.auth import auth_bp
from routes.incidents import incidents_bp
from routes.inventory import inventory_bp
from routes.requests_module import requests_bp
from routes.assignments import assignments_bp
from routes.notifications import notifications_bp
from routes.volunteers import volunteers_bp
from routes.reports import reports_bp
from routes.dashboard import dashboard_bp
from routes.audit import audit_bp

__all__ = [
    "auth_bp",
    "incidents_bp",
    "inventory_bp",
    "requests_bp",
    "assignments_bp",
    "notifications_bp",
    "volunteers_bp",
    "reports_bp",
    "dashboard_bp",
    "audit_bp",
]
