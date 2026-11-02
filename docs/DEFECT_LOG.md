# Defect Log & Observations Dossier

**Project**: Disaster Relief Resource Coordination System (Team 20)  
**Sprint**: Sprint 5 (Final Release Review)  
**Date**: 2026-11-02  
**Total Confirmed Defects**: 27  
**Total Resolved**: 27 (100% Resolution Rate)  
**Open Defects**: 0  

---

## 1. Cumulative Defect Summary by Sprint

| Sprint | Defects Logged | Critical | High | Medium | Low | Resolved | Open | Resolution Rate |
|---|---|---|---|---|---|---|---|---|
| **Sprints 1–2** | 10 | 2 | 4 | 3 | 1 | 10 | 0 | 100% |
| **Sprint 3** | 8 | 1 | 3 | 3 | 1 | 8 | 0 | 100% |
| **Sprint 4** | 4 | 0 | 2 | 2 | 0 | 4 | 0 | 100% |
| **Sprint 5 (UAT)** | 5 | 0 | 1 | 3 | 1 | 5 | 0 | 100% |
| **Total** | **27** | **3** | **10** | **11** | **3** | **27** | **0** | **100%** |

---

## 2. Sprint 5 Defect Observations & Resolutions

### DEF-023: Incomplete Coordinate Pair Acceptance in Relief Request Intake
- **Severity**: Medium
- **Module**: `requests_module.py` / `models.py`
- **SRS Reference**: FR 3.3.4
- **Description**: Submitting a relief request with only latitude provided (or only longitude) caused partial coordinate records that caused geospatial map query errors.
- **Reproduction Steps**:
  1. POST `/requests/` with `latitude=13.08` and `longitude=None`.
  2. Request was saved with incomplete spatial data.
- **Root Cause**: Validation checked whether coordinates were numeric only when both were non-null, failing to reject asymmetric coordinate submissions.
- **Resolution**: Enforced mutual requirement: both latitude and longitude must be valid floats in [-90, 90] and [-180, 180], or both must be null.
- **Retest Evidence**: `test_requests.py::test_incomplete_coordinate_pair_is_rejected` ✅ PASS.

---

### DEF-024: Leaflet Marker Clustering Fallback on CDN Interruption
- **Severity**: Medium
- **Module**: `templates/map.html` / `map_view.py`
- **SRS Reference**: FR 3.8.2
- **Description**: If the CDN resource `leaflet.markercluster.js` failed to load or network was disconnected, the disaster map initialization threw `ReferenceError: L.markerClusterGroup is not defined` and stopped rendering all markers.
- **Reproduction Steps**:
  1. Block or disable external CDN resources in browser.
  2. Load `/map/`.
  3. Map canvas loaded but pins failed to render.
- **Root Cause**: Map rendering script unconditionally invoked `L.markerClusterGroup()` without detecting script availability.
- **Resolution**: Added feature detection in `templates/map.html`: if `L.markerClusterGroup` is unavailable, the map automatically falls back to standard `L.layerGroup()` with individual markers and displays a non-intrusive status indicator.
- **Retest Evidence**: `test_map_view.py::test_map_page_loads_marker_clustering_assets_and_fallback` ✅ PASS.

---

### DEF-025: Activity History Missing Actor Name on Incident Status Transitions
- **Severity**: Low
- **Module**: `incidents.py` / `audit.py`
- **SRS Reference**: FR 3.8.3
- **Description**: When coordinators transitioned incident statuses, the audit log recorded the action string but omitted the coordinator's name from chronological activity responses.
- **Reproduction Steps**:
  1. Transition incident status via PATCH `/incidents/<id>/status`.
  2. Query `/incidents/<id>/history?format=json`.
  3. `actor_name` was null in returned records.
- **Root Cause**: `update_incident_status` passed `actor_id` but did not join `User.name` in audit serialization.
- **Resolution**: Updated `list_entity_activity()` in `audit.py` to join `User` table and populate `actor_name`, falling back to `"System"` for automated actions.
- **Retest Evidence**: `test_activity_history.py::test_incident_activity_history_records_creation_and_status_transitions` ✅ PASS.

---

### DEF-026: Database Backup Overwrite Prevention
- **Severity**: Medium
- **Module**: `database_backup.py`
- **SRS Reference**: Non-Functional / Data Integrity
- **Description**: Invoking database backup with a destination path that already existed would overwrite existing backup files without warning, risking inadvertent data loss.
- **Reproduction Steps**:
  1. Run `create_backup(source, dest)` where `dest` already exists.
  2. Destination file was overwritten silently.
