# src/retriever.py
import torch
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

client = QdrantClient(path="./vector_db")
model = SentenceTransformer("BAAI/bge-small-en")
COLLECTION = "student_docs"

def is_context_relevant(query, context, threshold=0.5):
    """Determine if a context is relevant to the query based on semantic similarity."""
    if not context or context.strip() == "":
        return False
        
    query_embedding = model.encode(query)
    context_embedding = model.encode(context)
    
    # Calculate cosine similarity
    similarity = torch.nn.functional.cosine_similarity(
        torch.tensor(query_embedding).unsqueeze(0),
        torch.tensor(context_embedding).unsqueeze(0)
    ).item()
    
    return similarity > threshold

def retrieve_similar_docs(query, top_k=5, min_score=0.6):
    """Retrieve similar documents and filter by relevance."""
    query_vector = model.encode(query).tolist()
    
    # Get more candidates initially
    search_result = client.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        limit=top_k * 2  # Get more candidates to filter from
    )
    
    # Initial filtering by score
    filtered_results = [point for point in search_result if point.score > min_score]
    
    # Extract text from search results
    candidate_docs = [
        {"text": point.payload["text"], "source": point.payload["source"], "score": point.score}
        for point in filtered_results
    ]
    
    # Secondary filtering with is_context_relevant
    relevant_docs = [
        doc for doc in candidate_docs 
        if is_context_relevant(query, doc["text"])
    ]
    
    # If no documents are relevant, return explicit message
    if not relevant_docs:
        return ["I don't have specific information relevant to your query in my knowledge base."]
    
    # Sort by score and take top_k
    relevant_docs.sort(key=lambda x: x["score"], reverse=True)
    relevant_docs = relevant_docs[:top_k]
    
    # Format docs with source citations
    formatted_docs = []
    for i, doc in enumerate(relevant_docs):
        formatted_docs.append(f"[Source: {doc['source']}]\n{doc['text']}")
    
    return formatted_docs