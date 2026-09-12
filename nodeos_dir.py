#!/usr/bin/env python3
import os
import sys
import json
from nodeos_read import resolve_target

def list_directory(directory_path=None, recursive=False):
    if not directory_path or directory_path in (".", "./"):
        dir_path = os.getcwd()
    elif not os.path.isabs(directory_path):
        resolved = resolve_target(directory_path)
        if resolved and os.path.isdir(resolved):
            dir_path = resolved
        else:
            dir_path = os.path.abspath(os.path.join(os.getcwd(), directory_path))
    else:
        dir_path = os.path.abspath(directory_path)

    if not os.path.exists(dir_path):
        return f"Error: Directory '{dir_path}' does not exist."

    if not os.path.isdir(dir_path):
        return f"Error: Path '{dir_path}' is a file, not a directory."

    items = []
    try:
        if recursive:
            for root, dirs, files in os.walk(dir_path):
                if ".git" in root or "__pycache__" in root or "node_modules" in root:
                    continue
                rel_root = os.path.relpath(root, dir_path)
                for d in dirs:
                    if d in (".git", "__pycache__", "node_modules"): continue
                    items.append({
                        "path": os.path.join(rel_root, d) if rel_root != "." else d,
                        "type": "directory"
                    })
                for f in files:
                    full_p = os.path.join(root, f)
                    items.append({
                        "path": os.path.join(rel_root, f) if rel_root != "." else f,
                        "type": "file",
                        "size_bytes": os.path.getsize(full_p)
                    })
        else:
            for entry in os.listdir(dir_path):
                if entry in (".git", "__pycache__", "node_modules"):
                    continue
                full_p = os.path.join(dir_path, entry)
                is_dir = os.path.isdir(full_p)
                items.append({
                    "name": entry,
                    "type": "directory" if is_dir else "file",
                    "size_bytes": os.path.getsize(full_p) if not is_dir else None
                })
                
        # Sort directories first, then files
        items.sort(key=lambda x: (x["type"] != "directory", x.get("name") or x.get("path")))
        return json.dumps({"directory": dir_path, "total_items": len(items), "items": items}, indent=2)
    except Exception as e:
        return f"Error listing directory '{dir_path}': {e}"

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    rec = "--recursive" in sys.argv or "-r" in sys.argv
    print(list_directory(target, recursive=rec))
