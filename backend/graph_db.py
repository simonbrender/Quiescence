"""
Graph Database Integration for Investor-Company Relationships

Provides Neo4j/FalkorDB integration for complex relationship queries and path finding.
Syncs data from DuckDB relational tables to graph database.
"""
from typing import List, Dict, Optional
import os
from datetime import datetime

# Try to import Neo4j driver
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    GraphDatabase = None

# Try to import FalkorDB driver (alternative)
try:
    import redis
    from redis.commands.graph import Graph
    FALKORDB_AVAILABLE = True
except ImportError:
    FALKORDB_AVAILABLE = False
    redis = None
    Graph = None


class GraphDB:
    """Graph database interface for investor-company relationships"""
    
    def __init__(self, db_type: str = "neo4j"):
        """
        Initialize graph database connection
        
        Args:
            db_type: "neo4j" or "falkor" (default: "neo4j")
        """
        self.db_type = db_type
        self.driver = None
        self.graph = None
        
        if db_type == "neo4j" and NEO4J_AVAILABLE:
            self._init_neo4j()
        elif db_type == "falkor" and FALKORDB_AVAILABLE:
            self._init_falkordb()
        else:
            print(f"Warning: Graph database ({db_type}) not available. Install neo4j or redis package.")
    
    def _init_neo4j(self):
        """Initialize Neo4j connection"""
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            print(f"[GraphDB] Connected to Neo4j at {uri}")
        except Exception as e:
            print(f"[GraphDB] Failed to connect to Neo4j: {e}")
            self.driver = None
    
    def _init_falkordb(self):
        """Initialize FalkorDB (Redis Graph) connection"""
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", "6379"))
        password = os.getenv("REDIS_PASSWORD")
        
        try:
            r = redis.Redis(host=host, port=port, password=password, decode_responses=True)
            self.graph = r.graph("investor_company_graph")
            print(f"[GraphDB] Connected to FalkorDB at {host}:{port}")
        except Exception as e:
            print(f"[GraphDB] Failed to connect to FalkorDB: {e}")
            self.graph = None
    
    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()
        if self.graph:
            # FalkorDB connection is managed by redis client
            pass
    
    def sync_companies(self, companies: List[Dict]):
        """Sync companies from DuckDB to graph database"""
        if not self.driver and not self.graph:
            return
        
        if self.db_type == "neo4j":
            self._sync_companies_neo4j(companies)
        elif self.db_type == "falkor":
            self._sync_companies_falkor(companies)
    
    def sync_investments(self, investments: List[Dict]):
        """Sync investment relationships from DuckDB to graph database"""
        if not self.driver and not self.graph:
            return
        
        if self.db_type == "neo4j":
            self._sync_investments_neo4j(investments)
        elif self.db_type == "falkor":
            self._sync_investments_falkor(investments)
    
    def _sync_companies_neo4j(self, companies: List[Dict]):
        """Sync companies to Neo4j"""
        if not self.driver:
            return
        
        with self.driver.session() as session:
            # Create companies
            for company in companies:
                session.run("""
                    MERGE (c:Company {id: $id})
                    SET c.name = $name,
                        c.domain = $domain,
                        c.created_at = $created_at
                """, {
                    "id": company['id'],
                    "name": company['name'],
                    "domain": company.get('domain', ''),
                    "created_at": str(company.get('created_at', datetime.now()))
                })
    
    def _sync_investments_neo4j(self, investments: List[Dict]):
        """Sync investment relationships to Neo4j"""
        if not self.driver:
            return
        
        with self.driver.session() as session:
            for inv in investments:
                # Create investor node if not exists
                session.run("""
                    MERGE (i:Investor {id: $investor_id})
                    SET i.firm_name = $firm_name,
                        i.type = $investor_type
                """, {
                    "investor_id": inv['investor_id'],
                    "firm_name": inv.get('firm_name', ''),
                    "investor_type": inv.get('investor_type', 'VC')
                })
                
                # Create investment relationship
                session.run("""
                    MATCH (c:Company {id: $company_id})
                    MATCH (i:Investor {id: $investor_id})
                    MERGE (c)-[r:INVESTED_BY]->(i)
                    SET r.investment_type = $investment_type,
                        r.funding_round = $funding_round,
                        r.amount = $amount,
                        r.date = $date,
                        r.lead_investor = $lead_investor,
                        r.valid_from = $valid_from,
                        r.valid_to = $valid_to
                """, {
                    "company_id": inv['company_id'],
                    "investor_id": inv['investor_id'],
                    "investment_type": inv.get('investment_type', ''),
                    "funding_round": inv.get('funding_round', ''),
                    "amount": inv.get('funding_amount'),
                    "date": str(inv.get('investment_date', '')) if inv.get('investment_date') else None,
                    "lead_investor": inv.get('lead_investor', False),
                    "valid_from": str(inv.get('valid_from', '')) if inv.get('valid_from') else None,
                    "valid_to": str(inv.get('valid_to', '')) if inv.get('valid_to') else None
                })
    
    def _sync_companies_falkor(self, companies: List[Dict]):
        """Sync companies to FalkorDB"""
        if not self.graph:
            return
        
        for company in companies:
            self.graph.query(f"""
                MERGE (c:Company {{id: {company['id']}}})
                SET c.name = '{company['name'].replace("'", "\\'")}',
                    c.domain = '{company.get('domain', '').replace("'", "\\'")}'
            """)
    
    def _sync_investments_falkor(self, investments: List[Dict]):
        """Sync investment relationships to FalkorDB"""
        if not self.graph:
            return
        
        for inv in investments:
            # Create investor node
            self.graph.query(f"""
                MERGE (i:Investor {{id: {inv['investor_id']}}})
                SET i.firm_name = '{inv.get('firm_name', '').replace("'", "\\'")}'
            """)
            
            # Create relationship
            self.graph.query(f"""
                MATCH (c:Company {{id: {inv['company_id']}}})
                MATCH (i:Investor {{id: {inv['investor_id']}}})
                MERGE (c)-[:INVESTED_BY {{type: '{inv.get('investment_type', '')}'}}]->(i)
            """)
    
    def find_co_investors(self, investor_id: int, limit: int = 10) -> List[Dict]:
        """
        Find VCs that co-invest with a given investor
        
        Returns list of investors with co-investment counts
        """
        if not self.driver and not self.graph:
            return []
        
        if self.db_type == "neo4j":
            return self._find_co_investors_neo4j(investor_id, limit)
        elif self.db_type == "falkor":
            return self._find_co_investors_falkor(investor_id, limit)
        return []
    
    def _find_co_investors_neo4j(self, investor_id: int, limit: int) -> List[Dict]:
        """Find co-investors using Neo4j"""
        if not self.driver:
            return []
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (i1:Investor {id: $investor_id})<-[:INVESTED_BY]-(c:Company)-[:INVESTED_BY]->(i2:Investor)
                WHERE i1 <> i2
                RETURN i2.id as investor_id, i2.firm_name as firm_name, count(c) as co_investment_count
                ORDER BY co_investment_count DESC
                LIMIT $limit
            """, {"investor_id": investor_id, "limit": limit})
            
            return [{
                "investor_id": record["investor_id"],
                "firm_name": record["firm_name"],
                "co_investment_count": record["co_investment_count"]
            } for record in result]
    
    def _find_co_investors_falkor(self, investor_id: int, limit: int) -> List[Dict]:
        """Find co-investors using FalkorDB"""
        if not self.graph:
            return []
        
        result = self.graph.query(f"""
            MATCH (i1:Investor {{id: {investor_id}}})<-[:INVESTED_BY]-(c:Company)-[:INVESTED_BY]->(i2:Investor)
            WHERE i1 <> i2
            RETURN i2.id, i2.firm_name, count(c) as count
            ORDER BY count DESC
            LIMIT {limit}
        """)
        
        return [{
            "investor_id": r[0],
            "firm_name": r[1],
            "co_investment_count": r[2]
        } for r in result.result_set]
    
    def find_investment_path(self, company_id1: int, company_id2: int, max_depth: int = 3) -> Optional[List[Dict]]:
        """
        Find path between two companies through shared investors
        
        Returns list of nodes and relationships forming the path
        """
        if not self.driver and not self.graph:
            return None
        
        if self.db_type == "neo4j":
            return self._find_path_neo4j(company_id1, company_id2, max_depth)
        elif self.db_type == "falkor":
            return self._find_path_falkor(company_id1, company_id2, max_depth)
        return None
    
    def _find_path_neo4j(self, company_id1: int, company_id2: int, max_depth: int) -> Optional[List[Dict]]:
        """Find path using Neo4j shortest path"""
        if not self.driver:
            return None
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH path = shortestPath(
                    (c1:Company {id: $id1})-[*..{max_depth}]-(c2:Company {id: $id2})
                )
                RETURN path
            """, {"id1": company_id1, "id2": company_id2, "max_depth": max_depth})
            
            record = result.single()
            if record:
                path = record["path"]
                return {
                    "length": len(path.relationships),
                    "nodes": [{"id": node["id"], "labels": list(node.labels)} for node in path.nodes],
                    "relationships": [{"type": rel.type, "properties": dict(rel)} for rel in path.relationships]
                }
        return None
    
    def _find_path_falkor(self, company_id1: int, company_id2: int, max_depth: int) -> Optional[List[Dict]]:
        """Find path using FalkorDB"""
        if not self.graph:
            return None
        
        # FalkorDB path finding would go here
        # Implementation depends on FalkorDB version
        return None


