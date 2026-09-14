import sys
import json
import telemetry

def invoke(payload_str):
    try:
        workflow = json.loads(payload_str)
        with open('workflow.json', 'w') as f:
            json.dump(workflow, f, indent=4)
        
        # Now natively stream the NodeOS telemetry to AGY's sys.stdout
        telemetry.track_workflow('workflow.json')
    except Exception as e:
        print(f"Failed to invoke workflow: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        invoke(sys.argv[1])
    else:
        print("Usage: python agy_invoke.py '<json_string>'")
