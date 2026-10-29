# Test Case Document — Sprint 3 (Review 3)

**Project**: Disaster Relief Resource Coordination System (Team 20)
**Branch**: `main` (post Sprint 3 integration)
**Date**: 2026-10-29
**Total Test Cases**: 94

---

## TC-001 to TC-010 — Assignment Module (`test_assignments.py`)

| ID | Test Name | Input | Expected | Status |
|---|---|---|---|---|
| TC-001 | `test_allocate_updates_stock_request_and_notification` | Valid request, volunteer, item | Stock decremented; request → Assigned; notification created | ✅ PASS |
| TC-002 | `test_allocation_rejects_insufficient_stock_without_changes` | quantity > available stock | 400 / ValueError; stock unchanged | ✅ PASS |
| TC-003 | `test_complete_assignment_marks_request_fulfilled` | Complete valid assignment | Status → Completed; request → Fulfilled | ✅ PASS |
| TC-004 | `test_non_volunteer_cannot_be_assigned` | Victim user as volunteer_id | ValueError raised | ✅ PASS |
| TC-005 | `test_allocation_rejects_nonexistent_request` | Invalid request_id | ValueError raised | ✅ PASS |
| TC-006 | `test_allocation_rejects_nonexistent_inventory` | Invalid item_id | ValueError raised | ✅ PASS |
| TC-007 | `test_invalid_allocation_quantity_changes_nothing[0]` | quantity_assigned=0 | ValueError raised; no side effects | ✅ PASS |
| TC-008 | `test_invalid_allocation_quantity_changes_nothing[-1]` | quantity_assigned=-1 | ValueError raised; no side effects | ✅ PASS |
| TC-009 | `test_invalid_allocation_quantity_changes_nothing[invalid]` | quantity_assigned="invalid" | ValueError raised; no side effects | ✅ PASS |
| TC-010 | `test_allocation_rejects_duplicate_request` | Active assignment exists | ValueError "already has an assignment" | ✅ PASS |

---

## TC-011 to TC-013 — Audit Trail (`test_audit.py`)

| ID | Test Name | Input | Expected | Status |
|---|---|---|---|---|
| TC-011 | `test_log_action_and_listing` | `log_action(action="LOGIN", ...)` | AuditLog row created; listing returns it | ✅ PASS |
| TC-012 | `test_log_action_requires_action` | `log_action()` without action | ValueError raised | ✅ PASS |
| TC-013 | `test_audit_routes_require_authorization` | Unauthenticated GET /audit/ | 401 / redirect | ✅ PASS |

---

## TC-014 to TC-030 — Authentication (`test_auth.py`)

| ID | Test Name | Input | Expected | Status |
|---|---|---|---|---|
| TC-014 | `test_register_success` | Valid name/email/password | 201 / user created as Victim | ✅ PASS |
| TC-015–019 | `test_api_registration_cannot_choose_role[*]` | role=Admin/Coordinator/Volunteer/etc. via JSON | Role ignored; user created as Victim | ✅ PASS |
| TC-020–022 | `test_html_registration_cannot_choose_role[*]` | role= via form | Role ignored; user created as Victim | ✅ PASS |
| TC-023 | `test_registration_page_does_not_offer_role_selector` | GET /register | Response HTML has no role `<select>` element | ✅ PASS |
| TC-024 | `test_register_duplicate_email` | Existing email | 409 Conflict | ✅ PASS |
| TC-025 | `test_register_short_password` | password < 8 chars | 400 Bad Request | ✅ PASS |
| TC-026 | `test_login_success_and_wrong_password` | Correct / wrong password | 200 success; 401 failure | ✅ PASS |
| TC-027 | `test_password_is_hashed` | Register then read DB | `password_hash` != raw password | ✅ PASS |
| TC-028 | `test_role_update_requires_authorization` | Non-Admin PATCH /auth/users/1/role | 401 or 403 | ✅ PASS |
| TC-029 | `test_admin_can_assign_role_through_protected_endpoint` | Admin PATCH /auth/users/1/role | Role updated; 200 | ✅ PASS |

---

## TC-030 to TC-031 — Dashboard (`test_dashboard.py`)

| ID | Test Name | Input | Expected | Status |
|---|---|---|---|---|
| TC-030 | `test_dashboard_summary_metrics` | Coordinator session + seeded data | Counts match DB state | ✅ PASS |
| TC-031 | `test_dashboard_routes` | GET /dashboard/ as Coordinator | 200 OK | ✅ PASS |

---

## TC-032 — End-to-End Workflow (`test_end_to_end_workflow.py`)

| ID | Test Name | Input | Expected | Status |
|---|---|---|---|---|
| TC-032 | `test_register_request_allocate_complete_and_notify` | Full lifecycle: register → request → allocate → complete | Request Fulfilled; notification delivered | ✅ PASS |

---

## TC-033 to TC-040 — Incidents (`test_incidents.py`)

