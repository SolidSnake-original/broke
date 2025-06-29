import numpy as np
from sentence_transformers import SentenceTransformer
import db_id_manager

def batch_insert(faiss_index, texts, collection, entity_type="EMAIL", metadatas=None, source=None, import_batch=None):
    """
    Fügt mehrere Texte + Metadaten in FAISS und Registry ein.
    faiss_index: geöffneter FAISS-Index (IndexFlatL2 etc.)
    texts: Liste von Strings
    collection: Collection-Name (z. B. 'emails')
    entity_type: Typ der Entities (z. B. 'EMAIL')
    metadatas: Liste von Dicts (optional)
    source: String (optional)
    import_batch: String (optional)
    """
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(texts)
    if metadatas is None:
        metadatas = [{} for _ in texts]
    vektor_indices = []
    ids = []
    # Insert Batch in FAISS und Registry
    for i, (text, meta) in enumerate(zip(texts, metadatas)):
        emb = np.array([embeddings[i]]).astype("float32")
        faiss_index.add(emb)
        vektor_index = faiss_index.ntotal - 1  # Index des gerade eingefügten Vektors
        vektor_indices.append(vektor_index)
        doc_id = db_id_manager.generate_id(
            collection=collection,
            entity_type=entity_type,
            source=source if source else meta.get("quelle"),
            unique_part=None
        )
        ids.append(doc_id)
        db_id_manager.add_entry(
            id=doc_id,
            collection=collection,
            entity_type=entity_type,
            primary_value=text,
            metadata=meta,
            source=source if source else meta.get("quelle"),
            import_batch=import_batch if import_batch else "batch_insert",
            vektor_index=vektor_index
        )
    return ids, vektor_indices  # Rückgabe für Kontrolle/Weiterverarbeitung
