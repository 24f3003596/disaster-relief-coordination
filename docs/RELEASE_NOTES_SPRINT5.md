# Release Notes — Disaster Relief Resource Coordination System

**Release Version**: 1.0.0 (Sprint 5 Final Release)  
**Release Date**: November 2, 2026  
**Project**: Disaster Relief Resource Coordination System (Team 20)  
**Target Environment**: Production / Staging  
**Quality Rating**: **Grade A (Cyclomatic Complexity: 4.96)** | **Test Pass Rate: 100% (149/149 Tests Passed)**  

---

## 1. Release Overview

Version 1.0.0 represents the final, production-ready release of the **Disaster Relief Resource Coordination System**. This milestone culminates five iterative sprints of collaborative development, rigorous verification, and quality engineering. The application provides an integrated, robust humanitarian logistics platform connecting citizens, emergency coordinators, field volunteers, and administrators.

---

## 2. What's New in Sprint 5

### 2.1 Chronological Activity History & Audit Trails (SRS FR 3.8.3)
- Relief requests and disaster incidents now feature a chronological audit history view (`/requests/<id>/history` and `/incidents/<id>/history`).
- Tracks entity creation, field edits, and all status transitions with actor attribution and human-readable event descriptions.
- Supports both interactive HTML rendering and machine-readable JSON representation (`?format=json`).
- Strict role isolation: Victims view only their own requests; Volunteers view assigned tasks; Coordinators and Admins view full operational history.

### 2.2 Leaflet Marker Clustering & Fallback Handling (SRS FR 3.8.1, FR 3.8.2)
- Upgraded the interactive geospatial disaster map with Leaflet.markercluster to group dense relief requests and incidents into visual clusters.
- Automatic fallback: If the external CDN resource is blocked or unavailable, the map gracefully reverts to individual markers without breaking the UI.
- Supports dynamic category, status, and viewport bounding-box filtering.

### 2.3 Automated Continuous Integration (CI) Pipeline
- Introduced a GitHub Actions workflow (`.github/workflows/ci.yml`) triggering on pushes and pull requests to `main`.
- Automates environment provisioning on Ubuntu Linux with Python 3.13/3.14, dependency installation, pytest suite execution, and JUnit XML test artifact publishing.

### 2.4 Database Backup, Integrity Checking & Recovery Utility
- Developed a standalone operational utility (`database_backup.py`) supporting:
  - Atomic database backup via SQLite online backup API.
  - Comprehensive database integrity checks (`PRAGMA integrity_check`).
  - Safe restoration into target databases.
  - Overwrite protection (`FileExistsError`) guarding against accidental data loss.

### 2.5 End-to-End User Acceptance Testing (UAT) Suite
- Added `tests/test_sprint5_uat.py` executing 10 comprehensive, multi-role user acceptance scenarios covering all functional requirements in SRS Sections 3.1 through 3.8.
- 100% pass rate achieved across all user scenarios.

---

## 3. Cumulative Sprint Delivery History

```
+---------------------------------------------------------------------------------------------------+
| SPRINT 1 (Foundations): Core Models, Public Registration, Relief Requests & Incidents            |
| SPRINT 2 (Operations):  Warehouse Inventory, Role Enforcement, Allocations & Volunteer Tasks       |
| SPRINT 3 (Integrity):   Atomic Consistency, Idempotency Guards, Regression Suite & Status FSM     |
| SPRINT 4 (Insights):    Disaster Map View, Admin Phone OTP & Approvals, Shortage Alerts & CSV    |
| SPRINT 5 (Acceptance):  Activity History, Map Clustering, CI Pipeline, DB Backup & Full UAT     |
+---------------------------------------------------------------------------------------------------+
```

| Sprint | Major Capabilities Delivered | Test Count | Defect Count | Quality Status |
|---|---|---|---|---|
| **Sprint 1** | User authentication, disaster incident logging, initial relief request intake | 30 tests | 5 logged / 5 fixed | Alpha Baseline |
| **Sprint 2** | Warehouse inventory tracking, volunteer dispatching, in-app notifications | 68 tests | 5 logged / 5 fixed | Beta Baseline |
| **Sprint 3** | Atomic stock deduction, idempotency protection, role security hardening | 100 tests | 8 logged / 8 fixed | RC 1 |
| **Sprint 4** | Leaflet map view, Admin approval queue, phone OTP, shortage alerts, CSV export | 126 tests | 4 logged / 4 fixed | RC 2 |
| **Sprint 5** | Activity history, marker clustering, CI/CD, backup utility, comprehensive UAT | **149 tests**| 5 logged / 5 fixed | **Production Ready** |

---

## 4. Quality & Non-Functional Verification

- **Automated Regression Suite**: 149 passed, 0 failures, 0 errors.
- **Cyclomatic Complexity (Radon CC)**: 413 blocks analyzed; average score: **Grade A (4.96)**.
- **Statement Code Coverage**: **83.8%** average across all active operational modules (`models.py`: 98%, `map_view.py`: 93%, `reports.py`: 92%, `dashboard.py`: 91%, `assignments.py`: 88%, `auth.py`: 85%, `database_backup.py`: 83%, `incidents.py`: 83%, `inventory.py`: 81%).
- **Security & Integrity**: Passwords hashed using Werkzeug PBKDF2; phone OTP challenges hashed; role tampering prevented; SQL injection guarded via SQLAlchemy ORM; cross-victim data isolated.

---

## 5. Resolved Defects in Sprint 5

| Defect ID | Severity | Component | Summary & Fix |
|---|---|---|---|
| **DEF-023** | Medium | `requests_module.py` | Asymmetric coordinates accepted. Fixed by enforcing mutual latitude/longitude presence. |
| **DEF-024** | Medium | `templates/map.html` | Marker clustering crash on CDN failure. Fixed with dynamic feature detection and fallback. |
| **DEF-025** | Low | `incidents.py` / `audit.py` | Missing actor name in incident activity. Fixed by joining `User.name` in audit response. |
| **DEF-026** | Medium | `database_backup.py` | Backup destination overwritten silently. Fixed by adding `FileExistsError` protection. |
| **DEF-027** | Low | `tests/test_sprint5_uat.py`| Password policy length edge case in fixtures. Standardized to 8+ characters. |

---

## 6. Installation & Deployment Guide

### 6.1 Prerequisites
- Python 3.11, 3.12, 3.13, or 3.14 (64-bit)
- Git (v2.30+)
- Virtual environment tool (`venv` or `virtualenv`)

### 6.2 Setup Steps
1. Clone the repository and navigate to project root:
   ```powershell
   git clone https://github.com/24f3003596/disaster-relief-coordination.git
   cd disaster-relief-coordination
   ```
2. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Configure environment settings:
   ```powershell
   Copy-Item .env.example .env
   ```
   Edit `.env` to configure `SECRET_KEY`, `DATABASE_URL`, and `OTP_DEMO_MODE`.

5. Run automated tests to verify deployment integrity:
   ```powershell
   pytest -v
   ```

6. Launch the application:
   ```powershell
   flask run --host=0.0.0.0 --port=5000
   ```
