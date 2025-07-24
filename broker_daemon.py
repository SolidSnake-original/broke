import threading
import os
import time
import json
import math
import tkinter as tk
from datetime import datetime
from PIL import Image, ImageTk, ImageEnhance

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

# Timer Circle GUI for the daemon
# This is a simple Tkinter-based GUI to visualize the daemon's interval as a timer circle
from PIL import Image, ImageTk  # Pillow braucht pip install pillow

class TimerCircle(tk.Canvas):
    def __init__(self, master, interval=900, image_path=None, scale=1.5, **kwargs):
        self.radius = int(100 * scale)
        self.center = self.radius + 10
        width = height = self.center * 2
        super().__init__(master, width=width, height=height + 60, bg='#300016', highlightthickness=0, **kwargs)
        self.interval = interval
        self.start_time = time.time()
        self.arc = None
        self.scale = scale

        self.img_tk = None
        if image_path:
            img = Image.open(image_path).convert("RGBA")
            # Transparenz und Aufhellung wie gehabt
            alpha = img.split()[-1].point(lambda x: int(x*0.33))
            img.putalpha(alpha)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.7)
            img = img.resize((int(120 * scale), int(120 * scale)), Image.Resampling.LANCZOS)
            self.img_tk = ImageTk.PhotoImage(img)

        self.after(100, self.update_circle)

    def update_circle(self):
        now = time.time()
        elapsed = (now - self.start_time) % self.interval
        angle = (elapsed / self.interval) * 360
        self.delete("all")

        c = self.center
        r = self.radius

        # Logo im Zentrum
        if self.img_tk:
            self.create_image(c, c - 10*self.scale, image=self.img_tk)

        # Kreis & Progress
        self.create_oval(c-r, c-r, c+r, c+r, outline='#a01a32', width=12*self.scale)
        self.create_arc(c-r, c-r, c+r, c+r, start=90, extent=-angle, style='arc', outline='#e62e4a', width=12*self.scale)

        # Timeranzeige UNTER dem Kreis
        remaining = int(self.interval - elapsed)
        mins, secs = divmod(remaining, 60)
        time_text = f"{mins:02d}:{secs:02d}"

        self.create_text(c, c + r + 30*self.scale, text=time_text, fill='#ffe1e1', font=('Arial', int(30*self.scale), 'bold'))
        self.after(100, self.update_circle)

def start_timer_gui(interval, image_path=None):
    root = tk.Tk()
    root.title("Dämonentimer")
    root.resizable(False, False)
    timer = TimerCircle(root, interval=interval, image_path=image_path, scale=1.5)
    timer.pack()
    root.mainloop()


# BrokerDaemon class to handle the daemon logic
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
                    reg_ok, reg_count = registry_healthcheck(name)
                    idx_ok, idx_count = faiss_healthcheck(idxfile)
                    log_audit(f"Healthcheck für Collection '{name}': Registry OK={reg_ok}, N={reg_count} | Index OK={idx_ok}, V={idx_count}", "AUDIT")
                    # Konsistenz-Check
                    sqlite_checkup()
                    #log_audit(f"SQLite Checkup abgeschlossen.", "CLEANUP")
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
    # --- HIER Timer-Fenster starten ---
    threading.Thread(target=start_timer_gui, args=(interval, "./media/daemon.png"), daemon=True).start()
    # -----------------------------------
    daemon = BrokerDaemon(collections, interval)
    daemon.daemon = True
    daemon.start()
    return daemon

# --- Beispiel-Aufruf im Main-CLI ---
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Shadow Broker Daemon")
    parser.add_argument("--once", action="store_true", help="Run the daemon logic only once and exit")
    parser.add_argument("--interval", type=int, default=300, help="Interval in seconds for normal mode")
    args = parser.parse_args()

    collections = load_config()
    if args.once:
        # Run the daemon logic only once
        log_audit("BrokerDaemon (manual --once) gestartet.", "START")
        try:
            for coll in collections:
                name = coll["name"]
                idxfile = coll["index_file"]
                reg_ok, reg_count = registry_healthcheck(name)
                idx_ok, idx_count = faiss_healthcheck(idxfile)
                log_audit(f"Healthcheck für Collection '{name}': Registry OK={reg_ok}, N={reg_count} | Index OK={idx_ok}, V={idx_count}", "AUDIT")
                sqlite_checkup()
                log_audit(f"SQLite Checkup abgeschlossen.", "CLEANUP")
                if reg_count != idx_count:
                    log_audit(f"KONSISTENZPROBLEM in '{name}': Registry({reg_count}) != Index({idx_count})", "WARNING")
                    log_audit(f"Starte Cleanup/Rebuild...", "ACTION")
                    n_new = rebuild_faiss_index(name, idxfile)
                    log_audit(f"Cleanup abgeschlossen. {n_new} Einträge neu indiziert.", "SUCCESS")
            stats = db_stats()
            log_audit(f"Stats: {stats}", "STATS")
        except Exception as e:
            log_audit(f"Daemon-Fehler: {e}", "ERROR")
        log_audit("BrokerDaemon (manual --once) beendet.", "STOP")
    else:
        daemon = BrokerDaemon(collections, interval=args.interval)
        daemon.daemon = True
        daemon.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            daemon.stop()
