from extensions import db
from models import User, Incident, ReliefRequest, InventoryItem
from dashboard import get_dashboard_summary
from constants import (
    CATEGORY_FOOD_WATER,
    URGENCY_HIGH,
    ROLE_VICTIM,
    ROLE_VOLUNTEER,
    ROLE_COORDINATOR,
)
from werkzeug.security import generate_password_hash

def test_dashboard_summary_metrics(app):
    with app.app_context():
        # Setup initial users
        victim = User(name="Victim A", email="v1@example.com", role=ROLE_VICTIM, password_hash=generate_password_hash("pass123"))
        volunteer = User(name="Volunteer B", email="v2@example.com", role=ROLE_VOLUNTEER, password_hash=generate_password_hash("pass123"))
        db.session.add_all([victim, volunteer])
        db.session.commit()

        # Add Inventory
        item1 = InventoryItem(category=CATEGORY_FOOD_WATER, quantity=100, storage_location="Hub 1", threshold=20)
        item2 = InventoryItem(category="Medical Supplies", quantity=5, storage_location="Hub 2", threshold=10) # low stock!
        db.session.add_all([item1, item2])

        # Add Incident
        incident = Incident(title="Flood in zone 1", latitude=13.0, longitude=80.0, severity="High", reported_by=victim.user_id)
        db.session.add(incident)

        # Add Relief Request
        req = ReliefRequest(user_id=victim.user_id, category=CATEGORY_FOOD_WATER, quantity=10, urgency=URGENCY_HIGH, location="Zone 1")
        db.session.add(req)

        db.session.commit()

        summary = get_dashboard_summary()
        assert summary["requests"]["total"] == 1
        assert summary["requests"]["pending"] == 1
        assert summary["inventory"]["total_items"] == 2
        assert summary["inventory"]["total_units"] == 105
        assert summary["inventory"]["low_stock_count"] == 1
        assert summary["incidents"]["active_count"] == 1
        assert summary["volunteers"]["total_count"] == 1

def test_dashboard_routes(client):
    # API Summary JSON endpoint
    res = client.get("/dashboard/summary")
    assert res.status_code == 200
    assert "requests" in res.json
    assert "inventory" in res.json

    # HTML page endpoint
    html_res = client.get("/dashboard/")
    assert html_res.status_code == 200
    assert b"Relief Activity Dashboard" in html_res.data
