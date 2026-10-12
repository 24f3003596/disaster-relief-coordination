from datetime import datetime
from flask import Flask, jsonify, request, redirect, url_for

from extensions import db
from auth import auth_bp
from incidents import incidents_bp
from reports import reports_bp
from inventory import inventory_bp
from requests_module import requests_bp
from dashboard import dashboard_bp
from audit import audit_bp
from assignments import assignments_bp
from volunteers import volunteers_bp
from notifications import notifications_bp

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="disaster-relief-secret-key-review2",
        SQLALCHEMY_DATABASE_URI="sqlite:///disaster_relief.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    # Register all feature blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(incidents_bp, url_prefix="/incidents")
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")
    app.register_blueprint(requests_bp, url_prefix="/requests")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(audit_bp, url_prefix="/audit")
    app.register_blueprint(assignments_bp, url_prefix="/assignments")
    app.register_blueprint(volunteers_bp, url_prefix="/volunteers")
    app.register_blueprint(notifications_bp, url_prefix="/notifications")

    @app.get("/")
    def index():
        # If requested by browser HTML, redirect to interactive dashboard
        if "text/html" in request.headers.get("Accept", ""):
            return redirect(url_for("dashboard.dashboard_page"))
        return jsonify({
            "project": "Disaster Relief Resource Coordination System",
            "version": "1.0.0",
            "review": "Project Review 2 increment",
            "status": "operational",
            "endpoints": {
                "dashboard": "/dashboard/",
                "dashboard_summary": "GET /dashboard/summary",
                "auth": {
                    "register": "POST /auth/register",
                    "login": "POST /auth/login",
                    "logout": "POST /auth/logout",
                    "me": "GET /auth/me",
                    "update_role": "PATCH /auth/users/<id>/role",
                },
                "inventory": {
                    "create": "POST /inventory/",
                    "list": "GET /inventory/",
                    "detail": "GET /inventory/<id>",
                    "low_stock": "GET /inventory/low-stock",
                },
                "relief_requests": {
                    "create": "POST /requests/",
                    "list": "GET /requests/",
                    "detail": "GET /requests/<id>",
                    "update_status": "PATCH /requests/<id>/status",
                },
                "assignments": {
                    "allocate": "POST /assignments/allocate",
                    "list": "GET /assignments/",
                    "update_status": "PATCH /assignments/<id>/status",
                    "complete": "POST /assignments/<id>/complete",
                },
                "incidents": {
                    "create": "POST /incidents/",
                    "list": "GET /incidents/",
                    "affected_areas": "GET /incidents/affected-areas",
                },
                "volunteers": {
                    "list": "GET /volunteers/",
                    "assignments": "GET /volunteers/<id>/assignments",
                },
                "notifications": {
                    "list": "GET /notifications/",
                    "mark_read": "PATCH /notifications/<id>/read",
                    "broadcast": "POST /notifications/broadcast",
                },
                "reports": {
                    "summary": "GET /reports/",
                },
                "audit": {
                    "logs": "GET /audit/",
                },
            },
        })

    with app.app_context():
        import models  # noqa: F401
        db.create_all()

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
