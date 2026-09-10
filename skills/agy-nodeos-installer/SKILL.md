---
name: agy-nodeos-installer
description: Standard Operating Procedure for injecting and activating the AGY-NodeOS background daemon and hook into a target workspace.
---

# AGY-NodeOS Injection Protocol

Whenever you are tasked with initializing a project or establishing the AGY-NodeOS 24/7 background architecture in a workspace, you MUST follow these steps to inject the lifecycle hooks.

## 1. Verify Target Workspace
Ensure you are operating inside the intended project directory. If the project does not have a local `.agents` folder, you must create it:
```bash
mkdir -p .agents
```

## 2. Copy the Lifecycle Hook
The master hook file resides in the core AGY-NodeOS repository. You must copy it into the local project's `.agents` directory so the Antigravity CLI binds the daemon to the workspace.
```bash
cp /data/data/com.termux/files/home/Projects/agy-nodeos/hooks.json .agents/hooks.json
```

## 3. Validate Daemon Boot
Once the hook is copied, the `agy-nodeos-boot` script will automatically trigger on the very next `PreInvocation` event (which means the next time the agent is prompted). 

The hook executes the following:
`pgrep -f 'python.*daemon.py' > /dev/null || (nohup python /data/data/com.termux/files/home/Projects/agy-nodeos/daemon.py > /data/data/com.termux/files/home/Projects/agy-nodeos/daemon.log 2>&1 &)`

This guarantees the native Python AST Engine, SQLite Graph Manager, and QuadTree Spatial Physics Matrix are running silently in the background 24/7.

## 4. Sub-Agent Intent Handling
Do NOT manually run `python daemon.py` in the terminal. The hook handles it autonomously.

Remember that AGY-NodeOS is completely decoupled from execution logic. It acts purely as a physical environment and **Intent Emitter**. 
When you (the main agent) observe `workflow.json` transitioning to `"status": "pending"`, you must use your `invoke_subagent` tool to spawn a specialized AGY agent to perform the task. 
## 5. Native Codebase Context (Search Protocol)
When operating inside an AGY-NodeOS initialized workspace, you are strictly prohibited from relying on manual `grep` scans for structural understanding. 
Instead, rely on the native Graph Database by querying the search utility:
```bash
python nodeos_search.py "<TargetClassNameOrFunction>"
```
This utility natively computes K-Nearest Neighbors (KNN) from the QuadTree physics matrix and pulls edge targets, providing you with a clean JSON payload of both direct code dependencies and physical spatial neighbors (blast radius context).
