# batch_insert.py
def batch_insert(collection, texts, metadatas=None, ids=None, embeddings=None):
    # texts: Liste von Texten (Pflicht)
    # metadatas: Liste von Dicts (Optional)
    # ids: Liste von Strings (Optional)
    # embeddings: Liste von Listen (Optional, sonst werden sie erzeugt)
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    if embeddings is None:
        embeddings = model.encode(texts).tolist()
    if metadatas is None:
        metadatas = [{} for _ in texts]
    if ids is None:
        ids = [f"doc_{abs(hash(text))}" for text in texts]
    collection.add(
        documents=texts,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings
    )
    return ids  # Liste der hinzugefügten IDs
