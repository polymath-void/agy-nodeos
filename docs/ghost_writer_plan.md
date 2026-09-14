# Spatial Context Ghost Writing Plan

## 1. File Spatial Coordinate Resolution
When a new file is created, the system drops its nodes into the simulation. Find the spatial center of the new file by calculating the centroid (average x and y) of its nodes:
```sql
SELECT AVG(x_coord), AVG(y_coord) FROM nodes WHERE filepath = 'path/to/new_file';
```

## 2. Nearest Neighbor Calculation
Determine the physical K-nearest neighbors to the new file's centroid using a fast SQLite squared-distance calculation, excluding nodes from the file itself:
```sql
SELECT node_id, filepath, node_type, name, 
       ((x_coord - ?)*(x_coord - ?) + (y_coord - ?)*(y_coord - ?)) AS dist 
FROM nodes 
WHERE filepath != 'path/to/new_file' 
ORDER BY dist ASC 
LIMIT 10;
```

## 3. Extract AST Signatures
For each nearest neighbor returned by the SQL query:
- Locate the node's schema file at `.jsagent/schema/{node_id}.json`.
- Read and extract the `source` attribute, which contains the raw AST signature / polyglot code mapped by the `JageASTEngine`.

## 4. Inject Context into `workflow.json`
Bundle the extracted AST signatures into a structured payload and drop it into `workflow.json` at the workspace root. The NodeOS daemon watchdog will detect this intent and dispatch the swarm agent with the spatial context.
```json
{
  "type": "JSON_Task",
  "status": "pending",
  "action": "ghost_write",
  "target_file": "path/to/new_file",
  "spatial_context": [
    {
      "node_name": "ExampleNode",
      "filepath": "path/to/neighbor.py",
      "signature": "def example_function():\\n    pass"
    }
  ]
}
```
