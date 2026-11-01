"""Regression tests for request and incident activity history."""

from werkzeug.security import generate_password_hash

from extensions import db
from models import Incident, ReliefRequest, User
from requests_module import create_relief_request
from incidents import create_incident, update_incident, update_incident_status
from assignments import allocate_request, update_assignment_status
from inventory import create_inventory_item
from audit import list_entity_activity


def make_user(app, name, role, email):
    with app.app_context():
        user = User(
            name=name,
            email=email,
            role=role,
            password_hash=generate_password_hash("safe-pass-123"),
        )
        db.session.add(user)
        db.session.commit()
        return user.user_id


def login(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = user_id


def test_request_activity_records_creation_and_status_transition(app, client):
    victim_id = make_user(app, "Activity Victim", "Victim", "activity-victim@example.com")
    coordinator_id = make_user(
        app, "Activity Coordinator", "Coordinator", "activity-coordinator@example.com"
    )

    login(client, victim_id)
    created = client.post("/requests/", json={
        "category": "Water",
        "quantity": 4,
        "urgency": "High",
        "location": "North Camp",
        "latitude": 13.08,
        "longitude": 80.27,
    })
    assert created.status_code == 201
    request_id = created.get_json()["request"]["request_id"]

    login(client, coordinator_id)
    updated = client.patch(f"/requests/{request_id}/status", json={"status": "Allocated"})
    assert updated.status_code == 200

    history = client.get(f"/requests/{request_id}/history?format=json")
    assert history.status_code == 200
    entries = history.get_json()["activity"]
    assert len(entries) == 2
    assert "Created relief request" in entries[0]["action"]
    assert entries[0]["actor_name"] == "Activity Victim"
    assert "Pending -> Allocated" in entries[1]["action"]
    assert entries[1]["actor_name"] == "Activity Coordinator"
    assert entries[0]["created_at"] <= entries[1]["created_at"]


def test_request_activity_obeys_request_visibility(app, client):
    owner_id = make_user(app, "History Owner", "Victim", "history-owner@example.com")
    other_id = make_user(app, "Other Victim", "Victim", "history-other@example.com")
    with app.app_context():
        req = create_relief_request(
            owner_id, "Water", 2, "Medium", location="Owner Camp", actor_id=owner_id
        )
        request_id = req.request_id

    login(client, owner_id)
    owner_history = client.get(f"/requests/{request_id}/history?format=json")
    assert owner_history.status_code == 200
    assert len(owner_history.get_json()["activity"]) == 1

    login(client, other_id)
    assert client.get(f"/requests/{request_id}/history?format=json").status_code == 403


def test_request_activity_requires_login_and_existing_request(client):
    assert client.get("/requests/999/history?format=json").status_code == 401


def test_incident_activity_records_creation_field_changes_and_status(app, client):
    coordinator_id = make_user(
        app, "Incident Coordinator", "Coordinator", "incident-history-coord@example.com"
    )
    login(client, coordinator_id)

    created = client.post("/incidents/", json={
        "title": "Initial flood",
        "description": "Road partially submerged",
        "latitude": 13.08,
        "longitude": 80.27,
        "severity": "High",
    })
    assert created.status_code == 201
    incident_id = created.get_json()["incident"]["incident_id"]

    edited = client.patch(f"/incidents/{incident_id}", json={
        "title": "Updated flood report",
        "severity": "Critical",
    })
    assert edited.status_code == 200

    status_update = client.patch(
        f"/incidents/{incident_id}/status", json={"status": "In Progress"}
    )
    assert status_update.status_code == 200

    history = client.get(f"/incidents/{incident_id}/history?format=json")
    assert history.status_code == 200
    entries = history.get_json()["activity"]
    assert len(entries) == 3
    assert "Created incident" in entries[0]["action"]
    assert "Incident updated" in entries[1]["action"]
    assert "title" in entries[1]["action"]
    assert "severity" in entries[1]["action"]
    assert "Open -> In Progress" in entries[2]["action"]
    assert all(item["actor_name"] == "Incident Coordinator" for item in entries)
    assert [item["log_id"] for item in entries] == sorted(item["log_id"] for item in entries)


def test_incident_noop_update_does_not_create_duplicate_activity(app):
    coordinator_id = make_user(
        app, "Noop Coordinator", "Coordinator", "incident-noop@example.com"
    )
    with app.app_context():
        incident = create_incident(
            "No-op incident", "Description", 13.0, 80.0, "Medium", coordinator_id
        )
        before = len(list_entity_activity("Incident", incident.incident_id))
        update_incident(
            incident.incident_id,
            {"title": "No-op incident", "description": "Description"},
            actor_id=coordinator_id,
        )
        after = len(list_entity_activity("Incident", incident.incident_id))
        assert after == before


def test_incident_history_is_restricted_to_operational_roles(app, client):
    coordinator_id = make_user(
        app, "History Incident Coordinator", "Coordinator", "history-incident-coord@example.com"
    )
    victim_id = make_user(app, "History Incident Victim", "Victim", "history-incident-victim@example.com")
    with app.app_context():
        incident = create_incident(
            "History incident", "Description", 13.0, 80.0, "Low", coordinator_id
        )
        incident_id = incident.incident_id

    assert client.get(f"/incidents/{incident_id}/history?format=json").status_code == 401
    login(client, victim_id)
    assert client.get(f"/incidents/{incident_id}/history?format=json").status_code == 403

    login(client, coordinator_id)
    html_history = client.get(f"/incidents/{incident_id}/history")
    assert html_history.status_code == 200
    assert b"Chronological record" in html_history.data
    assert b"Created incident" in html_history.data


def test_assignment_driven_request_status_changes_are_in_activity_history(app):
    victim_id = make_user(app, "Allocated Victim", "Victim", "allocated-victim@example.com")
    volunteer_id = make_user(app, "Allocated Volunteer", "Volunteer", "allocated-volunteer@example.com")
    with app.app_context():
        req = create_relief_request(victim_id, "Water", 3, "High", location="Depot Road")
        item = create_inventory_item("Water", 10, "Central Depot", threshold=2)
        assignment = allocate_request(req.request_id, volunteer_id, item.item_id)
        update_assignment_status(assignment.task_id, "Completed")

        events = list_entity_activity("ReliefRequest", req.request_id)
        actions = [item["action"] for item in events]
        assert any("Pending -> Assigned" in action for action in actions)
        assert any("Assigned -> Fulfilled" in action for action in actions)
