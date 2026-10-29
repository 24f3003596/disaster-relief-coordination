# Cyclomatic Complexity Report — Sprint 3 (Review 3)

**Project**: Disaster Relief Resource Coordination System (Team 20)
**Branch**: `main` (post Sprint 3 integration)
**Date**: 2026-10-29
**Tool**: Radon 6.x

---

## Summary

| Metric | Value |
|---|---|
| Blocks Analysed | 289 (functions, methods, classes) |
| Average Complexity | **4.65** |
| Grade | **A** |
| Risk Level | Low |

---

## Grade Scale

| Grade | Complexity Range | Risk |
|---|---|---|
| A | 1–5 | Low risk |
| B | 6–10 | Moderate risk |
| C | 11–15 | High risk |
| D–F | 16+ | Very high risk |

Our codebase remains firmly in **Grade A** territory even after adding 32 new tests and expanding `assignments.py`, `incidents.py`, and `requests_module.py` with RBAC, consistency guards, and state machine logic.

---

## Sprint History

| Sprint | Blocks | Average CC | Grade |
|---|---|---|---|
| Sprint 2 | 240 | 4.05 | A |
| Sprint 3 | **289** | **4.65** | **A** |

The +49 blocks increase reflects Sprint 3 feature additions. CC increased modestly due to the more complex allocation/RBAC/state-machine logic, but remains well within Grade A bounds.
