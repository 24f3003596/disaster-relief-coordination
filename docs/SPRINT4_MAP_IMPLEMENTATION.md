# Sprint 4 — Disaster Operations Map

## Delivered scope

- Coordinator/Admin map page: `GET /map/`.
- Protected map-data API: `GET /map/data`.
- Active relief request markers use saved request coordinates and urgency color. Completed/cancelled requests are omitted by default but can be selected explicitly with the status filter.
- Active incident markers use saved incident coordinates and severity color. Resolved/closed incidents are omitted by default but can be selected explicitly with the status filter.
- Filters support request category, status, text search over request location / incident title / incident description, and the current geographic map viewport.
- The browser refreshes map data immediately on filter changes and every 30 seconds. API responses include a refresh timestamp and no-cache headers.
- Marker popup content is assembled with DOM text nodes rather than interpolated HTML.

## Coordinate coverage and limitations

The supplied data model has latitude/longitude on incidents and optional latitude/longitude on relief requests. `User` has no coordinates, and `InventoryItem` has a storage-location label but no coordinates. Therefore, the application does not plot volunteer profiles or storage locations. The API reports how many such records are currently unmappable. It does not geocode addresses or fabricate coordinates.

The incident model has no separate region/address attribute. Region text search therefore searches the incident title and description; on requests it searches the saved `location`. The map-viewport region filter applies directly to coordinates for both entity types.

A formal SRS file was not present in the supplied ZIP. The implementation follows the agreed Sprint 4 task description and the fields/authorization already present in the supplied codebase. Confirm SRS traceability with the team’s authoritative SRS before marking the Jira task complete.

## Tests added

`tests/test_map_view.py` covers unauthenticated and role-based access, map rendering and refresh interval, geocoded marker payloads, unmapped-location counts, category/status/region filtering, viewport filtering, and invalid filter/bounds handling.

## Verification

- Python compilation: passed in the build workspace.
- Jinja template compilation: passed in the build workspace.
- Full pytest suite: not executed successfully in the build workspace because Flask and Flask-SQLAlchemy are not installed and package installation could not reach the package index. Run `python -m pip install -r requirements.txt` and `python -m pytest -v` in the team's Python 3.14 environment before merging.
