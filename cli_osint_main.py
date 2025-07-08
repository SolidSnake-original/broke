from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter

console = Console()
session = PromptSession()

CATEGORIES = {
    "emails": {
        "desc": "E-Mail OSINT",
        "cli": "cli_osint_email"
    },
    # Add more categories here, e.g.:
    # "usernames": {"desc": "Username OSINT", "cli": "cli_osint_username"}
}

CATEGORY_COMPLETER = WordCompleter(CATEGORIES.keys(), ignore_case=True)

def osint_main_menu():
    while True:
        console.print("\n[bold #f1fa8c]OSINT Kategorien[/bold #f1fa8c]")
        for cat, info in CATEGORIES.items():
            console.print(f"[cyan]{cat}[/cyan]: {info['desc']}")
        console.print("[blue]Wähle eine Kategorie oder tippe 'back'[/blue]")
        cat = session.prompt("[prompt]osint> [/prompt]", completer=CATEGORY_COMPLETER).strip().lower()
        if cat == "back":
            break
        if cat in CATEGORIES:
            # Dynamisch das passende CLI-Modul importieren und starten
            cli_mod = __import__(CATEGORIES[cat]["cli"])
            cli_mod.menu()
        else:
            console.print("[red]Unbekannte Kategorie.[/red]")

if __name__ == "__main__":
    osint_main_menu()