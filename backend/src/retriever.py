import torch
import os
import requests
import json
import re
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer, CrossEncoder

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../configs/.env"))

API_URL = os.getenv("GROQ_API_URL")
API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("GROQ_MODEL")

# --- MODELS ---
try:
    bi_encoder = SentenceTransformer("BAAI/bge-small-en")
except Exception as e:
    print(f"Failed to load BAAI/bge-small-en: {e}")
    print("Falling back to all-MiniLM-L6-v2")
    bi_encoder = SentenceTransformer("all-MiniLM-L6-v2")

try:
    cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
except Exception as e:
    print(f"Failed to load cross-encoder: {e}")
    cross_encoder = None

# --- DATABASE ---
# Qdrant Cloud Configuration
CLUSTER_URL = os.getenv("QDRANT_CLOUD_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Validate required environment variables
if not CLUSTER_URL:
    raise ValueError("QDRANT_CLOUD_URL environment variable is required")
if not QDRANT_API_KEY:
    raise ValueError("QDRANT_API_KEY environment variable is required")

# Connect to Qdrant Cloud
client = QdrantClient(url=CLUSTER_URL, api_key=QDRANT_API_KEY)
COLLECTION = "student_docs"

# Verify connection to Qdrant Cloud
try:
    collections = client.get_collections()
    collection_names = [c.name for c in collections.collections]
    if COLLECTION in collection_names:
        collection_info = client.get_collection(COLLECTION)
        print(f"✅ Connected to Qdrant Cloud - Collection has {collection_info.points_count} documents")
    else:
        print(f"❌ Collection '{COLLECTION}' not found in Qdrant Cloud")
except Exception as e:
    print(f"❌ Failed to connect to Qdrant Cloud: {e}")

def extract_keywords(query: str) -> list[str]:
    """
    Extracts potential course codes and key terms from a query.
    Example: "prerequisites for CYSEC 301" -> ["CYSEC 301", "prerequisites"]
    """
    # Regex to find patterns like "CYSEC 301" or "CIS 180"
    course_codes = re.findall(r'\b[A-Z]{3,5}\s\d{3}\b', query, re.IGNORECASE)
    
    # You can add other important keywords to look for
    other_keywords = [word for word in ["prerequisite", "gpa", "deadline", "policy"] if word in query.lower()]
    
    return [code.upper() for code in course_codes] + other_keywords

def generate_hypothetical_answer(query: str) -> str:
    """
    Uses a direct LLM call to generate a hypothetical answer for semantic search (HyDE).
    """
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    hyde_prompt = f"Please write a short, ideal, factual paragraph that directly answers the following question. This is for a semantic search system. Do not say you don't know the answer.\n\nQuestion: {query}"
    messages = [{"role": "system", "content": "You generate hypothetical documents for a search system."}, {"role": "user", "content": hyde_prompt}]
    body = {"model": MODEL_NAME, "messages": messages, "temperature": 0.3}

    try:
        response = requests.post(API_URL, headers=headers, json=body)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"HyDE generation failed: {e}")
        return f"The policy regarding '{query}' states that..."

def advanced_retrieve(query: str, top_k: int = 5):
    """
    A hybrid retrieval process:
    1. Extract keywords for filtering.
    2. Generate a hypothetical answer for semantic search.
    3. Perform both a keyword-based filtered search and a semantic search.
    4. Merge results and re-rank with a Cross-Encoder.
    """
    # 1. Extract Keywords
    keywords = extract_keywords(query)
    
    # 2. Generate Hypothetical Answer (for semantic search)
    hypothetical_answer = generate_hypothetical_answer(query)
    query_vector = bi_encoder.encode(hypothetical_answer).tolist()
    
    # 3. Perform Searches
    # Semantic search results
    semantic_hits = client.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        limit=top_k * 2
    )
    
    # Keyword search results - temporarily disabled due to missing text index
    keyword_hits = []
    # TODO: Re-enable keyword filtering after creating text index in Qdrant Cloud
    # if keywords:
    #     # Create a filter that requires all keywords to be present
    #     must_clauses = [models.FieldCondition(key="text", match=models.MatchText(text=kw)) for kw in keywords]
    #     keyword_filter = models.Filter(must=must_clauses)
    #     
    #     keyword_hits = client.scroll(
    #         collection_name=COLLECTION,
    #         scroll_filter=keyword_filter,
    #         limit=top_k * 2
    #     )[0] # scroll returns a tuple (points, next_page_offset)

    # 4. Merge and Re-rank
    # Combine results and remove duplicates
    all_hits = {hit.id: hit for hit in semantic_hits + keyword_hits}.values()
    candidate_docs = [hit.payload["text"] for hit in all_hits]

    print(f"🔍 Search debug:")
    print(f"   Query: {query}")
    print(f"   Keywords extracted: {keywords}")
    print(f"   Semantic hits: {len(semantic_hits)}")
    print(f"   Keyword hits: {len(keyword_hits)}")
    print(f"   Total candidate docs: {len(candidate_docs)}")
    
    if not candidate_docs:
        print("❌ No candidate documents found")
        return ["I was unable to find any information relevant to your query in the knowledge base."]

    # Re-rank using the more powerful Cross-Encoder (if available)
    if cross_encoder is not None:
        pairs = [[query, doc] for doc in candidate_docs]
        scores = cross_encoder.predict(pairs)
    else:
        # Fallback: use semantic similarity scores
        scores = [1.0] * len(candidate_docs)
    
    scored_docs = list(zip(scores, candidate_docs))
    scored_docs.sort(reverse=True)
    
    relevant_docs = [doc for score, doc in scored_docs[:top_k]]
    
    if not relevant_docs:
        return ["After careful review, I could not find a document with a precise answer to your question."]

    return relevant_docs