def sync_duckdb_to_graph(duckdb_conn, graph_db: GraphDB):
    """
    Sync all data from DuckDB to graph database
    
    Args:
        duckdb_conn: DuckDB connection
        graph_db: GraphDB instance
    """
    if not graph_db.driver and not graph_db.graph:
        print("[GraphDB] Graph database not available, skipping sync")
        return
    
    print("[GraphDB] Starting sync from DuckDB to graph database...")
    
    # Sync companies
    companies = duckdb_conn.execute("SELECT id, name, domain, created_at FROM companies").fetchall()
    company_dicts = [{
        "id": row[0],
        "name": row[1],
        "domain": row[2],
        "created_at": row[3]
    } for row in companies]
    graph_db.sync_companies(company_dicts)
    print(f"[GraphDB] Synced {len(company_dicts)} companies")
    
    # Sync investors
    investors = duckdb_conn.execute("SELECT id, firm_name, type FROM vcs").fetchall()
    investor_dicts = [{
        "id": row[0],
        "firm_name": row[1],
        "type": row[2]
    } for row in investors]
    
    # Sync investment relationships
    investments = duckdb_conn.execute("""
        SELECT 
            ci.company_id,
            ci.investor_id,
            ci.investment_type,
            ci.funding_round,
            ci.funding_amount,
            ci.investment_date,
            ci.lead_investor,
            ci.valid_from,
            ci.valid_to,
            v.firm_name,
            v.type as investor_type
        FROM company_investments ci
        JOIN vcs v ON ci.investor_id = v.id
    """).fetchall()
    
    investment_dicts = [{
        "company_id": row[0],
        "investor_id": row[1],
        "investment_type": row[2],
        "funding_round": row[3],
        "funding_amount": row[4],
        "investment_date": row[5],
        "lead_investor": row[6],
        "valid_from": row[7],
        "valid_to": row[8],
        "firm_name": row[9],
        "investor_type": row[10]
    } for row in investments]
    
    graph_db.sync_investments(investment_dicts)
    print(f"[GraphDB] Synced {len(investment_dicts)} investment relationships")
    
    print("[GraphDB] Sync complete!")

