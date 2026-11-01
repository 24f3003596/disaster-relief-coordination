# Code Coverage Report — Sprint 4 (Review 4)

**Project**: Disaster Relief Resource Coordination System (Team 20)  
**Branch**: `main` (post Sprint 4 integration)  
**Date**: 2026-11-01  
**Tool**: pytest-cov 7.1.0  

---

## Summary

| Metric | Value |
|---|---|
| Core App Modules Coverage | **~81% statement coverage** |
| Tests Passing | **126 / 126 (100%)** |

---

## Module Coverage Details

| Module | Statements | Missing | Coverage | Key Tested Capabilities |
|---|---|---|---|---|
| `dashboard.py` | 99 | 9 | **91%** | Analytics, avg response time, resource utilization rate |
| `reports.py` | 76 | 6 | **92%** | Operational summary, filtered reports, Admin CSV export |
| `assignments.py` | 191 | 38 | **80%** | Atomic allocation, stock deduction, status tracking |
| `inventory.py` | 126 | 28 | **78%** | Stock tracking, boundary threshold checks, shortage hooks |
| `notifications.py` | 111 | 31 | **72%** | Critical shortage automation, broadcasts, owner read guard |
| `map_view.py` | 102 | 14 | **86%** | Disaster map endpoints, bounding box, marker filtering |
| `models.py` | 132 | 4 | **97%** | 8 ORM models, PhoneOTP, constraints, helper methods |
| `auth.py` | 168 | 28 | **83%** | Registration, phone OTP verification, Admin approval |
| `incidents.py` | 176 | 31 | **82%** | Incident lifecycle state machine, validation, affected areas |
| `requests_module.py` | 212 | 65 | **69%** | Request intake, coordinate checks, owner protection |
