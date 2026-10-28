# Test Case Document — Review 2 Delivery
**Project**: Disaster Relief Resource Coordination System (Team 20)  
**Team Members**: Vishal K V, SIVANESH, Sree Naresh A  
**QA & Documentation Lead**: Sree Naresh A (TEAM20-57, TEAM20-58)  
**Execution Environment**: Python 3.14.5, pytest 9.1.1, SQLite In-Memory  
**Status**: **62 Test Cases Executed — 62 Passed (100% Pass Rate)**

---

## 1. Executive Summary

This formal Test Case Document specifies all automated regression test cases for the Disaster Relief Resource Coordination System for the Sprint 2 (Review 2) milestone. The test suite covers security, transactional integrity, boundary validations, role-based access control, resource allocation, and user interface workflows.

---

## 2. Master Test Case Register (All 62 Tests)

| Test ID | Module | Test Function Name | Focus / Precondition | Expected Result | Status |
|---|---|---|---|---|---|
| **TC-ASN-01** | Allocation | `test_allocate_updates_stock_request_and_notification` | Allocate 5 units of stock to volunteer | Stock decremented, request Assigned, volunteer notified | **PASSED** |
| **TC-ASN-02** | Allocation | `test_allocation_rejects_insufficient_stock_without_changes` | Request qty exceeds available inventory | Transaction rolls back, stock intact, status unchanged | **PASSED** |
| **TC-ASN-03** | Allocation | `test_complete_assignment_marks_request_fulfilled` | Volunteer completes assigned task | Assignment Completed, ReliefRequest Fulfilled | **PASSED** |
| **TC-ASN-04** | Allocation | `test_non_volunteer_cannot_be_assigned` | Attempt assigning task to Victim | HTTP 400 / ValueError rejected | **PASSED** |
| **TC-ASN-05** | Allocation | `test_allocation_rejects_nonexistent_request` | Nonexistent `request_id=9999` | Handled gracefully, returns error, stock unaffected | **PASSED** |
| **TC-ASN-06** | Allocation | `test_allocation_rejects_nonexistent_inventory` | Nonexistent `inventory_item_id=9999` | Handled gracefully, returns error | **PASSED** |
| **TC-ASN-07** | Allocation | `test_invalid_allocation_quantity_changes_nothing[0]` | Zero allocation quantity (`0`) | Rejected, stock intact | **PASSED** |
| **TC-ASN-08** | Allocation | `test_invalid_allocation_quantity_changes_nothing[-1]` | Negative allocation quantity (`-1`) | Rejected, stock intact | **PASSED** |
| **TC-ASN-09** | Allocation | `test_invalid_allocation_quantity_changes_nothing[invalid]` | Non-numeric string quantity (`"invalid"`) | Handled cleanly, rejected | **PASSED** |
| **TC-ASN-10** | Allocation | `test_allocation_rejects_duplicate_request` | Allocate request already Assigned | Duplicate allocation blocked | **PASSED** |
| **TC-AUD-01** | Audit | `test_log_action_and_listing` | Coordinator triggers audited event | AuditLog created with user, action, timestamp | **PASSED** |
| **TC-AUD-02** | Audit | `test_log_action_requires_action` | Action name missing | ValueError raised | **PASSED** |
| **TC-AUD-03** | Audit | `test_audit_routes_require_authorization` | Non-admin accesses `/audit/` | HTTP 403 Forbidden | **PASSED** |
| **TC-AUT-01** | Auth | `test_register_success` | Valid email and password registration | HTTP 201 Created, user persisted | **PASSED** |
| **TC-AUT-02** | Auth | `test_api_registration_cannot_choose_role[Admin]` | Malicious JSON POST `{"role": "Admin"}` | Role forced to `Victim`; privilege escalation blocked | **PASSED** |
| **TC-AUT-03** | Auth | `test_api_registration_cannot_choose_role[Coordinator]` | Malicious JSON POST `{"role": "Coordinator"}` | Role forced to `Victim`; escalation blocked | **PASSED** |
| **TC-AUT-04** | Auth | `test_api_registration_cannot_choose_role[Volunteer]` | Malicious JSON POST `{"role": "Volunteer"}` | Role forced to `Victim`; escalation blocked | **PASSED** |
| **TC-AUT-05** | Auth | `test_api_registration_cannot_choose_role[UnexpectedRole]` | Malicious JSON POST `{"role": "SuperUser"}` | Role forced to `Victim`; escalation blocked | **PASSED** |
| **TC-AUT-06** | Auth | `test_api_registration_cannot_choose_role[Victim]` | Legitimate JSON POST `{"role": "Victim"}` | Registered with role `Victim` | **PASSED** |
| **TC-AUT-07** | Auth | `test_html_registration_cannot_choose_role[Admin]` | Form POST with tampered field `role=Admin` | Registered user has role `Victim` | **PASSED** |
| **TC-AUT-08** | Auth | `test_html_registration_cannot_choose_role[Coordinator]` | Form POST with tampered field `role=Coordinator` | Registered user has role `Victim` | **PASSED** |
| **TC-AUT-09** | Auth | `test_html_registration_cannot_choose_role[Volunteer]` | Form POST with tampered field `role=Volunteer` | Registered user has role `Victim` | **PASSED** |
| **TC-AUT-10** | Auth | `test_registration_page_does_not_offer_role_selector` | GET `/register` page response | Role dropdown is absent; message informs Victim role | **PASSED** |
| **TC-AUT-11** | Auth | `test_register_duplicate_email` | Register existing email address | HTTP 400 Bad Request | **PASSED** |
| **TC-AUT-12** | Auth | `test_register_short_password` | Register with password `< 6` characters | HTTP 400 Bad Request | **PASSED** |
| **TC-AUT-13** | Auth | `test_login_success_and_wrong_password` | Valid vs wrong password login | HTTP 200 on valid; HTTP 401 on wrong | **PASSED** |
| **TC-AUT-14** | Auth | `test_password_is_hashed` | Inspect `User.password_hash` column | PBKDF2 hash stored; raw password never saved | **PASSED** |
| **TC-AUT-15** | Auth | `test_role_update_requires_authorization` | Unauthorized user calls role update endpoint | HTTP 401/403 returned | **PASSED** |
| **TC-AUT-16** | Auth | `test_admin_can_assign_role_through_protected_endpoint` | Admin promotes Victim to Volunteer | Role updated to Volunteer successfully | **PASSED** |
| **TC-DSH-01** | Dashboard | `test_dashboard_summary_metrics` | Aggregate requests, inventory, incidents | Accurate metric counts returned | **PASSED** |
| **TC-DSH-02** | Dashboard | `test_dashboard_routes` | Authorized Coordinator GET `/dashboard/` | HTTP 200 OK with summary KPIs | **PASSED** |
| **TC-E2E-01** | E2E | `test_register_request_allocate_complete_and_notify` | Complete browser workflow across roles | Full multi-role lifecycle verified | **PASSED** |
| **TC-INC-01** | Incidents | `test_create_incident_success` | Coordinator creates incident with coordinates | HTTP 201 Created | **PASSED** |
| **TC-INC-02** | Incidents | `test_incident_rejects_invalid_latitude` | Latitude `> 90` degrees | HTTP 400 Bad Request | **PASSED** |
| **TC-INC-03** | Incidents | `test_incident_requires_login` | Unauthenticated POST `/incidents/` | HTTP 401 Unauthorized | **PASSED** |
| **TC-INC-04** | Incidents | `test_list_affected_areas` | List active geographic incident zones | HTTP 200 OK with area summaries | **PASSED** |
| **TC-INT-01** | Integration | `test_main_pages_load` | HTTP GET across 11 application routes | All return HTTP 200/302 as expected | **PASSED** |
| **TC-INT-02** | Integration | `test_end_to_end_relief_workflow` | Multi-step request, stock deduction, dispatch | End-to-end integration confirmed | **PASSED** |
| **TC-INT-03** | Integration | `test_allocation_insufficient_stock_fails_atomically` | Atomicity test on allocation failure | Zero stock leakage, DB rolls back | **PASSED** |
| **TC-INT-04** | Integration | `test_automated_workflow_via_http_client` | Test client simulating real user actions | Complete HTTP session workflow passes | **PASSED** |
| **TC-INV-01** | Inventory | `test_create_inventory_item_success` | Create stock item with valid category & qty | HTTP 201 Created | **PASSED** |
| **TC-INV-02** | Inventory | `test_create_inventory_rejects_negative_quantity` | Quantity `< 0` | ValueError raised | **PASSED** |
| **TC-INV-03** | Inventory | `test_create_inventory_rejects_invalid_category` | Category outside allowed constants | ValueError raised | **PASSED** |
| **TC-INV-04** | Inventory | `test_create_inventory_rejects_negative_threshold` | Threshold `< 0` | ValueError raised | **PASSED** |
| **TC-INV-05** | Inventory | `test_boundary_threshold_low_stock` | Boundary testing at threshold (50 vs 51) | Low-stock flag evaluated correctly | **PASSED** |
| **TC-INV-06** | Inventory | `test_update_inventory_stock` | Restock and deduction adjustments | Accurate stock levels maintained | **PASSED** |
| **TC-INV-07** | Inventory | `test_inventory_routes_and_access` | Coordinator access vs unauthenticated access | Protected by authentication | **PASSED** |
| **TC-NOT-01** | Notifications | `test_mark_read_only_for_owner` | User attempts reading another user's alert | Unauthorized access blocked | **PASSED** |
| **TC-NOT-02** | Notifications | `test_broadcast_targets_operational_roles` | Emergency alert broadcast | Dispatched to Coordinators and Volunteers | **PASSED** |
| **TC-REP-01** | Reports | `test_summary_report_requires_login` | Unauthenticated GET `/reports/summary` | HTTP 401 Unauthorized | **PASSED** |
| **TC-REP-02** | Reports | `test_summary_report_forbidden_for_victim` | Victim role accesses `/reports/summary` | HTTP 403 Forbidden | **PASSED** |
| **TC-REP-03** | Reports | `test_summary_report_returns_counts` | Summary report aggregations | Accurate request and stock counts | **PASSED** |
| **TC-REP-04** | Reports | `test_relief_request_report_filters_by_status` | Filter requests by status (Pending, Assigned) | Correct filtered subsets returned | **PASSED** |
| **TC-REQ-01** | Requests | `test_create_relief_request_success` | Victim submits relief request | HTTP 201 Created with Pending status | **PASSED** |
| **TC-REQ-02** | Requests | `test_create_request_rejects_zero_or_negative_quantity` | Quantity `<= 0` | ValueError / HTTP 400 rejected | **PASSED** |
| **TC-REQ-03** | Requests | `test_create_request_rejects_invalid_coordinates` | Latitude/Longitude outside [-90,90],[-180,180] | Rejected with validation error | **PASSED** |
| **TC-REQ-04** | Requests | `test_update_request_status` | Status transition (Pending -> Assigned -> Fulfilled) | Valid transitions allowed | **PASSED** |
| **TC-REQ-05** | Requests | `test_relief_request_routes` | HTTP endpoints for requests | Correct HTTP status codes returned | **PASSED** |
| **TC-VOL-01** | Volunteers | `test_list_volunteers_returns_only_volunteer_role` | Query volunteer directory | Only users with role `Volunteer` returned | **PASSED** |
| **TC-VOL-02** | Volunteers | `test_get_volunteer_assignments_returns_assigned_tasks` | Query assigned tasks for volunteer | Accurate list of assignments returned | **PASSED** |
| **TC-VOL-03** | Volunteers | `test_get_volunteer_assignments_rejects_non_volunteer` | Query assignments for Victim user | Rejected with error | **PASSED** |
| **TC-VOL-04** | Volunteers | `test_get_volunteer_assignments_rejects_unknown_user` | Query assignments for nonexistent user | Handled gracefully with error | **PASSED** |
