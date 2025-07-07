import faiss
import numpy as np
import os
from datetime import datetime
from sentence_transformers import SentenceTransformer
from db_id_manager import list_all, find_by_collection

EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
AUDIT_LOG = "audit.txt"

def log_audit(msg, level="CLEANUP"):
    now = datetime.now().isoformat(timespec="seconds")
    import os
    pid = os.getpid()
    line = f"{now} [{level}] [PID:{pid}] {msg}"
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def rebuild_faiss_index(collection, index_file, embedding_dim=384, registry_func=find_by_collection):
    """
    Baut den FAISS-Index aus der SQLite-Registry neu auf (nur noch gültige Daten).
    """
    docs = registry_func(collection)
    if not docs:
        log_audit(f"Keine Einträge für Collection {collection}. Schreibe leeren Index.", "WARN")
        new_index = faiss.IndexFlatL2(embedding_dim)
        faiss.write_index(new_index, index_file)
        return 0

    texts = [row[3] for row in docs]   # primary_value-Spalte
    embeddings = EMBEDDING_MODEL.encode(texts).astype("float32")

    new_index = faiss.IndexFlatL2(embedding_dim)
    new_index.add(embeddings)
    faiss.write_index(new_index, index_file)

    log_audit(f"{len(texts)} Einträge in FAISS-Index '{index_file}' aktualisiert (Collection: {collection})", "SUCCESS")
    return len(texts)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Broker DB Cleanup – FAISS index rebuilds from SQLite registry.")
    parser.add_argument("--collection", required=True, help="Collection-Name (Registry-Lead)")
    parser.add_argument("--index_file", required=True, help="FAISS Index-File (z.B. emails.index)")
    parser.add_argument("--embedding_dim", type=int, default=384, help="Embedding Dimension (default: 384 für MiniLM)")
    args = parser.parse_args()
    rebuild_faiss_index(args.collection, args.index_file, args.embedding_dim)