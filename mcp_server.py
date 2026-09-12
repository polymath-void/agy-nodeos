#!/data/data/com.termux/files/usr/bin/python3
import sys
import json
import subprocess
import os
import re


def handle_request(req):
    method = req.get("method")
    params = req.get("params", {})
    req_id = req.get("id")
    
    # 1. Initialization Handshake
    if method in ("initialize", "server/discover"):
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "nodeos-mcp", "version": "1.0.0"}
            }
        }
    
    # 2. Tool Discovery
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "nodeos_semantic_code_search",
                        "description": "Natively query the NodeOS SQLite physical graph matrix for code dependencies and K-Nearest Neighbor (KNN) spatial blast radius. Use this instead of grep_search for ALL code queries.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The exact name of the Python Class or Function to query in the physics matrix."
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "nodeos_read_file",
                        "description": "Natively read the contents of a file inside the NodeOS matrix. Supports optional start_line and end_line.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filepath": {
                                    "type": "string",
                                    "description": "The absolute or relative path to the file to read."
                                },
                                "start_line": {
                                    "type": "integer",
                                    "description": "Optional 1-based start line number."
                                },
                                "end_line": {
                                    "type": "integer",
                                    "description": "Optional 1-based end line number."
                                }
                            },
                            "required": ["filepath"]
                        }
                    },
                    {
                        "name": "nodeos_write_file",
                        "description": "Natively create or write content to a file inside the NodeOS matrix. Verifies Python syntax and auto-indexes AST nodes.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filepath": {
                                    "type": "string",
                                    "description": "The absolute or relative destination file path."
                                },
                                "content": {
                                    "type": "string",
                                    "description": "The text content to write."
                                },
                                "overwrite": {
                                    "type": "boolean",
                                    "description": "Whether to overwrite existing files (default: true)."
                                }
                            },
                            "required": ["filepath", "content"]
                        }
                    },
                    {
                        "name": "nodeos_list_dir",
                        "description": "Natively list files and subdirectories inside a NodeOS workspace.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "directory_path": {
                                    "type": "string",
                                    "description": "Optional directory path to list (defaults to current working directory)."
                                },
                                "recursive": {
                                    "type": "boolean",
                                    "description": "Set true for recursive directory walk."
                                }
                            }
                        }
                    },
                    {
                        "name": "nodeos_status",
                        "description": "Natively check the health status of the AGY-NodeOS background daemon and SQLite graph matrix.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "nodeos_task_create",
                        "description": "Natively create a task/workflow intent in NodeOS for sub-agent swarm execution.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "action": {
                                    "type": "string",
                                    "description": "The action or intent name (e.g. code_generation, refactor, qa_check)."
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Detailed explanation of the task."
                                },
                                "agents": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of sub-agent type names to assign."
                                },
                                "target": {
                                    "type": "string",
                                    "description": "Target file or symbol name."
                                }
                            },
                            "required": ["action", "description"]
                        }
                    },
                    {
                        "name": "nodeos_task_list",
                        "description": "Natively list active and historical tasks/workflows in NodeOS.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "status_filter": {
                                    "type": "string",
                                    "description": "Filter tasks by status (e.g. pending, running, completed, failed_qa, cancelled, all)."
                                }
                            }
                        }
                    },
                    {
                        "name": "nodeos_task_update",
                        "description": "Natively update the status or result of a NodeOS task.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "task_id": {
                                    "type": "string",
                                    "description": "The ID of the task to update."
                                },
                                "status": {
                                    "type": "string",
                                    "description": "New status (running, completed, failed_qa, cancelled)."
                                },
                                "result": {
                                    "type": "string",
                                    "description": "Optional result output summary."
                                }
                            },
                            "required": ["task_id", "status"]
                        }
                    },
                    {
                        "name": "nodeos_task_cancel",
                        "description": "Natively cancel a pending or running NodeOS task.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "task_id": {
                                    "type": "string",
                                    "description": "The ID of the task to cancel."
                                }
                            },
                            "required": ["task_id"]
                        }
                    }
                ]
            }
        }
        
    # 3. Tool Execution
    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        
        if tool_name == "nodeos_semantic_code_search":
            query = args.get("query", "")
            
            # Subprocess to our existing zero-dependency search script
            script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "nodeos_search.py")
            result = subprocess.run([sys.executable, script_path, query], capture_output=True, text=True)
            
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": result.stdout}]
                }
            }
            
        elif tool_name == "nodeos_read_file":
            filepath = args.get("filepath", "")
            start_line = args.get("start_line")
            end_line = args.get("end_line")
            
            from nodeos_read import read_target
            output = read_target(filepath, start_line, end_line)
                
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": output}]
                }
            }

        elif tool_name == "nodeos_write_file":
            filepath = args.get("filepath", "")
            content = args.get("content", "")
            overwrite = args.get("overwrite", True)
            
            from nodeos_write import write_file
            output = write_file(filepath, content, overwrite)

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": output}]
                }
            }

        elif tool_name == "nodeos_list_dir":
            directory_path = args.get("directory_path")
            recursive = args.get("recursive", False)

            from nodeos_dir import list_directory
            output = list_directory(directory_path, recursive)

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": output}]
                }
            }

        elif tool_name == "nodeos_status":
            from nodeos_status import get_nodeos_status
            output = get_nodeos_status()

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": output}]
                }
            }

        elif tool_name == "nodeos_list_nodes":
            node_type_filter = args.get("node_type")
            db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "agy_nodeos.db")
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                if node_type_filter:
                    cursor.execute("SELECT node_id, node_type, name, filepath, x_coord, y_coord FROM nodes WHERE node_type = ?", (node_type_filter,))
                else:
                    cursor.execute("SELECT node_id, node_type, name, filepath, x_coord, y_coord FROM nodes")
                rows = cursor.fetchall()
                conn.close()
                nodes = [
                    {
                        "id": r[0], "type": r[1], "name": r[2], "filepath": r[3],
                        "coordinates": {"x": round(r[4], 2) if r[4] else 0, "y": round(r[5], 2) if r[5] else 0}
                    }
                    for r in rows
                ]
                output = json.dumps({"total_nodes": len(nodes), "nodes": nodes}, indent=2)
            except Exception as e:
                output = json.dumps({"error": f"Failed to list nodes: {e}"})

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": output}]
                }
            }

        elif tool_name == "nodeos_task_create":
            action = args.get("action", "")
            description = args.get("description", "")
            agents = args.get("agents")
            target = args.get("target")

            from nodeos_task import create_task
            output = create_task(action, description, agents, target)

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": output}]
                }
            }

        elif tool_name == "nodeos_task_list":
            status_filter = args.get("status_filter")

            from nodeos_task import list_tasks
            output = list_tasks(status_filter)

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": output}]
                }
            }

        elif tool_name == "nodeos_task_update":
            task_id = args.get("task_id", "")
            status = args.get("status", "")
            result = args.get("result")

            from nodeos_task import update_task
            output = update_task(task_id, status, result)

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": output}]
                }
            }

        elif tool_name == "nodeos_task_cancel":
            task_id = args.get("task_id", "")

            from nodeos_task import cancel_task
            output = cancel_task(task_id)

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": output}]
                }
            }
            
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": "Tool not found"}
            }
            
    # Ignore notifications
    return None

