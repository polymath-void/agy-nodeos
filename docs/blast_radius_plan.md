# Real-Time Blast Radius Warnings Plan

## 1. Context & SQLite Schema
The AGY-NodeOS uses a native SQLite graph (`agy_nodeos.db`) managed by `graph_manager.py` and `nodes_engine.py`:
- `nodes` table: Tracks entities (AST nodes) with `node_id`, `name`, `filepath`, etc.
- `edges` table: Tracks relationships with `source_id`, `target_id`, `relation_type`. In our case, `relation_type` is typically `"CALL"`. 
- **Dependency Flow**: A caller (dependent) is the `source_id`, and the callee (dependency) is the `target_id`. Downstream dependencies of a modified file are all `source_id`s that eventually target nodes within that file.

## 2. Capture Modification in `AGYRawWatchdog`
The watchdog in `daemon.py` detects file modifications and triggers `AGYNodeOSEventHandler.on_event(filepath, event_type)`.
We will inject the blast radius check immediately after detecting a modification (and before/after `self.jage.parse_file(filepath)`).

## 3. Querying the Blast Radius (SQLite Recursive CTE)
We can calculate the transitive dependents using a Recursive CTE. We query how many unique `source_id`s transitively depend on the nodes belonging to the modified `filepath`.

```python
import sqlite3

def get_blast_radius(db_path, filepath):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Recursive CTE to find all downstream nodes that depend on the modified file
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
    count = cursor.fetchone()[0]
    conn.close()
    return count
```

## 4. Threshold & Warning Emission
Inside `AGYNodeOSEventHandler.on_event` in `daemon.py`:

```python
    def on_event(self, filepath, event_type):
        if event_type == "modified" and filepath.endswith(('.py', '.js', '.ts')):
            # 1. Calculate Blast Radius
            radius_count = get_blast_radius(self.graph.db_path, filepath)
            
            # 2. Check Threshold
            if radius_count > 10:
                print(f"[Warning] High Blast Radius ({radius_count} dependents) for {filepath}")
                
                # 3a. Drop Ephemeral Intent (Agent Notification)
                workflow_file = os.path.join(self.graph.workspace, "workflow.json")
                workflow = {
                    "type": "JSON_Task",
                    "status": "pending",
                    "action": "blast_radius_warning",
                    "target_file": filepath,
                    "impacted_nodes_count": radius_count
                }
                with open(workflow_file, 'w') as f:
                    json.dump(workflow, f, indent=4)
                
                # 3b. OR write to a Warning Markdown file for the User
                warning_path = os.path.join(os.path.dirname(filepath), "warning.md")
                with open(warning_path, 'w') as w_file:
                    w_file.write(f"# High Blast Radius Warning\nModifying `{filepath}` impacts {radius_count} downstream nodes. Proceed with caution.")
```

## Summary of Integration
1. Add the `get_blast_radius` function to `AGYGraphManager` or `AGYNodeOSEventHandler`.
2. Intercept the `"modified"` event in `daemon.py`.
3. Drop the warning payload if the recursive threshold exceeds a safe limit (e.g., > 10 impacted nodes).
