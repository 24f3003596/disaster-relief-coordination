# Disaster Relief Resource Coordination System (Team 20)

**Software Engineering Project — Review 2 Delivery**

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
    └── test_end_to_end_workflow.py # Full lifecycle workflow tests
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
**Result**: 45 passed, 0 failures (100% pass rate) — verified on `main` @ `9ed4087`, Python 3.14.5, pytest 9.1.1.

### Run Test Coverage
```bash
pytest --cov=. --cov-report=term-missing
```
**Coverage**: **~76% statement coverage** across application modules (raw `pytest-cov` total is 44% because the `routes/` refactor package and `build_all_word_documents.py` are counted but not exercised by tests — see [`docs/CODE_COVERAGE_REPORT.md`](docs/CODE_COVERAGE_REPORT.md) for the full breakdown).

### Run Cyclomatic Complexity Check (Radon)
```bash
radon cc . -s -a
```
**Complexity Rating**: **Grade A (average 4.29)** across 79 analysed functions, methods, and classes (excluding doc-generation utilities).

---

## 🔄 Git Branching & Merge History

All team feature branches were developed on dedicated branch tracks and merged into `main` preserving commit authorship:

**Sprint 1 (Review 1)**
1. `feature/auth-incidents` by **Vishal K V** (PR #1 — merged)
2. `feature/relief-reports` by **Vishal K V** (PR #2 — merged)
3. `feature/sivanesh-assignments-notifications` by **SIVANESH** (merged via coordinator merge)
4. `naresh-feature` by **Sree Naresh A** (merged via coordinator merge)

**Sprint 2 (Review 2)**
5. `upload-sprint2` by **Vishal K V** (PR #3 — open, TEAM20-53/54: Fix public registration role escalation)
6. `feature/allocation-testing` by **SIVANESH** (PR pending — TEAM20-55/56: Expand allocation integration tests + fix dropdown)
7. `feature/test-documentation` by **Sree Naresh A** (this branch — TEAM20-57/58: Quality verification & documentation)

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

### Sprint 2 JIRA Tickets
| Ticket | Title | Assignee | Status |
|---|---|---|---|
| TEAM20-53 | Fix Public Registration Role Escalation | Vishal K V | Done |
| TEAM20-54 | Add Registration Security Regression Tests | Vishal K V | Done |
| TEAM20-55 | Expand Resource Allocation Integration Tests | SIVANESH | Done |
| TEAM20-56 | Validate Resource Allocation Failure Handling | SIVANESH | Done |
| TEAM20-57 | Full Test Suite and Quality Verification | Sree Naresh A | In Progress |
| TEAM20-58 | Update Technical Documentation and Review Evidence | Sree Naresh A | In Progress |

### Status for Review 2
45/45 tests pass on `main`. Sprint 2 feature branches are under review; integration into `main` is in progress per the defined git workflow.

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


