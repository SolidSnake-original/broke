from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import WordCompleter
from rich.console import Console
from rich.spinner import Spinner
from rich.table import Table
import cli_gateway as gateway_cli
import time
from broker_daemon import start_daemon_from_config
from monitoring_services import start_monitoring, stop_monitoring

# ==== Farbschema / Deepsea-Style ====
style = Style.from_dict({
    '':          '#b6f4ff bg:#0a1024',   # Default: blasses Eisblaulicht auf Tiefsee-Nacht
    'prompt':    'bold #00ffe7',         # Neon-Türkis, wie ein Anglerfisch-Köder
    'command':   '#24caff',
    'error':     'bold #ff3377',
    'success':   'bold #32ff7a',
    'warning':   'bold #9d68f6',
})

console = Console()
session = PromptSession()

MAIN_MODULES = {
    'gateway':      'Shadow Broker FAISS Gateway',
    'osint':        'OSINT/Profiling-Tools (WIP)',
    'pentest':      'Pentesting/Recon (WIP)',
    'monitoring start|stop':   'Monitoring (Loki/Promtail)',
    # ...weitere Module...
    'exit':         'Beenden. Danach ctrl+C zum Stoppen des Daemons.'
}
COMMAND_COMPLETER = WordCompleter(MAIN_MODULES.keys(), ignore_case=True)

def loading_screen():
    with console.status("[bold green]Starte Shadow Broker...", spinner="dots") as status:
        # Simulate loading time or place your heavy imports/initialization here
        time.sleep(3)  # Replace with actual loading code if needed

def print_main_menu():
    table = Table(title="[bold]Shadow Broker Control Center[/bold]", style="#f1fa8c", border_style="#181818")
    table.add_column("Modul", style="#61dafb")
    table.add_column("Beschreibung", style="#dddddd")
    for mod, desc in MAIN_MODULES.items():
        table.add_row(mod, desc)
    console.print(table)

def main():
    while True:
        print_main_menu()
        try:
            cmd = session.prompt(
                '[prompt]shadow-broker-main> [/prompt]',
                completer=COMMAND_COMPLETER,
                style=style
            ).strip().lower()
            if cmd == "gateway":
                gateway_cli.main()  # oder wie dein Gateway-CLI-Entrypoint heißt
            elif cmd == "osint":
                # osint_cli.start_cli()
                console.print("[warning]Noch nicht angebunden![/warning]")
            elif cmd == "pentest":
                # pentest_cli.start_cli()
                console.print("[warning]Noch nicht angebunden![/warning]")
            elif cmd == "monitoring start":
                start_monitoring()
                console.print("[success]Monitoring-Dienste gestartet.[/success]")
            elif cmd == "monitoring stop":
                stop_monitoring()
                console.print("[success]Monitoring-Dienste gestoppt.[/success]")
            elif cmd == "exit":
                # Hier könntest du auch den Daemon stoppen, wenn er läuft
                daemon.stop() if 'daemon' in globals() else None
                console.print("[bold #bd93f9]Der Broker verlässt das Control Center.[/bold #bd93f9]")
                break
            else:
                console.print("[error]Unbekanntes Modul.[/error]")
        except KeyboardInterrupt:
            console.print("[#ff5555]Abbruch (Ctrl+C)[/#ff5555]")
            break

if __name__ == "__main__":
    loading_screen()
    console.clear()
    daemon = start_daemon_from_config(interval=120)
    main()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        daemon.stop()