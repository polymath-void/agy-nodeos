import sys
import json
import subprocess
import os

def handle_request(req):
    method = req.get("method")
    params = req.get("params", {})
    req_id = req.get("id")
    
    # 1. Initialization Handshake
    if method == "initialize":
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
                        "name": "nodeos_spatial_search",
                        "description": "Natively query the NodeOS SQLite physical graph matrix for code dependencies and K-Nearest Neighbor (KNN) spatial blast radius.",
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
                    }
                ]
            }
        }
        
    # 3. Tool Execution
    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        
        if tool_name == "nodeos_spatial_search":
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
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": "Tool not found"}
            }
            
    # Ignore notifications
    return None

def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        try:
            req = json.loads(line)
            res = handle_request(req)
            if res:
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()
        except Exception as e:
            # Handle JSON parse errors or other fatal errors gracefully
            err = {"jsonrpc": "2.0", "error": {"code": -32700, "message": str(e)}}
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
