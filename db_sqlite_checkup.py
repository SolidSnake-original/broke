import sqlite3
import json
import os
from datetime import datetime

REGISTRY_DB = "broker_registry.db"
AUDIT_LOG = "audit.log"

def log_audit(msg, level="SQLITE_CHECK"):
    now = datetime.now().isoformat(timespec="seconds")
    pid = os.getpid()
    line = f"{now} [{level}] [PID:{pid}] {msg}"
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def repair_metadata(meta):
    # Step 1: Versuche json.loads wie gewohnt
    try:
        json.loads(meta)
        return meta, False  # Already valid
    except Exception:
        pass

    # Step 2: Ersetze Single Quotes mit Double Quotes
    repaired = meta.replace("'", '"')
    try:
        json.loads(repaired)
        return repaired, True
    except Exception:
        pass

    # Step 3: Fallback: Versuche ast.literal_eval (nur für kontrollierte Umgebungen)
    import ast
    try:
        obj = ast.literal_eval(meta)
        as_json = json.dumps(obj, ensure_ascii=False)
        return as_json, True
    except Exception:
        pass

    return meta, False  # Could not repair

def sqlite_checkup():
    conn = sqlite3.connect(REGISTRY_DB)
    c = conn.cursor()
    removed = 0

    # 1. Duplikate erkennen und entfernen
    # Zuerst: Duplikate selektieren und loggen
    c.execute('''
        SELECT rowid, id, collection, entity_type, primary_value
        FROM id_registry
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM id_registry
            GROUP BY collection, entity_type, primary_value
        )
    ''')
    dup_rows = c.fetchall()
    for row in dup_rows:
        log_audit(f"Duplikat gelöscht: rowid={row[0]}, id={row[1]}, collection={row[2]}, entity_type={row[3]}, primary_value={row[4]}", "CLEANUP")
    # Jetzt löschen
    c.execute("""
        DELETE FROM id_registry
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM id_registry
            GROUP BY collection, entity_type, primary_value
        )
    """)
    dupes = conn.total_changes
    if dupes > 0:
        log_audit(f"{dupes} Duplikate entfernt (gleiche Collection, entity_type, primary_value).", "CLEANUP")

    # 2. IDs prüfen (Format & Eindeutigkeit, wird durch PRIMARY KEY erzwungen, daher nur Format hier)
    c.execute("SELECT id FROM id_registry")
    bad_ids = [row[0] for row in c.fetchall() if not valid_id(row[0])]
    for bad_id in bad_ids:
        log_audit(f"ID mit ungültigem Format gefunden: {bad_id}", "WARNING")

    # 3. Leichen & Waisen (leere/null Pflichtfelder)
    c.execute("""
        SELECT rowid, id, collection, entity_type, primary_value
        FROM id_registry
        WHERE primary_value IS NULL OR TRIM(primary_value) = '' OR collection IS NULL OR entity_type IS NULL
    """)
    leichen_rows = c.fetchall()
    for row in leichen_rows:
        log_audit(f"Leiche/Waise gelöscht: rowid={row[0]}, id={row[1]}, collection={row[2]}, entity_type={row[3]}, primary_value={row[4]}", "CLEANUP")
    c.execute("DELETE FROM id_registry WHERE primary_value IS NULL OR TRIM(primary_value) = '' OR collection IS NULL OR entity_type IS NULL")
    leichen = conn.total_changes
    if leichen > 0:
        log_audit(f"{leichen} Leichen/Waisen entfernt (leere/null Pflichtfelder).", "CLEANUP")

    # 4. Zeitliche Anomalien
    c.execute("SELECT id, timestamp, metadata FROM id_registry")
    for id, ts, meta in c.fetchall():
        update_needed = False
        new_metadata = meta
        now_iso = datetime.now().isoformat(timespec="seconds")
        if not ts:
            # Add missing timestamp
            new_ts = now_iso
            try:
                meta_obj = json.loads(meta) if meta else {}
            except Exception:
                meta_obj = {}
            meta_obj["audited"] = "added missing timestamp"
            new_metadata = json.dumps(meta_obj, ensure_ascii=False)
            c.execute("UPDATE id_registry SET timestamp = ?, metadata = ?, import_batch = ? WHERE id = ?", (new_ts, new_metadata, "audited_by_demon", id))
            log_audit(f"Kein Timestamp bei ID {id} – gesetzt auf {new_ts} und auditiert.", "WARNING")
            continue
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00") if "Z" in ts else ts)
            if dt.year < 2000 or dt > datetime.now():
                # Timely anomaly
                new_ts = now_iso
                try:
                    meta_obj = json.loads(meta) if meta else {}
                except Exception:
                    meta_obj = {}
                meta_obj["audited"] = "timestamp anomaly"
                new_metadata = json.dumps(meta_obj, ensure_ascii=False)
                c.execute("UPDATE id_registry SET timestamp = ?, metadata = ?, import_batch = ? WHERE id = ?", (new_ts, new_metadata, "audited_by_demon", id))
                log_audit(f"Zeitliche Anomalie bei {id}: {ts} – gesetzt auf {new_ts} und auditiert.", "WARNING")
        except Exception:
            log_audit(f"Ungültiges Timestamp-Format bei {id}: {ts}", "WARNING")

    # 5. Metadaten-Integrität
    c.execute("SELECT id, metadata FROM id_registry")
    for id, meta in c.fetchall():
        if meta:
            repaired, fixed = repair_metadata(meta)
            if fixed:
                c.execute("UPDATE id_registry SET metadata = ?, import_batch = ? WHERE id = ?", (repaired, "audited_by_demon", id))
                log_audit(f"Metadata-JSON bei ID {id} auto-repariert.", "CLEANUP")
            else:
                try:
                    json.loads(meta)
                except Exception:
                    log_audit(f"Ungültiges Metadata-JSON bei ID: {id} konnte nicht auto-repariert werden.", "WARNING")

    # 6. Collection-Logik: leere Collectionnamen, Sammlungen ohne Index
    c.execute("SELECT DISTINCT collection FROM id_registry")
    collections = [row[0] for row in c.fetchall() if row[0] and row[0].strip()]
    for coll in collections:
        idxfile = f"{coll}.index"
        if not os.path.isfile(idxfile):
            log_audit(f"Registry-Sammlung '{coll}' ohne zugehörigen Index: {idxfile}", "WARNING")

    # 7. ID-Kollisionsschutz (bereits PRIMARY KEY, aber zur Sicherheit Report)
    c.execute("""
        SELECT id, COUNT(*)
        FROM id_registry
        GROUP BY id
        HAVING COUNT(*) > 1
    """)
    for id, count in c.fetchall():
        log_audit(f"KOLLISION: ID {id} taucht {count}x auf!", "ERROR")

    # 8. Leere/unnütze Einträge (sollten mit #3 abgedeckt sein, Redundanz für Sicherheit)
    c.execute("DELETE FROM id_registry WHERE primary_value IS NULL OR TRIM(primary_value) = ''")
    nulls = conn.total_changes
    if nulls > 0:
        log_audit(f"{nulls} Null/unnütze Einträge entfernt.", "CLEANUP")

    conn.commit()
    conn.close()
    log_audit("SQLite-Checkup abgeschlossen.", "SUCCESS")

def valid_id(id_str):
    # Beispiel-Regel: collection_entitytype_source_YYYYMMDD_uniq
    # Passe Regex an dein wirkliches ID-Schema an
    import re
    return bool(re.match(r"^[A-Z0-9]+_[A-Z0-9]+_[a-zA-Z0-9]+_\d{8}_[0-9]+$", str(id_str)))

if __name__ == "__main__":
    sqlite_checkup()
