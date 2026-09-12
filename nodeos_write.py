#!/data/data/com.termux/files/usr/bin/python3
import os
import sys
import ast
import json
import sqlite3
from jage_engine import JageASTEngine
from nodes_engine import NativeNodesEngine
from nodeos_read import resolve_target

def write_file(filepath, content, overwrite=True):
    if not filepath:
        return "Error: Filepath is required."

    # Resolve target destination path
    if not os.path.isabs(filepath):
        # Try resolving existing path first, or default to current workspace / Projects
        resolved = resolve_target(filepath)
        if resolved:
            target_path = resolved
        else:
            base = os.getcwd() if os.path.exists(os.getcwd()) else "/data/data/com.termux/files/home/Projects"
            target_path = os.path.abspath(os.path.join(base, filepath))
    else:
        target_path = os.path.abspath(filepath)

    if os.path.exists(target_path) and not overwrite:
        return f"Error: File '{target_path}' already exists and overwrite is set to False."

    # QA Verification for Python files before writing
    if target_path.endswith('.py'):
        try:
            ast.parse(content)
        except SyntaxError as e:
            return f"Error: Python SyntaxError on line {e.lineno}, offset {e.offset}: {e.msg}. Write rejected by NodeOS Firewall."

    # Ensure parent directory exists
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    # Atomic File Write
    try:
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        return f"Error writing to file '{target_path}': {e}"

    # Auto Re-index AST in NodeOS Database
    db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "agy_nodeos.db")
    reindexed_count = 0
    if os.path.exists(db_path) and target_path.endswith(('.py', '.js', '.ts')):
        try:
            engine = JageASTEngine(db_path=os.path.dirname(db_path))
            nodes_engine = NativeNodesEngine(db_path=db_path)
            parsed_nodes = engine.parse_file(target_path)
            if parsed_nodes:
                for node in parsed_nodes:
                    nodes_engine.add_node(
                        node_id=node['hash'],
                        node_type=node['type'],
                        name=node['name'],
                        calls=node.get('calls'),
                        filepath=target_path
                    )
                    reindexed_count += 1
                nodes_engine.sync_to_sqlite()
        except Exception as e:
            pass  # Background re-index is best-effort

    line_count = len(content.splitlines())
    byte_count = len(content.encode('utf-8'))
    return f"Successfully wrote {line_count} lines ({byte_count} bytes) to {target_path}. (AST Nodes indexed: {reindexed_count})"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: nodeos-write <filepath> <content>")
        sys.exit(1)

    path = sys.argv[1]
    data = sys.argv[2]
    print(write_file(path, data))