| ID | Test Name | Input | Expected | Status |
|---|---|---|---|---|
| TC-033 | `test_create_incident_success` | Valid incident payload | 201; incident in DB | ✅ PASS |
| TC-034 | `test_incident_rejects_invalid_latitude` | latitude=200 | 400 Bad Request | ✅ PASS |
| TC-035 | `test_incident_requires_login` | POST /incidents/ unauthenticated | 401 | ✅ PASS |
| TC-036 | `test_list_affected_areas` | GET /incidents/affected-areas | 200; list of areas | ✅ PASS |
| TC-037 | `test_incident_can_be_viewed_edited_and_transitioned` | PATCH /incidents/1 + status transition | Data updated; status advanced | ✅ PASS |
| TC-038 | `test_incident_edit_rejects_invalid_data` | Invalid severity | 400 | ✅ PASS |
| TC-039 | `test_incident_mutations_require_coordinator_or_admin` | Victim POST /incidents/ | 403 | ✅ PASS |
| TC-040 | `test_incident_rejects_non_object_payload` | POST /incidents/ with list body | 400 | ✅ PASS |

---

## TC-041 to TC-044 — Integration (`test_integration.py`)

| ID | Test Name | Input | Expected | Status |
|---|---|---|---|---|
| TC-041 | `test_main_pages_load` | GET /, /login, /register | 200 OK for all | ✅ PASS |
| TC-042 | `test_end_to_end_relief_workflow` | Full DB-level workflow | All state transitions correct | ✅ PASS |
| TC-043 | `test_allocation_insufficient_stock_fails_atomically` | Stock < requested | No partial state; ValueError | ✅ PASS |
| TC-044 | `test_automated_workflow_via_http_client` | HTTP client full workflow | 201/200 responses; DB consistent | ✅ PASS |

---

## TC-045 to TC-051 — Inventory (`test_inventory.py`)

| ID | Test Name | Input | Expected | Status |
|---|---|---|---|---|
| TC-045 | `test_create_inventory_item_success` | Valid item payload | 201; item in DB | ✅ PASS |
| TC-046 | `test_create_inventory_rejects_negative_quantity` | quantity=-1 | 400 | ✅ PASS |
| TC-047 | `test_create_inventory_rejects_invalid_category` | category="Invalid" | 400 | ✅ PASS |
| TC-048 | `test_create_inventory_rejects_negative_threshold` | low_stock_threshold=-1 | 400 | ✅ PASS |
| TC-049 | `test_boundary_threshold_low_stock` | quantity = threshold | Low-stock flag set | ✅ PASS |
| TC-050 | `test_update_inventory_stock` | PATCH /inventory/1 | quantity updated | ✅ PASS |
| TC-051 | `test_inventory_routes_and_access` | Victim GET /inventory/ | 403 Forbidden | ✅ PASS |

---

## TC-052 to TC-064 — Inventory & Resource Consistency (`test_inventory_resource_consistency.py`)

| ID | Test Name | AC | Status |
|---|---|---|---|
| TC-052 | `test_successful_allocation_updates_all_records_atomically` | AC1 | ✅ PASS |
| TC-053 | `test_allocation_rejects_category_mismatch_without_data_corruption` | AC2 | ✅ PASS |
| TC-054 | `test_allocation_rejects_quantity_exceeding_requested_amount` | AC2 | ✅ PASS |
| TC-055 | `test_failed_field_delivery_restores_inventory_and_resets_request` | AC2 | ✅ PASS |
| TC-056 | `test_cancelled_assignment_restores_inventory_and_resets_request` | AC2 | ✅ PASS |
| TC-057 | `test_reallocation_succeeds_after_previous_assignment_failed` | AC3 | ✅ PASS |
| TC-058 | `test_insufficient_stock_exact_boundary_conditions` | AC3 | ✅ PASS |
| TC-059 | `test_repeated_allocation_call_does_not_duplicate_or_leak_stock` | AC4 | ✅ PASS |
| TC-060 | `test_terminal_assignment_status_cannot_be_mutated` | AC4 | ✅ PASS |
| TC-061 | `test_repeated_status_update_is_idempotent` | AC4 | ✅ PASS |
| TC-062 | `test_repeated_failed_assignment_does_not_double_refund_stock` | AC4 | ✅ PASS |
| TC-063 | `test_mathematical_stock_consistency_across_multiple_allocations` | AC5 | ✅ PASS |
| TC-064 | `test_allocate_route_missing_parameters_returns_400_without_state_change` | AC5/AC6 | ✅ PASS |

---

## TC-065 to TC-066 — Notifications (`test_notifications.py`)

| ID | Test Name | Input | Expected | Status |
|---|---|---|---|---|
| TC-065 | `test_mark_read_only_for_owner` | Other user tries to mark notification | 403 | ✅ PASS |
| TC-066 | `test_broadcast_targets_operational_roles` | Coordinator broadcast | Only Coordinators/Volunteers receive | ✅ PASS |

---

## TC-067 to TC-075 — RBAC (`test_rbac.py`)

