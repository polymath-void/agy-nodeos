import time
import json
import os
import sys

def tail_agent_logs(log_file="daemon.log"):
    """Yields new lines from the log file, filtering only Agent actions."""
    if not os.path.exists(log_file):
        return
    with open(log_file, "r") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                yield None
            else:
                # Filter out background OS noise, only show Swarm and Agent actions
                if any(noise in line for noise in ["[Physics Engine]", "[Raw Watchdog]", "[Jage Polyglot]", "[Daemon]", "[NodeOS] Deep Scan"]):
                    yield None
                else:
                    yield line

def track_workflow(workflow_file="workflow.json"):
    if not os.path.exists(workflow_file):
        print("\033[93m[NodeOS] No active workflow detected in workspace.\033[0m")
        return

    last_status = None
    log_generator = tail_agent_logs()
    
    while True:
        # Print filtered agent action logs
        if log_generator:
            log_line = next(log_generator, None)
            while log_line:
                sys.stdout.write(f"\033[90m{log_line}\033[0m")
                sys.stdout.flush()
                log_line = next(log_generator, None)

        try:
            with open(workflow_file, 'r') as f:
                data = json.load(f)
            status = data.get('status', 'unknown')
            
            if status != last_status:
                if status == 'pending':
                    agents = ", ".join(data.get('agents', []))
                    intent = data.get('action', 'execute_agents')
                    print(f"\n\033[96m[NodeOS Swarm] Intent: {intent.upper()} -> [{agents}]\033[0m")
                    print("\033[94m[NodeOS] Status: PENDING\033[0m")
                elif status == 'running':
                    print("\033[93m[NodeOS] Status: RUNNING\033[0m")
                elif status == 'completed':
                    print("\033[92m[NodeOS] Status: COMPLETED\033[0m\n")
                elif status == 'failed_qa':
                    print("\033[91m[NodeOS] Status: FAILED\033[0m")
                    print(f"\033[91mError: {data.get('error_log', 'Unknown Error')}\033[0m\n")
                last_status = status
            
            if status in ['completed', 'failed_qa']:
                break
        except Exception:
            pass
            
        time.sleep(0.5)

if __name__ == "__main__":
    track_workflow()
