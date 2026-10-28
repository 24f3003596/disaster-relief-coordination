# Sprint Review and Retrospective Notes — Review 2 Delivery
**Project**: Disaster Relief Resource Coordination System (Team 20)  
**Sprint**: Sprint 2 (Review 2 Milestone)  
**Team Members**: Vishal K V, SIVANESH, Sree Naresh A  
**QA & Documentation Lead**: Sree Naresh A (TEAM20-57, TEAM20-58)  
**Sprint Delivery Status**: **100% Committed Scope Delivered (All Tickets Done)**

---

## 1. Sprint Review: Scope Delivery

### Sprint 1 Summary (Foundations & Security Baseline)
- **Committed & Delivered**: Data models schema, PBKDF2 password hashing, secure session management, incident reporting intake, inventory warehouse core (`TEAM20-16` through `TEAM20-19`).
- **Baseline Test Suite**: 13 foundational tests passing.

### Sprint 2 Summary (Operations, Coordination & Quality Verification)
- **Committed & Delivered**:
  - Relief requests intake with geographic coordinate bounds (`TEAM20-20`, `TEAM20-21`).
  - Atomic volunteer dispatch & stock allocation rollback (`TEAM20-22`, `TEAM20-23`).
  - Notification inbox & emergency alert broadcasts (`TEAM20-24`, `TEAM20-25`).
  - Coordinator analytics dashboard & operational reporting (`TEAM20-26`, `TEAM20-27`).
  - Immutable system audit trail (`TEAM20-28`).
  - Public registration role escalation vulnerability fix (`TEAM20-53`).
  - Registration security regression test suite (`TEAM20-54`).
  - Resource allocation dropdown context fix & edge-case validation (`TEAM20-55`, `TEAM20-56`).
  - Full automated test suite baseline, coverage, and quality verification (`TEAM20-57`).
  - Technical documentation, evidence compilation, and branch integration into `main` (`TEAM20-58`).

### Sprint 2 JIRA Tickets Master Status

| Ticket ID | Summary / Scope | Assignee | Status | Resolution |
|---|---|---|---|---|
| **TEAM20-53** | Fix Public Registration Role Escalation | Vishal K V | **Done** | Fixed; default role locked to `Victim` |
| **TEAM20-54** | Add Registration Security Regression Tests | Vishal K V | **Done** | 9 new test cases covering API and HTML form inputs |
| **TEAM20-55** | Expand Resource Allocation Integration Tests | SIVANESH | **Done** | Dropdown context helper added; edge-case guards implemented |
| **TEAM20-56** | Validate Resource Allocation Failure Handling | SIVANESH | **Done** | 8 new test cases for negative/zero qty, duplicate, invalid IDs |
| **TEAM20-57** | Full Test Suite and Quality Verification | Sree Naresh A | **Done** | Verified baseline (45 tests) and post-integration (62 tests, 100% pass) |
| **TEAM20-58** | Update Technical Documentation and Review Evidence | Sree Naresh A | **Done** | README updated, Word & Markdown dossiers compiled, merged into `main` |

---

## 2. Sprint Retrospective

### What Went Well (Successes)
1. **Zero-Regression Integration**: The 45 baseline tests ensured that when Vishal and Sivanesh merged their branches, no existing functionality broke, and the suite expanded cleanly to 62 tests.
2. **Defensive Security First**: Identifying and fixing the role escalation vulnerability (TEAM20-53) before Review 2 ensured that privilege separation between Victims, Volunteers, Coordinators, and Admins cannot be bypassed.
3. **Atomic Database Transactions**: The transaction rollback pattern in `allocate_request()` completely prevented stock leakage during failed allocation attempts.
4. **Transparent Documentation**: Providing both Markdown (`.md`) and Microsoft Word (`.docx`) evidence formats allows technical reviewers and evaluators to inspect test logs and metrics in their preferred format.

### Challenges Encountered & Resolutions
1. **Merge Conflict on README.md**:
   - *Challenge*: Both `upload-sprint2` and `feature/test-documentation` modified the testing section of `README.md`.
   - *Resolution*: Manually merged the conflict, retaining both Vishal's guidance to re-run metrics and our verified post-integration test numbers.
2. **SQLite Resource Warnings on Python 3.14**:
   - *Challenge*: 10 `ResourceWarning: unclosed database` warnings were triggered during test teardown.
   - *Resolution*: Investigated and verified they are non-blocking pool teardown warnings under Python 3.14's strict resource tracking with zero functional impact.

### Action Items for Future Sprints
- [ ] Migrate `routes/` refactor package into active import paths to consolidate code structure.
- [ ] Integrate SQLite connection pool cleanup in `conftest.py` teardown to silence Python 3.14 resource warnings.
- [ ] Implement pagination on `/requests` and `/inventory` tables for large-scale disaster deployments.
