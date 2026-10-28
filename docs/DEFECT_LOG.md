# Project Defect Log — Review 2 Delivery
**Project**: Disaster Relief Resource Coordination System (Team 20)  
**Document Version**: 2.1.0  
**QA Lead**: Sree Naresh A (TEAM20-57, TEAM20-58)  
**Total Defects Logged**: 10 Defects  
**Total Defects Resolved**: 10 Defects (100% Resolution Rate)  
**Open Defects Remaining**: 0 Defects  
**Quality Verdict**: **VERIFIED & CLOSED**

---

## 1. Defect Classification & Severity Scheme

| Severity Level | Definition & Impact | SLA & Resolution Policy |
|---|---|---|
| **Critical** | System crash, transactional data corruption, stock leakage, or security / privilege escalation breach | Immediate hotfix prior to branch merge; mandatory regression tests |
| **High** | Primary feature malfunction, broken template rendering, or unauthorized access | Resolved within sprint milestone with dedicated regression test |
| **Medium** | Data boundary bypass, input validation omission, or missing error feedback | Resolved with input validation guards and unit tests |
| **Low** | Minor UI alignment, cosmetic label mismatch, or non-blocking logging issue | Resolved during polish and refactor phase |

---

## 2. Master Defect Register (DEF-001 to DEF-010)

| Defect ID | Module | Severity | Description & Root Cause | Resolution Details | Verification Test | Status |
|---|---|---|---|---|---|---|
| **DEF-001** | Inventory UI | High | Template Context Missing `items`: Route passed `inventory=items` while template used `{% for item in items %}`, rendering blank tables. | Updated `render_template()` to pass both `items=items` and `inventory=items` for backwards compatibility. | `test_inventory_routes_and_access` | **CLOSED** |
| **DEF-002** | Allocation | Critical | Non-Atomic Stock Deduction: Stock decremented before volunteer validation; on failure, stock remained deducted without rollback. | Wrapped stock deduction, assignment creation, and request update into a single atomic transaction with `try...except db.session.rollback()`. | `test_allocation_insufficient_stock_fails_atomically` | **CLOSED** |
| **DEF-003** | Incidents & Requests | Medium | Geographic Coordinates Boundary Bypass: Latitudes `> 90` and longitudes `> 180` accepted without validation. | Added explicit boundary checks (`-90 <= lat <= 90`, `-180 <= lon <= 180`), raising HTTP 400 Bad Request on violation. | `test_incident_rejects_invalid_latitude`, `test_create_request_rejects_invalid_coordinates` | **CLOSED** |
| **DEF-004** | Inventory | Medium | Negative Quantity & Threshold Acceptance: Intake allowed negative numbers (`quantity=-5`), breaking low-stock calculation logic. | Added input guards in `create_inventory_item()` raising `ValueError` for negative values. | `test_create_inventory_rejects_negative_quantity`, `test_create_inventory_rejects_negative_threshold` | **CLOSED** |
| **DEF-005** | Reports & Audit | High | Unauthorized Access to Coordinator Reports & Logs: Endpoints protected with `@login_required` instead of role checks, exposing metrics to victims. | Applied `@roles_required(['Coordinator', 'Admin'])` decorator; unauthorized roles receive HTTP 403 Forbidden. | `test_summary_report_forbidden_for_victim`, `test_audit_routes_require_authorization` | **CLOSED** |
| **DEF-006** | Authentication | Critical | Plaintext Password Exposure Risk: Registration scripts risked persisting raw passwords directly without cryptographic hashing. | Enforced salted PBKDF2-SHA256 password hashing via `werkzeug.security.generate_password_hash()`. | `test_password_is_hashed` | **CLOSED** |
| **DEF-007** | Notifications | High | Cross-User Notification Read Tampering: `mark_notification_read()` failed to check ownership, letting any user dismiss others' alerts. | Added ownership check: `if notification.user_id != user_id: raise ValueError('Unauthorized')`. | `test_mark_read_only_for_owner` | **CLOSED** |
| **DEF-008** | Volunteer Dispatch | Medium | Non-Volunteer Role Assigned to Delivery: Console permitted assigning Victim role to delivery tasks. | Added validation: `if user.role != ROLE_VOLUNTEER: raise ValueError('Assigned user must be a Volunteer')`. | `test_non_volunteer_cannot_be_assigned` | **CLOSED** |
| **DEF-009** | Authentication & RBAC | Critical | Public Registration Role Escalation Vulnerability (TEAM20-53): Callers could send `role="Admin"` or `"Coordinator"` during self-registration, granting themselves elevated privileges. | Hardcoded `role = ROLE_VICTIM` in public registration routes; removed role selector dropdown from `templates/register.html`; added admin-only role update endpoint. | `test_api_registration_cannot_choose_role`, `test_html_registration_cannot_choose_role` (9 tests) | **CLOSED** |
| **DEF-010** | Resource Allocation | High | Allocation Context & Edge Cases (TEAM20-55): Dropdown context missing requests on error; allocating nonexistent request/item or invalid quantity led to 500 error instead of graceful error feedback. | Created `assignments_page_context()` helper to ensure dropdowns always populate; added guards in `allocate_request()` for nonexistent IDs, invalid quantities, and duplicate assignments. | `test_allocation_rejects_nonexistent_request`, `test_invalid_allocation_quantity_changes_nothing` (8 tests) | **CLOSED** |

---

## 3. Resolution Summary

- **Total Logged Defects**: 10
- **Closed / Resolved**: 10 (100%)
- **Open / Deferred**: 0 (0%)
- **Zero regressions**: All 10 defects have automated regression tests in the test suite and pass on `main`.
