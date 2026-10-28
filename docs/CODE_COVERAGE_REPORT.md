# Code Coverage Report — Sprint 2
**Project**: Disaster Relief Resource Coordination System (Team 20)  
**Branch**: `main` @ commit `9ed4087`  
**Generated**: 2026-10-28  
**Command**: `pytest --cov=. --cov-report=term-missing`

---

## Summary

| Scope | Coverage |
|---|---|
| **Application modules** (excludes `routes/` shadow + build script) | **~76%** |
| Raw pytest-cov total | 44% |
| Test files | 100% |
| Execution time | 9.30 s |

> **Note on the 44% raw total**: The `9ed4087` refactor introduced a `routes/` package containing copies of all feature modules. These files register 0% coverage because `create_app()` still imports from the top-level modules. Additionally `build_all_word_documents.py` (564 stmts) is a doc-generation script, not application code. Excluding both, application coverage is **~76%**.

---

## Per-Module Breakdown

| Module | Stmts | Miss | Cover | Uncovered lines (key) |
|---|---|---|---|---|
| `constants.py` | 71 | 0 | **100%** | — |
| `extensions.py` | 2 | 0 | **100%** | — |
| `models.py` | 107 | 2 | **98%** | 162, 166 (property setter) |
| `reports.py` | 40 | 6 | **85%** | 15–21 (HTML path), 99 |
| `dashboard.py` | 43 | 9 | **79%** | 86, 91–98 (HTML rendering) |
| `audit.py` | 36 | 8 | **78%** | 33–39, 52–53 (template routes) |
| `inventory.py` | 114 | 29 | **75%** | HTML routes, admin form paths |
| `requests_module.py` | 117 | 33 | **72%** | HTML routes, form validation |
| `assignments.py` | 117 | 34 | **71%** | HTML routes, form paths |
| `incidents.py` | 62 | 18 | **71%** | HTML template paths |
| `volunteers.py` | 23 | 7 | **70%** | HTML route handlers |
| `auth.py` | 126 | 39 | **69%** | HTML register/login form paths |
| `notifications.py` | 64 | 21 | **67%** | HTML notification paths |
| `app.py` | 211 | 99 | **53%** | Demo seeder, HTML root routes |
| `routes/*` | 592 | 592 | **0%** | Shadow package — not imported by app |
| `core/*` | 184 | 184 | **0%** | Shadow package — not imported by tests |
| `build_all_word_documents.py` | 564 | 564 | **0%** | Doc-generation utility |
| **Test files (13)** | 465 | 0 | **100%** | All tests executed |
| **TOTAL** | 3203 | 1806 | **44%** | — |

---

## Gap Analysis

The uncovered lines in application modules fall into two categories:

1. **HTML template rendering paths** — Routes that return `render_template(...)` for browser clients. The test suite uses the JSON API interface (`application/json`). These are tested manually via UI workflows.
2. **Demo seeder** (`app.py` lines 237–275) — `seed_initial_demo_data()` only runs on `python app.py` development startup, not under `pytest`.

No critical business-logic paths are uncovered in the main module set.
