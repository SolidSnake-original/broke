import argparse
import sys
import os
import json
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from rich.console import Console

# Module importieren:
import db_batch_insert
import db_export_import
import db_collection_management
import db_healthchecks
import db_logger  # optional

console = Console()
CHROMA_DIR = "./chroma_data"
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_MODEL = SentenceTransformer(MODEL_NAME)
os.environ["ANONYMIZED_TELEMETRY"] = "False"


client = chromadb.Client(Settings(
    persist_directory=CHROMA_DIR,
    anonymized_telemetry=False
))

# ---------- Core Functions ----------
def add_document(args):
    collection = client.get_or_create_collection(args.collection)
    text = args.text
    metadata = json.loads(args.metadata) if args.metadata else {}
    doc_id = args.id if args.id else f"doc_{hash(text)}"
    embedding = EMBEDDING_MODEL.encode([text])[0].tolist()
    collection.add(
        documents=[text],
        metadatas=[metadata],
        ids=[doc_id],
        embeddings=[embedding]
    )
    console.print(f"[bold green]Dokument hinzugefügt:[/bold green] {doc_id}")

def query_collection(args):
    collection = client.get_or_create_collection(args.collection)
    query = args.query
    n = args.n
    filters = json.loads(args.filters) if args.filters else None
    result = collection.query(
        query_texts=[query],
        n_results=n,
        where=filters
    )
    console.print(f"[bold cyan]Ergebnisse:[/bold cyan]")
    for i, doc in enumerate(result['documents'][0], 1):
        console.print(f"[{i}] [#f1fa8c]{doc}[/#f1fa8c]")
        if result['metadatas'][0][i-1]:
            console.print(f"     Meta: {result['metadatas'][0][i-1]}")

def update_document(args):
    collection = client.get_or_create_collection(args.collection)
    doc_id = args.id
    new_text = args.text
    new_metadata = json.loads(args.metadata) if args.metadata else None
    # ChromaDB kann nicht direkt "update", daher: Löschen + Neu hinzufügen
    collection.delete(ids=[doc_id])
    embedding = EMBEDDING_MODEL.encode([new_text])[0].tolist()
    collection.add(
        documents=[new_text],
        metadatas=[new_metadata] if new_metadata else [{}],
        ids=[doc_id],
        embeddings=[embedding]
    )
    console.print(f"[bold yellow]Dokument aktualisiert:[/bold yellow] {doc_id}")

def delete_document(args):
    collection = client.get_or_create_collection(args.collection)
    doc_id = args.id
    collection.delete(ids=[doc_id])
    console.print(f"[bold red]Dokument gelöscht:[/bold red] {doc_id}")

