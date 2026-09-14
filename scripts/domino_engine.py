import sqlite3
import json
import os
import argparse
from typing import List

class DominoEngine:
    """
    Advanced architecture module for executing the Domino Refactor blueprint.
    Manages querying the AST call graph and dispatching parallel refactor swarms.
    """
    
    def __init__(self, db_path: str = "agy_nodeos.db", workflow_path: str = "workflow.json"):
        self.db_path = db_path
        self.workflow_path = workflow_path

    def find_callers(self, target_hash: str) -> List[str]:
        """
        Finds all files calling a specific hash by querying the AST edges.
        Uses INNER JOIN logic to resolve source and target node filepaths.
        """
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at path: {self.db_path}")

        query = """
            SELECT DISTINCT caller.filepath 
            FROM edges e 
            JOIN nodes target ON e.target_id = target.node_id 
            JOIN nodes caller ON e.source_id = caller.node_id 
            WHERE target.hash = ? AND e.relation_type = 'CALL';
        """
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (target_hash,))
                rows = cursor.fetchall()
                return [row[0] for row in rows]
        except sqlite3.Error as e:
            print(f"Database error during find_callers: {e}")
            return []

    def generate_intent(self, target_hash: str, callers: List[str]) -> None:
        """
        Generates a multi-agent parallel intent payload and writes it to workflow.json.
        """
        if not callers:
            print(f"No callers found for hash '{target_hash}'. No workflow generated.")
            return

        workflow = {
            "status": "pending",
            "agents": []
        }

        for caller_file in callers:
            task = {
                "task": "refactor_domino",
                "target_file": caller_file,
                "instruction": f"Refactor function calls invoking hash {target_hash} to align with the newly updated signature."
            }
            workflow["agents"].append(task)

        try:
            with open(self.workflow_path, 'w', encoding='utf-8') as f:
                json.dump(workflow, f, indent=2)
            print(f"Successfully dispatched refactor swarm intent for {len(callers)} target files to {self.workflow_path}.")
        except IOError as e:
            print(f"IOError writing to {self.workflow_path}: {e}")

    def run_refactor(self, target_hash: str) -> None:
        """
        Executes the end-to-end domino refactor chain for a specific hash.
        """
        print(f"Starting Domino Refactor for hash: {target_hash}")
        callers = self.find_callers(target_hash)
        self.generate_intent(target_hash, callers)


def main():
    parser = argparse.ArgumentParser(description="Domino Refactor Engine")
    parser.add_argument("hash", help="The specific function hash to refactor")
    parser.add_argument("--db", default="agy_nodeos.db", help="Path to agy_nodeos.db SQLite database")
    parser.add_argument("--workflow", default="workflow.json", help="Path to output workflow.json payload")
    
    args = parser.parse_args()
    
    engine = DominoEngine(db_path=args.db, workflow_path=args.workflow)
    engine.run_refactor(args.hash)


if __name__ == "__main__":
    main()
