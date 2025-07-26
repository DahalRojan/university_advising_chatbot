import os
import json
import uuid
import hashlib
import datetime
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from langchain.text_splitter import RecursiveCharacterTextSplitter

QDRANT_COLLECTION = "student_docs"
PROCESSED_DIR = "data/processed"
META_FILE = "embeddings/metadata.json"

def hash_text(text):
    """Generates an MD5 hash for a given text to avoid re-processing."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def load_metadata():
    """Loads the metadata file tracking processed documents."""
    if os.path.exists(META_FILE):
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_metadata(meta):
    """Saves the updated metadata."""
    os.makedirs("embeddings", exist_ok=True)
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

def load_documents(folder_path):
    """Loads text documents from a specified folder."""
    docs = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as f:
                docs.append({"text": f.read(), "source": filename})
    return docs

def ingest():
    """
    Processes, chunks, and embeds text documents into a Qdrant vector database.
    """
    try:
        model = SentenceTransformer("BAAI/bge-small-en")
    except Exception as e:
        print(f"Failed to load BAAI/bge-small-en: {e}")
        print("Falling back to all-MiniLM-L6-v2")
        model = SentenceTransformer("all-MiniLM-L6-v2")
    client = QdrantClient(path="./vector_db")

    # Use a sophisticated, context-aware text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len,
        add_start_index=True,
    )

    # Ensure the Qdrant collection exists
    collection_names = [c.name for c in client.get_collections().collections]
    if QDRANT_COLLECTION not in collection_names:
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

        print(f"Processing and embedding: {doc['source']}")
        chunks = text_splitter.split_text(doc["text"])
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