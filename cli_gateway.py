from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import WordCompleter
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
import sys, json

# ==== Gateway & Manager Imports (deine echten Module!) ====
from db_faiss_gateway import (
    add_document,
    query_collection,
    update_document,
    delete_document,
    load_or_create_faiss_index
)
from db_id_manager import list_all, find_by_collection
from db_export_import import export_registry_and_vectors, import_registry_and_vectors
from db_batch_insert import batch_insert
from sentence_transformers import SentenceTransformer

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

# ==== Kommandos für die CLI ====
COMMANDS = {
    'help':    'Alle Kommandos anzeigen',
    'add':     'Dokument hinzufügen',
    'query':   'Semantische Suche',
    'update':  'Dokument aktualisieren',
    'delete':  'Dokument löschen',
    'batch_insert': 'Mehrere Dokumente einfügen',
    'export':  'Registry + Index exportieren',
    'import':  'Registry + Index importieren',
    'list':    'Alle Dokumente einer Collection anzeigen',
    'stats':   'Sammlungseintragszahlen',
    'clear':   'Konsole leeren',
    'exit':    'Shadow Broker verlassen'
}
COMMAND_COMPLETER = WordCompleter(COMMANDS.keys(), ignore_case=True)

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_MODEL = SentenceTransformer(MODEL_NAME)
INDEX_DIR = "./faiss_indices"

def print_welcome():
    console.print("\n[bold #f1fa8c]Willkommen im[/bold #f1fa8c] [#bd93f9]SHADOW BROKER GATEWAY[/#bd93f9]", style="bold")
    console.print("[#ff5555]Die Nacht sieht alles – aber du lenkst den Blick...[/#ff5555]\n")

def print_help():
    table = Table(title="[bold]Verfügbare Kommandos[/bold]", style="#f1fa8c", border_style="#181818")
    table.add_column("Kommando", style="#61dafb", no_wrap=True)
    table.add_column("Beschreibung", style="#dddddd")
    for cmd, desc in COMMANDS.items():
        table.add_row(cmd, desc)
    console.print(table)

def cli_add():
    collection = Prompt.ask("[prompt]Collection[/prompt]")
    text = Prompt.ask("[prompt]Text[/prompt]")
    metadata = Prompt.ask("[prompt]Metadaten (JSON, optional)[/prompt]", default="{}")
    class Args: pass
    args = Args()
    args.collection = collection
    args.text = text
    args.metadata = metadata
    try:
        add_document(args, EMBEDDING_MODEL)
        console.print("[success]Dokument hinzugefügt.[/success]")
    except Exception as e:
        console.print(f"[error]Fehler beim Hinzufügen:[/error] {e}")

def cli_query():
    collection = Prompt.ask("[prompt]Collection[/prompt]")
    query = Prompt.ask("[prompt]Suchtext[/prompt]")
    n = int(Prompt.ask("[prompt]Anzahl Ergebnisse[/prompt]", default="3"))
    class Args: pass
    args = Args()
    args.collection = collection
    args.query = query
    args.n = n
    try:
        query_collection(args, EMBEDDING_MODEL)
    except Exception as e:
        console.print(f"[error]Fehler bei Suche:[/error] {e}")

def cli_update():
    collection = Prompt.ask("[prompt]Collection[/prompt]")
    id_ = Prompt.ask("[prompt]Dokument-ID[/prompt]")
    text = Prompt.ask("[prompt]Neuer Text[/prompt]")
    metadata = Prompt.ask("[prompt]Metadaten (JSON, optional)[/prompt]", default="{}")
    class Args: pass
    args = Args()
    args.collection = collection
    args.id = id_
    args.text = text
    args.metadata = metadata
    try:
        update_document(args, EMBEDDING_MODEL)
        console.print("[success]Dokument aktualisiert.[/success]")
    except Exception as e:
        console.print(f"[error]Fehler beim Update:[/error] {e}")

def cli_delete():
    collection = Prompt.ask("[prompt]Collection[/prompt]")
    id_ = Prompt.ask("[prompt]Dokument-ID[/prompt]")
    class Args: pass
    args = Args()
    args.collection = collection
    args.id = id_
    try:
        delete_document(args)
        console.print("[success]Dokument gelöscht.[/success]")
    except Exception as e:
        console.print(f"[error]Fehler beim Löschen:[/error] {e}")

