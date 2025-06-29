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

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
