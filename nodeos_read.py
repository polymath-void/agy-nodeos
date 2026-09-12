#!/usr/bin/env python3
import os
import sys
import glob
import sqlite3
import json

def resolve_target(target, db_path=None):
    if not target:
        return None

    # 1. Absolute file path
    if os.path.isabs(target) and os.path.exists(target):
        return os.path.abspath(target)

    # 2. Direct relative path from CWD
    if os.path.exists(target) and os.path.isfile(target):
        return os.path.abspath(target)

    # 3. Dynamic Portable Workspace Relative Bases
    home = os.path.expanduser("~")
    nodeos_dir = os.path.dirname(os.path.realpath(__file__))
    projects_dir = os.environ.get("PROJECTS_DIR", os.path.join(home, "Projects"))
    config_dir = os.path.join(home, ".gemini", "config")

    base_dirs = [
        os.getcwd(),
        nodeos_dir,
        projects_dir,
        config_dir,
        home
    ]
    for base in base_dirs:
        candidate = os.path.join(base, target)
        if os.path.exists(candidate) and os.path.isfile(candidate):
            return os.path.abspath(candidate)

    # 4. Database Lookup by Symbol Name, Node ID, or Filepath
    if db_path is None:
        db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "agy_nodeos.db")

    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # Exact match on name or node_id
            cursor.execute("SELECT filepath FROM nodes WHERE (name = ? OR node_id = ?) AND filepath IS NOT NULL", (target, target))
            row = cursor.fetchone()
            if row and row[0] and os.path.exists(row[0]):
                conn.close()
                return row[0]

            # Partial match on name or filepath
            cursor.execute("SELECT filepath FROM nodes WHERE (name LIKE ? OR filepath LIKE ?) AND filepath IS NOT NULL", (f"%{target}%", f"%{target}"))
            rows = cursor.fetchall()
            conn.close()
            for r in rows:
                if r[0] and os.path.exists(r[0]):
                    return r[0]
        except Exception:
            pass

    # 5. Recursive Glob Fallback
    for base in base_dirs[:3]:
        matches = glob.glob(os.path.join(base, "**", target), recursive=True)
        if matches and os.path.isfile(matches[0]):
            return os.path.abspath(matches[0])

    return None

def read_target(target, start_line=None, end_line=None):
    filepath = resolve_target(target)
    if not filepath:
        return f"Error: Could not resolve target file or symbol '{target}' anywhere in workspace or NodeOS DB."

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            
        total_lines = len(lines)
        if start_line is not None or end_line is not None:
            s = max(1, int(start_line)) if start_line else 1
            e = min(total_lines, int(end_line)) if end_line else total_lines
            selected = lines[s-1:e]
            content = "".join(f"{i+s:4d} | {line}" for i, line in enumerate(selected))
            header = f"--- FILE: {filepath} (Lines {s}-{e} of {total_lines}) ---"
        else:
            content = "".join(f"{i+1:4d} | {line}" for i, line in enumerate(lines))
            header = f"--- FILE: {filepath} ({total_lines} lines) ---"

        return f"{header}\n{content}"
    except Exception as e:
        return f"Error reading file '{filepath}': {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: nodeos-read <file_path_or_symbol_name> [start_line] [end_line]")
        sys.exit(1)

    target = sys.argv[1]
    s_line = int(sys.argv[2]) if len(sys.argv) > 2 else None
    e_line = int(sys.argv[3]) if len(sys.argv) > 3 else None
    print(read_target(target, s_line, e_line))