# ---------- CLI Interface ----------
def main():
    parser = argparse.ArgumentParser(
        description="Shadow Broker ChromaDB Gateway – CLI-Modul"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ADD
    add_p = subparsers.add_parser("add", help="Fügt ein Dokument hinzu")
    add_p.add_argument("--collection", required=True, help="Collection-Name")
    add_p.add_argument("--text", required=True, help="Textinhalt des Dokuments")
    add_p.add_argument("--metadata", help="Metadaten als JSON-String")
    add_p.add_argument("--id", help="Optional: Dokument-ID")
    add_p.set_defaults(func=add_document)

    # QUERY
    query_p = subparsers.add_parser("query", help="Suche Collection nach Query")
    query_p.add_argument("--collection", required=True, help="Collection-Name")
    query_p.add_argument("--query", required=True, help="Text oder Frage")
    query_p.add_argument("--n", type=int, default=3, help="Anzahl Ergebnisse")
    query_p.add_argument("--filters", help="Filter als JSON (z.B. '{\"quelle\": \"leak\"}')")
    query_p.set_defaults(func=query_collection)

    # UPDATE
    upd_p = subparsers.add_parser("update", help="Dokument aktualisieren")
    upd_p.add_argument("--collection", required=True, help="Collection-Name")
    upd_p.add_argument("--id", required=True, help="Dokument-ID")
    upd_p.add_argument("--text", required=True, help="Neuer Text")
    upd_p.add_argument("--metadata", help="Neue Metadaten als JSON")
    upd_p.set_defaults(func=update_document)

    # DELETE
    del_p = subparsers.add_parser("delete", help="Dokument löschen")
    del_p.add_argument("--collection", required=True, help="Collection-Name")
    del_p.add_argument("--id", required=True, help="Dokument-ID")
    del_p.set_defaults(func=delete_document)

     # Batch-Insert
    batch_p = subparsers.add_parser("batch_insert", help="Batch-Inserts durchführen")
    batch_p.add_argument("--collection", required=True)
    batch_p.add_argument("--texts", required=True, help="JSON-Array von Texten")
    batch_p.add_argument("--metadatas", help="JSON-Array von Metadaten")
    batch_p.add_argument("--ids", help="JSON-Array von IDs")
    batch_p.set_defaults(func="batch_insert")

    # Export
    exp_p = subparsers.add_parser("export", help="Collection als JSON exportieren")
    exp_p.add_argument("--collection", required=True)
    exp_p.add_argument("--out", default="export.json")
    exp_p.set_defaults(func="export")

    # Import
    imp_p = subparsers.add_parser("import", help="JSON in Collection importieren")
    imp_p.add_argument("--collection", required=True)
    imp_p.add_argument("--file", required=True)
    imp_p.set_defaults(func="import_")

    # Collection Management
    list_p = subparsers.add_parser("list_collections", help="Liste aller Collections")
    list_p.set_defaults(func="list_collections")

    create_p = subparsers.add_parser("create_collection", help="Neue Collection erstellen")
    create_p.add_argument("--name", required=True)
    create_p.set_defaults(func="create_collection")

    drop_p = subparsers.add_parser("drop_collection", help="Collection löschen")
    drop_p.add_argument("--name", required=True)
    drop_p.set_defaults(func="drop_collection")

    # Healthcheck
    health_p = subparsers.add_parser("healthcheck", help="Healthcheck einer Collection")
    health_p.add_argument("--collection", required=True)
    health_p.set_defaults(func="healthcheck")

    stats_p = subparsers.add_parser("stats", help="Sammlungseintragszahlen aller Collections")
    stats_p.set_defaults(func="stats")

    # Logging ist in den einzelnen Funktionen nutzbar
    # logger.log_event("xy") überall im Code verwenden

    args = parser.parse_args()

    # ChromaDB-Setup (einmalig)
    #CHROMA_DIR = "./chroma_data"
    #MODEL_NAME = "all-MiniLM-L6-v2"
    #EMBEDDING_MODEL = SentenceTransformer(MODEL_NAME)
    #client = chromadb.Client(Settings(persist_directory=CHROMA_DIR))

     # ADD
    if args.command == "add":
        col = client.get_or_create_collection(args.collection)
        metadata = json.loads(args.metadata) if args.metadata else {}
        doc_id = args.id if args.id else f"doc_{hash(args.text)}"
        embedding = EMBEDDING_MODEL.encode([args.text])[0].tolist()
        col.add(
            documents=[args.text],
            metadatas=[metadata],
            ids=[doc_id],
            embeddings=[embedding]
        )
        db_logger.log_event(f"Dokument hinzugefügt: {doc_id}")

    # QUERY
    elif args.command == "query":
        col = client.get_or_create_collection(args.collection)
        filters = json.loads(args.filters) if args.filters else None
        result = col.query(
            query_texts=[args.query],
            n_results=args.n,
            where=filters
        )
        print(f"Ergebnisse für '{args.query}':")
        for i, doc in enumerate(result['documents'][0], 1):
            print(f"[{i}] {doc}")
            if result['metadatas'][0][i-1]:
                print(f"     Meta: {result['metadatas'][0][i-1]}")
        db_logger.log_event(f"Query ausgeführt: '{args.query}' in {args.collection}")

    # UPDATE
    elif args.command == "update":
        col = client.get_or_create_collection(args.collection)
        doc_id = args.id
        new_metadata = json.loads(args.metadata) if args.metadata else None
        col.delete(ids=[doc_id])
        embedding = EMBEDDING_MODEL.encode([args.text])[0].tolist()
        col.add(
            documents=[args.text],
            metadatas=[new_metadata] if new_metadata else [{}],
            ids=[doc_id],
            embeddings=[embedding]
        )
        db_logger.log_event(f"Dokument aktualisiert: {doc_id}")

    # DELETE
    elif args.command == "delete":
        col = client.get_or_create_collection(args.collection)
        doc_id = args.id
        col.delete(ids=[doc_id])
        db_logger.log_event(f"Dokument gelöscht: {doc_id}")

    # Batch-Insert
    elif args.command == "batch_insert":
        col = client.get_or_create_collection(args.collection)
        texts = json.loads(args.texts)
        metadatas = json.loads(args.metadatas) if args.metadatas else None
        ids = json.loads(args.ids) if args.ids else None
        db_batch_insert.batch_insert(col, texts, metadatas, ids)
        db_logger.log_event(f"Batch-Insert in {args.collection}: {len(texts)} Dokumente")

    # Export
    elif args.command == "export":
        col = client.get_or_create_collection(args.collection)
        out = db_export_import.export_collection(col, args.out)
        db_logger.log_event(f"Export {args.collection} -> {out}")

    # Import
    elif args.command == "import_":
        col = client.get_or_create_collection(args.collection)
        n = db_export_import.import_to_collection(col, args.file)
        db_logger.log_event(f"Import in {args.collection}: {n} Dokumente aus {args.file}")

    # Collection Management
    elif args.command == "list_collections":
        result = db_collection_management.list_collections(client)
        print(result)
        db_logger.log_event("Collections gelistet.")

    elif args.command == "create_collection":
        db_collection_management.create_collection(client, args.name)
        db_logger.log_event(f"Collection erstellt: {args.name}")

    elif args.command == "drop_collection":
        db_collection_management.drop_collection(client, args.name)
        db_logger.log_event(f"Collection gelöscht: {args.name}")

    # Healthchecks
    elif args.command == "healthcheck":
        ok, count = db_healthchecks.chroma_healthcheck(client, args.collection)
        print(f"OK: {ok} – Einträge: {count}")
        db_logger.log_event(f"Healthcheck {args.collection}: OK={ok}, N={count}")

    elif args.command == "stats":
        stats = db_healthchecks.database_stats(client)
        print(stats)
        db_logger.log_event("Stats aufgerufen.")


if __name__ == "__main__":
    main()
