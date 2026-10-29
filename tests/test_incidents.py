from extensions import db
from models import User, Incident
from werkzeug.security import generate_password_hash

def create_coordinator(app):
    with app.app_context():
        user = User(name="Coordinator", email="coord@example.com",
                    role="Coordinator", password_hash=generate_password_hash("safe-pass-123"))
        db.session.add(user)
        db.session.commit()
        return user.user_id

def login_coordinator(client, user_id):
    # Set session as an authenticated coordinator for route testing.
    with client.session_transaction() as sess:
        sess["user_id"] = user_id

def test_create_incident_success(app, client):
    user_id = create_coordinator(app)
    login_coordinator(client, user_id)
    response = client.post("/incidents/", json={
        "title": "Flooding", "description": "Road submerged",
        "latitude": 13.08, "longitude": 80.27, "severity": "High"
    })
    assert response.status_code == 201
    assert response.json["incident"]["title"] == "Flooding"

def test_incident_rejects_invalid_latitude(app, client):
    user_id = create_coordinator(app)
    login_coordinator(client, user_id)
    response = client.post("/incidents/", json={
        "title": "Flooding", "latitude": 91, "longitude": 80,
        "severity": "High"
    })
    assert response.status_code == 400

def test_incident_requires_login(client):
    response = client.post("/incidents/", json={
        "title": "Flooding", "latitude": 13, "longitude": 80, "severity": "High"
    })
    assert response.status_code == 401

def test_list_affected_areas(app, client):
    user_id = create_coordinator(app)
    with app.app_context():
        db.session.add(Incident(title="Active flood", description="", latitude=13,
            longitude=80, severity="Critical", status="Open", reported_by=user_id))
        db.session.add(Incident(title="Resolved storm", description="", latitude=12,
            longitude=79, severity="Low", status="Resolved", reported_by=user_id))
        db.session.commit()
    response = client.get("/incidents/affected-areas")
    assert response.status_code == 200
    assert len(response.json["affected_areas"]) == 1
    assert response.json["affected_areas"][0]["title"] == "Active flood"


def test_incident_can_be_viewed_edited_and_transitioned(app, client):
    user_id = create_coordinator(app)
    login_coordinator(client, user_id)
    created = client.post("/incidents/", json={
        "title": "Initial flood",
        "description": "Water on the road",
        "latitude": 13.08,
        "longitude": 80.27,
        "severity": "High",
    })
    assert created.status_code == 201
    incident_id = created.json["incident"]["incident_id"]

    detail = client.get(f"/incidents/{incident_id}")
    assert detail.status_code == 200
    assert detail.json["incident"]["title"] == "Initial flood"
    listing = client.get("/incidents/")
    assert listing.status_code == 200
    assert any(item["incident_id"] == incident_id for item in listing.json["incidents"])

    edited = client.patch(f"/incidents/{incident_id}", json={
        "title": "Updated flood report",
        "description": "Road access is blocked",
        "severity": "Critical",
    })
    assert edited.status_code == 200
    assert edited.json["incident"]["title"] == "Updated flood report"
    assert edited.json["incident"]["severity"] == "Critical"

    progress = client.patch(f"/incidents/{incident_id}/status", json={"status": "In Progress"})
    assert progress.status_code == 200
    assert progress.json["incident"]["status"] == "In Progress"

    resolved = client.patch(f"/incidents/{incident_id}/status", json={"status": "Resolved"})
    assert resolved.status_code == 200
    assert resolved.json["incident"]["status"] == "Resolved"

    closed = client.patch(f"/incidents/{incident_id}/status", json={"status": "Closed"})
    assert closed.status_code == 200
    assert closed.json["incident"]["status"] == "Closed"

    invalid_transition = client.patch(
        f"/incidents/{incident_id}/status", json={"status": "Open"}
    )
    assert invalid_transition.status_code == 400
    detail_after = client.get(f"/incidents/{incident_id}")
    assert detail_after.json["incident"]["status"] == "Closed"


def test_incident_edit_rejects_invalid_data(app, client):
    user_id = create_coordinator(app)
    login_coordinator(client, user_id)
    created = client.post("/incidents/", json={
        "title": "Storm",
        "latitude": 13,
        "longitude": 80,
        "severity": "Medium",
    })
    incident_id = created.json["incident"]["incident_id"]

    empty_title = client.patch(f"/incidents/{incident_id}", json={"title": "   "})
    assert empty_title.status_code == 400
    bad_severity = client.patch(f"/incidents/{incident_id}", json={"severity": "Extreme"})
    assert bad_severity.status_code == 400
    invalid_coords = client.patch(f"/incidents/{incident_id}", json={"latitude": 95})
    assert invalid_coords.status_code == 400
    # The original incident remains unchanged after rejected updates.
    detail = client.get(f"/incidents/{incident_id}")
    assert detail.json["incident"]["title"] == "Storm"
    assert detail.json["incident"]["latitude"] == 13.0


def test_incident_mutations_require_coordinator_or_admin(app, client):
    create_response = client.post("/incidents/", json={
        "title": "Unauthorized create",
        "latitude": 13,
        "longitude": 80,
        "severity": "Low",
    })
    assert create_response.status_code == 401

    coordinator_id = create_coordinator(app)
    login_coordinator(client, coordinator_id)
    incident_response = client.post("/incidents/", json={
        "title": "Controlled incident",
        "latitude": 13,
        "longitude": 80,
        "severity": "Low",
    })
    incident_id = incident_response.json["incident"]["incident_id"]

    with app.app_context():
        victim = User(
            name="Victim",
            email="incident-victim@example.com",
            role="Victim",
            password_hash=generate_password_hash("safe-pass-123"),
        )
        db.session.add(victim)
        db.session.commit()
        victim_id = victim.user_id

    with client.session_transaction() as sess:
        sess["user_id"] = victim_id
    edit_response = client.patch(f"/incidents/{incident_id}", json={"title": "Tampered"})
    status_response = client.patch(
        f"/incidents/{incident_id}/status", json={"status": "In Progress"}
    )
    assert edit_response.status_code == 403
    assert status_response.status_code == 403


def test_incident_rejects_non_object_payload(app, client):
    user_id = create_coordinator(app)
    login_coordinator(client, user_id)
    response = client.post("/incidents/", json=["invalid", "payload"])
    assert response.status_code == 400
    assert "error" in response.json