- **Root Cause**: Backup implementation did not verify destination existence before starting SQLite copy.
- **Resolution**: Added `if dest_path.exists(): raise FileExistsError("Destination file already exists")` before initiating backup and restore operations.
- **Retest Evidence**: `test_database_backup.py::test_backup_does_not_overwrite_existing_destination` ✅ PASS.

---

### DEF-027: Password Length Boundary Handling in Test Fixtures
- **Severity**: Low
- **Module**: `tests/test_sprint5_uat.py` / `auth.py`
- **SRS Reference**: FR 3.1.1
- **Description**: Initial UAT scenario fixtures used 7-character passwords (`Pass123`), violating the system's 8-character minimum security constraint.
- **Reproduction Steps**:
  1. Call `register_user(..., password="Pass123")`.
  2. Registration rejected with `ValueError: password must contain at least 8 characters`.
- **Root Cause**: Test fixture convenience values were below production security policy threshold.
- **Resolution**: Standardized test fixture credentials across all UAT scenarios to meet policy (`Pass12345` / `SecurePassword123`).
- **Retest Evidence**: `tests/test_sprint5_uat.py` (all 10 scenarios) ✅ PASS.

---

## 3. Cumulative Sprint 1 to 4 Defect Register

| ID | Title | Module | Severity | Resolution Summary |
|---|---|---|---|---|
| DEF-001 | Public registration role tampering | `auth.py` | Critical | Ignored user-supplied role; forced `ROLE_VICTIM`. |
| DEF-002 | Plaintext password storage | `auth.py` | Critical | Implemented Werkzeug `generate_password_hash`. |
| DEF-003 | Allocation without stock decrement | `assignments.py`| High | Added atomic `item.quantity -= alloc_qty`. |
| DEF-004 | Negative stock on over-allocation | `assignments.py`| High | Added strict quantity validation against stock. |
| DEF-005 | Double allocation on duplicate click | `assignments.py`| High | Enforced active assignment uniqueness check. |
| DEF-006 | Incident latitude range out of bounds | `incidents.py` | Medium | Added [-90, 90] and [-180, 180] validation. |
| DEF-007 | Unauthenticated relief request submission | `requests.py` | High | Enforced `@login_required` on all request routes. |
| DEF-008 | Cross-victim request visibility | `requests.py` | Medium | Filtered queries by authenticated `current_user.id`. |
| DEF-009 | Non-volunteer assigned to relief mission | `assignments.py`| Medium | Enforced `volunteer.role == ROLE_VOLUNTEER`. |
| DEF-010 | Missing audit trail on user login | `auth.py` | Low | Added `log_action(user_id, "LOGIN", ...)`. |
| DEF-011 | Inconsistent inventory state on allocation failure | `assignments.py`| High | Added atomic `db.session.rollback()` in exception handler. |
| DEF-012 | Repeated allocation attempt reduces inventory stock | `assignments.py`| High | Guarded allocation with idempotency check before DB write. |
| DEF-013 | Zero allocation quantity accepted | `assignments.py`| Medium | Validated `quantity_assigned > 0`. |
| DEF-014 | Negative inventory stock inward accepted | `inventory.py` | Medium | Validated `quantity > 0` on stock inward. |
| DEF-015 | Invalid severity string accepted for incidents | `incidents.py` | Low | Enforced `VALID_SEVERITIES` whitelist validation. |
| DEF-016 | Request status skipping workflow directly to Fulfilled | `requests.py` | High | Enforced status transition state machine rules. |
| DEF-017 | Non-admin user able to promote user roles | `auth.py` | Critical | Restricted `/auth/users/<id>/role` to `ROLE_ADMIN`. |
| DEF-018 | Unapproved privileged user able to log in | `auth.py` | High | Blocked login for pending/rejected accounts. |
| DEF-019 | Division by zero in dashboard on empty database | `dashboard.py` | High | Safe denominator checks with fallback to `0.0`. |
| DEF-020 | CSV export accessible by non-Admin coordinators | `reports.py` | Medium | Restricted export endpoints strictly to `ROLE_ADMIN`. |
| DEF-021 | Critical shortage notifications duplicated on updates | `notifications.py`| High | Added unread alert existence check for deduplication. |
| DEF-022 | Shortage notification triggered with 0 pending requests| `notifications.py`| Medium | Added pending request count check before alert creation. |

---

## 4. Defect Trend & Quality Assessment

```
Defects per Sprint:
Sprint 1-2: [##########] 10
Sprint 3:   [########]    8
Sprint 4:   [####]        4
Sprint 5:   [#####]       5 (all UAT edge cases resolved)

Open Defects: 0
Defect Resolution Rate: 100.0%
```

All confirmed defects across all sprints have been remediated with regression test coverage. No known defects or security vulnerabilities remain in the codebase.
