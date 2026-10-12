# Disaster Relief Resource Coordination System

**Stack:** Python, Flask, SQLite, Flask-SQLAlchemy, HTML/Bootstrap, pytest.

## Run on Windows PowerShell
Open this folder (the one containing `app.py` and `requirements.txt`) in VS Code.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. The SQLite database is created automatically. To run automated tests:

```powershell
python -m pytest -v
```

## Sivenesh's assigned stories
- **TEAM20-21 — Allocate Resources to Requests:** validates pending request, volunteer role, matching category and stock; creates the assignment, reduces inventory and creates a notification in a transaction.
- **TEAM20-22 — Track Resource Distribution:** list/filter assignments and update allowed statuses; completing an assignment marks the relief request fulfilled.
- **TEAM20-23 — Manage Relief Volunteers:** list volunteers and retrieve their assignments.
- **TEAM20-24 — Assign Volunteers:** allocation associates a volunteer with a request.
- **TEAM20-25 — Emergency Alert Notifications:** create/read notifications and broadcast to operational roles or selected users.

## Demonstration workflow
1. Register a Victim and a Volunteer from **Register**. (This prototype allows role selection for classroom demonstration.)
2. Add 10 units of Water in Inventory.
3. Submit a Water request for 4 units. The requester must be selected from registered users.
4. Allocate the request to the Volunteer using matching category stock.
5. Verify stock becomes 6, request status becomes Assigned, and a notification is created.
6. Update the assignment to Completed and verify the request becomes Fulfilled.
7. Use Alerts to send a message to selected users, or leave recipients unselected to broadcast to Volunteers, Coordinators and Admins.

## Tests
The `tests/` folder contains unit/component tests and an end-to-end Flask test-client workflow. Your earlier local run of the 22 existing tests reported `22 passed`. Run `python -m pytest -v` after extracting this final package to verify all tests including the added end-to-end test. Do not mark JIRA stories Done based only on the existence of tests—verify each acceptance criterion and save actual terminal output.

## Limitations to disclose during review
- This is a classroom prototype, not production-ready. Login currently validates credentials but does not establish a persistent authenticated session, and route-level role authorization/CSRF protection must be added before deployment. Do not expose this app publicly with the demo role-selection form.
- The proposed schema permits only one Assignment per ReliefRequest because `Assignment.request_id` is unique. The SRS may describe multiple volunteers per request; confirm with the team whether the unique constraint should be removed before final schema approval.
- The app uses SQLite for local development. Team members should agree on one shared database configuration for integrated demonstrations; do not commit personal database files.
