# export_import.py
import json

def export_collection(collection, out_path="export.json"):
    data = collection.get()
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return out_path

def import_to_collection(collection, in_path):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    with open(in_path, encoding="utf-8") as f:
        data = json.load(f)
    docs = data["documents"]
    metadatas = data["metadatas"]
    ids = data["ids"]
    embeddings = model.encode(docs).tolist()
    collection.add(
        documents=docs,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings
    )
    return len(docs)
