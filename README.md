# Disaster Relief Resource Coordination System (Team 20)

**Software Engineering Project — Sprint 3 (Review 3) Delivery**

An integrated, role-based web application and API for managing disaster incidents, emergency relief requests, warehouse inventory, volunteer dispatching, notifications, and coordinator operations.

---

## 👥 Team 20 Members & Task Allocation (JIRA)

| Team Member | Role / Responsibilities | JIRA Issue IDs |
|---|---|---|
| **Vishal K V** | User Authentication, Password Hashing, Session Management, Incident Logging, Affected Areas, Relief Reports | `TEAM20-16`, `TEAM20-17`, `TEAM20-27` |
| **SIVANESH** | Relief Task Allocation, Volunteer Status Updates, In-App Notifications, Emergency Broadcast Alerts, Volunteer Directory | `TEAM20-21`, `TEAM20-22`, `TEAM20-23`, `TEAM20-24`, `TEAM20-25` |
| **Sree Naresh A** | Relief Request Intake, Warehouse Inventory Management, Coordinator Analytics Dashboard, System Audit Logging, Integration & E2E Testing, Branch Merging | `TEAM20-18`, `TEAM20-19`, `TEAM20-20`, `TEAM20-26`, `TEAM20-28` |

---

## 🏗 System Architecture & Folder Structure

The project strictly follows the **Application Factory** and **Flask Blueprint** architecture with **SQLAlchemy ORM** and **Jinja2 Templates**:

```text
disaster-relief-coordination/
├── app.py                      # Application factory (create_app), session management, error handlers, demo seeder
├── requirements.txt            # Project dependencies (Flask, SQLAlchemy, pytest, pytest-cov, radon)
├── README.md                   # Complete Review 2 documentation & user guide
│
├── core/                       # Core database models, system constants & extensions
│   ├── __init__.py             # Exposes db, models, constants
│   ├── models.py               # 7 SQLAlchemy ORM models (User, Incident, ReliefRequest, InventoryItem, Assignment, Notification, AuditLog)
│   ├── constants.py            # Global enums, validation boundaries, and role definitions
│   └── extensions.py           # Shared SQLAlchemy database instance (db)
│
├── routes/                     # Modular feature blueprints
│   ├── __init__.py             # Exposes all blueprint instances
│   ├── auth.py                 # Authentication blueprint & helpers (register, login, logout, roles)
│   ├── incidents.py            # Incident reporting and affected areas blueprint
│   ├── inventory.py            # Warehouse inventory tracking and low-stock alerts blueprint
│   ├── requests_module.py      # Victim relief request intake and status tracking blueprint
│   ├── assignments.py          # Atomic resource allocation and volunteer dispatch blueprint
│   ├── notifications.py        # User notification inbox and coordinator emergency broadcast blueprint
│   ├── volunteers.py           # Volunteer task assignments and directory blueprint
│   ├── reports.py              # Operational summary and relief status reporting blueprint
│   ├── dashboard.py            # Coordinator metrics and analytics dashboard blueprint
│   └── audit.py                # Action logging and security audit trail blueprint
│
├── static/
│   └── style.css               # Clean styling and UI accents
│
├── templates/                  # 12 Responsive Bootstrap Jinja2 templates (role-adaptive navigation)
│   ├── base.html               # Master layout with dynamic role indicators, navbar, & alerts
│   ├── login.html              # Login page with 1-click Quick Demo logins
│   ├── register.html           # User registration page
│   ├── dashboard.html          # Coordinator analytical overview
│   ├── incidents.html          # Incident management interface
│   ├── inventory.html          # Stock management interface
│   ├── requests.html           # Relief requests intake & status view
│   ├── assignments.html        # Dispatch & assignment management
│   ├── volunteers.html         # Volunteer directory and task view
│   ├── notifications.html      # User notifications inbox
│   ├── alerts.html             # Emergency broadcast console
│   └── reports.html            # Operational reporting page
│
└── tests/
    ├── conftest.py             # Test app fixtures, in-memory SQLite DB, and client setup
    ├── test_auth.py            # Unit tests for authentication and role guards
    ├── test_incidents.py       # Unit tests for incident creation & area discovery
    ├── test_inventory.py       # Boundary and stock management tests
    ├── test_requests.py        # Relief request intake validation tests
    ├── test_assignments.py     # Atomic allocation and stock deduction tests
    ├── test_volunteers.py      # Volunteer dispatch validation tests
    ├── test_notifications.py   # Notification delivery and broadcast tests
    ├── test_reports.py         # Summary report metrics and status filter tests
    ├── test_dashboard.py       # Dashboard metrics calculation tests
    ├── test_audit.py           # Audit trail integrity tests
    ├── test_integration.py     # Multi-module end-to-end integration tests
    ├── test_end_to_end_workflow.py # Full lifecycle workflow tests
    ├── test_rbac.py                # RBAC enforcement and access-control regression tests
    └── test_inventory_resource_consistency.py # Inventory and allocation consistency (Sprint 3)
```

