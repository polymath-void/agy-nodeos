# AGY-NodeOS Re-Architect Blueprint

## 1. Current State Analysis
The existing AGY-NodeOS architecture in `/Projects/agy-nodeos` provides a foundational baseline for an agentic operating system:
* **`daemon.py`**: A `watchdog`-based event listener that captures file modifications in real-time.
* **`jage_engine.py`**: An AST parser that chunks Python code into semantic blocks and hashes them into `.jsagent/schema/` JSON files.
* **`nodes_engine.py`**: An in-memory QuadTree spatial matrix for visual/spatial clustering of contextual nodes.
* **`graph_manager.py`**: An SQLite database mapping system rules, skills, and node edges, alongside a stubbed internal swarm dispatcher.

## 2. Missing Features, Tools, and Dependencies

To evolve this into a robust **24/7 Autonomous Agentic OS**, the following components must be re-architected or introduced:

### A. Persistent Spatial Sync & Hooke's Law Clustering (Implemented)
* **Status**: Complete. The `NativeNodesEngine` (QuadTree) now syncs `x_coord` and `y_coord` to the SQLite `nodes` table. It utilizes Euler Integration with Coulomb Repulsion and Hooke's Law Spring Attraction to physically cluster code components based on AST dependencies.

### B. Zero-Dependency Native AST Parsing (Implemented)
* **Status**: Complete. `jage_engine.py` relies exclusively on Python's native `ast` module. Attempts to use `tree-sitter` were rejected to maintain zero-dependency compliance within Android Termux ABI. It recursively walks the AST to map `ast.Call` execution edges natively.

### C. Decoupled Intent Dispatcher (Implemented)
* **Status**: Complete. `daemon.py` does not execute python scripts natively. Instead, it acts as a decoupled Intent Emitter. It creates `workflow.json` with a `pending` status. The external AGY Agent Swarm monitors this telemetry, executes the intelligence dynamically, and updates the status to `completed`.

### D. Zero-Dependency System
* **Strict Rule**: No `requirements.txt` or third-party packages allowed.
  * File monitoring uses native `asyncio` (AGYRawWatchdog).
  * Physics engine uses native `math` module.
  * DB uses native `sqlite3`.
  * AST mapping uses native `ast`.
  * Telemetry is tracked natively via `sys.stdout` and JSON.

## 3. The Architectural Relationship: SQLite Parent DB and JSON Child Nodes

A core design principle of AGY-NodeOS is that the **SQLite DB acts as the Parent Node (Source of Truth)**, while **JSON files act as Child Nodes (Agent Workflows & State)**. 

### Why this design?

1. **Agent-Centric Interfaces (JSON)**: 
   LLM-based autonomous agents natively consume and produce JSON. By providing workflows, AST blocks, and task instructions as physical JSON files on the filesystem, agents can easily read, parse, and edit their state using standard file I/O tools. They do not need complex SQL drivers, connection pooling, or query building logic.
   
2. **ACID Compliance & Global State (SQLite)**: 
   While JSON is great for individual agent consumption, it is terrible for concurrent writes, relational mapping, and complex graph querying. The SQLite database serves as the centralized parent node that maintains ACID properties. It tracks the global graph structure, edges (relationships between tasks and files), spatial coordinates, and timestamps.

3. **The Synchronization Loop**:
   * **Downstream**: When a user request or system event creates a new task in the SQLite DB, the OS generates a standardized `workflow.json` (Child Node) in the agent's active directory.
   * **Upstream**: The agent executes the task and writes its output/state to the `workflow.json`. The `daemon.py` detects this modification, parses the JSON, and updates the global SQLite graph (Parent Node).

By decoupling the strict relational tracking (SQLite) from the flexible execution context (JSON), AGY-NodeOS achieves both system stability and agent accessibility.
