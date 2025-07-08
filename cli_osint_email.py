from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
import osint_email_holehe

console = Console()
session = PromptSession()

TOOLS = {
    "holehe": "E-Mail Check mit Holehe",
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
            email = session.prompt("E-Mail: ").strip()
            result = osint_email_holehe.osint_email_holehe(email)
            console.print(result)
            out, err = osint_email_holehe.send_to_gateway(email, result)
            console.print(f"[green]Gateway stdout:[/green]\n{out}")
            if err:
                console.print(f"[red]Gateway stderr:[/red]\n{err}")
        else:
            console.print("[red]Unbekanntes Tool.[/red]")