---

## 🗄 Database Models Summary

1. **`User`**: `user_id`, `name`, `phone`, `email` (unique), `password_hash`, `role` (`Victim`, `Volunteer`, `Coordinator`, `Admin`).
2. **`Incident`**: `incident_id`, `title`, `description`, `severity`, `status`, `latitude`, `longitude`, `created_at`.
3. **`ReliefRequest`**: `request_id`, `user_id`, `category`, `quantity`, `urgency`, `latitude`, `longitude`, `status`, `incident_id`, `created_at`.
4. **`InventoryItem`**: `item_id`, `name`, `category`, `quantity`, `low_stock_threshold`, `warehouse_location`, `updated_at`.
5. **`Assignment`**: `assignment_id`, `request_id`, `volunteer_id`, `item_id`, `quantity_allocated`, `status`, `assigned_at`, `completed_at`.
6. **`Notification`**: `notification_id`, `user_id`, `message`, `type`, `is_read`, `created_at`.
7. **`AuditLog`**: `log_id`, `actor_user_id`, `action`, `entity_type`, `entity_id`, `details`, `created_at`.

---

## 🔐 Public Registration and Role Security

Public registration through both `/auth/register` (JSON API) and `/register` (browser form) always creates a `Victim` account. Any `role` value submitted by a public client is ignored; users cannot grant themselves `Volunteer`, `Coordinator`, or `Admin` permissions. The browser registration form does not offer a role selector. Role changes are handled through `PATCH /auth/users/<user_id>/role`, which requires an authenticated `Admin` account.

---

## Relief Request and Incident Workflow API

Relief-request records require authentication. A request submitted by an ordinary signed-in user is associated with that user's session identity; a user-supplied `user_id` cannot be used to impersonate another account. Coordinators and Admins may use the requester field in the existing intake workflow. Victims can view only their own requests, volunteers can view requests assigned to them, and Coordinators/Admins can view all requests.

| Method | Endpoint | Permission | Purpose |
|---|---|---|---|
| `POST` | `/requests/` | Signed in | Create a validated relief request |
| `GET` | `/requests/` | Signed in; results filtered by role | List visible requests, optionally filtered by status |
| `GET` | `/requests/<request_id>` | Signed in; owner, assigned volunteer, Coordinator or Admin | View one request |
| `PATCH` | `/requests/<request_id>/status` | Coordinator or Admin | Apply a valid request status transition |

Request creation validates category, positive integer quantity, urgency, coordinate ranges, paired coordinates and an optional existing incident ID. Invalid input returns a client error rather than creating a partial record. Status transitions are checked against the configured workflow; completed and cancelled requests are terminal.

Incident listing and detail retrieval are available through `GET /incidents/` and `GET /incidents/<incident_id>`. Incident creation, editing and status changes are restricted to Coordinators and Admins.

| Method | Endpoint | Permission | Purpose |
|---|---|---|---|
| `POST` | `/incidents/` | Coordinator or Admin | Create an incident |
| `GET` | `/incidents/` | Public read | List incidents, optionally filtered by status |
| `GET` | `/incidents/<incident_id>` | Public read | Retrieve one incident |
| `PATCH` | `/incidents/<incident_id>` | Coordinator or Admin | Update title, description, severity or coordinates |
| `PATCH` | `/incidents/<incident_id>/status` | Coordinator or Admin | Advance/reopen/close an incident through valid status transitions |
| `GET` | `/incidents/affected-areas` | Public read | Retrieve active affected areas |

