import sqlite3
import json
import os
import time
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class OrphanedNode:
    node_id: str
    filepath: str
    node_type: str

class SemanticDeadCodeEngine:
    """
    Advanced engine for eradicating semantic dead code in AGY-NodeOS.
    Queries the SQLite dependency graph to identify orphaned nodes
    and generates swarm intents for safe deletion.
    """
    
    def __init__(self, db_path: str, workspace_root: str):
        self.db_path = db_path
        self.workspace_root = workspace_root
        self.workflow_path = os.path.join(self.workspace_root, "workflow.json")
        
    def check_database_exists(self) -> bool:
        """Verifies if the agy_nodeos.db exists."""
        return os.path.exists(self.db_path)
        
    def find_orphaned_nodes(self) -> List[OrphanedNode]:
        """
        Executes the SQL query to find nodes with 0 incoming edges.
        Excludes 'entry_point' nodes to prevent removing roots.
        """
        if not self.check_database_exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}")
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = """
                SELECT n.node_id, n.filepath, n.node_type
                FROM nodes n
                LEFT JOIN edges e ON n.node_id = e.target_id
                WHERE e.source_id IS NULL 
                  AND n.node_type != 'entry_point';
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            
        return [OrphanedNode(node_id=r[0], filepath=r[1], node_type=r[2]) for r in rows]

    def _build_intent_payload(self, nodes: List[OrphanedNode]) -> Dict[str, Any]:
        """Constructs the intent JSON payload based on NodeOS schema."""
        targets = [
            {
                "id": node.node_id,
                "file_path": node.filepath,
                "action": "delete"
            }
            for node in nodes
        ]
        
        return {
            "intent": "eradicate_dead_code",
            "status": "Pending",
            "targets": targets,
            "context": "Node has 0 incoming edges in agy_nodeos.db",
            "timestamp": time.time()
        }

    def generate_deletion_intents(self) -> None:
        """
        Identifies orphaned nodes and dispatches a deletion intent to workflow.json.
        """
        orphans = self.find_orphaned_nodes()
        if not orphans:
            print("[DeadCodeEngine] No orphaned nodes detected. System clean.")
            return
            
        print(f"[DeadCodeEngine] Discovered {len(orphans)} orphaned nodes. Generating intent...")
        intent_payload = self._build_intent_payload(orphans)
        
        # Write intent to workflow.json to trigger swarm intelligence
        with open(self.workflow_path, "w") as f:
            json.dump(intent_payload, f, indent=2)
            
        print(f"[DeadCodeEngine] Intent dispatched to {self.workflow_path}")


def main():
    # Resolve paths relative to this script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.abspath(os.path.join(script_dir, ".."))
    db_path = os.path.join(workspace_root, "agy_nodeos.db")
    
    engine = SemanticDeadCodeEngine(db_path=db_path, workspace_root=workspace_root)
    try:
        engine.generate_deletion_intents()
    except Exception as e:
        print(f"[DeadCodeEngine] Error: {e}")

if __name__ == "__main__":
    main()
