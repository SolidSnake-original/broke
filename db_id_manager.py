# id_manager.py

import sqlite3
from datetime import datetime

REGISTRY_DB = "broker_registry.db"

def get_connection():
    return sqlite3.connect(REGISTRY_DB)

def setup_registry():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS id_registry (
            id TEXT PRIMARY KEY,
            collection TEXT,
            entity_type TEXT,
            primary_value TEXT,
            metadata TEXT,
            timestamp TEXT,
            source TEXT,
            import_batch TEXT,
            vektor_index INTEGER UNIQUE
        )
    """)
    conn.commit()
    conn.close()


def generate_id(collection, entity_type, source=None, unique_part=None):
    # ID-Schema: <COLL>_<TYPE>_<SRC>_<YYYYMMDD>_<unique>
    date_part = datetime.utcnow().strftime("%Y%m%d")
    src_part = source if source else "misc"
    uniq = unique_part if unique_part else datetime.utcnow().strftime("%H%M%S%f")
    return f"{collection.upper()}_{entity_type.upper()}_{src_part}_{date_part}_{uniq}"

def add_entry(id, collection, entity_type, primary_value, metadata=None, source=None, import_batch=None, vektor_index=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO id_registry
        (id, collection, entity_type, primary_value, metadata, timestamp, source, import_batch, vektor_index)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        id,
        collection,
        entity_type,
        primary_value,
        str(metadata) if metadata else None,
        datetime.utcnow().isoformat(),
        source,
        import_batch,
        vektor_index
    ))
    conn.commit()
    conn.close()

#obsolete?
def get_by_id(id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM id_registry WHERE id = ?", (id,))
    row = c.fetchone()
    conn.close()
    return row

def get_by_vektor_index(vektor_index):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM id_registry WHERE vektor_index = ?", (vektor_index,))
    row = c.fetchone()
    conn.close()
    return row

def find_by_collection(collection):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM id_registry WHERE collection = ?", (collection,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_id(id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM id_registry WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def list_all():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM id_registry")
    rows = c.fetchall()
    conn.close()
    return rows

def export_registry(out_file="id_registry_export.jsonl"):
    import json
    with open(out_file, "w", encoding="utf-8") as f:
        for row in list_all():
            entry = {
                "id": row[0],
                "collection": row[1],
                "entity_type": row[2],
                "primary_value": row[3],
                "metadata": row[4],
                "timestamp": row[5],
                "source": row[6],
                "import_batch": row[7]
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return out_file

# Setup direkt beim Import
setup_registry()
