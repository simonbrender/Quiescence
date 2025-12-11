"""
Discovery Sources Management
Allows dynamic configuration of discovery sources via UI and API
"""
import json
from typing import List, Dict, Optional
from datetime import datetime
import duckdb

class DiscoverySourceManager:
    """Manages discovery sources configuration"""
    
    def __init__(self, db_conn=None):
        if db_conn is None:
            import duckdb
            self.conn = duckdb.connect("celerio_scout.db")
        else:
            self.conn = db_conn
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure discovery_sources table exists"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS discovery_sources (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                source_type TEXT NOT NULL,  -- 'VC', 'Accelerator', 'Studio', 'Incubator', 'Custom'
                discovery_method TEXT NOT NULL,  -- 'scrape', 'api', 'search', 'portfolio'
                enabled BOOLEAN DEFAULT 1,
                priority INTEGER DEFAULT 100,  -- Lower = higher priority
                config JSON,  -- Additional configuration (pagination, selectors, etc.)
                last_run TIMESTAMP,
                last_success BOOLEAN,
                last_count INTEGER,  -- Number of entities discovered last run
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_added BOOLEAN DEFAULT 0
            )
        """)
        
        # Create default sources if table is empty
        if self.conn.execute("SELECT COUNT(*) FROM discovery_sources").fetchone()[0] == 0:
            self._create_default_sources()
    
    def _create_default_sources(self):
        """Create default discovery sources"""
        default_sources = [
            {
                'name': 'Crunchbase VC Directory',
                'url': 'https://www.crunchbase.com/discover/organization.companies/venture_capital',
                'source_type': 'VC',
                'discovery_method': 'scrape',
                'priority': 10,
                'config': {'pages': 10, 'pagination': True}
            },
            {
                'name': 'F6S Accelerators',
                'url': 'https://www.f6s.com/accelerators',
                'source_type': 'Accelerator',
                'discovery_method': 'scrape',
                'priority': 20,
                'config': {'pages': 20, 'pagination': True}
            },
            {
                'name': 'StudioHub Studios',
                'url': 'https://studiohub.io/studios',
                'source_type': 'Studio',
                'discovery_method': 'scrape',
                'priority': 30,
                'config': {'pages': 10, 'pagination': True}
            },
            {
                'name': 'CB Insights VC Research',
                'url': 'https://www.cbinsights.com/research-venture-capital-firms',
                'source_type': 'VC',
                'discovery_method': 'scrape',
                'priority': 40,
                'config': {'pages': 5, 'pagination': False}
            },
            {
                'name': 'TheVC.com Directory',
                'url': 'https://www.thevc.com/',
                'source_type': 'VC',
                'discovery_method': 'scrape',
                'priority': 50,
                'config': {'pages': 1, 'pagination': False}
            },
        ]
        
        for idx, source in enumerate(default_sources):
            self.conn.execute("""
                INSERT INTO discovery_sources 
                (id, name, url, source_type, discovery_method, priority, config, enabled, user_added)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                idx + 1,
                source['name'],
                source['url'],
                source['source_type'],
                source['discovery_method'],
                source['priority'],
                json.dumps(source['config']),
                True,
                False
            ))
        
        self.conn.commit()
    
    def get_all_sources(self, enabled_only: bool = False) -> List[Dict]:
        """Get all discovery sources"""
        query = "SELECT * FROM discovery_sources"
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY priority ASC, name ASC"
        
        rows = self.conn.execute(query).fetchall()
        
        sources = []
        for row in rows:
            sources.append({
                'id': row[0],
                'name': row[1],
                'url': row[2],
                'source_type': row[3],
                'discovery_method': row[4],
                'enabled': bool(row[5]),
                'priority': row[6],
                'config': json.loads(row[7]) if row[7] else {},
                'last_run': row[8],
                'last_success': bool(row[9]) if row[9] is not None else None,
                'last_count': row[10],
                'created_at': row[11],
                'updated_at': row[12],
                'user_added': bool(row[13])
            })
        
        return sources
    
    def add_source(self, source_data: Dict) -> int:
        """Add a new discovery source"""
        source_id = abs(hash(source_data['name'] + source_data['url'])) % 1000000
        
        self.conn.execute("""
            INSERT INTO discovery_sources 
            (id, name, url, source_type, discovery_method, priority, config, enabled, user_added, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source_id,
            source_data['name'],
            source_data['url'],
            source_data.get('source_type', 'VC'),
            source_data.get('discovery_method', 'scrape'),
            source_data.get('priority', 100),
            json.dumps(source_data.get('config', {})),
            source_data.get('enabled', True),
            True,  # user_added
            datetime.now(),
            datetime.now()
        ))
        
        self.conn.commit()
        return source_id
    
    def update_source(self, source_id: int, updates: Dict):
        """Update a discovery source"""
        updates['updated_at'] = datetime.now()
        
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            if key == 'config' and isinstance(value, dict):
                set_clauses.append(f"{key} = ?")
                values.append(json.dumps(value))
            else:
                set_clauses.append(f"{key} = ?")
                values.append(value)
        
        values.append(source_id)
        
        query = f"UPDATE discovery_sources SET {', '.join(set_clauses)} WHERE id = ?"
        self.conn.execute(query, values)
        self.conn.commit()
    
    def delete_source(self, source_id: int):
        """Delete a discovery source (only user-added ones)"""
        self.conn.execute("DELETE FROM discovery_sources WHERE id = ? AND user_added = 1", (source_id,))
        self.conn.commit()
    
    def update_source_stats(self, source_id: int, success: bool, count: int):
        """Update source statistics after discovery run"""
        self.conn.execute("""
            UPDATE discovery_sources 
            SET last_run = ?, last_success = ?, last_count = ?, updated_at = ?
            WHERE id = ?
        """, (datetime.now(), success, count, datetime.now(), source_id))
        self.conn.commit()

