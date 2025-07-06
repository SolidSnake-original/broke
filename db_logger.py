# logger.py

from rich.console import Console
from datetime import datetime

console = Console()
LOGFILE = "shadowbroker_chroma.log"

def log_event(event, level="INFO"):
    line = f"{datetime.now().isoformat()} [{level}] {event}"
    # Schreibe in Logfile
    with open(LOGFILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    # Schreibe auf Konsole (optional farbig)
    color = {
        "INFO": "#176030",
        "WARN": "#ffbe4d",
        "ERROR": "#ff5555",
        "DEBUG": "#24caff"
    }.get(level, "#dddddd")
    console.print(f"[{color}]{line}[/{color}]")
