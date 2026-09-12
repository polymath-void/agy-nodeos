#!/data/data/com.termux/files/usr/bin/python3
import os
import sys
import json
import sqlite3
import subprocess

def get_nodeos_status():
    db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "agy_nodeos.db")
    
    # Check daemon process
    try:
        res = subprocess.run(["pgrep", "-fa", "python.*daemon.py"], capture_output=True, text=True)
        daemon_running = res.returncode == 0
        daemon_info = res.stdout.strip() if daemon_running else "Not running"
    except Exception:
        daemon_running = False
        daemon_info = "Unknown"

    total_nodes = 0
    total_edges = 0
    node_types = {}
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM nodes")
            total_nodes = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM edges")
            total_edges = cursor.fetchone()[0]

            cursor.execute("SELECT node_type, COUNT(*) FROM nodes GROUP BY node_type")
            node_types = dict(cursor.fetchall())
            conn.close()
        except Exception as e:
            pass

    status_data = {
        "status": "healthy" if daemon_running else "degraded",
        "daemon": {
            "running": daemon_running,
            "info": daemon_info
        },
        "database": {
            "path": db_path,
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "node_type_breakdown": node_types
        }
    }
    return json.dumps(status_data, indent=2)

if __name__ == "__main__":
    print(get_nodeos_status())
