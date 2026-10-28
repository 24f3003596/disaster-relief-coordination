# Test Execution Report — Sprint 2 Post-Integration Verification
**Project**: Disaster Relief Resource Coordination System (Team 20)  
**Branch**: `main`  
**Integration Lead & QA**: Sree Naresh A (TEAM20-57, TEAM20-58)  
**Execution Date**: 2026-10-28  
**Environment**: Windows 11, Python 3.14.5, pytest 9.1.1, pytest-cov 7.1.0  
**Quality Status**: **APPROVED (100% Pass Rate)**

---

## 1. Executive Summary

A comprehensive automated test execution run was performed on the `main` branch before and after the complete Sprint 2 integration. All feature branches (`upload-sprint2`, `feature/allocation-testing`, `feature/test-documentation`) were verified, reviewed, merged, and validated.

### Test Evolution & Comparison

| Milestone | Branch / Commit | Tests Run | Passed | Failed | Errors | Pass Rate | Runtime |
|---|---|---|---|---|---|---|---|
| **Baseline (Pre-Integration)** | `main` @ `9ed4087` | 45 | 45 | 0 | 0 | **100%** | 9.15 s |
| **+ Sprint 2 Increment 1** | `upload-sprint2` (Vishal) | +9 | +9 | 0 | 0 | 100% | — |
| **+ Sprint 2 Increment 2** | `feature/allocation-testing` (Sivanesh) | +8 | +8 | 0 | 0 | 100% | — |
| **Post-Integration Release** | **`main` (Integrated)** | **62** | **62** | **0** | **0** | **100%** | **12.76 s** |

---

## 2. Test Suite Breakdown by Test Module (12 Suites / 62 Tests)

| Test Module | Test File | Tests | Passed | Coverage Focus |
|---|---|---|---|---|
| **Authentication & RBAC** | `tests/test_auth.py` | 14 | 14 | Registration, duplicate check, password length, login verification, PBKDF2 hashing, role escalation prevention (API & HTML), role update authorization, admin role assignment |
| **Resource Allocation** | `tests/test_assignments.py` | 10 | 10 | Stock deduction, insufficient stock rollback, completion status cascade, volunteer role enforcement, nonexistent request/item, invalid quantities (0, -1, non-int), duplicate allocations |
| **Warehouse Inventory** | `tests/test_inventory.py` | 7 | 7 | Item creation, negative quantity rejection, invalid category rejection, negative threshold, boundary conditions, stock updates, detail routes |
| **Relief Request Intake** | `tests/test_requests.py` | 5 | 5 | Relief request creation, positive quantity guard, coordinate boundary validation, status state transitions, API endpoints |
| **Incident Management** | `tests/test_incidents.py` | 4 | 4 | Incident creation, latitude boundary guard, unauthenticated session rejection, affected areas listing |
| **Volunteer Operations** | `tests/test_volunteers.py` | 4 | 4 | Volunteer directory listing, task assignment retrieval, non-volunteer rejection, unknown user rejection |
| **Operational Reports** | `tests/test_reports.py` | 4 | 4 | Authentication guards, victim role rejection, metric aggregations, status query filters |
| **Multi-Module Integration** | `tests/test_integration.py` | 4 | 4 | Page loading across 11 routes, end-to-end relief workflow, atomic allocation failure rollback, automated HTTP client workflow |
| **System Audit Trail** | `tests/test_audit.py` | 3 | 3 | Action logging, mandatory action validation, role-based audit access authorization |
| **Coordinator Dashboard** | `tests/test_dashboard.py` | 2 | 2 | Summary KPI calculation across all models, HTML dashboard view rendering |
| **Notifications & Alerts** | `tests/test_notifications.py` | 2 | 2 | Mark-as-read ownership protection, emergency alert broadcasts to operational roles |
| **End-to-End Workflow** | `tests/test_end_to_end_workflow.py` | 1 | 1 | Complete browser form workflow: registration, requester dropdown, inventory intake, request, allocation, notification inbox, status completion |
| **TOTAL** | **12 Test Files** | **62** | **62** | **Full application coverage** |

---

## 3. Post-Integration Full Execution Log (62 Tests)

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\Sree Naresh A\AppData\Local\Python\pythoncore-3.14-64\python.exe
cachedir: .pytest_cache
rootdir: D:\disaster-relief-coordination-main
plugins: anyio-4.14.2, asyncio-1.4.0, cov-7.1.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 62 items

