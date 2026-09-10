import sys
from multiprocessing.connection import Client

def send_ipc_syscall(command):
    """
    Cross-platform IPC Hook.
    Acts as a syscall client to securely communicate with the invisible AGY-NodeOS background daemon.
    """
    address = ('localhost', 6000)
    try:
        # Connect to the IPC Listener opened by the daemon
        with Client(address, authkey=b'agy-nodeos-secret') as conn:
            conn.send(command)
            response = conn.recv()
            print(f"[IPC Hook Response]: {response}")
    except ConnectionRefusedError:
        print("[IPC Error] Connection refused. Is the background daemon running?")
    except Exception as e:
        print(f"[IPC Error] {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ipc_hook.py [ping|status]")
        sys.exit(1)
        
    syscall_command = sys.argv[1]
    send_ipc_syscall(syscall_command)
