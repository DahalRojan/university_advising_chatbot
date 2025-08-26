import torch
import os
import requests
import json
import re
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer, CrossEncoder

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../config/.env"))

API_URL = os.getenv("GROQ_API_URL")
API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("GROQ_MODEL")

# --- MODELS ---
try:
    print("Loading BAAI/bge-large-en-v1.5 for retrieval...")
    bi_encoder = SentenceTransformer("BAAI/bge-large-en-v1.5")
    print("Successfully loaded BAAI/bge-large-en-v1.5 for retrieval")
except Exception as e:
    print(f"Failed to load BAAI/bge-large-en-v1.5: {e}")
    print("Falling back to BAAI/bge-small-en")
    try:
        bi_encoder = SentenceTransformer("BAAI/bge-small-en")
    except Exception as e2:
        print(f"Failed to load BAAI/bge-small-en: {e2}")
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
COLLECTION = "university_docs_v2"

# Verify connection to Qdrant Cloud
try:
    collections = client.get_collections()
    collection_names = [c.name for c in collections.collections]
    if COLLECTION in collection_names:
        collection_info = client.get_collection(COLLECTION)
        print(f"[OK] Connected to Qdrant Cloud - Collection has {collection_info.points_count} documents")
    else:
        print(f"[ERROR] Collection '{COLLECTION}' not found in Qdrant Cloud")
except Exception as e:
    print(f"[ERROR] Failed to connect to Qdrant Cloud: {e}")

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
    Original retrieval function - maintained for backward compatibility
    """
    result = advanced_retrieve_with_confidence(query, top_k)
    if result.get("documents"):
        return result["documents"]
    else:
        return ["I was unable to find any information relevant to your query in the knowledge base."]

def advanced_retrieve_with_confidence(query: str, top_k: int = 5):
    """
    Enhanced retrieval with comprehensive confidence scoring and detailed analysis.
    Uses hybrid search (semantic + keyword) with cross-encoder reranking and confidence metrics.
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
        limit=top_k * 2,
        with_payload=True,
        with_vectors=False
    )
    
    # Keyword search results - temporarily disabled due to missing text index
    keyword_hits = []
    # TODO: Re-enable keyword filtering after creating text index in Qdrant Cloud
    
    print(f"[DEBUG] Enhanced Search Debug:")
    print(f"   Query: {query}")
    print(f"   Keywords extracted: {keywords}")
    print(f"   Semantic hits: {len(semantic_hits)}")
    print(f"   Keyword hits: {len(keyword_hits)}")
    
    # 4. Calculate retrieval confidence
    confidence_analysis = calculate_retrieval_confidence(
        semantic_hits, keyword_hits, query, hypothetical_answer, keywords
    )
    
    # 5. Merge and Re-rank
    all_hits = {hit.id: hit for hit in semantic_hits + keyword_hits}.values()
    candidate_docs = [hit.payload["text"] for hit in all_hits]
    
    print(f"   Total candidate docs: {len(candidate_docs)}")
    print(f"   Retrieval confidence: {confidence_analysis['confidence_score']:.2f}")
    
    if not candidate_docs:
        print("[ERROR] No candidate documents found")
        return {
            "documents": [],
            "documents_text": "",
            "confidence": confidence_analysis,
            "recommendation": {
                "action": "request_clarification",
                "message": "No relevant documents found - request more specific information",
                "should_use_fallback": True
            },
            "retrieval_details": {
                "semantic_hits_count": 0,
                "keyword_hits_count": 0,
                "final_docs_count": 0,
                "keywords_extracted": keywords,
                "hypothetical_answer": hypothetical_answer[:200] + "..." if len(hypothetical_answer) > 200 else hypothetical_answer
            }
        }

    # Re-rank using the more powerful Cross-Encoder (if available)
    if cross_encoder is not None:
        pairs = [[query, doc] for doc in candidate_docs]
        try:
            scores = cross_encoder.predict(pairs)
            reranking_confidence = calculate_reranking_confidence(scores)
        except Exception as e:
            print(f"Cross-encoder reranking failed: {e}")
            scores = [hit.score for hit in all_hits] if all_hits else []
            reranking_confidence = {"average_score": 0.5, "score_variance": 0.0}
    else:
        # Fallback: use semantic similarity scores
        scores = [hit.score for hit in all_hits] if all_hits else [1.0] * len(candidate_docs)
        reranking_confidence = {"average_score": 0.5, "score_variance": 0.0}
    
    scored_docs = list(zip(scores, candidate_docs))
    scored_docs.sort(reverse=True)
    
    relevant_docs = [doc for score, doc in scored_docs[:top_k]]
    final_scores = [score for score, doc in scored_docs[:top_k]]
    
    # 6. Generate comprehensive confidence report
    overall_confidence = calculate_overall_confidence(
        confidence_analysis, reranking_confidence, final_scores, query
    )
    
    # 7. Determine recommendation
    recommendation = determine_retrieval_recommendation(overall_confidence, query)
    
    print(f"   Final confidence: {overall_confidence['confidence_score']:.2f} ({overall_confidence['level']})")
    print(f"   Recommendation: {recommendation['action']}")
    
    return {
        "documents": relevant_docs,
        "documents_text": "\n".join(relevant_docs) if relevant_docs else "",
        "confidence": overall_confidence,
        "recommendation": recommendation,
        "retrieval_details": {
            "semantic_hits_count": len(semantic_hits),
            "keyword_hits_count": len(keyword_hits),
            "final_docs_count": len(relevant_docs),
            "keywords_extracted": keywords,
            "hypothetical_answer": hypothetical_answer[:200] + "..." if len(hypothetical_answer) > 200 else hypothetical_answer
        }
    }