def main():
    # Save true stdout stream exclusively for JSON-RPC framing
    real_stdout = sys.stdout
    # Redirect default sys.stdout to sys.stderr to prevent any print(...) calls from polluting stdio
    sys.stdout = sys.stderr

    # Setup debug logging to a file in the same directory
    log_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "mcp_debug.log")
    
    with open(log_file, "a") as f:
        f.write("MCP Server started.\n")
        
    buf = ""
    while True:
        line = sys.stdin.readline()
        if not line:
            break
            
        buf += line
        try:
            req = json.loads(buf)
            buf = ""
            with open(log_file, "a") as f:
                f.write(f"RECV: {json.dumps(req)}\n")
                
            res = handle_request(req)
            if res:
                out = json.dumps(res) + "\n"
                with open(log_file, "a") as f:
                    f.write(f"SEND: {out}")
                real_stdout.write(out)
                real_stdout.flush()
        except json.JSONDecodeError as e:
            # If payload contains unescaped newlines inside strings, attempt control char sanitization
            sanitized = re.sub(r'(?<!\\)[\r\n]+', r'\\n', buf)
            try:
                req = json.loads(sanitized)
                buf = ""
                with open(log_file, "a") as f:
                    f.write(f"RECV_SANITIZED: {json.dumps(req)}\n")
                res = handle_request(req)
                if res:
                    out = json.dumps(res) + "\n"
                    with open(log_file, "a") as f:
                        f.write(f"SEND: {out}")
                    real_stdout.write(out)
                    real_stdout.flush()
            except Exception:
                # Keep buffering if waiting for complete JSON structure
                if len(buf) > 1000000: # Safety cap
                    buf = ""
        except Exception as e:
            err = {"jsonrpc": "2.0", "error": {"code": -32700, "message": str(e)}}
            out = json.dumps(err) + "\n"
            with open(log_file, "a") as f:
                f.write(f"ERR: {out}\nEXCEPTION: {str(e)}\n")
            real_stdout.write(out)
            real_stdout.flush()
            buf = ""

if __name__ == "__main__":
    main()
