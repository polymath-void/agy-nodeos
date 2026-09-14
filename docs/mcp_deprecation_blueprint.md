# MCP & Standalone Tools Deprecation Blueprint for AGY-NodeOS

## 1. Executive Summary
The AGY-NodeOS project is transitioning to a purely native agentic interaction paradigm. We are deprecating the middleman abstraction layer represented by the Model Context Protocol (MCP) Server (`mcp_server.py`) and its associated standalone CLI wrappers (`nodeos_*.py`). Agents will now interact directly with the OS file system, SQLite matrices, and the event-driven workflow engine, significantly reducing latency, complexity, and dependencies.

## 2. Impact Analysis
The removal of `mcp_server.py`, `nodeos_read.py`, `nodeos_write.py`, `nodeos_dir.py`, `nodeos_task.py`, `nodeos_status.py`, and `nodeos_search.py` will have the following impacts:

*   **Daemon Core Operations:** **ZERO IMPACT**. The core event loop (`daemon.py`), `jage_engine.py`, `nodes_engine.py`, and `graph_manager.py` are fully decoupled from the MCP server. The background raw watchdog natively listens to file system events independently.
*   **Agent Interaction:** Agents will lose access to MCP-specific tools (e.g., `nodeos_semantic_code_search`, `nodeos_read_file`). They must fall back to their built-in native capabilities for file reading, editing, and bash execution.
*   **Symbol Lookup & Spatial Search:** Instead of calling the `nodeos_search.py` script to query KNN physical dependencies, agents can run `sqlite3 agy_nodeos.db` commands natively via command execution tools, or query exported spatial JSONs.
*   **Task/Workflow Management:** Agents can no longer use tools like `nodeos_task_create`. Instead, they must directly author or update `workflow.json` drops in the workspace, which the daemon natively picks up and executes.

## 3. The New Purely Native Interaction Paradigm
Moving forward, agents will act as native residents of the NodeOS ecosystem rather than external API consumers:

### A. Reading, Writing, and File Management
Agents will use their own built-in, highly optimized tools (e.g., `view_file`, `write_to_file`, `multi_replace_file_content`, `list_dir`) to interact with the file system directly. This completely eliminates the brittle Python CLI wrappers and enables much more robust multi-line modifications that the old `nodeos_write.py` script struggled with.

### B. Task and Swarm Management
Task dispatching will rely strictly on **JSON Workflow Drops**.
1. To initiate a swarm task, an agent creates or modifies `workflow.json` at the root of the workspace.
2. The `AGYRawWatchdog` in `daemon.py` detects the modification natively within seconds.
3. The `AGYNodeOSEventHandler` parses the JSON and delegates the intent to internal processing, such as the `InternalSwarmDispatcher` or by forking an AGY CLI subprocess.
4. Agents monitor progress and output by reading state updates written back to `workflow.json` or by observing `daemon.log`.

### C. Node & Spatial Matrix Queries
For architectural insight and dependency resolution:
1. **Direct SQLite Querying:** Agents can use terminal tools to run SQL queries against `agy_nodeos.db` (e.g., `sqlite3 agy_nodeos.db "SELECT * FROM nodes WHERE name LIKE '%Jage%';"`) to evaluate spatial dependencies and AST edges.
2. **Matrix Exports (Future Enhancement):** As a seamless alternative to SQL, the daemon can be extended to continually serialize a lightweight map of active nodes into a `spatial_matrix.json` read-only file, allowing instant semantic consumption.

## 4. Step-by-Step Technical Migration Procedure

### Phase 1: Verification & Decoupling
1. **Audit Imports:** Verify that `daemon.py`, `graph_manager.py`, and engine scripts contain absolutely no import references to `nodeos_*.py` or `mcp_server.py`. (Audit completed: No dependencies exist).
2. **Update Core System Prompts:** Update agent system prompts and embedded skills (like `nodeshub-engine`) to stop calling MCP tools. Instruct agents to natively manipulate `workflow.json` for task queuing.

### Phase 2: Component Deletion
Execute the safe deletion of the deprecated scripts.
```bash
# In the terminal, execute:
cd /data/data/com.termux/files/home/Projects/agy-nodeos
rm mcp_server.py
rm nodeos_read.py
rm nodeos_write.py
rm nodeos_dir.py
rm nodeos_task.py
rm nodeos_status.py
rm nodeos_search.py
```

### Phase 3: Update System Documentation
1. Modify `README.md` to purge any configuration, startup instructions, or references related to the MCP server.
2. Document the structure and schema of `workflow.json` in the README or a dedicated doc so agents understand exactly how to format drops (e.g., required fields: `type`, `status`, `action`, `agents`, `target`).

### Phase 4: Refine the Watchdog Engine (Optional)
Ensure the `AGYRawWatchdog` inside `daemon.py` handles rapid overwrites of `workflow.json` gracefully without race conditions. Introduce file-lock mechanisms or slight debouncing in `daemon.py` to prevent I/O read conflicts when agents perform high-frequency workflow manipulations.