def calculate_retrieval_confidence(semantic_hits, keyword_hits, query, hypothetical_answer, keywords):
    """Calculate comprehensive confidence scores for retrieval results"""
    
    confidence_factors = {
        "result_count": 0.0,
        "top_semantic_score": 0.0,
        "keyword_match_quality": 0.0,
        "query_specificity": 0.0,
        "document_diversity": 0.0,
        "semantic_keyword_alignment": 0.0
    }
    
    # Factor 1: Result count confidence
    total_results = len(semantic_hits) + len(keyword_hits)
    confidence_factors["result_count"] = min(total_results / 10.0, 1.0)  # Normalize to 0-1
    
    # Factor 2: Top semantic score
    if semantic_hits:
        top_score = semantic_hits[0].score if hasattr(semantic_hits[0], 'score') else 0.8
        confidence_factors["top_semantic_score"] = min(max(top_score, 0.0), 1.0)
    
    # Factor 3: Keyword match quality (simplified since keyword search is disabled)
    if keywords:
        # Check how many keywords appear in top semantic results
        keyword_matches = 0
        for hit in semantic_hits[:3]:  # Check top 3 results
            text_lower = hit.payload["text"].lower()
            matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
            keyword_matches += matches
        
        max_possible_matches = len(keywords) * min(3, len(semantic_hits))
        confidence_factors["keyword_match_quality"] = keyword_matches / max_possible_matches if max_possible_matches > 0 else 0.5
    else:
        confidence_factors["keyword_match_quality"] = 0.3  # No keywords extracted
    
    # Factor 4: Query specificity
    query_specificity = calculate_query_specificity(query)
    confidence_factors["query_specificity"] = query_specificity
    
    # Factor 5: Document diversity (avoid results from same source)
    if semantic_hits:
        sources = [hit.payload.get("source", "unknown") for hit in semantic_hits]
        unique_sources = len(set(sources))
        confidence_factors["document_diversity"] = min(unique_sources / 5.0, 1.0)  # Normalize to 0-1
    
    # Factor 6: Semantic-keyword alignment (simplified)
    confidence_factors["semantic_keyword_alignment"] = 0.5  # Default since keyword search disabled
    
    # Weighted confidence calculation
    weights = {
        "result_count": 0.15,
        "top_semantic_score": 0.30,  # Increased weight since we rely more on semantic
        "keyword_match_quality": 0.20,
        "query_specificity": 0.15,
        "document_diversity": 0.10,
        "semantic_keyword_alignment": 0.10  # Reduced weight
    }
    
    overall_confidence = sum(confidence_factors[factor] * weights[factor] 
                           for factor in confidence_factors)
    
    return {
        "confidence_score": overall_confidence,
        "factors": confidence_factors,
        "weights": weights,
        "threshold_met": overall_confidence > 0.6,
        "quality_level": categorize_confidence_level(overall_confidence)
    }

