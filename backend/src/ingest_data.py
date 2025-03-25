import os
import json
import uuid
import hashlib
import datetime
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance

QDRANT_COLLECTION = "student_docs"
PROCESSED_DIR = "data/processed"
META_FILE = "embeddings/metadata.json"

def hash_text(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def load_metadata():
    if os.path.exists(META_FILE):
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_metadata(meta):
    os.makedirs("embeddings", exist_ok=True)
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

def load_documents(folder_path):
    docs = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as f:
                docs.append({"text": f.read(), "source": filename})
    return docs

def chunk_text(text, size=500, overlap=50):
    chunks = []
    for i in range(0, len(text), size - overlap):
        chunks.append(text[i:i + size])
    return chunks

def ingest():
    model = SentenceTransformer("BAAI/bge-small-en")
    client = QdrantClient(path="./vector_db")

    if QDRANT_COLLECTION not in client.get_collections().collections:
        client.recreate_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )

    metadata = load_metadata()
    existing_hashes = {m["hash"] for m in metadata}

    documents = load_documents(PROCESSED_DIR)

    for doc in documents:
        doc_hash = hash_text(doc["text"])
        if doc_hash in existing_hashes:
            print(f"✅ Skipping (already embedded): {doc['source']}")
            continue

        chunks = chunk_text(doc["text"])
        embeddings = model.encode(chunks)
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=emb.tolist(),
                payload={"text": chunk, "source": doc["source"]}
            )
            for chunk, emb in zip(chunks, embeddings)
        ]
        client.upsert(collection_name=QDRANT_COLLECTION, points=points)
        print(f"✅ Embedded and added to Qdrant: {doc['source']}")

        metadata.append({
            "filename": doc["source"],
            "hash": doc_hash,
            "embedded_on": datetime.datetime.now().isoformat()
        })

    save_metadata(metadata)
    print("✅ All done!")

if __name__ == "__main__":
    ingest()
