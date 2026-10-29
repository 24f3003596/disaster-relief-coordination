# Sprint Review & Retrospective — Sprint 3 (Review 3)

**Project**: Disaster Relief Resource Coordination System (Team 20)
**Sprint Duration**: Sprint 3
**Review Date**: 2026-10-29
**Participants**: Vishal K V, SIVANESH, Sree Naresh A

---

## Sprint 3 Goal

Harden the application through incident and request workflow validation, RBAC enforcement on all API routes, and inventory/resource consistency guarantees; then integrate all changes and demonstrate 100% test pass rate.

---

## Scope Delivered

| Ticket | Title | Assignee | Points | Status |
|---|---|---|---|---|
| TEAM20-59 | Validate Relief Request and Incident Workflows | Vishal K V | 5 | ✅ Done |
| TEAM20-60 | Integrate and Review Sprint 3 — Vishal | Vishal K V | 3 | ✅ Done |
| TEAM20-61 | Strengthen RBAC and Regression Testing | SIVANESH | 5 | ✅ Done |
| TEAM20-62 | Integrate and Review Sprint 3 — Sivanesh | SIVANESH | 3 | ✅ Done |
| TEAM20-63 | Verify Inventory and Resource Consistency | Sree Naresh A | 5 | ✅ Done |
| TEAM20-64 | Integrate and Review Sprint 3 Changes | Sree Naresh A | 3 | ✅ Done |

**Total Story Points Delivered**: 24 / 24 (100%)

---

## Key Deliverables

### Vishal K V — Sprint 3
- Input validation on `POST /requests/` for coordinate pair completeness, non-zero quantities, category enum.
- Incident state machine: valid transitions between `Active → Contained → Resolved → Closed`, guarded transitions, audit trail entries on every mutation.
- 8 new `test_incidents.py` tests; 4 new `test_requests.py` tests covering coordinate checks, forged user_id, and payload edge cases.
- PR #4 (`feature/sprint3-relief-incident-workflow`) reviewed, approved, and merged.

### SIVANESH — Sprint 3
- RBAC decorators applied to all inventory and assignment routes.
- Victim-scoped request filtering — `GET /requests/` returns only own requests for Victim role.
- Volunteer-scoped assignment filtering — `GET /assignments/` returns only own assignments for Volunteer role.
- Cross-volunteer assignment update protection — Volunteer cannot update another's assignment status.
- 9 `test_rbac.py` tests covering all role boundary cases.
- `sprint-3-sivanesh` branch reviewed, approved, and merged (conflict resolution in `requests_module.py`, `test_end_to_end_workflow.py`, `test_integration.py`).

### Sree Naresh A — Sprint 3
- **Task 1 — Inventory & Resource Consistency (5 SP)**:
  - Fixed stock leakage on delivery failure/cancellation (`DEF-011`).
  - Fixed reallocation blocked by DB UNIQUE constraint (`DEF-012`).
  - Fixed HTTP 500 on missing allocate payload (`DEF-013`).
  - Fixed over-allocation guard (`DEF-014`).
  - Fixed terminal status mutation and double refund (`DEF-015`, `DEF-016`).
  - 13 automated tests in `test_inventory_resource_consistency.py` (all 6 ACs verified).
- **Task 2 — Integration & Review (3 SP)**:
  - Reviewed PR #4 (Vishal) and `sprint-3-sivanesh` (SIVANESH).
  - Created `integration/sprint3-main` branch; merged all 3 Sprint 3 feature branches.
  - Resolved 3-way merge conflicts in `requests_module.py`, `test_end_to_end_workflow.py`, `test_integration.py`.
  - Ran full test suite: **94 passed, 0 failures**.
  - Merged `integration/sprint3-main` into `main`.
  - Updated all project evidence documentation.

---

## Integration Test Evidence

```
============================= 94 passed in 41.59s =============================
Branch: main | Python 3.14.5 | pytest 9.1.1
```

---

## Retrospective

### What Went Well
- Careful merge-conflict resolution preserved all three teammates' work without any discards.
- Fixing the UNIQUE constraint reallocation issue required understanding the SQLAlchemy identity map — resolved cleanly by reusing the existing row.
- All 8 Sprint 3 defects were identified via automated tests before merging.
- 100% test pass rate maintained throughout integration.

### What Could Improve
- The `routes/` mirror package creates duplicate coverage noise; future sprints should consolidate to a single blueprint registration pattern.
- `ResourceWarning` about unclosed SQLite connections in Python 3.14 should be addressed by explicit teardown in `conftest.py`.

### Action Items for Next Sprint
- [ ] Consolidate `routes/` mirror package with top-level modules.
- [ ] Add explicit `db.engine.dispose()` in conftest teardown to eliminate ResourceWarnings.
- [ ] Expand `notifications.py` test coverage (currently 67%).

---

## Cumulative Sprint Metrics

| Sprint | Story Points | Tests | Coverage | CC Grade |
|---|---|---|---|---|
| Sprint 1 | — | 45 | ~70% | A |
| Sprint 2 | — | 62 | ~76% | A (4.05) |
| Sprint 3 | 24 | **94** | **~80%** | **A (4.65)** |
