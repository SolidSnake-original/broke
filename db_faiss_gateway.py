import argparse
import sys
import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from rich.console import Console

import db_id_manager
# Module importieren:
import db_batch_insert
import db_export_import
import db_collection_management
import db_healthchecks
import db_logger  # optional

def load_or_create_faiss_index(collection_name, index_dim, index_dir="."):
    index_file = os.path.join(index_dir, f"{collection_name}.index")
    if os.path.exists(index_file):
        index = faiss.read_index(index_file)
    else:
        index = faiss.IndexFlatL2(index_dim)
        faiss.write_index(index, index_file)
    return index, index_file

console = Console()

# ---------- Core Functions ----------
def add_document(args, embedding_model):
    # Lade oder erstelle den passenden FAISS-Index (Dimension je nach Model, z. B. 384 für MiniLM)
    index, index_file = load_or_create_faiss_index(args.collection, embedding_model.get_sentence_embedding_dimension())
    metadata = json.loads(args.metadata) if args.metadata else {}
    entity_type = getattr(args, 'entity_type', "EMAIL")
    doc_id = db_id_manager.generate_id(
        collection=args.collection,
        entity_type=entity_type,
        source=metadata.get("quelle") if metadata else None
    )
    embedding = embedding_model.encode([args.text]).astype("float32")
    index.add(embedding)
    vektor_index = index.ntotal - 1
    db_id_manager.add_entry(
        id=doc_id,
        collection=args.collection,
        entity_type=entity_type,
        primary_value=args.text,
        metadata=metadata,
        source=metadata.get("quelle") if metadata else None,
        import_batch="manual_insert",
        vektor_index=vektor_index
    )
    faiss.write_index(index, index_file)
    print(f"Dokument & Registry hinzugefügt: {doc_id} (Vektor-Index: {vektor_index})")

def query_collection(args, embedding_model):
    index, _ = load_or_create_faiss_index(args.collection, embedding_model.get_sentence_embedding_dimension())
    query_emb = embedding_model.encode([args.query]).astype("float32")
    n = args.n
    D, I = index.search(query_emb, n)
    from db_id_manager import get_by_vektor_index
    console.print(f"[bold cyan]Ergebnisse:[/bold cyan]")
    for rank, vektor_index in enumerate(I[0], 1):
        row = get_by_vektor_index(int(vektor_index))
        if row:
            console.print(f"[{rank}] [#f1fa8c]{row[3]}[/#f1fa8c]")  # primary_value
            meta = row[4]
            if meta:
                console.print(f"     Meta: {meta}")
        else:
            console.print(f"[{rank}] Kein Dokument zu Vektor-Index {vektor_index} gefunden.")

def update_document(args, embedding_model):
    # Lösung: Flagge alten Eintrag als gelöscht, füge neuen ein (Index bleibt append-only)
    index, index_file = load_or_create_faiss_index(args.collection, embedding_model.get_sentence_embedding_dimension())
    old_row = db_id_manager.get_by_id(args.id)
    if not old_row:
        print(f"[ERROR] ID {args.id} nicht in Registry.")
        return
    # Optional: Registry-Flag für "deleted" setzen oder Eintrag entfernen
    db_id_manager.delete_id(args.id)
    # Neuen Eintrag generieren (wie ADD)
    metadata = json.loads(args.metadata) if args.metadata else None
    entity_type = getattr(args, 'entity_type', "EMAIL")
    doc_id = db_id_manager.generate_id(
        collection=args.collection,
        entity_type=entity_type,
        source=metadata.get("quelle") if metadata else None
    )
    embedding = embedding_model.encode([args.text]).astype("float32")
    index.add(embedding)
    vektor_index = index.ntotal - 1
    db_id_manager.add_entry(
        id=doc_id,
        collection=args.collection,
        entity_type=entity_type,
        primary_value=args.text,
        metadata=metadata,
        source=metadata.get("quelle") if metadata else None,
        import_batch="update",
        vektor_index=vektor_index
    )
    faiss.write_index(index, index_file)
    print(f"Dokument aktualisiert: {doc_id} (Vektor-Index: {vektor_index})")

