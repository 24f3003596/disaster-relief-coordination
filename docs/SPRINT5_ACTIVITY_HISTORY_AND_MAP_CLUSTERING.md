# Sprint 5 Implementation Notes

## Task 1 — Request and incident activity history

- Reused the existing `AuditLog` table; no database schema changes or migration are required.
- Added chronological entity history retrieval with actor display names.
- Added `/requests/<request_id>/history` with the same visibility rules as the request itself (owner, assigned volunteer, Coordinator or Admin).
- Added `/incidents/<incident_id>/history`, restricted to Coordinator and Admin roles.
- Added HTML timelines and JSON responses (`?format=json`).
- New activity text records request/incident creation, incident field changes, incident status transitions, request status transitions, and request status changes caused by assignment/allocation.
- Added links from the request and incident listing pages to their authorized activity views.
- No-op incident edits do not create misleading duplicate activity entries.

## Task 2 — Map clustering

- Added Leaflet.markercluster 1.5.3 CSS and JavaScript assets.
- Replaced the plain map marker layer with a cluster group using chunked loading, spiderfying at maximum zoom and removal of markers outside visible bounds.
- Retained a plain Leaflet layer fallback if the optional clustering library cannot load.
- Retained the existing category, status, area, viewport filters, manual refresh and 30-second automatic refresh.

## Validation

The full pytest suite must be run in the team's Python 3.14 environment with the dependencies from `requirements.txt`. The current execution workspace does not have Flask or Flask-SQLAlchemy installed and cannot reach the package index, so runtime pytest execution could not be completed here. Static Python compilation, Jinja template parsing, JavaScript syntax checks and archive integrity checks are performed separately and reported in the handover.
