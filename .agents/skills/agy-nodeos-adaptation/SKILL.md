---
name: agy-nodeos-adaptation
description: Standard Operating Procedure for all Agents adapting to and operating within the AGY-NodeOS ecosystem (Jage Re-Stitcher, Swarm Workflows, and Zero-Dependency Architecture).
---

# AGY-NodeOS Adaptation Protocol

You are operating inside **AGY-NodeOS**, a highly advanced, zero-dependency, physics-driven operating system designed to handle massive legacy codebases with zero file I/O latency for agents. 

To safely and efficiently operate within this workspace, you **MUST** adhere to the following architectural rules:

## 1. Do Not Edit Massive Source Files Directly
If you need to edit a function or class inside a massive codebase (e.g., a 10,000-line `engine.py` file), **DO NOT** use your standard `replace_file_content` or `write_to_file` tools to edit the `.py` file directly. 
Instead, you must delegate the file writing to the OS Kernel using the **Jage Re-Stitcher**.

## 2. Reading Code via JSON Nodes
The OS automatically parses the entire AST of the project and stores every function, class, and method as a tiny, isolated JSON node inside the `.jsagent/schema/` directory.
When you need to read a codebase, simply list the `.jsagent/schema/` directory and read the specific JSON file you need. 

Example of a cached node (`.jsagent/schema/abc123xx...json`):
```json
{
    "metadata": {
        "type": "FunctionDef",
        "name": "calculate_tax",
        "hash": "abc123xx...",
        "file": "/path/to/legacy_math.py"
    },
    "source": "def calculate_tax(amount):\n    return amount * 0.15"
}
```

## 3. Writing Code via the NodeOS Invoker
To safely edit a function, you must invoke the NodeOS Swarm Dispatcher using the `agy_invoke.py` script. This handles dropping the JSON payload and automatically streams the background OS telemetry back into your standard output.

Use your `run_command` tool to execute it synchronously:

```bash
python agy_invoke.py '{
    "type": "JSON_Task",
    "status": "pending",
    "action": "stitch",
    "node_hash": "<THE_EXACT_FULL_HASH_FROM_THE_SCHEMA>",
    "new_source": "def calculate_tax(amount):\n    print(\"Optimized\")\n    return amount * 0.12"
}'
```

The terminal will automatically stream the Swarm's telemetry and QA Firewall results back to you.

## 4. The Swarm Feedback Loop (QA Firewall)
If the NodeOS firewall detects a syntax error, your terminal output will display `FAILED QA FIREWALL` along with the error log. You must read the trace, fix your `new_source` string, and run the `agy_invoke.py` command again.

---
**By adhering to this skill, you guarantee sub-millisecond agent reaction times, native real-time terminal telemetry, and mathematically prevent corruption in massive enterprise architectures.**
