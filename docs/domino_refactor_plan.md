# The Domino Refactor Engine Plan

## 1. Querying the Call Graph (AST Edges)
AGY-NodeOS natively stores parsed polyglot AST nodes and edges in `agy_nodeos.db` (`nodes` and `edges` tables). 
- **Nodes Table**: Maps `FunctionDef`, `AsyncFunctionDef`, `ClassDef` and JS fallbacks to `node_id`, `hash`, and `filepath`.
- **Edges Table**: Maps dependencies using `source_id` to `target_id` with `relation_type = 'CALL'`.

To extract the exact list of files invoking a specific function hash, query the SQLite database via `run_command` with this inner join:

```bash
sqlite3 agy_nodeos.db "SELECT DISTINCT caller.filepath FROM edges e JOIN nodes target ON e.target_id = target.node_id JOIN nodes caller ON e.source_id = caller.node_id WHERE target.hash = '<SPECIFIC_FUNCTION_HASH>' AND e.relation_type = 'CALL';"
```

## 2. Dispatching Parallel Refactor Swarm Tasks
The AGY-NodeOS Daemon runs a Zero-Dependency Raw Watchdog that constantly polls for changes to `workflow.json` in the workspace root. To trigger the deterministic refactor loop across the found files, format and drop a JSON workflow payload.

Create or update `workflow.json` with an array of tasks under the `agents` key:

```json
{
  "status": "pending",
  "agents": [
    {
      "task": "refactor_domino",
      "target_file": "<FILEPATH_1_FROM_SQL>",
      "instruction": "Refactor function calls invoking hash <SPECIFIC_FUNCTION_HASH> to align with the newly updated signature."
    },
    {
      "task": "refactor_domino",
      "target_file": "<FILEPATH_2_FROM_SQL>",
      "instruction": "Refactor function calls invoking hash <SPECIFIC_FUNCTION_HASH> to align with the newly updated signature."
    }
  ]
}
```

## 3. Execution & Validation
Once `workflow.json` is modified, the event loop will immediately detect it, transition the status to `running`, and emit the intent for external Antigravity swarm agents to pick up. 
As agents generate refactored code blocks, they can sequentially drop `stitch` action workflows to leverage the built-in JAGE Re-Stitcher, which incorporates a Native QA Verifier kernel that guarantees structural syntax integrity before committing the file modification.
