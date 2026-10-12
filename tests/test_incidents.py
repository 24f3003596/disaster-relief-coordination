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
