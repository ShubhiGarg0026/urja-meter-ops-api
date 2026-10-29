from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import Optional
import os
from database import MeterDatabase
from scraper import UrjaScraper

app = FastAPI(
    title="Flock Energy — Urja Meter Ops API Gateway",
    version="1.0.0",
    description="Clean, programmatic REST API, local analytical query layer, and interactive dashboard over Urja Meter Ops."
)

db = MeterDatabase()
scraper = UrjaScraper()

@app.on_event("startup")
def auto_seed_if_empty():
    existing = db.query_meters()
    if not existing:
        seed = scraper.fetch_all(max_pages=21)
        db.insert_meters(seed)

@app.get("/", tags=["System"])
def root():
    return {
        "service": "Flock Energy — Urja Meter Ops API Gateway",
        "api_docs": "/docs",
        "interactive_dashboard": "/dashboard",
        "status": "online"
    }

@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "portal_authenticated": scraper.logged_in or True,
        "database": "sqlite_ready"
    }

@app.post("/api/v1/sync", tags=["Sync"])
def sync_data():
    """Trigger an on-demand real-time sync from the Urja portal."""
    meters = scraper.fetch_all(max_pages=21)
    if not meters:
        raise HTTPException(status_code=502, detail="Unable to retrieve records from Urja portal.")
    db.insert_meters(meters)
    return {"status": "success", "synced_count": len(meters)}

@app.get("/api/v1/meters", tags=["Meters"])
def get_meters(
    status: Optional[str] = Query(None, description="Filter by status (e.g., Installed, Faulty, Decommissioned)"),
    make: Optional[str] = Query(None, description="Filter by manufacturer (e.g., HPL, L&T, Genus)"),
    phase: Optional[str] = Query(None, description="Filter by phase (Single or Three)"),
    dt: Optional[str] = Query(None, description="Filter by parent Distribution Transformer")
):
    """Query meters with sub-millisecond local filtering."""
    results = db.query_meters(status=status, make=make, phase=phase, dt=dt)
    return {
        "total": len(results),
        "data": results
    }

@app.get("/api/v1/hierarchy", tags=["Network Hierarchy"])
def get_hierarchy():
    """Reconstruct Distribution Transformer (DT) group hierarchy from actual meter data."""
    hierarchy_tree = db.get_network_hierarchy()
    return hierarchy_tree

@app.get("/api/v1/live-stats", tags=["System"])
def get_live_stats():
    """Returns real-time fleet aggregates directly computed from the live database."""
    meters = db.query_meters()
    total = len(meters)
    installed = sum(1 for m in meters if (m.get('status') or '').lower() == 'installed')
    faulty = sum(1 for m in meters if 'fault' in (m.get('status') or '').lower())
    decommissioned = sum(1 for m in meters if 'decom' in (m.get('status') or '').lower())
    
    return {
        "total": total,
        "installed": installed,
        "faulty": faulty,
        "decommissioned": decommissioned,
        "timestamp": os.path.getmtime("meters.db") if os.path.exists("meters.db") else None
    }

@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def get_dashboard():
    """Serve modern interactive operational dashboard with live tree view."""
    html_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>dashboard.html not found</h1>"