def cli_batch_insert():
    collection = Prompt.ask("[prompt]Collection[/prompt]")
    texts = Prompt.ask("[prompt]Texte (JSON-Array)[/prompt]")
    metadatas = Prompt.ask("[prompt]Metadaten (JSON-Array, optional)[/prompt]", default=None)
    class Args: pass
    args = Args()
    args.collection = collection
    args.texts = texts
    args.metadatas = metadatas
    try:
        index, index_file = load_or_create_faiss_index(
            collection, EMBEDDING_MODEL.get_sentence_embedding_dimension()
        )
        batch_insert(index, json.loads(texts), collection,
                     metadatas=json.loads(metadatas) if metadatas else None)
        console.print("[success]Batch-Insert abgeschlossen.[/success]")
    except Exception as e:
        console.print(f"[error]Fehler bei Batch-Insert:[/error] {e}")

def cli_export():
    collection = Prompt.ask("[prompt]Collection[/prompt]")
    out = Prompt.ask("[prompt]Export-Dateiname[/prompt]", default="export.jsonl")
    try:
        index, _ = load_or_create_faiss_index(
            collection, EMBEDDING_MODEL.get_sentence_embedding_dimension()
        )
        export_registry_and_vectors(out, index, f"{collection}.index")
        console.print(f"[success]Exportiert nach {out} + {collection}.index[/success]")
    except Exception as e:
        console.print(f"[error]Fehler beim Export:[/error] {e}")

def cli_import():
    collection = Prompt.ask("[prompt]Collection[/prompt]")
    in_file = Prompt.ask("[prompt]Import-Dateiname[/prompt]", default="export.jsonl")
    try:
        import_registry_and_vectors(in_file, f"{collection}.index")
        console.print(f"[success]Import abgeschlossen für {collection}.[/success]")
    except Exception as e:
        console.print(f"[error]Fehler beim Import:[/error] {e}")

def cli_list():
    collection = Prompt.ask("[prompt]Collection (leer für alle)[/prompt]", default=None)
    if collection:
        docs = find_by_collection(collection)
    else:
        docs = list_all()
    table = Table(title=f"Dokumente in {collection or 'allen Collections'}", border_style="#181818")
    table.add_column("ID", style="#61dafb")
    table.add_column("Text", style="#b6f4ff")
    table.add_column("Meta", style="#9d68f6")
    for row in docs:
        table.add_row(str(row[0]), str(row[3])[:80], str(row[4]))
    console.print(table)

def cli_stats():
    from db_healthchecks import db_stats
    stats = db_stats()
    table = Table(title="[bold]Collection Stats[/bold]", border_style="#181818")
    table.add_column("Collection", style="#00ffe7")
    table.add_column("Anzahl Dokumente", style="#32ff7a")
    for coll, n in stats.items():
        table.add_row(coll, str(n))
    console.print(table)

def handle_command(cmdline):
    cmd, *args = cmdline.strip().split(maxsplit=1)
    arg = args[0] if args else ""
    if cmd == "help":
        print_help()
    elif cmd == "add":
        cli_add()
    elif cmd == "query":
        cli_query()
    elif cmd == "update":
        cli_update()
    elif cmd == "delete":
        cli_delete()
    elif cmd == "batch_insert":
        cli_batch_insert()
    elif cmd == "export":
        cli_export()
    elif cmd == "import":
        cli_import()
    elif cmd == "list":
        cli_list()
    elif cmd == "stats":
        cli_stats()
    elif cmd == "clear":
        console.clear()
    elif cmd == "exit":
        console.print("[bold #bd93f9]Adieu, Broker. Die Schatten erwarten dich.[/bold #bd93f9]")
        raise EOFError
    else:
        console.print(f"[error]Unbekanntes Kommando:[/error] [bold]{cmd}[/bold]. Gib 'help' für eine Übersicht.")

def main():
    print_welcome()
    while True:
        try:
            cmdline = session.prompt(
                '[prompt]shadow-broker-gateway> [/prompt]',
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
