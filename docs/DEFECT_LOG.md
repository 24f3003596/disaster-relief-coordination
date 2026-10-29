# Defect Log — Sprint 3 (Review 3)

**Project**: Disaster Relief Resource Coordination System (Team 20)
**Branch**: `main` (post Sprint 3 integration)
**Date**: 2026-10-29

---

## Sprint 1–2 Resolved Defects (DEF-001 to DEF-010)

Previously documented and resolved in Sprint 2. All 10 defects closed. See Sprint 2 evidence archive.

---

## Sprint 3 Defects

| ID | Title | Severity | Module | Assignee | Status | Resolution |
|---|---|---|---|---|---|---|
| DEF-011 | Allocation stock permanently lost on delivery failure / Unable To Complete | High | `assignments.py` | Sree Naresh A | **Resolved** | `update_assignment_status()` now restores `item.quantity` and reverts request to `Pending` on `Unable to Complete` and `Cancelled` transitions |
| DEF-012 | Reallocation blocked by DB UNIQUE constraint on `assignments.request_id` | High | `assignments.py`, `models.py` | Sree Naresh A | **Resolved** | `allocate_request()` reuses the existing `Assignment` row when its status is in `INACTIVE_ASSIGNMENT_STATUSES`, satisfying the UNIQUE constraint while resetting to `Assigned` |
| DEF-013 | `POST /assignments/allocate` returns 500 on missing payload fields | Medium | `routes/assignments.py` | Sree Naresh A | **Resolved** | Explicit `None` check on `request_id`, `volunteer_id`, `item_id` before casting to `int`; returns HTTP 400 with descriptive error |
| DEF-014 | Over-allocation permitted: `quantity_assigned > req.quantity` | Medium | `assignments.py` | Sree Naresh A | **Resolved** | Guard added: raises `ValueError` if `alloc_qty > req.quantity` |
| DEF-015 | Terminal assignment states (`Completed`, `Cancelled`, `Unable to Complete`) could be mutated | High | `assignments.py` | Sree Naresh A | **Resolved** | `TERMINAL_ASSIGNMENT_STATUSES` set defined; `update_assignment_status()` raises `ValueError` on any mutation attempt |
| DEF-016 | Double stock refund possible when `Unable to Complete` is applied twice | High | `assignments.py` | Sree Naresh A | **Resolved** | Idempotency guard: if `assignment.status == new_status`, return immediately without side effects |
| DEF-017 | Relief request intake accepts missing latitude with longitude present (asymmetric coordinate validation) | Medium | `requests_module.py` | Vishal K V | **Resolved** | Coordinate pair completeness check added in Sprint 3 PR #4 — both or neither must be supplied |
| DEF-018 | Victim can read another victim's requests via `user_id` query filter | High | `requests_module.py` | SIVANESH | **Resolved** | RBAC decorator enforces Victim can only access own requests; `user_id` filter is ignored / overridden for Victim role |

---

## Summary

| Sprint | Defects Logged | Resolved | Open |
|---|---|---|---|
| Sprint 1–2 | 10 | 10 | 0 |
| Sprint 3 | 8 | 8 | 0 |
| **Total** | **18** | **18** | **0** |
