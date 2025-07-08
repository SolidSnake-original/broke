from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
import osint_email_holehe
import os  # <--- Import für Datei-Check

console = Console()
session = PromptSession()

TOOLS = {
    "holehe": "E-Mail Check mit Holehe",
    "back": "Zurück zum Hauptmenü"
    # Add more tools here
}
TOOL_COMPLETER = WordCompleter(TOOLS.keys(), ignore_case=True)

def menu():
    while True:
        console.print("\n[bold #f1fa8c]E-Mail OSINT Tools[/bold #f1fa8c]")
        for tool, desc in TOOLS.items():
            console.print(f"[cyan]{tool}[/cyan]: {desc}")
        console.print("[blue]Wähle ein Tool oder tippe 'back'[/blue]")
        tool = session.prompt("[prompt]osint-email> [/prompt]", completer=TOOL_COMPLETER).strip().lower()
        if tool == "back":
            break
        if tool == "holehe":
            mode = session.prompt("[yellow]Modus wählen: 'single' für Einzelabfrage, 'file' für Datei-Import[/yellow]\n> ").strip().lower()
            if mode == "file":
                filepath = session.prompt("Pfad zur Datei mit E-Mail-Adressen: ").strip()
                if not filepath or not os.path.isfile(filepath):
                    console.print(f"[red]Datei nicht gefunden: {filepath}[/red]")
                    continue
                console.print(f"[blue]Starte Bulk-Import für Datei: {filepath}[/blue]")
                osint_email_holehe.process_email_file(filepath)
                console.print(f"[green]Bulk-Import abgeschlossen. Ergebnisse/Audit siehe audit.log.[/green]")
            else:
                email = session.prompt("E-Mail: ").strip()
                result = osint_email_holehe.osint_email_holehe(email)
                console.print(result)
                out, err = osint_email_holehe.send_to_gateway(email, result)
                console.print(f"[green]Gateway stdout:[/green]\n{out}")
                if err:
                    console.print(f"[red]Gateway stderr:[/red]\n{err}")
        else:
            console.print("[red]Unbekanntes Tool.[/red]")