from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import WordCompleter
from rich.console import Console
from rich.table import Table

# Farbpalette & Stil
style = Style.from_dict({
    '':          '#b6f4ff bg:#0a1024',   # Default: blasses Eisblaulicht auf Tiefsee-Nacht
    'prompt':    'bold #00ffe7',         # Neon-Türkis, wie ein Anglerfisch-Köder
    'command':   '#24caff',              # Eiskalte Cyan-Strahlen
    'error':     'bold #ff3377',         # Blass-Korallenrot, wie ein Warnlicht am Hydrothermalfeld
    'success':   'bold #32ff7a',         # Biolumineszenz-Grün, wie Leuchtalgen
    'warning':   'bold #9d68f6',         # Tiefes Violett – wie das Leuchten einer Quallenkrone
})

console = Console()
session = PromptSession()

# Aktuelle Commands (modular erweiterbar)
COMMANDS = {
    'help':    'Alle Kommandos anzeigen',
    'find':    'Suche alles zu einer Entität (Person, Domain, E-Mail...)',
    'refresh': 'Aktualisiere/erneuere Infos zu einer Entität',
    'stats':   'Statistiken & Audit-Ergebnisse anzeigen',
    'report':  'Bericht zu einer Entität erzeugen',
    'daemon':  'Daemon/Jobs steuern',
    'clear':   'Konsole leeren',
    'exit':    'Shadow Broker verlassen'
}
COMMAND_COMPLETER = WordCompleter(COMMANDS.keys(), ignore_case=True)

def print_welcome():
    console.print("\n[bold #f1fa8c]Willkommen im[/bold #f1fa8c] [#bd93f9]SHADOW BROKER INTERFACE[/#bd93f9]", style="bold")
    console.print("[#ff5555]Die Nacht sieht alles – aber du lenkst den Blick...[/#ff5555]\n")

def print_help():
    table = Table(title="[bold]Verfügbare Kommandos[/bold]", style="#f1fa8c", border_style="#181818")
    table.add_column("Kommando", style="#61dafb", no_wrap=True)
    table.add_column("Beschreibung", style="#dddddd")
    for cmd, desc in COMMANDS.items():
        table.add_row(cmd, desc)
    console.print(table)

def handle_command(cmdline):
    cmd, *args = cmdline.strip().split(maxsplit=1)
    arg = args[0] if args else ""
    if cmd == "help":
        print_help()
    elif cmd == "find":
        find_entity(arg)
    elif cmd == "refresh":
        refresh_entity(arg)
    elif cmd == "stats":
        show_stats()
    elif cmd == "report":
        generate_report(arg)
    elif cmd == "daemon":
        handle_daemon(arg)
    elif cmd == "clear":
        console.clear()
    elif cmd == "exit":
        console.print("[bold #bd93f9]Adieu, Broker. Die Schatten erwarten dich.[/bold #bd93f9]")
        raise EOFError
    else:
        console.print(f"[#ff5555]Unbekanntes Kommando:[/#ff5555] [bold]{cmd}[/bold]. Gib 'help' für eine Übersicht.")

# Dummy-Handler für Kommandos (später mit echten Funktionen verknüpfen)
def find_entity(arg):    console.print(f"[#61dafb]Suche nach:[/#61dafb] [bold]{arg}[/bold]")
def refresh_entity(arg): console.print(f"[#ae81ff]Aktualisiere:[/#ae81ff] [bold]{arg}[/bold]")
def show_stats():        console.print(f"[#f1fa8c]Statistik/QA-Modul kommt bald...[/#f1fa8c]")
def generate_report(arg):console.print(f"[#bd93f9]Generiere Bericht für:[/#bd93f9] [bold]{arg}[/bold]")
def handle_daemon(arg):  console.print(f"[#f1fa8c]Daemon-Task Management WIP...[/#f1fa8c]")

def main():
    print_welcome()
    while True:
        try:
            cmdline = session.prompt(
                '[prompt]shadow-broker> [/prompt]',
                completer=COMMAND_COMPLETER,
                style=style
            )
            if cmdline.strip():
                handle_command(cmdline)
        except EOFError:
            break
        except KeyboardInterrupt:
            console.print("[#ff5555]Unterbrochen. (Ctrl+C)[/#ff5555]")

if __name__ == "__main__":
    main()