| ID | Test Name | Boundary | Status |
|---|---|---|---|
| TC-067 | `test_inventory_write_requires_authentication` | Unauthenticated POST /inventory/ | 401 | ✅ PASS |
| TC-068 | `test_non_coordinator_cannot_create_inventory[Victim]` | Victim POST /inventory/ | 403 | ✅ PASS |
| TC-069 | `test_non_coordinator_cannot_create_inventory[Volunteer]` | Volunteer POST /inventory/ | 403 | ✅ PASS |
| TC-070 | `test_victim_cannot_allocate_resources` | Victim POST /assignments/allocate | 403 | ✅ PASS |
| TC-071 | `test_victim_cannot_update_request_status` | Victim PATCH /requests/1/status | 403 | ✅ PASS |
| TC-072 | `test_victim_cannot_read_another_victims_request` | Victim GET /requests/2 | 403 | ✅ PASS |
| TC-073 | `test_victim_cannot_spoof_request_owner` | Victim POST /requests/ with forged user_id | user_id set from session | ✅ PASS |
| TC-074 | `test_victim_cannot_see_other_users_requests_by_filter` | Victim GET /requests/?user_id=other | Returns 0 results | ✅ PASS |
| TC-075 | `test_volunteer_cannot_update_another_volunteers_assignment` | Volunteer PATCH /assignments/other/status | 403 | ✅ PASS |

---

## TC-076 to TC-079 — Reports (`test_reports.py`)

| ID | Test Name | Input | Expected | Status |
|---|---|---|---|---|
| TC-076 | `test_summary_report_requires_login` | Unauthenticated GET /reports/ | 401 | ✅ PASS |
| TC-077 | `test_summary_report_forbidden_for_victim` | Victim GET /reports/ | 403 | ✅ PASS |
| TC-078 | `test_summary_report_returns_counts` | Coordinator GET /reports/ | Counts match DB | ✅ PASS |
| TC-079 | `test_relief_request_report_filters_by_status` | GET /reports/requests?status=Pending | Only Pending requests returned | ✅ PASS |

---

## TC-080 to TC-090 — Relief Requests (`test_requests.py`)

| ID | Test Name | Input | Expected | Status |
|---|---|---|---|---|
| TC-080 | `test_create_relief_request_success` | Valid request payload | 201; request in DB | ✅ PASS |
| TC-081 | `test_create_request_rejects_zero_or_negative_quantity` | quantity=0 / -1 | 400 | ✅ PASS |
| TC-082 | `test_create_request_rejects_invalid_coordinates` | latitude=200 | 400 | ✅ PASS |
| TC-083 | `test_update_request_status` | Coordinator PATCH status | 200; status updated | ✅ PASS |
| TC-084 | `test_relief_request_routes` | GET /requests/ as Coordinator | 200; list returned | ✅ PASS |
| TC-085 | `test_request_status_transition_rejects_skipping_workflow` | Skip Pending→Fulfilled | 400 | ✅ PASS |
| TC-086 | `test_request_creation_requires_login` | Unauthenticated POST /requests/ | 401 | ✅ PASS |
| TC-087 | `test_request_creation_ignores_forged_user_id` | POST with user_id=other | user_id from session | ✅ PASS |
| TC-088 | `test_victim_only_sees_own_requests_and_cannot_change_status` | Victim sees only own; tries PATCH | Own requests; 403 on PATCH | ✅ PASS |
| TC-089 | `test_incomplete_coordinate_pair_is_rejected` | latitude only, no longitude | 400 | ✅ PASS |
| TC-090 | `test_invalid_http_request_payload_returns_client_error` | Non-JSON body | 400 | ✅ PASS |

---

## TC-091 to TC-094 — Volunteers (`test_volunteers.py`)

| ID | Test Name | Input | Expected | Status |
|---|---|---|---|---|
| TC-091 | `test_list_volunteers_returns_only_volunteer_role` | GET /volunteers/ | Only Volunteer-role users | ✅ PASS |
| TC-092 | `test_get_volunteer_assignments_returns_assigned_tasks` | GET /volunteers/1/assignments | Tasks for that volunteer | ✅ PASS |
| TC-093 | `test_get_volunteer_assignments_rejects_non_volunteer` | GET /volunteers/1/assignments for non-Volunteer user_id | 400 | ✅ PASS |
| TC-094 | `test_get_volunteer_assignments_rejects_unknown_user` | GET /volunteers/999/assignments | 404 | ✅ PASS |

---

## Summary

| Module | Tests | Pass |
|---|---|---|
| Assignments | 10 | 10 |
| Audit | 3 | 3 |
| Auth | 16 | 16 |
| Dashboard | 2 | 2 |
| End-to-End | 1 | 1 |
| Incidents | 8 | 8 |
| Integration | 4 | 4 |
| Inventory | 7 | 7 |
| Inventory Consistency (Sprint 3) | 13 | 13 |
| Notifications | 2 | 2 |
| RBAC (Sprint 3) | 9 | 9 |
| Reports | 4 | 4 |
| Requests | 11 | 11 |
| Volunteers | 4 | 4 |
| **TOTAL** | **94** | **94** |
