import json
import os

WORKFLOW_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "workflow.json")

def main():
    if not os.path.exists(WORKFLOW_FILE):
        print("{}")
        return
        
    try:
        with open(WORKFLOW_FILE, "r") as f:
            data = json.load(f)
            
        status = data.get("status")
        if status in ["pending", "running"]:
            response = {
                "decision": "continue",
                "reason": f"NodeOS has an active intent with status '{status}'. Please process it."
            }
            print(json.dumps(response))
        else:
            print("{}")
    except Exception:
        print("{}")

if __name__ == "__main__":
    main()
