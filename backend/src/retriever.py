from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

client = QdrantClient(path="./vector_db")
model = SentenceTransformer("BAAI/bge-small-en")
COLLECTION = "student_docs"

def retrieve_similar_docs(query, top_k=3):
    query_vector = model.encode(query).tolist()
    search_result = client.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        limit=top_k
    )
    return [point.payload["text"] for point in search_result]


