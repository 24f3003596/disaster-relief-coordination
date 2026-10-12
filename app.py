from datetime import datetime
from flask import Flask, jsonify, request, redirect, url_for, render_template, session, flash

from extensions import db
from auth import auth_bp, register_user, authenticate_user
from incidents import incidents_bp
from reports import reports_bp
from inventory import inventory_bp, create_inventory_item, list_inventory_items
from requests_module import requests_bp, create_relief_request, list_relief_requests
from dashboard import dashboard_bp, get_dashboard_summary
from audit import audit_bp
from assignments import assignments_bp, allocate_request, list_assignments, update_assignment_status
from volunteers import volunteers_bp, list_volunteers
from notifications import notifications_bp, list_notifications, broadcast_emergency_alert
from models import User, Notification, ReliefRequest, InventoryItem, Incident

def create_app(test_config=None):
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.update(
        SECRET_KEY="disaster-relief-secret-key-review2",
        SQLALCHEMY_DATABASE_URI="sqlite:///disaster_relief.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    # Register blueprints
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

    @app.context_processor
    def inject_auth_context():
        user_id = session.get("user_id")
        user = db.session.get(User, user_id) if user_id else None
        return {
            "current_user": user,
            "logged_in": user is not None,
            "user_role": user.role if user else None,
        }

    @app.get("/")
    def index():
        if "text/html" in request.headers.get("Accept", ""):
            user_id = session.get("user_id")
            if user_id:
                user = db.session.get(User, user_id)
                if user and user.role in ["Coordinator", "Admin"]:
                    return redirect(url_for("dashboard.dashboard_page"))
                elif user and user.role == "Volunteer":
                    return redirect(url_for("root_assignments"))
                else:
                    return redirect("/requests")
            return redirect(url_for("root_login"))
        return jsonify({
            "project": "Disaster Relief Resource Coordination System",
            "version": "1.0.0",
            "review": "Project Review 2 increment",
            "status": "operational",
            "endpoints": {
                "dashboard": "/dashboard/",
                "dashboard_summary": "GET /dashboard/summary",
                "auth": "POST /auth/login, POST /auth/register",
                "inventory": "GET/POST /inventory/",
                "relief_requests": "GET/POST /requests/",
                "assignments": "GET/POST /assignments/",
                "incidents": "GET/POST /incidents/",
                "reports": "GET /reports/summary",
            },
        })

    # Supporting root HTML form and page routes for browser and automated client workflows
    @app.route("/register", methods=["GET", "POST"])
    def root_register():
        if request.method == "POST":
            data = request.form
            try:
                user = register_user(
                    name=data.get("name"),
                    phone=data.get("phone"),
                    email=data.get("email"),
                    password=data.get("password"),
                    role=data.get("role", "Victim"),
                )
                return render_template("register.html", message="Account created", user=user), 200
            except ValueError as e:
                return render_template("register.html", error=str(e)), 400
        return render_template("register.html"), 200

    @app.route("/login", methods=["GET", "POST"])
    def root_login():
        if request.method == "POST":
            data = request.form
            user = authenticate_user(data.get("email"), data.get("password"))
            if user:
                session["user_id"] = user.user_id
                session["user_name"] = user.name
                session["role"] = user.role
                flash(f"Signed in as {user.name} ({user.role})", "success")
                if user.role in ["Coordinator", "Admin"]:
                    return redirect(url_for("dashboard.dashboard_page"))
                elif user.role == "Volunteer":
                    return redirect(url_for("root_assignments"))
                else:
                    return redirect("/requests")
            return render_template("login.html", error="Invalid credentials"), 401
        return render_template("login.html"), 200

    @app.route("/logout", methods=["GET", "POST"])
    def root_logout():
        session.clear()
        flash("You have been signed out successfully.", "info")
        return redirect(url_for("root_login"))

    @app.route("/assignments", methods=["GET", "POST"])
    def root_assignments():
        user_id = session.get("user_id")
        user = db.session.get(User, user_id) if user_id else None
        if not app.config.get("TESTING"):
            if not user:
                flash("Please sign in to access assignments.", "warning")
                return redirect(url_for("root_login"))
            if user.role == "Victim":
                flash("Access denied: Assignments are restricted to volunteers and coordinators.", "danger")
                return redirect("/requests")

        if request.method == "POST":
            data = request.form
            try:
                assignment = allocate_request(
                    request_id=int(data.get("request_id")),
                    volunteer_id=int(data.get("volunteer_id")),
                    item_id=int(data.get("item_id")),
                )
                tasks = list_assignments()
                return render_template("assignments.html", message="Resource allocated and volunteer notified", assignment=assignment, assignments=tasks), 200
            except Exception as e:
                tasks = list_assignments()
                return render_template("assignments.html", error=str(e), assignments=tasks), 400
        tasks = list_assignments()
        return render_template("assignments.html", assignments=tasks), 200

    @app.route("/assignments/<int:task_id>/status", methods=["POST"])
    def root_assignment_status(task_id):
        new_status = request.form.get("status")
        try:
            task = update_assignment_status(task_id, new_status)
            tasks = list_assignments()
            return render_template("assignments.html", message="Assignment status updated", assignment=task, assignments=tasks), 200
        except Exception as e:
            tasks = list_assignments()
            return render_template("assignments.html", error=str(e), assignments=tasks), 400

    @app.route("/notifications", methods=["GET"])
    def root_notifications():
        user_id = session.get("user_id")
        if user_id:
            notifs = list_notifications(user_id)
        else:
            notifs = Notification.query.order_by(Notification.created_at.desc()).all()
        return render_template("notifications.html", notifications=notifs), 200

    @app.route("/volunteers", methods=["GET"])
    def root_volunteers():
        user_id = session.get("user_id")
        user = db.session.get(User, user_id) if user_id else None
        if not app.config.get("TESTING"):
            if not user:
                flash("Please sign in to view the volunteer directory.", "warning")
                return redirect(url_for("root_login"))
            if user.role not in ["Coordinator", "Admin"]:
                flash("Access denied: Volunteer directory requires coordinator permissions.", "danger")
                return redirect(url_for("index"))
        vols = list_volunteers()
        return render_template("volunteers.html", volunteers=vols), 200

    @app.route("/alerts", methods=["GET", "POST"])
    def root_alerts():
        user_id = session.get("user_id")
        user = db.session.get(User, user_id) if user_id else None
        if not app.config.get("TESTING"):
            if not user:
                flash("Please sign in as coordinator to broadcast alerts.", "warning")
                return redirect(url_for("root_login"))
            if user.role not in ["Coordinator", "Admin"]:
                flash("Access denied: Emergency broadcasts require coordinator permissions.", "danger")
                return redirect(url_for("index"))

        if request.method == "POST":
            message = request.form.get("message")
            type_val = request.form.get("type", "Emergency")
            recipient_ids = request.form.getlist("recipient_user_ids")
            try:
                recipients = [int(x) for x in recipient_ids if str(x).isdigit()]
                broadcast_emergency_alert(message=message, notification_type=type_val, recipient_user_ids=recipients if recipients else None)
                return render_template("alerts.html", message="Alert broadcast sent", users=User.query.all()), 200
            except Exception as e:
                return render_template("alerts.html", error=str(e), users=User.query.all()), 400
        return render_template("alerts.html", users=User.query.all()), 200

    @app.route("/incidents", methods=["GET"])
    def root_incidents():
        incidents = Incident.query.order_by(Incident.created_at.desc()).all()
        return render_template("incidents.html", incidents=incidents), 200

    @app.route("/reports", methods=["GET"])
    def root_reports():
        user_id = session.get("user_id")
        user = db.session.get(User, user_id) if user_id else None
        if not app.config.get("TESTING"):
            if not user:
                flash("Please sign in to access reports.", "warning")
                return redirect(url_for("root_login"))
            if user.role not in ["Coordinator", "Admin"]:
                flash("Access denied: Operational reports require coordinator permissions.", "danger")
                return redirect(url_for("index"))
        summary = get_dashboard_summary()
        return render_template("reports.html", summary=summary), 200

    with app.app_context():
        import models  # noqa: F401
        db.create_all()

    return app

def seed_initial_demo_data():
    from werkzeug.security import generate_password_hash
    from constants import (
        ROLE_COORDINATOR, ROLE_VOLUNTEER, ROLE_VICTIM, ROLE_ADMIN,
        STATUS_INCIDENT_OPEN, STATUS_INCIDENT_IN_PROGRESS,
        STATUS_REQUEST_PENDING, URGENCY_HIGH, URGENCY_MEDIUM,
        CATEGORY_WATER, CATEGORY_FOOD, CATEGORY_MEDICAL, CATEGORY_SHELTER,
        SEVERITY_HIGH, SEVERITY_CRITICAL
    )
    if User.query.first() is None:
        c = User(name="Coordinator Alice", email="coordinator@example.com", phone="+1234567890", role=ROLE_COORDINATOR, password_hash=generate_password_hash("password123"))
        v = User(name="Volunteer Bob", email="volunteer@example.com", phone="+1234567891", role=ROLE_VOLUNTEER, password_hash=generate_password_hash("password123"))
        vic = User(name="Victim Carol", email="victim@example.com", phone="+1234567892", role=ROLE_VICTIM, password_hash=generate_password_hash("password123"))
        adm = User(name="Admin Dave", email="admin@example.com", phone="+1234567893", role=ROLE_ADMIN, password_hash=generate_password_hash("password123"))
        db.session.add_all([c, v, vic, adm])
        db.session.commit()
    else:
        c = User.query.filter_by(role=ROLE_COORDINATOR).first()
        vic = User.query.filter_by(role=ROLE_VICTIM).first()

    if Incident.query.first() is None and c:
        inc1 = Incident(title="Coastal Flooding - Sector 4", description="Severe storm surge and river overflow in Sector 4", severity=SEVERITY_HIGH, status=STATUS_INCIDENT_OPEN, latitude=13.0827, longitude=80.2707, reported_by=c.user_id)
        inc2 = Incident(title="Earthquake Tremors - District 2", description="Structural damage reported in low-lying commercial blocks", severity=SEVERITY_CRITICAL, status=STATUS_INCIDENT_IN_PROGRESS, latitude=13.0450, longitude=80.2200, reported_by=c.user_id)
        db.session.add_all([inc1, inc2])
        db.session.commit()
    inc1 = Incident.query.first()

    if InventoryItem.query.first() is None:
        item1 = InventoryItem(category=CATEGORY_WATER, quantity=500, threshold=100, storage_location="Warehouse A - Bay 1")
        item2 = InventoryItem(category=CATEGORY_MEDICAL, quantity=120, threshold=30, storage_location="Warehouse A - Medical Wing")
        item3 = InventoryItem(category=CATEGORY_FOOD, quantity=350, threshold=80, storage_location="Warehouse B - Cold Storage")
        item4 = InventoryItem(category=CATEGORY_SHELTER, quantity=25, threshold=50, storage_location="Warehouse B - Dry Storage")
        db.session.add_all([item1, item2, item3, item4])
        db.session.commit()

    if ReliefRequest.query.first() is None and vic:
        req1 = ReliefRequest(user_id=vic.user_id, category=CATEGORY_WATER, quantity=50, urgency=URGENCY_HIGH, location="Sector 4 Emergency Center", latitude=13.0827, longitude=80.2707, status=STATUS_REQUEST_PENDING, incident_id=inc1.incident_id if inc1 else None)
        req2 = ReliefRequest(user_id=vic.user_id, category=CATEGORY_FOOD, quantity=30, urgency=URGENCY_MEDIUM, location="District 2 Relief Camp", latitude=13.0820, longitude=80.2710, status=STATUS_REQUEST_PENDING, incident_id=inc1.incident_id if inc1 else None)
        db.session.add_all([req1, req2])
        db.session.commit()


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        seed_initial_demo_data()
    app.run(debug=True, port=5000)

