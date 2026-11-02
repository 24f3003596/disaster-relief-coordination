# Defect Log & Observations Dossier

**Project**: Disaster Relief Resource Coordination System (Team 20)  
**Sprint**: Sprint 6 (Review 6 Delivery)  
**Date**: 2026-11-02  
**Total Confirmed Defects**: 30  
**Total Resolved**: 30 (100% Resolution Rate)  
**Open Defects**: 0  

---

## 1. Cumulative Defect Summary by Sprint

| Sprint | Defects Logged | Critical | High | Medium | Low | Resolved | Open | Resolution Rate |
|---|---|---|---|---|---|---|---|---|
| **Sprints 1–2** | 10 | 2 | 4 | 3 | 1 | 10 | 0 | 100% |
| **Sprint 3** | 8 | 1 | 3 | 3 | 1 | 8 | 0 | 100% |
| **Sprint 4** | 4 | 0 | 2 | 2 | 0 | 4 | 0 | 100% |
| **Sprint 5** | 5 | 0 | 1 | 3 | 1 | 5 | 0 | 100% |
| **Sprint 6** | 3 | 0 | 2 | 1 | 0 | 3 | 0 | 100% |
| **Total** | **30** | **3** | **12** | **12** | **3** | **30** | **0** | **100%** |

---

## 2. Sprint 6 Defect Observations & Resolutions

### DEF-028: Expired Inventory Items Eligible for Allocation
- **Severity**: High
- **Module**: `assignments.py`
- **SRS Reference**: FR 3.4.1, FR 3.5.1
- **Description**: Inventory items with an `expiry_date` strictly before the current date could be successfully allocated to relief requests, posing serious safety and regulatory risks during disaster relief.
- **Reproduction Steps**:
  1. Create an inventory item with `expiry_date = today - 3 days`.
  2. Invoke `allocate_request(request_id, volunteer_id, expired_item_id)`.
  3. The allocation succeeded and decremented expired stock.
- **Root Cause**: `allocate_request` verified category match and quantity, but lacked date validation against `item.expiry_date`.
- **Resolution**: Added temporal validation in `allocate_request`: if `item.expiry_date < datetime.now(timezone.utc).date()`, raise `ValueError("Cannot allocate expired inventory items")`.
- **Retest Evidence**: `test_inventory_resource_consistency.py::test_expired_inventory_cannot_be_allocated` ✅ PASS.

---

### DEF-029: Unapproved or Inactive Volunteers Eligible for Mission Dispatch
- **Severity**: High
- **Module**: `assignments.py`
- **SRS Reference**: FR 3.1.4, FR 3.5.2
- **Description**: Volunteer accounts pending administrative review (`approval_status == 'pending'`) or deactivated accounts (`is_active == False`) could be dispatched to relief requests.
- **Reproduction Steps**:
  1. Register a volunteer account with `approval_status = "pending"`.
  2. Invoke `allocate_request(request_id, pending_volunteer_id, item_id)`.
  3. Assignment task was created for the unverified user.
- **Root Cause**: Validation checked `volunteer.role == ROLE_VOLUNTEER` but did not verify `approval_status == 'approved'` or `is_active`.
- **Resolution**: Enforced strict status verification: `if volunteer.approval_status != "approved" or not volunteer.is_active: raise ValueError("Volunteer must be active and approved")`.
- **Retest Evidence**: `test_inventory_resource_consistency.py::test_unapproved_or_inactive_volunteer_rejected_from_allocation` ✅ PASS.

---

### DEF-030: Multi-Table Transaction Failure Atomicity Guarantee
- **Severity**: Medium
- **Module**: `assignments.py`
- **SRS Reference**: FR 3.4.3, FR 3.5.1
- **Description**: If a network interruption or unexpected database constraint failure occurred during multi-table writes (stock decrement, task creation, dual notifications, audit trail), the database session could retain dirty states.
- **Reproduction Steps**:
  1. Simulate mid-transaction failure during `db.session.commit()`.
  2. Observe whether dirty entities persist in session.
- **Root Cause**: While outer try-except existed, explicit test verification of transactional rollback on simulated commit failures was absent.
- **Resolution**: Enhanced rollback guarantees: wrapped all multi-table mutations in transactional try-except with explicit `db.session.rollback()` and comprehensive regression tests.
- **Retest Evidence**: `test_inventory_resource_consistency.py::test_allocation_atomic_rollback_on_database_commit_failure` ✅ PASS.

---

## 3. Cumulative Sprint 1 to 5 Defect Register

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
| DEF-023 | Asymmetric coordinate pair accepted | `requests_module.py` | Medium | Enforced mutual latitude/longitude presence. |
| DEF-024 | Marker clustering crash on CDN failure | `templates/map.html` | Medium | Added dynamic CDN detection and layer group fallback. |
| DEF-025 | Missing actor name in incident activity | `incidents.py` / `audit.py` | Low | Joined `User.name` in audit response. |
| DEF-026 | Backup destination overwritten silently | `database_backup.py` | Medium | Added `FileExistsError` target protection. |
| DEF-027 | Password policy length edge case in fixtures | `test_sprint5_uat.py` | Low | Standardized fixtures to 8+ characters. |
| DEF-028 | Expired inventory items allocated to relief requests | `assignments.py` | High | Added `item.expiry_date` validation check. |
| DEF-029 | Unapproved/inactive volunteers assigned to relief tasks | `assignments.py` | High | Enforced `approval_status == 'approved'` and `is_active`. |
| DEF-030 | Multi-table transaction failure atomicity guarantee | `assignments.py` | Medium | Added atomic rollback handling and regression tests. |

---

## 4. Defect Trend & Quality Assessment

```
Defects per Sprint:
Sprint 1-2: [##########] 10
Sprint 3:   [########]    8
Sprint 4:   [####]        4
Sprint 5:   [#####]       5
Sprint 6:   [###]         3

Total Logged: 30 | Total Resolved: 30 | Open: 0
Defect Resolution Rate: 100.0%
```

All 30 confirmed defects across all 6 sprints have been resolved with regression test coverage. No open defects remain.
