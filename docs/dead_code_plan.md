# Semantic Dead Code Eradication in AGY-NodeOS

## Overview
This document outlines the implementation plan for identifying and removing orphaned code (Semantic Dead Code) within the AGY-NodeOS environment. Dead code eradication leverages the SQLite dependency graph to safely delete nodes (files, classes, functions) that are no longer referenced.

## Database Schema Context
*To verify the exact schema, run:*
`sqlite3 agy_nodeos.db "SELECT sql FROM sqlite_master WHERE type='table';"`

Typically, the schema consists of:
- `nodes`: Contains entities with a unique `id` and `node_type`.
- `edges`: Contains dependencies mapping `source_id` (caller) to `target_id` (callee).

## Querying Orphaned Nodes
To identify nodes that have zero incoming edges (nothing depends on them), use the following SQL query:

```sql
SELECT n.node_id, n.filepath, n.node_type
FROM nodes n
LEFT JOIN edges e ON n.node_id = e.target_id
WHERE e.source_id IS NULL 
  AND n.node_type != 'entry_point'; -- Exclude main execution points/roots
```

## Triggering Swarm Intent via `daemon.py`
The `daemon.py` script acts as the NodeOS watchdog. To automate eradication:

1. **Periodic Scan:** `daemon.py` runs the orphaned node SQL query periodically or hooks into a post-refactoring event.
2. **Intent Generation:** For each identified orphaned node, the daemon constructs a swarm intent.
3. **Dispatch:** The daemon writes this intent to `workflow.json` at the root of the workspace.

**Example `workflow.json` intent:**
```json
{
  "intent": "eradicate_dead_code",
  "status": "Pending",
  "targets": [
    {
      "id": "node_123",
      "file_path": "src/utils/old_helper.py",
      "action": "delete"
    }
  ],
  "context": "Node has 0 incoming edges in agy_nodeos.db"
}
```

4. **Execution:** The External Swarm Intelligence (AI agents) reads `workflow.json`, executes the physical deletion of the files, and updates the SQLite graph to reflect the removed dead code.