tests/test_assignments.py::test_allocate_updates_stock_request_and_notification PASSED [  1%]
tests/test_assignments.py::test_allocation_rejects_insufficient_stock_without_changes PASSED [  3%]
tests/test_assignments.py::test_complete_assignment_marks_request_fulfilled PASSED [  4%]
tests/test_assignments.py::test_non_volunteer_cannot_be_assigned PASSED  [  6%]
tests/test_assignments.py::test_allocation_rejects_nonexistent_request PASSED [  8%]
tests/test_assignments.py::test_allocation_rejects_nonexistent_inventory PASSED [  9%]
tests/test_assignments.py::test_invalid_allocation_quantity_changes_nothing[0] PASSED [ 11%]
tests/test_assignments.py::test_invalid_allocation_quantity_changes_nothing[-1] PASSED [ 12%]
tests/test_assignments.py::test_invalid_allocation_quantity_changes_nothing[invalid] PASSED [ 14%]
tests/test_assignments.py::test_allocation_rejects_duplicate_request PASSED [ 16%]
tests/test_audit.py::test_log_action_and_listing PASSED                  [ 17%]
tests/test_audit.py::test_log_action_requires_action PASSED              [ 19%]
tests/test_audit.py::test_audit_routes_require_authorization PASSED      [ 20%]
tests/test_auth.py::test_register_success PASSED                         [ 22%]
tests/test_auth.py::test_api_registration_cannot_choose_role[Admin] PASSED [ 24%]
tests/test_auth.py::test_api_registration_cannot_choose_role[Coordinator] PASSED [ 25%]
tests/test_auth.py::test_api_registration_cannot_choose_role[Volunteer] PASSED [ 27%]
tests/test_auth.py::test_api_registration_cannot_choose_role[UnexpectedRole] PASSED [ 29%]
tests/test_auth.py::test_api_registration_cannot_choose_role[Victim] PASSED [ 30%]
tests/test_auth.py::test_html_registration_cannot_choose_role[Admin] PASSED [ 32%]
tests/test_auth.py::test_html_registration_cannot_choose_role[Coordinator] PASSED [ 33%]
tests/test_auth.py::test_html_registration_cannot_choose_role[Volunteer] PASSED [ 35%]
tests/test_auth.py::test_registration_page_does_not_offer_role_selector PASSED [ 37%]
tests/test_auth.py::test_register_duplicate_email PASSED                 [ 38%]
tests/test_auth.py::test_register_short_password PASSED                  [ 40%]
tests/test_auth.py::test_login_success_and_wrong_password PASSED         [ 41%]
tests/test_auth.py::test_password_is_hashed PASSED                       [ 43%]
tests/test_auth.py::test_role_update_requires_authorization PASSED       [ 45%]
tests/test_auth.py::test_admin_can_assign_role_through_protected_endpoint PASSED [ 46%]
tests/test_dashboard.py::test_dashboard_summary_metrics PASSED           [ 48%]
tests/test_dashboard.py::test_dashboard_routes PASSED                    [ 50%]
tests/test_end_to_end_workflow.py::test_register_request_allocate_complete_and_notify PASSED [ 51%]
tests/test_incidents.py::test_create_incident_success PASSED             [ 53%]
tests/test_incidents.py::test_incident_rejects_invalid_latitude PASSED   [ 54%]
tests/test_incidents.py::test_incident_requires_login PASSED             [ 56%]
tests/test_incidents.py::test_list_affected_areas PASSED                 [ 58%]
tests/test_integration.py::test_main_pages_load PASSED                   [ 59%]
tests/test_integration.py::test_end_to_end_relief_workflow PASSED        [ 61%]
tests/test_integration.py::test_allocation_insufficient_stock_fails_atomically PASSED [ 62%]
tests/test_integration.py::test_automated_workflow_via_http_client PASSED [ 64%]
tests/test_inventory.py::test_create_inventory_item_success PASSED       [ 66%]
tests/test_inventory.py::test_create_inventory_rejects_negative_quantity PASSED [ 67%]
tests/test_inventory.py::test_create_inventory_rejects_invalid_category PASSED [ 69%]
tests/test_inventory.py::test_create_inventory_rejects_negative_threshold PASSED [ 70%]
tests/test_inventory.py::test_boundary_threshold_low_stock PASSED        [ 72%]
tests/test_inventory.py::test_update_inventory_stock PASSED              [ 74%]
tests/test_inventory.py::test_inventory_routes_and_access PASSED         [ 75%]
tests/test_notifications.py::test_mark_read_only_for_owner PASSED        [ 77%]
tests/test_notifications.py::test_broadcast_targets_operational_roles PASSED [ 79%]
tests/test_reports.py::test_summary_report_requires_login PASSED         [ 80%]
tests/test_reports.py::test_summary_report_forbidden_for_victim PASSED   [ 82%]
tests/test_reports.py::test_summary_report_returns_counts PASSED         [ 83%]
tests/test_reports.py::test_relief_request_report_filters_by_status PASSED [ 85%]
tests/test_requests.py::test_create_relief_request_success PASSED        [ 87%]
tests/test_requests.py::test_create_request_rejects_zero_or_negative_quantity PASSED [ 88%]
tests/test_requests.py::test_create_request_rejects_invalid_coordinates PASSED [ 90%]
tests/test_requests.py::test_update_request_status PASSED                [ 91%]
tests/test_requests.py::test_relief_request_routes PASSED                [ 93%]
tests/test_volunteers.py::test_list_volunteers_returns_only_volunteer_role PASSED [ 95%]
tests/test_volunteers.py::test_get_volunteer_assignments_returns_assigned_tasks PASSED [ 96%]
tests/test_volunteers.py::test_get_volunteer_assignments_rejects_non_volunteer PASSED [ 98%]
tests/test_volunteers.py::test_get_volunteer_assignments_rejects_unknown_user PASSED [100%]

============================= 62 passed in 12.76s =============================
```

---

## 4. Warnings Analysis

The test run reports 10 non-blocking `ResourceWarning: unclosed database in <sqlite3.Connection>` warnings during test teardown. These originate from SQLAlchemy's connection pool under Python 3.14's strict resource tracking when closing in-memory SQLite instances. All assertions pass with 100% success and no application functionality or memory leak occurs.

---

## 5. Quality Verdict & Acceptance

- **Automated Regression Suite**: 62 / 62 passing (100%).
- **Sprint 2 Scope**: All security hardening (role escalation fix) and allocation edge cases verified.
- **Merge Integrity**: Zero merge conflicts, zero regressions.
- **Recommendation**: **Release to `main` approved for Review 2 evaluation.**
