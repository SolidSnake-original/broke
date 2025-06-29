import json
import numpy as np
import db_id_manager
import faiss

def export_registry_and_vectors(out_jsonl="export.jsonl", faiss_index=None, out_faiss="export.index"):
    """
    Exportiert die Registry (Text, IDs, Meta, vektor_index) als JSONL,
    und den FAISS-Index als Datei.
    """
    # 1. Exportiere Registry
    db_id_manager.export_registry(out_jsonl)
    # 2. Exportiere FAISS-Index, falls gegeben
    if faiss_index is not None:
        faiss.write_index(faiss_index, out_faiss)
    return out_jsonl, out_faiss

def import_registry_and_vectors(in_jsonl, faiss_index_file):
    """
    Importiert Registry aus JSONL und lädt FAISS-Index.
    """
    # 1. Registry importieren (optional: Duplikate vermeiden!)
    with open(in_jsonl, encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            db_id_manager.add_entry(
                id=entry["id"],
                collection=entry["collection"],
                entity_type=entry["entity_type"],
                primary_value=entry["primary_value"],
                metadata=entry["metadata"],
                source=entry.get("source"),
                import_batch=entry.get("import_batch"),
                vektor_index=entry.get("vektor_index")
            )
    # 2. FAISS-Index laden
    index = faiss.read_index(faiss_index_file)
    return index
