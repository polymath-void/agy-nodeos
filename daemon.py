#!/data/data/com.termux/files/usr/bin/python3
import asyncio
import os
import sys

import subprocess
import threading
import json
from multiprocessing.connection import Listener

from graph_manager import AGYGraphManager
from jage_engine import JageASTEngine
from nodes_engine import NativeNodesEngine

class AGYRawWatchdog:
    """
    ZERO-DEPENDENCY RAW FILE OBSERVER
    Eliminates the need for 'pip install watchdog'. Uses lightweight asyncio polling.
    """
    def __init__(self, directory, callback, interval=1.0):
        self.directory = directory
        self.callback = callback
        self.interval = interval
        self.state = {}
        self.running = False
        self._initialize_state()

    def _should_ignore(self, path):
        # Ignore internal OS state folders and dependencies to prevent recursive loops and bloat
        ignores = ['.jsagent', '.agents', '__pycache__', '.git', 'node_modules', 'build', 'dist', '.venv', 'venv', '.build_cache', 'site-packages', 'env']
        return any(ign in path for ign in ignores)

    def _initialize_state(self):
        for root, _, files in os.walk(self.directory):
            if self._should_ignore(root):
                continue
            for file in files:
                if file.endswith(('.py', '.json')):
                    path = os.path.join(root, file)
                    self.state[path] = os.stat(path).st_mtime

    async def start(self):
        self.running = True
        print(f"[Raw Watchdog] Natively polling {self.directory} every {self.interval}s...")
        while self.running:
            await asyncio.sleep(self.interval)
            for root, _, files in os.walk(self.directory):
                if self._should_ignore(root):
                    continue
                for file in files:
                    if file.endswith(('.py', '.json')):
                        path = os.path.join(root, file)
                        try:
                            mtime = os.stat(path).st_mtime
                            if path not in self.state or mtime > self.state[path]:
                                self.state[path] = mtime
                                self.callback(path)
                        except FileNotFoundError:
                            pass

class AGYNodeOSEventHandler:
    def __init__(self, jage, spatial, graph, loop):
        self.jage = jage
        self.spatial = spatial
        self.graph = graph
        self.loop = loop

    def on_modified(self, filepath):
        print(f"\n[Daemon] Detected modification in: {filepath}")
        
        if filepath.endswith('.json'):
            print(f"[Event Loop] Picked up agent JSON workflow from {filepath}!")
            asyncio.run_coroutine_threadsafe(
                self.dispatch_workflow([{'hash': 'workflow', 'type': 'JSON_Task', 'file': filepath}]), self.loop
            )
            return
        
        ast_nodes = self.jage.parse_file(filepath)
        if ast_nodes:
            for node in ast_nodes:
                self.spatial.add_node(node['hash'], node['type'])

    async def dispatch_workflow(self, nodes):
        """True Swarm Dispatcher: Parses JSON and emits intents for AGY Agents to execute, acting as the state manager."""
        for node in nodes:
            if node['type'] == 'JSON_Task':
                workflow_file = node['file']
                try:
                    with open(workflow_file, 'r') as f:
                        workflow = json.load(f)
                    
                    status = workflow.get('status')
                    
                    if status == 'pending':
                        # Handle native Re-Stitch action requested by an agent
                        if workflow.get('action') == 'stitch':
                            print(f"[Swarm Dispatcher] Processing Re-Stitch request for hash {workflow.get('node_hash')[:8]}...")
                            workflow['status'] = 'running'
                            with open(workflow_file, 'w') as f: json.dump(workflow, f, indent=4)
                            
                            result = self.jage.re_stitch(workflow.get('node_hash'), workflow.get('new_source'))
                            
                            if result is True:
                                workflow['status'] = 'completed'
                            else:
                                workflow['status'] = 'failed_qa'
                                workflow['error_log'] = result
                                print(f"[Swarm Feedback Loop] Sent QA failure back to agent: {result}")
                                
                            with open(workflow_file, 'w') as f: json.dump(workflow, f, indent=4)
                            print(f"[Event Loop] Jage Re-Stitch workflow completed.")
                            continue
                            
                        # Handle Swarm Agent execution
                        agent_list = workflow.get('agents', [])
                        print(f"[Swarm Dispatcher] Emitting Swarm intent for AGY external swarm: {agent_list}")
                        print(f"[Swarm Dispatcher] Actively spawning AGY CLI Subprocess...")
                        
                        # Active AGY CLI Subprocessing
                        prompt = f"System OS Alert: A workflow intent '{workflow.get('action')}' has been requested. Required agents: {agent_list}. Please fulfill this workflow by acting as the requested agents. When finished, update {workflow_file} status to 'completed'."
                        cmd = f'agy --print "{prompt}"'
                        
                        # Run the shell command asynchronously so it doesn't block the daemon
                        async def spawn_agent():
                            process = await asyncio.create_subprocess_shell(
                                cmd,
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE
                            )
                            stdout, stderr = await process.communicate()
                            if stderr:
                                print(f"[Swarm Dispatcher] AGY CLI Warning: {stderr.decode('utf-8').strip()}")
                            print(f"[Swarm Dispatcher] AGY CLI Subprocess execution finished.")
                            
                        asyncio.create_task(spawn_agent())
                    
                    elif status == 'running':
                        print(f"[Swarm Dispatcher] AGY Swarm has picked up the task. Monitoring execution...")
                        
                    elif status == 'completed':
                        print(f"[Event Loop] Swarm workflow fully executed by AGY agents.")
                        
                    elif status == 'failed_execution' or status == 'failed_qa':
                        print(f"[Swarm Error] AGY Workflow failed. Awaiting human or agent intervention.")
                        
                except Exception as e:
                    print(f"[Swarm Error] Failed to process workflow state: {e}")

