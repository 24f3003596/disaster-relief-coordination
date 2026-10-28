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

## 🔐 Public Registration and Role Security

Public registration through both `/auth/register` (JSON API) and `/register` (browser form) always creates a `Victim` account. Any `role` value submitted by a public client is ignored; users cannot grant themselves `Volunteer`, `Coordinator`, or `Admin` permissions. The browser registration form does not offer a role selector. Role changes are handled through `PATCH /auth/users/<user_id>/role`, which requires an authenticated `Admin` account.

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
Use the actual output from your current checkout as the source of truth. Test counts, coverage, and complexity metrics must be regenerated after code or tests change; previously recorded figures may no longer apply.

### Run Test Coverage
```bash
pytest --cov=. --cov-report=term-missing
```

### Run Cyclomatic Complexity Check (Radon)
```bash
radon cc . -s -a
```

---

## 🔄 Git Branching & Merge History

All team feature branches were developed on dedicated branch tracks and merged into `main` preserving commit authorship:
1. `feature/auth-incidents` by **Vishal K V** (PR #1)
2. `feature/relief-reports` by **Vishal K V** (PR #2)
3. `feature/sivanesh-assignments-notifications` by **SIVANESH**
4. `naresh-feature` by **Sree Naresh A**

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
- **Sprint 2 (Operations, Coordination & Delivery)**: Relief requests intake, Volunteer assignment & atomic stock deduction, Notifications & emergency broadcast, Analytics dashboard, Audit logging (`TEAM20-20` through `TEAM20-28`).

### Status for Review 2
All sprint user stories and subtasks are marked **Done** in accordance with the 100% passing test suite and demonstrable live increment.
