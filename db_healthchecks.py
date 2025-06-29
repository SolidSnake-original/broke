# healthchecks.py

def chroma_healthcheck(client, collection_name):
    # Prüft Existenz und gibt Eintragszahl zurück
    colls = client.list_collections()
    if collection_name not in [c.name for c in colls]:
        return False, 0
    col = client.get_collection(collection_name)
    docs = col.get()
    count = len(docs['ids'])
    return True, count

def database_stats(client):
    info = {}
    colls = client.list_collections()
    for c in colls:
        col = client.get_collection(c.name)
        docs = col.get()
        info[c.name] = len(docs['ids'])
    return info  # dict {collection_name: n_entries}
