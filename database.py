import sqlite3
from typing import List, Dict, Any, Optional

class MeterDatabase:
    def __init__(self, db_path: str = "meters.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS meters (
                    meter TEXT PRIMARY KEY,
                    serial TEXT,
                    make TEXT,
                    phase TEXT,
                    status TEXT,
                    dt TEXT
                )
            """)
            conn.commit()

    def insert_meters(self, meters_list: List[Dict[str, Any]]):
        if not meters_list:
            return
        with self._get_connection() as conn:
            conn.executemany("""
                INSERT OR REPLACE INTO meters (meter, serial, make, phase, status, dt)
                VALUES (:meter, :serial, :make, :phase, :status, :dt)
            """, meters_list)
            conn.commit()

    def query_meters(
        self, 
        status: Optional[str] = None, 
        make: Optional[str] = None, 
        phase: Optional[str] = None,
        dt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM meters WHERE 1=1"
        params = []
        if status:
            query += " AND LOWER(status) = LOWER(?)"
            params.append(status)
        if make:
            query += " AND LOWER(make) = LOWER(?)"
            params.append(make)
        if phase:
            query += " AND LOWER(phase) = LOWER(?)"
            params.append(phase)
        if dt:
            query += " AND LOWER(dt) = LOWER(?)"
            params.append(dt)

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_network_hierarchy(self) -> Dict[str, Any]:
        """
        Reconstructs the hierarchical grid topology from live records:
        Root Grid -> Feeders -> Distribution Transformers -> Meters
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COALESCE(dt, 'Unassigned DT') as dt_node,
                    COUNT(*) as total_meters,
                    SUM(CASE WHEN LOWER(status) = 'installed' THEN 1 ELSE 0 END) as active_count,
                    SUM(CASE WHEN LOWER(status) LIKE '%fault%' THEN 1 ELSE 0 END) as fault_count,
                    SUM(CASE WHEN LOWER(phase) = 'three' THEN 1 ELSE 0 END) as three_phase_count,
                    SUM(CASE WHEN LOWER(phase) = 'single' THEN 1 ELSE 0 END) as single_phase_count
                FROM meters
                GROUP BY dt_node
                ORDER BY total_meters DESC
            """)
            dt_stats = [dict(row) for row in cursor.fetchall()]

        tree = {
            "name": "Northern Regional Grid (Urja Ops)",
            "type": "grid_substation",
            "children": []
        }

        # Cluster DTs into upstream feeders based on DT naming conventions
        feeders: Dict[str, List[Dict[str, Any]]] = {}
        for dt_entry in dt_stats:
            dt_name = dt_entry["dt_node"]
            # Extract feeder identifier (e.g. DT-01 -> Feeder F1) or allocate systematically
            feeder_key = f"Feeder {dt_name[:4]}" if len(dt_name) >= 4 else "Feeder Main-1"
            if feeder_key not in feeders:
                feeders[feeder_key] = []
            
            # Fetch the actual meters attached to this DT
            meters_cursor = conn.execute(
                "SELECT meter, serial, make, phase, status FROM meters WHERE dt = ? ORDER BY meter ASC",
                (dt_name,)
            )
            attached_meters = [dict(m) for m in meters_cursor.fetchall()]
            
            dt_entry["meters"] = attached_meters
            feeders[feeder_key].append(dt_entry)

        for feeder_name, dts in feeders.items():
            tree["children"].append({
                "name": feeder_name,
                "type": "feeder",
                "total_transformers": len(dts),
                "children": dts
            })

        return tree