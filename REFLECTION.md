# REFLECTION.md

### 1. What assumptions did you make?
I assumed that data in the Urja Meter Ops legacy portal changes infrequently and is primarily read-only. Based on this, I chose a local indexing architecture (using an embedded SQLite database) populated via an on-demand `/api/v1/sync` endpoint. This decouples user API requests from upstream portal latency and downtime.

### 2. Which part was the most difficult, and how did you get unstuck?
The primary challenge was managing execution constraints under Windows Application Control / Device Guard policies, which blocked compiled third-party C-extension `.dll` and `.pyd` binaries (such as DuckDB and Pandas) when running inside user directories. I solved this by refactoring the storage and query engine to Python's standard library `sqlite3`, which ships directly in Microsoft's trusted runtime path, removing binary execution friction while preserving ACID compliance and SQL query capabilities.

### 3. If you had another day, what would you improve?
With an additional day, I would:
- Introduce automated background polling using `APScheduler` or a Redis task queue so records stay synchronized automatically without manual intervention.
- Enhance the network hierarchy to trace higher upstream grid nodes (e.g., Feeders and Substations).
- Add geo-coordinates to Distribution Transformers and render an interactive Leaflet/Mapbox geospatial cluster map on the web dashboard.

### 4. What mistake did you make while solving this?
Initially, I attempted to trigger a blocking multi-page scraping loop directly inside FastAPI's startup event (`@app.on_event("startup")`). This caused the Uvicorn server to hang before binding to port 8000. I corrected this by decoupling the scrape into an explicit `/api/v1/sync` endpoint, allowing the server to boot instantly and handle requests deterministically.

### 5. If you were reviewing your own submission, what would you criticise?
The HTML scraper relies on the structure of the `<table>` element remaining static. If the legacy portal updates its CSS class names, table ordering, or switches to a client-side JavaScript SPA (Single Page App), BeautifulSoup would fail to extract records without a headless browser layer (like Playwright).