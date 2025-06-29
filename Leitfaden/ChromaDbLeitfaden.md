# Shadow Broker ChromaDB Gateway – Dokumentation

Das Shadow Broker Gateway ist ein modulares, CLI-basiertes Universal-Gateway für semantische OSINT-Datenhaltung in ChromaDB.  
Jede Funktionalität ist als Modul eingebunden und lässt sich per Kommandozeile ausführen.  
Das Gateway dient als Brücke zwischen CLI, Daemon/Automation, weiteren Modulen und deinem OSINT-Archiv.

## Features

- Einzel-Dokument-Insert, Query, Update, Delete
- Batch-Inserts für Massenimporte
- Export & Import als JSON
- Collection-Management (Listen, Anlegen, Löschen)
- Healthchecks & Datenbank-Statistiken
- Logging/Monitoring für Nachvollziehbarkeit
- Modular und beliebig erweiterbar

## Systemanforderungen

- Python 3.9+
- Pakete: `chromadb`, `sentence-transformers`, `rich`
- Installation:
  ```bash
  pip install chromadb sentence-transformers rich
  ```

## Beispielhafte Aufrufe
### Dokument einfügen
Fügt ein einzelnes Dokument (mit Metadaten) in eine Collection ein.
 ```bash
python .\db_faiss_gateway.py add --collection emails --text "Trump ist in Wahrheit eine Orange." --metadata '"{""quelle"": ""informant"", ""timestamp"": ""2024-06-22""}"'
 ```

### Semantische Suche (Query)
Findet die ähnlichsten Einträge zu einem Suchbegriff.
 ```bash
 python chroma_gateway.py query --collection emails --query "Holunder Leak LinkedIn" --n 5
 ```

### Dokument aktualisieren
Ersetzt einen Eintrag durch einen neuen Text (und neue Metadaten).
 ```bash
python .\db_faiss_gateway.py update --collection emails --id EMAILS_EMAIL_leak_20250629_212831782420 --text "patrick@beispiel.com korrigiert" --metadata '"{""quelle"": ""leak"", ""timestamp"": ""2025-06-23""}"'
 ```

### Dokument löschen
Löscht ein Dokument per ID.
 ```bash
 python chroma_gateway.py delete --collection emails --id doc_1234
 ```

### Batch-Inserts
Fügt mehrere Dokumente auf einmal ein (Texte, Metadaten, IDs als JSON-Array).
 ```bash
 python chroma_gateway.py batch_insert --collection emails --texts '["A","B","C"]' --metadatas '[{"quelle": "a"},{"quelle": "b"},{"quelle": "c"}]' --ids '["doc1","doc2","doc3"]'
 # eventuell Double Quote
 ```

### Export einer Collection (JSON)
Exportiert alle Einträge einer Collection in eine JSON-Datei.
 ```bash
 python chroma_gateway.py export --collection emails --out emails_export.json
 ```

### Import von Dokumenten (JSON)
Importiert Einträge aus einer JSON-Datei in eine Collection.
 ```bash
 python chroma_gateway.py import --collection emails --file emails_export.json
 ```

### Collection Management
 ```bash
 #Alle Collections auflisten:
 python chroma_gateway.py list_collections

 #Neue Collection anlegen:
 python chroma_gateway.py create_collection --name contacts

 #Collection löschen:
 python chroma_gateway.py drop_collection --name contacts
 ```

### Healthchecks & Stats
 ```bash
 #Existenz und Größe einer Collection prüfen:
 python chroma_gateway.py healthcheck --collection emails

 #Alle Collections & Eintragszahlen anzeigen:
 python chroma_gateway.py stats
 ```

### Logging & Monitoring
- Alle Aktionen werden im File shadowbroker_chroma.log und farbig in der Konsole protokolliert.
- Fehler, Warnungen und Erfolge sind direkt nachvollziehbar.

---

## Beispiel-Projektstruktur

```lua
shadowbroker/
├── batch_insert.py
├── collection_management.py
├── export_import.py
├── healthchecks.py
├── logger.py
├── chroma_gateway.py
└── shadowbroker_chroma.log
```

---
## Hinweise & Best Practices

- JSON-Argumente (bei Metadaten, Batch) müssen korrekt formatiert sein (sonst Fehler).
- Doppelte IDs werden von ChromaDB nicht überschrieben – vor dem erneuten Insert löschen.
- ChromaDB Telemetrie-Fehler („Failed to send telemetry event …“) sind kosmetisch und können ignoriert oder durch Setzen von anonymized_telemetry=False in den Settings unterdrückt werden.
- Automation: Das Gateway eignet sich für direkte Cronjob-Integration, CI/CD, Daemons, sowie für OSINT-APIs und CLIs.

## Beispielhafte JSON Struktur
```json
{
  "ids": [
    "doc_001",
    "doc_002",
    "doc_003"
  ],
  "documents": [
    "patrick@beispiel.com in Leak gefunden",
    "john.doe@mail.com entdeckt auf Pastebin",
    "alice@osint.org in kompromittierter DB"
  ],
  "metadatas": [
    {
      "quelle": "leak",
      "timestamp": "2025-06-22"
    },
    {
      "quelle": "pastebin",
      "timestamp": "2025-06-15"
    },
    {
      "quelle": "dump",
      "timestamp": "2025-06-01"
    }
  ]
}
```

### Wichtige Hinweise:
- Die Arrays ids, documents und metadatas müssen die gleiche Länge haben und im selben Index zueinander gehören.
- Die Metadaten können beliebig erweitert werden (z. B. mit „confidence“, „type“, „fundstelle“).
- Ein "embeddings"-Array wird nicht benötigt – das Gateway erzeugt Embeddings beim Import automatisch.

## Erweiterung & Integration

- Neue Module lassen sich als eigene Dateien und neue Subcommands ins Gateway einfügen.
- Ein REST-API-Interface (z.B. via FastAPI) ist problemlos möglich.
- Das Gateway ist als Backend für große OSINT-Systeme, automatisierte Datenerhebung und Recherche-Tools gedacht.

## Separate ID-Registry (Mapping-Tabelle)
Eine flache Datenbank/Tabelle/Datei, z. B. id_registry.jsonl oder SQLite-DB, die für jede ID einen Index anlegt:
```json
{
  "id": "EMAIL_leak_20250622_00001",
  "collection": "emails",
  "primary": "patrick@beispiel.com in Leak gefunden",
  "timestamp": "2025-06-22T12:34:56",
  "source": "leak",
  "import_batch": "import_20250622"
}
```

Format:
| Sammlung | ID-Format                            | Beispiel                               |
| -------- | ------------------------------------ | -------------------------------------- |
| emails   | EMAIL\_{quelle}*{yyyymmdd}*{nummer}  | EMAIL\_leak\_20250622\_00001           |
| news     | NEWS\_{quelle}*{yyyymmddhhmm}*{hash} | NEWS\_standard\_202506221130\_abcd1234 |
| personen | PERSON\_{name}\_{geburtstag}         | PERSON\_maxmustermann\_19911224        |
