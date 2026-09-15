#!/usr/bin/env python3
import argparse
import sys
import os
import subprocess
import runpy

def run_daemon(run_as_daemon=False):
    """Boot the Polymath-NodeOS background daemon."""
    if run_as_daemon:
        # Load heavy dependencies only when actually starting the daemon
        from polymath_nodeos.daemon import AGYDaemon
        target_workspace = os.getcwd()
        daemon = AGYDaemon(target_workspace)
        daemon.run()
    else:
        print("[System] Detaching Polymath-NodeOS Daemon (Zero-Dependency) to background process...")
        if os.name == 'nt':
            CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen([sys.executable, sys.argv[0], '--run-as-daemon'], creationflags=CREATE_NO_WINDOW)
        else:
            log_file = open(os.path.join(os.getcwd(), 'daemon.log'), 'a')
            subprocess.Popen(
                [sys.executable, '-u', sys.argv[0], '--run-as-daemon'],
                start_new_session=True,
                stdout=log_file,
                stderr=log_file
            )
        sys.exit(0)

def run_script(script_name, script_args):
    """Run a specific script or engine from polymath_nodeos.scripts."""
    script_module = f"polymath_nodeos.scripts.{script_name}"
    try:
        # Patch sys.argv so the target script parses arguments correctly
        sys.argv = [script_name] + script_args
        runpy.run_module(script_module, run_name="__main__")
    except ImportError as e:
        print(f"[Error] Could not find or load script '{script_name}'.")
        print(f"Details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[Error] Execution of '{script_name}' failed: {e}")
        sys.exit(1)

def execute_command(command, command_args):
    """Execute internal function calls or specific internal commands."""
    commands = {
        "ping": lambda args: _ping_daemon(),
        # Add future internal commands here
    }
    
    if command in commands:
        commands[command](command_args)
    else:
        print(f"[Error] Unknown command '{command}'.")
        print(f"Available commands: {', '.join(commands.keys())}")
        sys.exit(1)

def _ping_daemon():
    """Helper command to check if the IPC daemon is alive."""
    from multiprocessing.connection import Client
    try:
        with Client(('localhost', 6000), authkey=b'agy-nodeos-secret') as conn:
            conn.send('ping')
            response = conn.recv()
            print(f"[Daemon Status] {response}")
    except ConnectionRefusedError:
        print("[Daemon Status] Offline or not running.")

def main():
    parser = argparse.ArgumentParser(
        prog="nodeos",
        description="Polymath-NodeOS: The Autonomous Swarm Operating System CLI",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument('-v', '--version', action='version', version='Polymath-NodeOS 1.0.1')
    
    # Core actions must be mutually exclusive (choose one mode of operation)
    group = parser.add_mutually_exclusive_group(required=True)
    
    group.add_argument('-d', '--daemon', action='store_true', 
                       help='Boot the NodeOS background daemon.')
    group.add_argument('--run-as-daemon', action='store_true', 
                       help=argparse.SUPPRESS) # Internal synchronous start
    
    group.add_argument('-s', '--script', type=str, metavar='SCRIPT', 
                       help='Run a specific script or engine (e.g., intent_injector, intent_stopper).')
    group.add_argument('-c', '--command', type=str, metavar='CMD', 
                       help='Execute an internal command (e.g., ping).')
    group.add_argument('-i', '--install', action='store_true', 
                       help='Install global Antigravity rules and skills for NodeOS.')

    # parse_known_args permits forwarding remaining arbitrary flags directly to the underlying scripts
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
        
    args, unknown = parser.parse_known_args()

    if args.daemon:
        run_daemon(run_as_daemon=False)
    elif args.run_as_daemon:
        run_daemon(run_as_daemon=True)
    elif args.script:
        run_script(args.script, unknown)
    elif args.command:
        execute_command(args.command, unknown)
    elif args.install:
        from polymath_nodeos.installer import install_nodeos
        install_nodeos()

if __name__ == "__main__":
    main()
