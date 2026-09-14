# NodeOS Native Interaction Paradigm

Whenever operating inside this NodeOS-managed workspace, you MUST follow these constraints:
1. You MUST use built-in system tools (view_file, list_dir, replace_file_content) to interact directly with the file system.
2. For spatial architectural insight and dependency resolution, query the SQLite database natively (e.g., `sqlite3 agy_nodeos.db "SELECT * FROM nodes;"`).
3. For task dispatching and swarm intent, directly modify `workflow.json` at the root of the workspace.
