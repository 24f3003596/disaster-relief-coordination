# Disaster Relief Resource Coordination System

Initial working increment: user registration/login, basic role-based authorization, incident registration, incident listing, affected-area listing, and pytest tests.

## Setup (Git Bash)
```bash
source .venv/Scripts/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000/` to see the endpoint list.

## Run tests
```bash
pytest -q
```

## API examples
Register:
```bash
curl -X POST http://127.0.0.1:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"safe-pass-123"}'
```

Login:
```bash
curl -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"safe-pass-123"}'
```

Incident creation requires a logged-in Coordinator or Admin. Use a browser/API client that preserves the session cookie, or test with pytest.

## Important
- Public registration always creates a `Victim` account; users cannot self-assign Coordinator/Admin.
- This is a starter increment, not a complete production-ready system.
- Change `SECRET_KEY` to a strong environment-provided secret before deployment.
- Extend status/severity choices to match the team's approved SRS.
- Coordinate model changes with teammates before merging.
