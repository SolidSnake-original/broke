import db_id_manager
import os

def registry_healthcheck():
    """Prüft, ob Registry erreichbar ist und wie viele Einträge sie hat."""
    try:
        rows = db_id_manager.list_all()
        return True, len(rows)
    except Exception as e:
        return False, str(e)

def faiss_healthcheck(index_file_path):
    """Prüft, ob ein FAISS-Indexfile existiert und gibt grobe Infos."""
    if os.path.exists(index_file_path):
        import faiss
        index = faiss.read_index(index_file_path)
        return True, index.ntotal
    else:
        return False, 0

def db_stats():
    """Gibt die Anzahl aller Dokumente pro Collection laut Registry zurück."""
    rows = db_id_manager.list_all()
    stats = {}
    for row in rows:
        coll = row[1]  # collection
        stats[coll] = stats.get(coll, 0) + 1
    return stats
