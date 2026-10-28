# Test Execution Report — Sprint 2 Baseline
**Project**: Disaster Relief Resource Coordination System (Team 20)  
**Branch**: `main` @ commit `9ed4087`  
**Executed by**: Sree Naresh A (TEAM20-57)  
**Execution Date**: 2026-10-28  
**Environment**: Windows 11, Python 3.14.5, pytest 9.1.1, pytest-cov 7.1.0

---

## Execution Summary

| Metric | Value |
|---|---|
| Total collected | 45 |
| **Passed** | **45** |
| Failed | 0 |
| Errors | 0 |
| Warnings | 12 (non-blocking, see below) |
| **Pass Rate** | **100%** |
| **Execution Time** | **9.15 s** |

---

## Test Execution Log

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\disaster-relief-coordination-main
plugins: anyio-4.14.2, asyncio-1.4.0, cov-7.1.0
collected 45 items

tests/test_assignments.py::test_allocate_updates_stock_request_and_notification PASSED [  2%]
tests/test_assignments.py::test_allocation_rejects_insufficient_stock_without_changes PASSED [  4%]
tests/test_assignments.py::test_complete_assignment_marks_request_fulfilled PASSED [  6%]
tests/test_assignments.py::test_non_volunteer_cannot_be_assigned PASSED  [  8%]
tests/test_audit.py::test_log_action_and_listing PASSED                  [ 11%]
tests/test_audit.py::test_log_action_requires_action PASSED              [ 13%]
tests/test_audit.py::test_audit_routes_require_authorization PASSED      [ 15%]
tests/test_auth.py::test_register_success PASSED                         [ 17%]
tests/test_auth.py::test_register_duplicate_email PASSED                 [ 20%]
tests/test_auth.py::test_register_short_password PASSED                  [ 22%]
tests/test_auth.py::test_login_success_and_wrong_password PASSED         [ 24%]
tests/test_auth.py::test_password_is_hashed PASSED                       [ 26%]
tests/test_dashboard.py::test_dashboard_summary_metrics PASSED           [ 28%]
tests/test_dashboard.py::test_dashboard_routes PASSED                    [ 31%]
tests/test_end_to_end_workflow.py::test_register_request_allocate_complete_and_notify PASSED [ 33%]
tests/test_incidents.py::test_create_incident_success PASSED             [ 35%]
tests/test_incidents.py::test_incident_rejects_invalid_latitude PASSED   [ 37%]
tests/test_incidents.py::test_incident_requires_login PASSED             [ 40%]
tests/test_incidents.py::test_list_affected_areas PASSED                 [ 42%]
tests/test_integration.py::test_main_pages_load PASSED                   [ 44%]
tests/test_integration.py::test_end_to_end_relief_workflow PASSED        [ 46%]
tests/test_integration.py::test_allocation_insufficient_stock_fails_atomically PASSED [ 48%]
tests/test_integration.py::test_automated_workflow_via_http_client PASSED [ 51%]
tests/test_inventory.py::test_create_inventory_item_success PASSED       [ 53%]
tests/test_inventory.py::test_create_inventory_rejects_negative_quantity PASSED [ 55%]
tests/test_inventory.py::test_create_inventory_rejects_invalid_category PASSED [ 57%]
tests/test_inventory.py::test_create_inventory_rejects_negative_threshold PASSED [ 60%]
tests/test_inventory.py::test_boundary_threshold_low_stock PASSED        [ 62%]
tests/test_inventory.py::test_update_inventory_stock PASSED              [ 64%]
tests/test_inventory.py::test_inventory_routes_and_access PASSED         [ 66%]
tests/test_notifications.py::test_mark_read_only_for_owner PASSED        [ 68%]
tests/test_notifications.py::test_broadcast_targets_operational_roles PASSED [ 71%]
tests/test_reports.py::test_summary_report_requires_login PASSED         [ 73%]
tests/test_reports.py::test_summary_report_forbidden_for_victim PASSED   [ 75%]
tests/test_reports.py::test_summary_report_returns_counts PASSED         [ 77%]
tests/test_reports.py::test_relief_request_report_filters_by_status PASSED [ 80%]
tests/test_requests.py::test_create_relief_request_success PASSED        [ 82%]
tests/test_requests.py::test_create_request_rejects_zero_or_negative_quantity PASSED [ 84%]
tests/test_requests.py::test_create_request_rejects_invalid_coordinates PASSED [ 86%]
tests/test_requests.py::test_update_request_status PASSED                [ 88%]
tests/test_requests.py::test_relief_request_routes PASSED                [ 91%]
tests/test_volunteers.py::test_list_volunteers_returns_only_volunteer_role PASSED [ 93%]
tests/test_volunteers.py::test_get_volunteer_assignments_returns_assigned_tasks PASSED [ 95%]
tests/test_volunteers.py::test_get_volunteer_assignments_rejects_non_volunteer PASSED [ 97%]
tests/test_volunteers.py::test_get_volunteer_assignments_rejects_unknown_user PASSED [100%]

============================= 45 passed in 9.15s ==============================
```

---

## Warnings Analysis

All 12 warnings are `ResourceWarning: unclosed database` from SQLAlchemy's connection pool during test teardown. These are non-blocking — all 45 assertions pass successfully. The warnings arise because Python 3.14 applies stricter resource tracking to SQLite connections that SQLAlchemy closes lazily via its pool. No application behaviour is affected.

---

## Coverage Summary (from `pytest --cov=. --cov-report=term-missing`)

- **Application modules** (auth, assignments, inventory, requests, incidents, notifications, reports, dashboard, audit, volunteers, models, constants, extensions): **~76% coverage**
- Raw `pytest-cov` total: **44%** (includes `routes/` shadow package at 0% and `build_all_word_documents.py` doc-generation script at 0%)
- All 13 test files: **100% coverage**

---

## Defect Status

No failing tests. All 8 previously logged defects (Sprint 1 defect log) are resolved. Sprint 2 defects being tracked:
- `DEF-S2-01`: Public registration role escalation — **Fixed** by Vishal (upload-sprint2, TEAM20-53)
- `DEF-S2-02`: Assignment dropdowns empty on page load — **Fixed** by Sivanesh (feature/allocation-testing, TEAM20-56)
