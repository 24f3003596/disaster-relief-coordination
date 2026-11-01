# Defect Log — Sprint 4 (Review 4)

**Project**: Disaster Relief Resource Coordination System (Team 20)  
**Branch**: `main`  
**Date**: 2026-11-01  

---

## Cumulative Defect Summary

| Sprint | Defects Logged | Resolved | Open | Resolution Rate |
|---|---|---|---|---|
| Sprints 1–2 | 10 | 10 | 0 | 100% |
| Sprint 3 | 8 | 8 | 0 | 100% |
| Sprint 4 | 4 | 4 | 0 | 100% |
| **Total** | **22** | **22** | **0** | **100%** |

---

## Sprint 4 Resolved Defects

| ID | Title | Module | Severity | Resolution |
|---|---|---|---|---|
| DEF-019 | Division by zero in dashboard analytics on empty database | `dashboard.py` | High | Guarded total capacity and response duration denominator with safe fallback to `0.0`. |
| DEF-020 | CSV export accessible by non-Admin coordinators | `reports.py` | Medium | Restricted export routes strictly to `ROLE_ADMIN` per SRS FR 3.7.2. |
| DEF-021 | Critical shortage notifications duplicated on repeated stock adjustments | `notifications.py` | High | Implemented unread alert check per category/user to suppress redundant notifications. |
| DEF-022 | Shortage notification triggered for category without pending requests | `notifications.py` | Medium | Added pending relief request count check; suppressed alerts when pending requests == 0. |
