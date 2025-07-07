import threading
import os
import time
import json
from datetime import datetime

from db_sqlite_checkup import sqlite_checkup
from db_cleanup import rebuild_faiss_index
from db_healthchecks import registry_healthcheck, faiss_healthcheck, db_stats

AUDIT_LOG = "audit.log"
CONFIG_FILE = "daemon_config.json"

def log_audit(msg, level="INFO"):
    now = datetime.now().isoformat(timespec="seconds")
    pid = os.getpid()
    line = f"{now} [{level}] [PID:{pid}] {msg}"
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    #print(line)

def load_config():
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)["collections"]

class BrokerDaemon(threading.Thread):
    def __init__(self, collections, interval=300):
        super().__init__()
        self.collections = collections  # List of dicts: [{"name":..., "index_file":...}, ...]
        self.interval = interval
        self.running = True

    def run(self):
        log_audit("BrokerDaemon gestartet.", "START")
        while self.running:
            try:
                for coll in self.collections:
                    name = coll["name"]
                    idxfile = coll["index_file"]
                    reg_ok, reg_count = registry_healthcheck()
                    idx_ok, idx_count = faiss_healthcheck(idxfile)
                    log_audit(f"Healthcheck für Collection '{name}': Registry OK={reg_ok}, N={reg_count} | Index OK={idx_ok}, V={idx_count}", "AUDIT")
                    # Konsistenz-Check
                    sqlite_checkup()
                    log_audit(f"SQLite Checkup abgeschlossen.", "CLEANUP")
                    if reg_count != idx_count:
                        log_audit(f"KONSISTENZPROBLEM in '{name}': Registry({reg_count}) != Index({idx_count})", "WARNING")
                        log_audit(f"Starte Cleanup/Rebuild...", "ACTION")
                        n_new = rebuild_faiss_index(name, idxfile)
                        log_audit(f"Cleanup abgeschlossen. {n_new} Einträge neu indiziert.", "SUCCESS")
                # Alle Collections: Stats loggen
                stats = db_stats()
                log_audit(f"Stats: {stats}", "STATS")
                time.sleep(self.interval)
            except Exception as e:
                log_audit(f"Daemon-Fehler: {e}", "ERROR")
                time.sleep(self.interval)

    def stop(self):
        self.running = False
        log_audit("BrokerDaemon gestoppt.", "STOP")

def start_daemon_from_config(interval=300):
    try:
        collections = load_config()
    except Exception as e:
        log_audit(f"Config-Fehler: {e}", "ERROR")
        return None
    daemon = BrokerDaemon(collections, interval)
    daemon.daemon = True
    daemon.start()
    return daemon

# --- Beispiel-Aufruf im Main-CLI ---
#if __name__ == "__main__":
#    daemon = start_daemon_from_config(interval=120)
    # ...hier CLI oder andere Runtime...
#    try:
#        while True:
#            time.sleep(1)
#    except KeyboardInterrupt:
#        daemon.stop()
