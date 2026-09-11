import sys
import json
import subprocess
import os

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
                        "description": "Natively read the contents of a file inside the NodeOS matrix. Use this instead of view_file.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "filepath": {
                                    "type": "string",
                                    "description": "The absolute or relative path to the file to read."
                                }
                            },
                            "required": ["filepath"]
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
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nodeos_search.py")
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
            try:
                with open(filepath, "r") as f:
                    content = f.read()
                output = f"--- FILE: {filepath} ---\n" + content
            except Exception as e:
                output = f"Error reading file: {e}"
                
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
    # Setup debug logging to a file in the same directory
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_debug.log")
    
    with open(log_file, "a") as f:
        f.write("MCP Server started.\n")
        
    while True:
        line = sys.stdin.readline()
        if not line:
            break
            
        with open(log_file, "a") as f:
            f.write(f"RECV: {line}")
            
        try:
            req = json.loads(line)
            res = handle_request(req)
            if res:
                out = json.dumps(res) + "\n"
                with open(log_file, "a") as f:
                    f.write(f"SEND: {out}")
                sys.stdout.write(out)
                sys.stdout.flush()
        except Exception as e:
            err = {"jsonrpc": "2.0", "error": {"code": -32700, "message": str(e)}}
            out = json.dumps(err) + "\n"
            with open(log_file, "a") as f:
                f.write(f"ERR: {out}\nEXCEPTION: {str(e)}\n")
            sys.stdout.write(out)
            sys.stdout.flush()

if __name__ == "__main__":
    main()