class AGYDaemon:
    def __init__(self, workspace_dir):
        self.workspace = workspace_dir
        self.graph = AGYGraphManager()
        self.jage = JageASTEngine()
        self.spatial = NativeNodesEngine()
        self.loop = asyncio.new_event_loop()
        
        self.event_handler = AGYNodeOSEventHandler(self.jage, self.spatial, self.graph, self.loop)
        
        # Initialize our zero-dependency raw watchdog
        self.raw_watchdog = AGYRawWatchdog(self.workspace, self.event_handler.on_modified, interval=1.0)
        
        self.ipc_thread = threading.Thread(target=self.start_ipc_server, daemon=True)
        self.ipc_thread.start()

    def start_ipc_server(self):
        address = ('localhost', 6000)
        try:
            with Listener(address, authkey=b'agy-nodeos-secret') as listener:
                while True:
                    with listener.accept() as conn:
                        msg = conn.recv()
                        if msg == 'ping':
                            conn.send('pong: OS Daemon is alive and running invisibly.')
                        elif msg == 'status':
                            conn.send(f'Active Workflows: OK | Watchdog: {self.workspace}')
                        else:
                            conn.send('unknown_syscall')
        except OSError:
            print("[System] IPC Address 6000 already in use. A daemon is already running! Terminating duplicate process.")
            os._exit(1)

    def cold_start_ingestion(self):
        if len(self.spatial.all_nodes) == 0:
            print("[NodeOS] Detected Uninitialized Project Workspace. Initiating Deep Ingestion...")
            # 1. Deep scan the workspace
            for root, _, files in os.walk(self.workspace):
                if self.raw_watchdog._should_ignore(root):
                    continue
                for file in files:
                    if file.endswith(('.py', '.js', '.ts')):
                        filepath = os.path.join(root, file)
                        ast_nodes = self.jage.parse_file(filepath)
                        if ast_nodes:
                            for node in ast_nodes:
                                # We now pass the node name and the calls it makes to the spatial matrix
                                self.spatial.add_node(node['hash'], node['type'], node.get('name', 'unknown'), node.get('calls', []))
            
            # Resolve physical edges using AST calls
            self.spatial.resolve_edges()
            
            print(f"[NodeOS] Deep Scan complete. Ingested {len(self.spatial.all_nodes)} kinetic nodes.")
            
            # 2. Check for missing Architectural Nodes
            architect_exists = os.path.exists(os.path.join(self.workspace, "architect_parent_node.md"))
            blueprint_exists = os.path.exists(os.path.join(self.workspace, "impl_blueprint_node.md"))
            
            if not architect_exists or not blueprint_exists:
                print("[NodeOS] Essential structural nodes missing. Dispatching Architect Designer Sub-Agent...")
                workflow_file = os.path.join(self.workspace, "workflow.json")
                workflow = {
                    "type": "JSON_Task",
                    "status": "pending",
                    "action": "execute_agents",
                    "agents": ["architect_designer"]
                }
                import json
                with open(workflow_file, "w") as f:
                    json.dump(workflow, f, indent=4)
                print("[NodeOS] Workflow payload dropped. Architect worker will bootstrap the project.")

    async def _async_run(self):
        # Run the deep scan ingestion immediately before starting the real-time event loop
        self.cold_start_ingestion()
        
        # The raw watchdog runs in the asyncio event loop natively
        await self.raw_watchdog.start()

    def run(self):
        try:
            self.loop.run_until_complete(self._async_run())
        finally:
            self.loop.close()

def daemonize_and_run():
    if len(sys.argv) > 1 and sys.argv[-1] == '--run-as-daemon':
        target_workspace = os.getcwd()
        daemon = AGYDaemon(target_workspace)
        daemon.run()
    else:
        print("[System] Detaching AGY-NodeOS Daemon (Zero-Dependency) to background process...")
        if os.name == 'nt':
            CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen([sys.executable, __file__, '--run-as-daemon'], creationflags=CREATE_NO_WINDOW)
        else:
            log_file = open(os.path.join(os.getcwd(), 'daemon.log'), 'a')
            subprocess.Popen([sys.executable, '-u', __file__, '--run-as-daemon'], start_new_session=True, stdout=log_file, stderr=log_file)
        sys.exit(0)

if __name__ == "__main__":
    daemonize_and_run()
