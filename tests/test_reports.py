from werkzeug.security import generate_password_hash

from extensions import db
from models import User, ReliefRequest, Incident, InventoryItem


def create_user(app, role="Coordinator"):
    with app.app_context():
        user = User(
            name="Report User",
            email=f"{role.lower()}@example.com",
            role=role,
            password_hash=generate_password_hash("safe-pass-123"),
        )
        db.session.add(user)
        db.session.commit()
        return user.user_id


def login_as(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = user_id


def test_summary_report_requires_login(client):
    response = client.get("/reports/summary")
    assert response.status_code == 401


def test_summary_report_forbidden_for_victim(app, client):
    user_id = create_user(app, "Victim")
    login_as(client, user_id)
    response = client.get("/reports/summary")
    assert response.status_code == 403


def test_summary_report_returns_counts(app, client):
    user_id = create_user(app, "Coordinator")
    with app.app_context():
        db.session.add(ReliefRequest(
            user_id=user_id, category="Water", quantity=10, urgency="High",
            location="North area", status="Pending"
        ))
        db.session.add(Incident(
            title="Flood", description="", latitude=13.0, longitude=80.0,
            severity="High", status="Open", reported_by=user_id
        ))
        db.session.add(InventoryItem(
            category="Water", quantity=2, storage_location="Warehouse A", threshold=5
        ))
        db.session.commit()
    login_as(client, user_id)

    response = client.get("/reports/summary")
    assert response.status_code == 200
    body = response.get_json()
    assert body["relief_requests"]["total"] == 1
    assert body["relief_requests"]["by_status"]["Pending"] == 1
    assert body["incidents"]["total"] == 1
    assert body["inventory"]["total_quantity"] == 2
    assert body["inventory"]["low_stock_item_types"] == 1


def test_relief_request_report_filters_by_status(app, client):
    user_id = create_user(app, "Admin")
    with app.app_context():
        db.session.add_all([
            ReliefRequest(user_id=user_id, category="Water", quantity=4,
                          urgency="High", location="North", status="Pending"),
            ReliefRequest(user_id=user_id, category="Food", quantity=2,
                          urgency="Low", location="South", status="Approved"),
        ])
        db.session.commit()
    login_as(client, user_id)

    response = client.get("/reports/relief-requests?status=Pending")
    assert response.status_code == 200
    body = response.get_json()
    assert body["count"] == 1
    assert body["relief_requests"][0]["status"] == "Pending"
