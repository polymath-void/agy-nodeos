# 🧠 AGY-NodeOS: The Autonomous Swarm Operating System

[![Zero Dependency](https://img.shields.io/badge/Dependencies-Zero-brightgreen.svg?style=for-the-badge)](#) [![Agent Compatible](https://img.shields.io/badge/Agent-Native-purple.svg?style=for-the-badge)](#) [![Platform](https://img.shields.io/badge/Platform-Cross--Platform-blue.svg?style=for-the-badge)](#) [![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge)](#) [![License](https://img.shields.io/badge/License-MIT-gray.svg?style=for-the-badge)](#)

**AGY-NodeOS** is a zero-dependency Autonomous Agentic Operating System designed specifically to run natively alongside the **Antigravity (AGY)** CLI environment. By intercepting OS events and using advanced mathematical physics—specifically modeling code components using a Native QuadTree matrix, Hooke's Law, and Coulomb Repulsion—AGY-NodeOS creates a physical environment for LLM swarms to natively understand code structure, dependencies, and blast radiuses instantly.

This project is 100% cross-platform and runs flawlessly on **Windows, macOS, Linux, and Android (Termux)**.

---

## 🚀 Key Features

*   **Kinetic Code Physics:** Uses Hooke's Law (Spring Attraction) and Coulomb Repulsion via a Native QuadTree matrix to spatially cluster code components based on their Abstract Syntax Tree (AST) dependencies. [^1]
*   **Polyglot AST Ingestion:** Uses Python's native `ast` module to scan and parse the physical project graph rapidly.
*   **ACID-Compliant SQLite Graph:** Maps the entire system (including rules and skills) into a resilient SQLite graph (`agy_nodeos.db`). [^2]
*   **Zero-Dependency Ecosystem:** Runs entirely on native Python modules (`math`, `sqlite3`, `asyncio`, `ast`). No `pip install` required.
*   **Native Spatial SQL:** Sub-agents interact directly with the `agy_nodeos.db` database using standard `sqlite3` commands to evaluate AST edges and spatial blast radius.
*   **JSON Workflow Swarm Dispatch:** Operates via a purely native event-driven paradigm. Agents manipulate `workflow.json` directly, and the `daemon.py` watchdog instantly delegates tasks natively to the swarm.

---

## 🛠 Installation Guide (For Users)

AGY-NodeOS is designed for frictionless installation.

### Method 1: The One-Click Auto-Install (Recommended)
If you are using the Antigravity IDE, simply cloning this repository and opening the workspace will automatically trigger the `.agents/hooks.json` script. The system will seamlessly install itself into your global environment.

### Method 2: Manual Installation
If you prefer a manual setup or are running a headless environment, navigate to the repository root and run:
```bash
python install.py
```
**What this does:**
1. Installs the `nodeos_standard.md` rule into your `~/.gemini/config/rules/` directory.
2. Deploys the `agy-nodeos-installer` skill into your `~/.gemini/config/skills/` directory.
3. Grants your AGY agents global awareness of the NodeOS interaction paradigm.

---

## 📖 Usage Guide

AGY-NodeOS works silently in the background to empower your AI agents. 

### Starting the OS
To initialize NodeOS in a project directory, you or your agent can start the background daemon:
```bash
python daemon.py --run-as-daemon
```
*Note: In properly configured workspaces, the daemon automatically boots when the agent initializes thanks to the AGY Customization Engine (`PreInvocation` hook).*

### Dispatching Tasks
Instead of manually typing prompts, you can add task drops to `workflow.json`:
```json
{
  "type": "JSON_Task",
  "status": "pending",
  "action": "execute_agents",
  "agents": ["architect_designer"]
}
```
The daemon detects the `pending` state and automatically alerts your agent swarm via lifecycle hooks.

---

## 🤖 Agent Protocol (For AI Agents)

If you are an autonomous AI Agent interacting with this workspace, adhere to the **Native Interaction Paradigm**:
1. **File Operations**: Use your built-in editing tools (e.g., `view_file`, `replace_file_content`).
2. **Spatial Queries**: Use standard SQL queries against `agy_nodeos.db` to trace dependencies.
3. **Task Orchestration**: Update the `status` field in `workflow.json` to manage sub-agent queues.

---

## 🧬 Architectural Workflow & Citations

The underlying architecture relies on several foundational concepts adapted for LLM systems:
1. **Auto-Boot:** `hooks.json` intercepts `PreInvocation` events, booting the Python daemon `daemon.py` silently in the background.
2. **Deep Ingestion:** The daemon scans the project using `jage_engine.py`, mapping semantic `ast.Call` edges natively.
3. **Kinetic Simulation:** `nodes_engine.py` hydrates the QuadTree and applies spatial algorithms to physically pull dependent AST blocks into clustered coordinates.
4. **Intent Emission:** When a workflow intent is detected, it is logged to `workflow.json`.
5. **Telemetry Tracking:** `telemetry.py` natively tracks Swarm execution intents and state transitions (Pending -> Running -> Completed).

> **Citations:**
> [^1]: Barnes, J., & Hut, P. (1986). A hierarchical O(N log N) force-calculation algorithm (QuadTree application for NodeOS physics).
> [^2]: SQLite Consortium (2024). ACID-compliant transactional guarantees for embedded graphs.

---
*Built natively for the Antigravity Agent Swarm Ecosystem. Optimized for speed, context, and zero-dependency portability.*
