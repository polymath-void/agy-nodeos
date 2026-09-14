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
        if status == "pending":
            message = f"NodeOS emitted an intent. Please fulfill this workflow:\n{json.dumps(data, indent=2)}"
            response = {
                "injectSteps": [
                    {
                        "ephemeralMessage": message
                    }
                ]
            }
            print(json.dumps(response))
        else:
            print("{}")
    except Exception:
        print("{}")

if __name__ == "__main__":
    main()
