#!/data/data/com.termux/files/usr/bin/python3
import os
import sys
import json
import time
import sqlite3
import uuid

def _get_db():
    db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "agy_nodeos.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            action TEXT,
            description TEXT,
            agents TEXT,
            target TEXT,
            status TEXT,
            result TEXT,
            error_log TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def create_task(action, description, agents=None, target=None):
    task_id = f"task_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    agents_list = agents if isinstance(agents, list) else ([agents] if agents else ["NodeOSAgent"])
    
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tasks (task_id, action, description, agents, target, status)
        VALUES (?, ?, ?, ?, ?, 'pending')
    ''', (task_id, action, description, json.dumps(agents_list), target or ""))
    conn.commit()
    conn.close()

    # Update active workflow.json for background daemon picking
    workflow_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "workflow.json")
    workflow_payload = {
        "task_id": task_id,
        "action": action,
        "description": description,
        "agents": agents_list,
        "target": target or "",
        "status": "pending",
        "timestamp": time.time()
    }
    try:
        with open(workflow_path, "w") as f:
            json.dump(workflow_payload, f, indent=2)
    except Exception as e:
        return f"Error updating workflow.json: {e}"

    return json.dumps({"message": f"Task '{task_id}' created successfully.", "task": workflow_payload}, indent=2)

def list_tasks(status_filter=None):
    conn = _get_db()
    cursor = conn.cursor()
    if status_filter and status_filter.lower() != "all":
        cursor.execute("SELECT task_id, action, description, agents, target, status, result, created_at, updated_at FROM tasks WHERE status = ? ORDER BY created_at DESC", (status_filter.lower(),))
    else:
        cursor.execute("SELECT task_id, action, description, agents, target, status, result, created_at, updated_at FROM tasks ORDER BY created_at DESC")
    
    rows = cursor.fetchall()
    conn.close()

    tasks = []
    for r in rows:
        try:
            agent_data = json.loads(r[3]) if r[3] else []
        except Exception:
            agent_data = [r[3]]
            
        tasks.append({
            "task_id": r[0],
            "action": r[1],
            "description": r[2],
            "agents": agent_data,
            "target": r[4],
            "status": r[5],
            "result": r[6],
            "created_at": r[7],
            "updated_at": r[8]
        })

    # Read current workflow.json active task
    workflow_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "workflow.json")
    active_workflow = None
    if os.path.exists(workflow_path):
        try:
            with open(workflow_path, "r") as f:
                active_workflow = json.load(f)
        except Exception:
            pass

    return json.dumps({
        "total_tasks": len(tasks),
        "active_workflow": active_workflow,
        "tasks": tasks
    }, indent=2)

def update_task(task_id, status, result=None, error_log=None):
    valid_statuses = ["pending", "running", "completed", "failed_qa", "cancelled"]
    if status not in valid_statuses:
        return f"Error: Invalid status '{status}'. Must be one of {valid_statuses}."

    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tasks 
        SET status = ?, result = ?, error_log = ?, updated_at = CURRENT_TIMESTAMP
        WHERE task_id = ?
    ''', (status, json.dumps(result) if isinstance(result, (dict, list)) else result, error_log, task_id))
    conn.commit()
    conn.close()

    # Also update workflow.json if it matches task_id or current active workflow
    workflow_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "workflow.json")
    if os.path.exists(workflow_path):
        try:
            with open(workflow_path, "r") as f:
                wf = json.load(f)
            if wf.get("task_id") == task_id or wf.get("status") != status:
                wf["status"] = status
                if result: wf["result"] = result
                if error_log: wf["error_log"] = error_log
                with open(workflow_path, "w") as f:
                    json.dump(wf, f, indent=2)
        except Exception:
            pass

    return json.dumps({"message": f"Task '{task_id}' updated to '{status}'.", "task_id": task_id, "status": status})

def cancel_task(task_id):
    return update_task(task_id, "cancelled", result="Cancelled by user or system.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: nodeos-task <list|create|update|cancel> [args...]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "list":
        flt = sys.argv[2] if len(sys.argv) > 2 else None
        print(list_tasks(flt))
    elif cmd == "create":
        action = sys.argv[2] if len(sys.argv) > 2 else "execute_task"
        desc = sys.argv[3] if len(sys.argv) > 3 else "NodeOS Task"
        print(create_task(action, desc))
    elif cmd == "update":
        tid = sys.argv[2] if len(sys.argv) > 2 else ""
        st = sys.argv[3] if len(sys.argv) > 3 else "completed"
        print(update_task(tid, st))
    elif cmd == "cancel":
        tid = sys.argv[2] if len(sys.argv) > 2 else ""
        print(cancel_task(tid))
    else:
        print(f"Unknown task command: {cmd}")
