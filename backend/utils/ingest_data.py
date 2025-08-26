import os
import json
import uuid
import hashlib
import datetime
import time
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../configs/.env"))

# Qdrant Cloud Configuration
CLUSTER_URL = os.getenv("QDRANT_CLOUD_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Validate required environment variables
if not CLUSTER_URL:
    raise ValueError("QDRANT_CLOUD_URL environment variable is required")
if not QDRANT_API_KEY:
    raise ValueError("QDRANT_API_KEY environment variable is required")

QDRANT_COLLECTION="university_docs_v2"

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

def upload_points_with_retry(client, collection_name, points, max_retries=3, batch_size=50):
    """
    Upload points to Qdrant with retry mechanism and batch processing
    """
    total_points = len(points)
    print(f"[UPLOAD] Uploading {total_points} chunks in batches of {batch_size}")
    
    uploaded = 0
    for i in range(0, total_points, batch_size):
        batch = points[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_points + batch_size - 1) // batch_size
        
        print(f"  [BATCH] Batch {batch_num}/{total_batches}: {len(batch)} chunks")
        
        for attempt in range(max_retries):
            try:
                client.upsert(collection_name=collection_name, points=batch)
                uploaded += len(batch)
                print(f"  [OK] Batch {batch_num} uploaded successfully ({uploaded}/{total_points} total)")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # Exponential backoff
                    print(f"  [RETRY] Batch {batch_num} failed (attempt {attempt + 1}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"  [ERROR] Batch {batch_num} failed after {max_retries} attempts: {str(e)}")
                    raise e
        
        # Small delay between batches to avoid overwhelming the server
        if i + batch_size < total_points:
            time.sleep(0.5)
    
    return uploaded

def ingest():
    """
    Processes, chunks, and embeds text documents into a Qdrant vector database.
    """
    try:
        print("Loading BAAI/bge-large-en-v1.5 embedding model...")
        model = SentenceTransformer("BAAI/bge-large-en-v1.5")
        print("Successfully loaded BAAI/bge-large-en-v1.5")
    except Exception as e:
        print(f"Failed to load BAAI/bge-large-en-v1.5: {e}")
        print("Falling back to BAAI/bge-small-en")
        try:
            model = SentenceTransformer("BAAI/bge-small-en")
        except Exception as e2:
            print(f"Failed to load BAAI/bge-small-en: {e2}")
            print("Falling back to all-MiniLM-L6-v2")
            model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Create Qdrant client with increased timeout
    client = QdrantClient(
        url=CLUSTER_URL, 
        api_key=QDRANT_API_KEY,
        timeout=120,  # 2 minutes timeout
    )

    # Use a sophisticated, context-aware text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len,
        add_start_index=True,
    )

    # Get embedding dimension from the model
    embedding_dimension = model.get_sentence_embedding_dimension()
    print(f"Model embedding dimension: {embedding_dimension}")
    
    # Verify Qdrant Cloud collection exists and check dimensions
    collection_names = [c.name for c in client.get_collections().collections]
    if QDRANT_COLLECTION not in collection_names:
        print(f"❌ Collection '{QDRANT_COLLECTION}' not found in Qdrant Cloud")
        print("💡 Please create the collection first or use the cloud ingestion script")
        return
    else:
        collection_info = client.get_collection(QDRANT_COLLECTION)
        existing_dimension = collection_info.config.params.vectors.size
        print(f"Existing collection dimension: {existing_dimension}")
        print(f"New model dimension: {embedding_dimension}")
        
        if existing_dimension != embedding_dimension:
            print(f"⚠️  WARNING: Vector dimension mismatch!")
            print(f"   Existing collection: {existing_dimension}D")
            print(f"   New model: {embedding_dimension}D")
            print(f"   You'll need to recreate the collection or use a new collection name")
            return
        
        print(f"✅ Using Qdrant Cloud collection with {collection_info.points_count} existing documents")

    metadata = load_metadata()
    existing_hashes = {m["hash"] for m in metadata}
    documents = load_documents(PROCESSED_DIR)

    total_docs = len(documents)
    print(f"📚 Found {total_docs} documents to process")

    for doc_idx, doc in enumerate(documents, 1):
        doc_hash = hash_text(doc["text"])
        if doc_hash in existing_hashes:
            print(f"✅ [{doc_idx}/{total_docs}] Skipping (already embedded): {doc['source']}")
            continue

        print(f"🔄 [{doc_idx}/{total_docs}] Processing: {doc['source']}")
        print(f"📄 Document size: {len(doc['text']):,} characters")
        
        # Split into chunks
        chunks = text_splitter.split_text(doc["text"])
        print(f"✂️  Split into {len(chunks)} chunks")
        
        # Generate embeddings
        print(f"🧠 Generating embeddings...")
        embeddings = model.encode(chunks, show_progress_bar=True)
        
        # Create points
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=emb.tolist(),
                payload={"text": chunk, "source": doc["source"]}
            )
            for chunk, emb in zip(chunks, embeddings)
        ]
        
        # Upload with retry and batch processing
        try:
            uploaded_count = upload_points_with_retry(client, QDRANT_COLLECTION, points)
            print(f"✅ [{doc_idx}/{total_docs}] Successfully uploaded {uploaded_count} chunks for {doc['source']}")
            
            # Update metadata
            metadata.append({
                "filename": doc["source"],
                "hash": doc_hash,
                "embedded_on": datetime.datetime.now().isoformat(),
                "chunks_count": len(chunks)
            })
            save_metadata(metadata)
            
        except Exception as e:
            print(f"❌ [{doc_idx}/{total_docs}] Failed to upload {doc['source']}: {str(e)}")
            print("⏭️  Continuing with next document...")
            continue

    print("✅ All documents processed!")
    
    # Final collection status
    try:
        final_info = client.get_collection(QDRANT_COLLECTION)
        print(f"📊 Final collection status: {final_info.points_count} total points")
    except Exception as e:
        print(f"⚠️  Could not get final collection status: {e}")

if __name__ == "__main__":
    ingest()