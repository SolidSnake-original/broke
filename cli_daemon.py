import json
import os
import subprocess
import sys
from rich.console import Console
from rich.table import Table
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter

CONFIG_FILE = "daemon_config.json"
DAEMON_SCRIPT = "broker_daemon.py"  # Adjust if your daemon entrypoint is different

COMMANDS = {
    'show':      'Daemon Konfiguration anzeigen',
    'add':        'Collection hinzufügen',
    'remove':      'Collection entfernen',
    'run':       'Daemon manuell starten',
    'back':   'Zurück zum Hauptmenü',
}
COMMAND_COMPLETER = WordCompleter(COMMANDS.keys(), ignore_case=True)

console = Console()
session = PromptSession()

def print_main_menu():
    table = Table(title="[bold]Shadow Broker Control Center[/bold]", style="#f1fa8c", border_style="#181818")
    table.add_column("Modul", style="#61dafb")
    table.add_column("Beschreibung", style="#dddddd")
    for mod, desc in COMMANDS.items():
        table.add_row(mod, desc)
    console.print(table)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"collections": []}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

def show_config():
    cfg = load_config()
    table = Table(title="Daemon Config: Collections")
    table.add_column("Name")
    table.add_column("Index File")
    for entry in cfg.get("collections", []):
        table.add_row(entry.get("name", ""), entry.get("index_file", ""))
    console.print(table)

def add_entry():
    name = session.prompt("Collection name: ").strip()
    index_file = session.prompt("Index file: ").strip()
    cfg = load_config()
    if any(e["name"] == name for e in cfg["collections"]):
        console.print(f"[red]Collection '{name}' already exists![/red]")
        return
    cfg["collections"].append({"name": name, "index_file": index_file})
    save_config(cfg)
    console.print(f"[green]Added collection '{name}'.[/green]")

def remove_entry():
    name = session.prompt("Collection name to remove: ").strip()
    cfg = load_config()
    before = len(cfg["collections"])
    cfg["collections"] = [e for e in cfg["collections"] if e["name"] != name]
    if len(cfg["collections"]) < before:
        save_config(cfg)
        console.print(f"[green]Removed collection '{name}'.[/green]")
    else:
        console.print(f"[yellow]Collection '{name}' not found.[/yellow]")

def run_manual_daemon():
    console.print("[cyan]Launching manual daemon instance...[/cyan]")
    proc = subprocess.Popen(
        [sys.executable, DAEMON_SCRIPT, "--once"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    out, err = proc.communicate()
    console.print(f"[bold green]Daemon output:[/bold green]\n{out}")
    if err:
        console.print(f"[bold red]Daemon errors:[/bold red]\n{err}")
    console.print(f"[green]Manual daemon run complete. PID was {proc.pid}[/green]")

def daemon_menu():
    while True:
        print_main_menu()
        cmd = session.prompt("[prompt]daemon> [/prompt]", completer=COMMAND_COMPLETER).strip().lower()
        if cmd == "show":
            show_config()
        elif cmd == "add":
            add_entry()
        elif cmd == "remove":
            remove_entry()
        elif cmd == "run":
            run_manual_daemon()
        elif cmd == "back":
            break
        else:
            console.print("[red]Unknown command.[/red]")

if __name__ == "__main__":
    daemon_menu()