Incident creation and editing validate required titles, supported severity values and geographic coordinate ranges. Incident status changes use an explicit transition table, and incident creation, edits and status updates are recorded in the audit log.

## 🚀 Setup & Execution

### Prerequisites
- Python 3.10+ (tested on Python 3.12 / 3.14)
- Git

### 1. Clone & Activate Virtual Environment
```bash
git clone https://github.com/24f3003596/disaster-relief-coordination.git
cd disaster-relief-coordination

# Windows (Command Prompt / PowerShell)
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS / Git Bash
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Development Server
```bash
python app.py
```
Open **`http://127.0.0.1:5000/`** in your browser.

---

## 🧪 Testing, Quality & Code Metrics

### Run Test Suite
```bash
pytest -v
```
**Result**: **94 passed, 0 failures (100% pass rate)** — verified on `main` post Sprint 3 integration, Python 3.14.5, pytest 9.1.1. (Baseline pre-Sprint 3: 62 passed; +32 new tests added in Sprint 3). Always re-run after any code or test change to get current figures.

### Run Test Coverage
```bash
pytest --cov=. --cov-report=term-missing
```
**Coverage**: **~80% statement coverage** across core application modules (raw `pytest-cov` total is 50%; the `routes/` mirror package and `build_all_word_documents.py` inflate the denominator — see [`docs/CODE_COVERAGE_REPORT.md`](docs/CODE_COVERAGE_REPORT.md) for the full breakdown).

### Run Cyclomatic Complexity Check (Radon)
```bash
radon cc . -s -a
```
**Complexity Rating**: **Grade A (average 4.65)** across 289 analysed functions, methods, and classes.

---

## 🔄 Git Branching & Merge History

All team feature branches were developed on dedicated branch tracks and merged into `main` preserving commit authorship:

**Sprint 1 (Review 1)**
1. `feature/auth-incidents` by **Vishal K V** (PR #1 — merged)
2. `feature/relief-reports` by **Vishal K V** (PR #2 — merged)
3. `feature/sivanesh-assignments-notifications` by **SIVANESH** (merged via coordinator merge)
4. `naresh-feature` by **Sree Naresh A** (merged via coordinator merge)

**Sprint 2 (Review 2)**
5. `upload-sprint2` by **Vishal K V** (PR #3 — merged, TEAM20-53/54: Fix public registration role escalation)
6. `feature/allocation-testing` by **SIVANESH** (merged, TEAM20-55/56: Expand allocation integration tests + fix dropdown)
7. `feature/test-documentation` by **Sree Naresh A** (merged, TEAM20-57/58: Quality verification & documentation)


**Sprint 3 (Review 3)**
8. `feature/sprint3-relief-incident-workflow` by **Vishal K V** (PR #4 — merged, TEAM20-59/60: Validate relief requests and incident workflows)
9. `sprint-3-sivanesh` by **SIVANESH** (merged, TEAM20-61/62: Strengthen RBAC and regression testing)
10. `feature/sprint3-inventory-consistency` by **Sree Naresh A** (merged, TEAM20-63: Verify inventory and resource allocation consistency)

All authors are credited in the Git commit tree and appear on GitHub's Contributors graph.

---

## 🔐 Role-Based Access Control (RBAC) Matrix

| Feature / URL | Unauthenticated | Victim | Volunteer | Coordinator / Admin |
|---|---|---|---|---|
| **Public Incidents** (`/incidents`) | ✅ View list | ✅ View list | ✅ View list | ✅ Full management |
| **Relief Request Intake** (`/requests`) | 🔄 Redirect /login | ✅ Submit & view own | ✅ View list | ✅ Full management & status |
| **Volunteer Assignments** (`/assignments`) | 🔄 Redirect /login | ❌ Forbidden | ✅ View my tasks & update status | ✅ Full allocation console |
| **Warehouse Inventory** (`/inventory`) | 🔄 Redirect /login | ❌ Forbidden | ❌ Forbidden | ✅ Full stock tracking & intake |
| **Coordinator Dashboard** (`/dashboard/`) | 🔄 Redirect /login | ❌ Forbidden | ❌ Forbidden | ✅ Full analytics & KPIs |
| **Emergency Alerts** (`/alerts`) | 🔄 Redirect /login | ❌ Forbidden | ❌ Forbidden | ✅ Broadcast alerts |
| **Operational Reports** (`/reports`) | 🔄 Redirect /login | ❌ Forbidden | ❌ Forbidden | ✅ Filtered metrics |
| **Notifications Inbox** (`/notifications`) | 🔄 Redirect /login | ✅ Own alerts | ✅ Own dispatch alerts | ✅ All system notices |

---

## 📋 JIRA Review 2 Agile Execution Guide

### Sprint Breakdown
- **Sprint 1 (Foundations & Authentication)**: Models schema, Password hashing, Registration, Incidents intake, Inventory core (`TEAM20-16`, `TEAM20-17`, `TEAM20-18`, `TEAM20-19`).
- **Sprint 2 (Operations, Coordination & Delivery)**: Relief requests intake, Volunteer assignment & atomic stock deduction, Notifications & emergency broadcast, Analytics dashboard, Audit logging, Registration security hardening, Allocation integration tests, Quality verification & documentation (`TEAM20-20` through `TEAM20-28`, `TEAM20-53` through `TEAM20-58`).
- **Sprint 3 (Quality, Security & Integration)**: Incident workflow validation, Input coordinate checks, RBAC strengthening, Inventory & resource consistency guarantees, Integration & review of all Sprint 3 changes (`TEAM20-59` through `TEAM20-64`).

### Sprint 2 JIRA Tickets
| Ticket | Title | Assignee | Status |
|---|---|---|---|
| TEAM20-53 | Fix Public Registration Role Escalation | Vishal K V | Done |
| TEAM20-54 | Add Registration Security Regression Tests | Vishal K V | Done |
| TEAM20-55 | Expand Resource Allocation Integration Tests | SIVANESH | Done |
| TEAM20-56 | Validate Resource Allocation Failure Handling | SIVANESH | Done |
| TEAM20-57 | Full Test Suite and Quality Verification | Sree Naresh A | Done |
| TEAM20-58 | Update Technical Documentation and Review Evidence | Sree Naresh A | Done |


### Sprint 3 JIRA Tickets
| Ticket | Title | Assignee | Story Points | Status |
|---|---|---|---|---|
| TEAM20-59 | Validate Relief Request and Incident Workflows | Vishal K V | 5 | Done |
| TEAM20-60 | Integrate and Review Sprint 3 — Vishal | Vishal K V | 3 | Done |
| TEAM20-61 | Strengthen RBAC and Regression Testing | SIVANESH | 5 | Done |
| TEAM20-62 | Integrate and Review Sprint 3 — Sivanesh | SIVANESH | 3 | Done |
| TEAM20-63 | Verify Inventory and Resource Consistency | Sree Naresh A | 5 | Done |
| TEAM20-64 | Integrate and Review Sprint 3 Changes | Sree Naresh A | 3 | Done |

### Status for Review 3
All 6 Sprint 3 tickets are **Done**. All Sprint 3 feature branches merged into `main` via `integration/sprint3-main`. Post-integration test suite: **94 passed, 0 failures (100% pass rate)** (see [`docs/TEST_EXECUTION_REPORT.md`](docs/TEST_EXECUTION_REPORT.md)).


### Status for Review 2
All 6 Sprint 2 tickets are **Done**. All feature branches merged into `main`. Post-integration test suite: **62 passed, 0 failures (100% pass rate)** (see [`docs/TEST_EXECUTION_REPORT.md`](docs/TEST_EXECUTION_REPORT.md)).

---

## 📁 Project Evidence & Review 2 Documentation

Comprehensive evidence documents prepared for the Review 2 evaluation are available in the [`docs/`](docs/README.md) directory in both **Microsoft Word (`.docx`)** and **Markdown (`.md`)** formats:

- 📑 **Master Dossier (All Sections Combined)**: [**`docs/Master_Project_Evidence_Review2.docx`**](docs/Master_Project_Evidence_Review2.docx)
- **1. Test Case Document**: [Word (`.docx`)](docs/Test_Case_Document.docx) | [Markdown (`.md`)](docs/TEST_CASE_DOCUMENT.md) — 45 automated test cases, inputs, expected/actual results, and 13 foundational passing tests.
- **2. Test Execution Report**: [Word (`.docx`)](docs/Test_Execution_Report.docx) | [Markdown (`.md`)](docs/TEST_EXECUTION_REPORT.md) — 45 passed (100% pass rate in 31.73s), execution logs, and detailed timing for the 13 core passing tests.
- **3. Defect Log**: [Word (`.docx`)](docs/Defect_Log.docx) | [Markdown (`.md`)](docs/DEFECT_LOG.md) — 8 logged defects across UI, atomic allocation rollback, coordinates, and RBAC with 100% resolution.
- **4. Code Coverage Report**: [Word (`.docx`)](docs/Code_Coverage_Report.docx) | [Markdown (`.md`)](docs/CODE_COVERAGE_REPORT.md) — 86% statement coverage breakdown generated via `pytest-cov`.
- **5. Cyclomatic Complexity Report**: [Word (`.docx`)](docs/Cyclomatic_Complexity_Report.docx) | [Markdown (`.md`)](docs/CYCLOMATIC_COMPLEXITY_REPORT.md) — Radon complexity analysis across 211 blocks with Grade A average (4.18).
- **6. UI Automation Evidence**: [Word (`.docx`)](docs/UI_Automation_Evidence.docx) | [Markdown (`.md`)](docs/UI_AUTOMATION_EVIDENCE.md) — Multi-role automated browser workflow (`Victim -> Coordinator -> Volunteer`) verification.
- **7. Sprint Review & Retrospective Notes**: [Word (`.docx`)](docs/Sprint_Review_and_Retrospective.docx) | [Markdown (`.md`)](docs/SPRINT_REVIEW_AND_RETROSPECTIVE.md) — Scope delivery across 13 JIRA user stories (`TEAM20-16` to `TEAM20-28`) and retrospective analysis.




## Sprint 4 security workflows

### Phone OTP registration

Public registration (`POST /auth/register` or the browser `/register` form) always creates a **Victim** account, regardless of any submitted role. The account is inactive until phone verification succeeds. OTPs are six digits, expire after five minutes by default, allow at most five incorrect attempts, are stored only as password hashes, and are single-use.

For a local demonstration without an SMS provider, enable the development-only delivery mode before starting Flask:

- Windows PowerShell: `$env:OTP_DEMO_MODE="1"`
- macOS/Linux: `export OTP_DEMO_MODE=1`

The OTP is printed to the Flask server console and included in the registration response/page **only** when this flag is enabled. Keep it disabled in production (`OTP_DEMO_MODE=0`). The demo code is not persisted in plaintext. In a production deployment, replace the console demonstration delivery with an approved SMS provider while keeping the verification endpoint and hashed challenge storage.

API verification: `POST /auth/verify-phone` with `{ "email": "...", "phone": "...", "otp": "123456" }`.

### Privileged account approval

An Admin may assign `Coordinator` or `Admin` to an existing account through `PATCH /auth/users/<user_id>/role`. Such a role change sets `approval_status` to `pending`, and the target cannot log in with privileged access until reviewed.

- `GET /auth/admin/pending-approvals` — list pending privileged accounts (Admin only).
- `POST /auth/admin/users/<user_id>/approval` — Admin-only JSON body: `{ "decision": "approve" }` or `{ "decision": "reject", "reason": "..." }`.

Rejected accounts remain blocked. A later role change by an Admin resets the approval state to pending. The approval reviewer and review timestamp are persisted. Public registration never accepts a privileged role. The Python `register_user` helper is intended for trusted internal provisioning/seed/test setup; it must not be exposed as a public endpoint.

### Database update

The application creates the new OTP table and applies additive columns to the existing `users` table at startup. Back up `disaster_relief.db` before deploying the update.
