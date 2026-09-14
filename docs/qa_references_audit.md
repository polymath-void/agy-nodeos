# QA References Audit Report

## Audit Scope
The objective was to audit the `agy-nodeos` codebase to fix broken Python imports and hardcoded paths resulting from moving several scripts (`telemetry.py`, `agy_invoke.py`, `ipc_hook.py`, `intent_injector.py`, `intent_stopper.py`) into the `scripts/` directory.

## Tools Used
- `grep_search` to trace all file dependencies and module imports across the codebase.
- Offline Universal QA Analyzer (`python ~/.gemini/config/skills/qa-analyzer/scripts/analyzer.py .`) for structural integrity checks.

## Findings & Resolutions

1. **`install.py` (Markdown Docstring Injection)**
   - **Issue:** `install.py` writes a global rule instruction to `.gemini/config/rules/nodeos_standard.md`. This instruction previously referenced `telemetry.py` directly: `You must read \`telemetry.py\` logs or execute it...`
   - **Resolution:** Modified the hardcoded reference in `install.py` to `scripts/telemetry.py` to correctly reflect the new directory structure. Re-ran `install.py` to seamlessly propagate this fix to the global configuration.

2. **`scripts/intent_injector.py` & `scripts/intent_stopper.py` (Broken Workflow Paths)**
   - **Issue:** Both scripts contained a hardcoded relative resolution to the `workflow.json` payload file via `WORKFLOW_FILE = os.path.join(os.path.dirname(__file__), "workflow.json")`. Due to their relocation to the `scripts/` directory, `os.path.dirname(__file__)` was resolving to `scripts/workflow.json` instead of the root directory workspace's `workflow.json`.
   - **Resolution:** Adjusted the path logic in both scripts to safely traverse one level up by utilizing `WORKFLOW_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "workflow.json")`.

3. **Python Import Dependencies (`scripts/agy_invoke.py` -> `scripts/telemetry.py`)**
   - **Issue:** `agy_invoke.py` relies on `import telemetry`.
   - **Resolution:** No changes needed. Both files were moved into `scripts/` side-by-side, which implies `sys.path` correctly resolves local imports when executing `python scripts/agy_invoke.py`. 

4. **`daemon.py` and Other Root Level Core Services**
   - **Issue:** Checked for hardcoded paths or `import` statements relying on the moved files.
   - **Resolution:** No direct references to these scripts were found in the daemon or engines. They handle the NodeOS orchestration independently of these external utility scripts.

## QA Verification
The Offline Universal QA Analyzer has successfully passed on the entire codebase, and all file logic paths are accurate.
