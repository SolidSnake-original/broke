# collection_management.py

def list_collections(client):
    # client: chromadb.Client()
    return client.list_collections()

def create_collection(client, name):
    return client.create_collection(name)

def drop_collection(client, name):
    client.delete_collection(name)
    return True
