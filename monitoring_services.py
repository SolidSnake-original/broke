import subprocess
import os
import signal
import sys
from datetime import datetime

AUDIT_LOG = "audit.log"
LOKI_DIR = os.path.join(os.path.dirname(__file__), "Loki")
LOKI_CMD = [os.path.join(LOKI_DIR, "loki-windows-amd64.exe"), "--config.file=" + os.path.join(LOKI_DIR, "loki-config.yaml")]
PROMTAIL_CMD = [os.path.join(LOKI_DIR, "promtail-windows-amd64.exe"), "--config.file=" + os.path.join(LOKI_DIR, "promtail-config.yaml")]

loki_proc = None
promtail_proc = None

def log_audit(action, pid):
    now = datetime.now().isoformat(timespec="seconds")
    line = f"{now} [MONITOR] [PID:{pid}] {action}"
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def start_monitoring():
    global loki_proc, promtail_proc
    if loki_proc is None:
        loki_proc = subprocess.Popen(
            LOKI_CMD,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        log_audit("LOKI STARTED", loki_proc.pid)
    if promtail_proc is None:
        promtail_proc = subprocess.Popen(
            PROMTAIL_CMD,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        log_audit("PROMTAIL STARTED", promtail_proc.pid)

def stop_monitoring():
    global loki_proc, promtail_proc
    if loki_proc:
        loki_proc.terminate()
        log_audit("LOKI STOPPED", loki_proc.pid)
        loki_proc = None
    if promtail_proc:
        promtail_proc.terminate()
        log_audit("PROMTAIL STOPPED", promtail_proc.pid)
        promtail_proc = None

def cleanup_on_exit(signum=None, frame=None):
    stop_monitoring()
    sys.exit(0)

# Register cleanup for normal exit and signals
import atexit
atexit.register(cleanup_on_exit)
signal.signal(signal.SIGINT, cleanup_on_exit)
signal.signal(signal.SIGTERM, cleanup_on_exit)

# Example CLI integration
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Manage Loki/Promtail monitoring services")
    parser.add_argument("action", choices=["start", "stop"], help="Start or stop monitoring services")
    args = parser.parse_args()
    if args.action == "start":
        start_monitoring()
        print("Monitoring services started.")
    elif args.action == "stop":
        stop_monitoring()
        print("Monitoring services stopped.")