def calculate_query_specificity(query):
    """Calculate how specific/targeted a query is"""
    specificity_score = 0.0
    query_lower = query.lower()
    
    # Course code mentions (highly specific)
    course_codes = re.findall(r'\b[A-Z]{2,5}\s*\d{3,4}\b', query)
    if course_codes:
        specificity_score += 0.3
    
    # Specific academic terms
    specific_terms = ["prerequisite", "corequisite", "credit", "hour", "gpa", "semester"]
    term_matches = sum(1 for term in specific_terms if term in query_lower)
    specificity_score += min(term_matches * 0.1, 0.3)
    
    # Question specificity
    specific_question_words = ["what", "when", "where", "how", "which", "who"]
    if any(word in query_lower for word in specific_question_words):
        specificity_score += 0.2
    
    # Length factor (longer queries tend to be more specific)
    word_count = len(query.split())
    if word_count > 5:
        specificity_score += min((word_count - 5) * 0.05, 0.2)
    
    return min(specificity_score, 1.0)

def calculate_reranking_confidence(scores):
    """Calculate confidence based on reranking scores"""
    if not scores:
        return {"average_score": 0.0, "score_variance": 0.0, "top_score": 0.0}
    
    import numpy as np
    scores_array = np.array(scores)
    
    variance = float(np.var(scores_array))
    return {
        "average_score": float(np.mean(scores_array)),
        "score_variance": variance,
        "top_score": float(np.max(scores_array)),
        "score_distribution": "concentrated" if variance < 0.1 else "distributed"
    }

def calculate_overall_confidence(retrieval_confidence, reranking_confidence, final_scores, query):
    """Calculate overall confidence combining all factors"""
    
    # Base confidence from retrieval
    base_confidence = retrieval_confidence["confidence_score"]
    
    # Reranking confidence boost
    reranking_boost = 0.0
    if final_scores:
        avg_final_score = sum(final_scores) / len(final_scores)
        reranking_boost = min(avg_final_score * 0.2, 0.2)  # Max 0.2 boost
    
    # Query complexity factor
    complexity_factor = calculate_query_complexity_factor(query)
    
    # Combine all factors
    overall_score = base_confidence + reranking_boost + complexity_factor
    overall_score = min(max(overall_score, 0.0), 1.0)  # Clamp to 0-1
    
    return {
        "confidence_score": overall_score,
        "base_retrieval_confidence": base_confidence,
        "reranking_boost": reranking_boost,
        "complexity_factor": complexity_factor,
        "level": categorize_confidence_level(overall_score),
        "factors_breakdown": retrieval_confidence["factors"],
        "reranking_details": reranking_confidence,
        "recommendation_threshold": overall_score > 0.6
    }

def calculate_query_complexity_factor(query):
    """Calculate confidence adjustment based on query complexity"""
    complexity_score = 0.0
    query_lower = query.lower()
    
    # Simple, clear questions get a boost
    simple_patterns = [
        r'\bwhat\s+(is|are)\s+the\s+prerequisite',
        r'\bhow\s+many\s+credit',
        r'\bwhen\s+(is|are)\s+.*\s+offered',
        r'\bwhere\s+(can|do)\s+i\b'
    ]
    
    if any(re.search(pattern, query_lower) for pattern in simple_patterns):
        complexity_score += 0.1
    
    # Complex, multi-part questions get a penalty
    if len(query.split('?')) > 1 or len(query.split(' and ')) > 2:
        complexity_score -= 0.1
    
    # Very short queries (likely too vague) get a penalty
    if len(query.split()) < 3:
        complexity_score -= 0.15
    
    return complexity_score

def categorize_confidence_level(score):
    """Categorize confidence score into descriptive levels"""
    if score >= 0.8:
        return "high"
    elif score >= 0.6:
        return "medium"
    elif score >= 0.4:
        return "low"
    else:
        return "very_low"

def determine_retrieval_recommendation(confidence_analysis, query):
    """Determine recommendation based on confidence analysis"""
    confidence_score = confidence_analysis["confidence_score"]
    confidence_level = confidence_analysis["level"]
    
    recommendations = {
        "high": "proceed",
        "medium": "proceed_with_context",
        "low": "proceed_with_caution",
        "very_low": "request_clarification"
    }
    
    recommendation = recommendations[confidence_level]
    
    # Generate specific recommendation message
    messages = {
        "proceed": "High confidence in retrieved information - proceed with response",
        "proceed_with_context": "Medium confidence - proceed but acknowledge potential limitations",
        "proceed_with_caution": "Low confidence - provide response but suggest verification",
        "request_clarification": "Very low confidence - request more specific information from user"
    }
    
    return {
        "action": recommendation,
        "message": messages[recommendation],
        "confidence_score": confidence_score,
        "should_use_fallback": confidence_score < 0.6
    }
