import db_id_manager
import os

def list_collections():
    """Gibt eine Liste aller in der Registry verwendeten Collections zurück."""
    rows = db_id_manager.list_all()
    return sorted(set(row[1] for row in rows))  # row[1] == collection

def create_collection(name, index_dim, index_dir="."):
    """
    Legt einen neuen (leeren) FAISS-Index für die Collection an.
    index_dim: Dimension der Embeddings, z. B. 384 oder 768.
    """
    import faiss
    index = faiss.IndexFlatL2(index_dim)
    out_file = os.path.join(index_dir, f"{name}.index")
    faiss.write_index(index, out_file)
    return out_file

def drop_collection(name, index_dir="."):
    """Löscht die Registry-Einträge und die Index-Datei einer Collection."""
    # 1. Registry löschen
    import sqlite3
    conn = db_id_manager.get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM id_registry WHERE collection = ?", (name,))
    conn.commit()
    conn.close()
    # 2. Index-File löschen
    index_file = os.path.join(index_dir, f"{name}.index")
    if os.path.exists(index_file):
        os.remove(index_file)
        return True
    return False