def delete_document(args):
    # Eintrag nur aus Registry entfernen; FAISS kennt kein echtes Delete!
    db_id_manager.delete_id(args.id)
    print(f"Registry-Eintrag gelöscht: {args.id}")
    print("[WARN] FAISS-Vektor verbleibt physisch bis zum periodischen Neuaufbau (empfohlen als Cronjob/Daemon).")


# ---------- CLI Interface ----------
def main():
    parser = argparse.ArgumentParser(
        description="Shadow Broker FAISS Gateway – CLI-Modul"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ADD
    add_p = subparsers.add_parser("add", help="Fügt ein Dokument hinzu")
    add_p.add_argument("--collection", required=True, help="Collection-Name")
    add_p.add_argument("--text", required=True, help="Textinhalt des Dokuments")
    add_p.add_argument("--metadata", help="Metadaten als JSON-String")
    add_p.set_defaults(func=add_document)

    # QUERY
    query_p = subparsers.add_parser("query", help="Semantische Suche in einer Collection")
    query_p.add_argument("--collection", required=True, help="Collection-Name (entspricht FAISS-Index & Registry-Feld)")
    query_p.add_argument("--query", required=True, help="Suchtext oder Frage")
    query_p.add_argument("--n", type=int, default=3, help="Anzahl der Top-Ergebnisse")
    # filters ist für FAISS+Registry erstmal nicht sinnvoll, weil du semantisch suchst und Filter später via Registry umsetzen könntest
    query_p.set_defaults(func=query_collection)

    # UPDATE
    upd_p = subparsers.add_parser("update", help="Dokument aktualisieren (löscht alten Eintrag und fügt neuen ein)")
    upd_p.add_argument("--collection", required=True, help="Collection-Name")
    upd_p.add_argument("--id", required=True, help="Dokument-ID in der Registry (nicht im FAISS-Index!)")
    upd_p.add_argument("--text", required=True, help="Neuer Text")
    upd_p.add_argument("--metadata", help="Neue Metadaten als JSON")
    upd_p.set_defaults(func=update_document)

    # DELETE
    del_p = subparsers.add_parser("delete", help="Dokument löschen (aus Registry)")
    del_p.add_argument("--collection", required=True, help="Collection-Name")
    del_p.add_argument("--id", required=True, help="Dokument-ID in der Registry")
    del_p.set_defaults(func=delete_document)

     # Batch-Insert
    batch_p = subparsers.add_parser("batch_insert", help="Mehrere Dokumente einfügen")
    batch_p.add_argument("--collection", required=True, help="Collection-Name")
    batch_p.add_argument("--texts", required=True, help="JSON-Array von Texten")
    batch_p.add_argument("--metadatas", help="JSON-Array von Metadaten (optional, gleiche Länge wie texts)")
    # --ids ist überflüssig, wird eh generiert
    batch_p.set_defaults(func=db_batch_insert.batch_insert_cli)

    # Export
    exp_p = subparsers.add_parser("export", help="Registry + FAISS-Index exportieren")
    exp_p.add_argument("--collection", required=True, help="Collection-Name")
    exp_p.add_argument("--out", default="export.jsonl", help="JSONL-Dateiname für Registry-Export")
    exp_p.set_defaults(func=db_export_import.export_registry_and_vectors)

    # Import
    imp_p = subparsers.add_parser("import", help="Registry + FAISS-Index importieren")
    imp_p.add_argument("--collection", required=True, help="Collection-Name")
    imp_p.add_argument("--file", required=True, help="JSONL-Datei für Registry-Import")
    # Du kannst hier später optional noch --faiss hinzufügen, für Index-Datei
    imp_p.set_defaults(func=db_export_import.import_registry_and_vectors)

    # Collection Management
    list_p = subparsers.add_parser("list_collections", help="Alle genutzten Collections anzeigen")
    list_p.set_defaults(func=db_collection_management.list_collections)

    create_p = subparsers.add_parser("create_collection", help="Neue Collection (Index) anlegen")
    create_p.add_argument("--name", required=True, help="Name der Collection")
    # Für create_collection könnte ein --dim Argument (Dimension des Embeddings) sinnvoll sein
    create_p.set_defaults(func=db_collection_management.create_collection)

    drop_p = subparsers.add_parser("drop_collection", help="Collection (Index + Registry-Einträge) löschen")
    drop_p.add_argument("--name", required=True, help="Name der Collection")
    drop_p.set_defaults(func=db_collection_management.drop_collection)

    # Healthcheck
    health_p = subparsers.add_parser("healthcheck", help="Healthcheck für Registry und Index")
    health_p.add_argument("--collection", required=True, help="Collection-Name")
    health_p.set_defaults(func=db_healthchecks.registry_healthcheck)

    stats_p = subparsers.add_parser("stats", help="Eintragszahlen aller Collections")
    stats_p.set_defaults(func=stats)

    # Logging ist in den einzelnen Funktionen nutzbar
    # logger.log_event("xy") überall im Code verwenden

    args = parser.parse_args()
    # Embedding Model
    MODEL_NAME = "all-MiniLM-L6-v2"
    EMBEDDING_MODEL = SentenceTransformer(MODEL_NAME)
    INDEX_DIR = "./faiss_indices"
    os.makedirs(INDEX_DIR, exist_ok=True)
    if args.command == "add":
        add_document(args, EMBEDDING_MODEL)
        db_logger.log_event(f"Dokument hinzugefügt: {args.text[:80]}...")

    elif args.command == "query":
        query_collection(args, EMBEDDING_MODEL)
        db_logger.log_event(f"Query ausgeführt: '{args.query}' in {args.collection}")

    elif args.command == "update":
        update_document(args, EMBEDDING_MODEL)
        db_logger.log_event(f"Dokument aktualisiert: {args.id}")

    elif args.command == "delete":
        delete_document(args)
        db_logger.log_event(f"Dokument gelöscht: {args.id}")

    elif args.command == "batch_insert":
        # Lade oder erstelle Index!
        index, index_file = load_or_create_faiss_index(
        args.collection, EMBEDDING_MODEL.get_sentence_embedding_dimension()
        )
        texts = json.loads(args.texts)
        metadatas = json.loads(args.metadatas) if args.metadatas else None
        ids, vektor_indices = db_batch_insert.batch_insert(
            index, texts, args.collection, metadatas=metadatas
        )
        faiss.write_index(index, index_file)
        db_logger.log_event(f"Batch-Insert in {args.collection}: {len(ids)} Dokumente")

    elif args.command == "export":
        out_jsonl, out_index = db_export_import.export_registry_and_vectors(
            out_jsonl=args.out,
            faiss_index=load_or_create_faiss_index(
                args.collection, EMBEDDING_MODEL.get_sentence_embedding_dimension()
            )[0],
            out_faiss=f"{args.collection}.index"
        )
        db_logger.log_event(f"Export {args.collection} -> {out_jsonl} & {out_index}")

    elif args.command == "import_":
        db_export_import.import_registry_and_vectors(
            args.file, f"{args.collection}.index"
        )
        db_logger.log_event(f"Import in {args.collection}: aus {args.file} + {args.collection}.index")

    elif args.command == "list_collections":
        result = db_collection_management.list_collections()
        print(result)
        db_logger.log_event("Collections gelistet.")

    elif args.command == "create_collection":
        # Dimension der Embeddings muss bekannt sein!
        out_file = db_collection_management.create_collection(
            args.name, EMBEDDING_MODEL.get_sentence_embedding_dimension()
        )
        db_logger.log_event(f"Collection erstellt: {args.name} ({out_file})")

    elif args.command == "drop_collection":
        db_collection_management.drop_collection(args.name)
        db_logger.log_event(f"Collection gelöscht: {args.name}")

    elif args.command == "healthcheck":
        ok, count = db_healthchecks.registry_healthcheck()
        print(f"Registry OK: {ok} – Einträge: {count}")
        index_ok, n_vecs = db_healthchecks.faiss_healthcheck(f"{args.collection}.index")
        print(f"FAISS-Index OK: {index_ok} – Vektoren: {n_vecs}")
        db_logger.log_event(f"Healthcheck {args.collection}: Registry OK={ok}, N={count} | Index OK={index_ok}, V={n_vecs}")

    elif args.command == "stats":
        stats = db_healthchecks.db_stats()
        print(stats)
        db_logger.log_event("Stats aufgerufen.")

if __name__ == "__main__":
    main()