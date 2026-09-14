import sqlite3
import json
import os
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

class BlastRadiusEngine:
    """
    Engine to calculate the blast radius of file modifications using a Recursive CTE
    against the NodeOS SQLite graph.
    """
    
    def __init__(self, db_path: str, workspace: str, threshold: int = 10):
        self.db_path = db_path
        self.workspace = workspace
        self.threshold = threshold

    def get_blast_radius(self, filepath: str) -> int:
        """
        Calculates the number of downstream nodes that depend on the given filepath.
        
        Args:
            filepath: The path of the modified file.
            
        Returns:
            int: The number of distinct downstream nodes impacted.
        """
        if not os.path.exists(self.db_path):
            logger.error(f"Database not found at {self.db_path}")
            return 0

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = '''
                    WITH RECURSIVE downstream AS (
                        -- Base Case: Nodes that directly call nodes in the modified file
                        SELECT e.source_id 
                        FROM edges e 
                        JOIN nodes n ON e.target_id = n.node_id 
                        WHERE n.filepath = ?
                        
                        UNION
                        
                        -- Recursive Step: Nodes that call the nodes found in the previous step
                        SELECT e.source_id
                        FROM edges e
                        INNER JOIN downstream d ON e.target_id = d.source_id
                    )
                    SELECT COUNT(DISTINCT source_id) FROM downstream;
                '''
                cursor.execute(query, (filepath,))
                result = cursor.fetchone()
                return result[0] if result else 0
        except sqlite3.Error as e:
            logger.error(f"SQLite error while calculating blast radius: {e}")
            return 0

    def enforce_threshold(self, filepath: str) -> None:
        """
        Checks the blast radius for the filepath and emits warnings if it exceeds the threshold.
        
        Args:
            filepath: The path of the modified file.
        """
        radius_count = self.get_blast_radius(filepath)
        logger.info(f"Blast radius for {filepath}: {radius_count} downstream nodes.")

        if radius_count > self.threshold:
            logger.warning(f"High Blast Radius ({radius_count} dependents) for {filepath}")
            self._drop_intent(filepath, radius_count)
            self._write_warning_file(filepath, radius_count)

    def _drop_intent(self, filepath: str, radius_count: int) -> None:
        """
        Drops a workflow.json intent to notify the agent swarm.
        """
        workflow_file = os.path.join(self.workspace, "workflow.json")
        workflow = {
            "type": "JSON_Task",
            "status": "pending",
            "action": "blast_radius_warning",
            "target_file": filepath,
            "impacted_nodes_count": radius_count
        }
        
        try:
            with open(workflow_file, 'w') as f:
                json.dump(workflow, f, indent=4)
            logger.info(f"Dropped intent at {workflow_file}")
        except IOError as e:
            logger.error(f"Failed to write workflow.json: {e}")

    def _write_warning_file(self, filepath: str, radius_count: int) -> None:
        """
        Writes a warning.md file in the same directory as the modified file.
        """
        warning_path = os.path.join(os.path.dirname(filepath), "warning.md")
        
        content = (
            f"# High Blast Radius Warning\n"
            f"Modifying `{filepath}` impacts {radius_count} downstream nodes. "
            f"Proceed with caution.\n"
        )
        
        try:
            with open(warning_path, 'w') as w_file:
                w_file.write(content)
            logger.info(f"Wrote warning markdown at {warning_path}")
        except IOError as e:
            logger.error(f"Failed to write warning.md: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Calculate Blast Radius for a file in AGY-NodeOS.")
    parser.add_argument("--db", required=True, help="Path to agy_nodeos.db")
    parser.add_argument("--workspace", required=True, help="Path to workspace root")
    parser.add_argument("--file", required=True, help="Modified filepath to check")
    parser.add_argument("--threshold", type=int, default=10, help="Blast radius threshold")
    
    args = parser.parse_args()
    engine = BlastRadiusEngine(db_path=args.db, workspace=args.workspace, threshold=args.threshold)
    engine.enforce_threshold(args.file)
