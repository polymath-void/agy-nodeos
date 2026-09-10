---
name: qa-analyzer
description: A completely offline, Universal Static QA Analyzer to verify syntax, brackets, and structural integrity across Kotlin, Python, JS/TS, and C/C++ codebases.
trigger: model_decision
---

# Universal Offline QA Analyzer Skill

When the user asks you to act as a QA Tester or when you need to verify the codebase offline, use this universal tool to scan the project. It uses a Plugin Architecture to support multiple languages.

## Instructions

1.  Run the Universal Python static analyzer script located at:
    `python ~/.gemini/config/skills/qa-analyzer/scripts/analyzer.py /path/to/project`
2.  If the script reports unbalanced brackets or string closures, fix them immediately.
3.  Because this is an offline Python tool, you should also manually perform a quick visual AST check (grep for class methods) on the files you just modified to ensure no `Unresolved reference` errors exist, simulating a real compiler.
4.  Do not push to main until you are confident the code passes both the Python bracket check and your manual method reference check.
