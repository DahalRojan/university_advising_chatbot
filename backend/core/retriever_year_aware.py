#!/usr/bin/env python3
"""
Year-Aware Academic Retrieval System

Enhanced retrieval system that provides year-specific academic information
based on student enrollment year and catalog context.

Features:
- Year-filtered document retrieval
- Priority-based ranking by enrollment year
- Fallback strategies for missing year data
- Academic level filtering (undergraduate/graduate)
"""

import torch
import os
import re
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer, CrossEncoder

# Load environment variables
config_path = os.path.join(os.path.dirname(__file__), "../config/.env")
load_dotenv(config_path)

# Configuration
CLUSTER_URL = os.getenv("QDRANT_CLOUD_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
YEAR_AWARE_COLLECTION = "university_docs_year_aware_v1"
FALLBACK_COLLECTION = "university_docs_v2"  # Original collection for fallback

class YearAwareRetriever:
    """Advanced retrieval system with year-specific academic context"""

    def __init__(self):
        self.bi_encoder = self._load_embedding_model()
        self.cross_encoder = self._load_cross_encoder()
        self.client = self._setup_qdrant_client()

    def _load_embedding_model(self):
        """Load the embedding model (same as original)"""
        try:
            print("Loading BAAI/bge-large-en-v1.5 for year-aware retrieval...")
            bi_encoder = SentenceTransformer("BAAI/bge-large-en-v1.5")
            print("Successfully loaded BAAI/bge-large-en-v1.5")
            return bi_encoder
        except Exception as e:
            print(f"Failed to load BAAI/bge-large-en-v1.5: {e}")
            try:
                return SentenceTransformer("BAAI/bge-small-en")
            except Exception as e2:
                print(f"Failed to load BAAI/bge-small-en: {e2}")
                return SentenceTransformer("all-MiniLM-L6-v2")

    def _load_cross_encoder(self):
        """Load cross-encoder for reranking"""
        try:
            return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        except Exception as e:
            print(f"Failed to load cross-encoder: {e}")
            return None

    def _setup_qdrant_client(self):
        """Setup Qdrant client"""
        if not CLUSTER_URL or not QDRANT_API_KEY:
            raise ValueError("QDRANT_CLOUD_URL and QDRANT_API_KEY environment variables are required")
        return QdrantClient(url=CLUSTER_URL, api_key=QDRANT_API_KEY)

    def get_query_embedding(self, query: str):
        """Generate embedding for a query string"""
        try:
            if self.bi_encoder is None:
                return None
            embedding = self.bi_encoder.encode([query], convert_to_tensor=False)
            return embedding[0] if len(embedding) > 0 else None
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            return None

    def get_applicable_catalog_year(self, enrolled_year: Optional[int]) -> str:
        """
        Determine the applicable catalog year based on enrollment year

        Args:
            enrolled_year: Year the student enrolled (e.g., 2023)

        Returns:
            Academic year string (e.g., "2023-2024")
        """
        if not enrolled_year:
            # Default to current academic year
            current_year = datetime.now().year
            current_month = datetime.now().month

            # Academic year starts in August/September
            if current_month >= 8:
                return f"{current_year}-{current_year + 1}"
            else:
                return f"{current_year - 1}-{current_year}"

        # Convert enrollment year to academic year format
        return f"{enrolled_year}-{enrolled_year + 1}"

    def build_year_filters(self, enrolled_year: Optional[int], academic_level: str) -> List[Dict]:
        """
        Build filtering conditions for year-aware retrieval

        Returns list of filter conditions in priority order
        """
        filters = []

        if enrolled_year:
            target_year = self.get_applicable_catalog_year(enrolled_year)

            # Primary filter: Exact year and level match
            filters.append({
                "filter": models.Filter(
                    must=[
                        models.FieldCondition(
                            key="academic_year",
                            match=models.MatchValue(value=target_year)
                        ),
                        models.FieldCondition(
                            key="catalog_type",
                            match=models.MatchValue(value=academic_level)
                        )
                    ]
                ),
                "priority": 1.0,
                "description": f"Exact match: {target_year} {academic_level}"
            })

            # Secondary filter: Adjacent years with same level
            adjacent_years = [
                f"{enrolled_year - 1}-{enrolled_year}",
                f"{enrolled_year + 1}-{enrolled_year + 2}"
            ]

            for adj_year in adjacent_years:
                filters.append({
                    "filter": models.Filter(
                        must=[
                            models.FieldCondition(
                                key="academic_year",
                                match=models.MatchValue(value=adj_year)
                            ),
                            models.FieldCondition(
                                key="catalog_type",
                                match=models.MatchValue(value=academic_level)
                            )
                        ]
                    ),
                    "priority": 0.8,
                    "description": f"Adjacent year: {adj_year} {academic_level}"
                })

        # Fallback filter: Just academic level
        filters.append({
            "filter": models.Filter(
                must=[
                    models.FieldCondition(
                        key="catalog_type",
                        match=models.MatchValue(value=academic_level)
                    )
                ]
            ),
            "priority": 0.6,
            "description": f"Level only: {academic_level}"
        })

        # Emergency fallback: No filters (get anything)
        filters.append({
            "filter": None,
            "priority": 0.3,
            "description": "No filters (emergency fallback)"
        })

        return filters

    def retrieve_with_year_awareness(
        self,
        query: str,
        enrolled_year: Optional[int] = None,
        academic_level: str = "undergraduate",
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Main retrieval function with year-aware filtering

        Args:
            query: User's question
            enrolled_year: Year student enrolled (e.g., 2023)
            academic_level: "undergraduate" or "graduate"
            top_k: Number of results to return

        Returns:
            Dictionary with documents, confidence scores, and metadata
        """
        print(f"Year-aware search: '{query}' (enrolled: {enrolled_year}, level: {academic_level})")

        # Generate query embedding
        print(f"      [ENCODE] Encoding query: '{query[:60]}{'...' if len(query) > 60 else ''}'")
        query_vector = self.bi_encoder.encode(query).tolist()
        print(f"      [SUCCESS] Generated embedding: {len(query_vector)} dimensions")
        print(f"      [STATS] Embedding values (first 10): {[round(val, 4) for val in query_vector[:10]]}")
        print(f"      [RANGE] Embedding range: [{round(min(query_vector), 4)}, {round(max(query_vector), 4)}]")
        
        # Calculate embedding norm for additional insight
        import numpy as np
        embedding_norm = np.linalg.norm(query_vector)
        print(f"      [NORM] Embedding norm: {round(embedding_norm, 4)}")

        # Build filtering strategy
        year_filters = self.build_year_filters(enrolled_year, academic_level)

        all_results = []
        retrieval_attempts = []

        # Try each filter in priority order
        for filter_config in year_filters:
            try:
                search_params = {
                    "collection_name": YEAR_AWARE_COLLECTION,
                    "query_vector": query_vector,
                    "limit": top_k * 2,  # Get more for reranking
                    "with_payload": True,
                    "with_vectors": False
                }

                if filter_config["filter"]:
                    search_params["query_filter"] = filter_config["filter"]

                hits = self.client.search(**search_params)

                if hits:
                    # Apply priority weight to scores and store in metadata
                    for hit in hits:
                        # Store priority metadata in payload
                        hit.payload["_priority_weight"] = filter_config["priority"]
                        hit.payload["_adjusted_score"] = hit.score * filter_config["priority"]

                    all_results.extend(hits)
                    retrieval_attempts.append({
                        "filter": filter_config["description"],
                        "hits": len(hits),
                        "priority": filter_config["priority"]
                    })

                    # If we got good results from high-priority filter, we can stop early
                    if filter_config["priority"] >= 0.8 and len(hits) >= top_k:
                        print(f"Got {len(hits)} results from high-priority filter")
                        break

            except Exception as e:
                print(f"Filter failed ({filter_config['description']}): {e}")
                retrieval_attempts.append({
                    "filter": filter_config["description"],
                    "hits": 0,
                    "error": str(e),
                    "priority": filter_config["priority"]
                })
                continue

        # Fallback to original collection if year-aware collection failed
        if not all_results:
            print("Falling back to original collection...")
            try:
                fallback_hits = self.client.search(
                    collection_name=FALLBACK_COLLECTION,
                    query_vector=query_vector,
                    limit=top_k,
                    with_payload=True
                )

                for hit in fallback_hits:
                    hit.payload["_priority_weight"] = 0.2  # Low priority for fallback
                    hit.payload["_adjusted_score"] = hit.score * 0.2

                all_results.extend(fallback_hits)
                retrieval_attempts.append({
                    "filter": "Fallback collection",
                    "hits": len(fallback_hits),
                    "priority": 0.2
                })

            except Exception as e:
                print(f"Fallback collection also failed: {e}")

        if not all_results:
            return self._create_empty_response(query, enrolled_year, academic_level, retrieval_attempts)

        # Remove duplicates and sort by adjusted score
        unique_results = {}
        for hit in all_results:
            text_hash = hash(hit.payload.get("text", ""))
            adjusted_score = hit.payload.get("_adjusted_score", hit.score)
            if text_hash not in unique_results or adjusted_score > unique_results[text_hash].payload.get("_adjusted_score", unique_results[text_hash].score):
                unique_results[text_hash] = hit

        sorted_results = sorted(unique_results.values(), key=lambda x: x.payload.get("_adjusted_score", x.score), reverse=True)

        # Rerank top results if cross-encoder is available
        final_results = self._rerank_results(query, sorted_results[:top_k * 2], top_k)

        # Extract documents and calculate confidence
        documents = [hit.payload["text"] for hit in final_results]
        confidence_analysis = self._calculate_year_aware_confidence(
            final_results, enrolled_year, academic_level, retrieval_attempts
        )

        print(f"Retrieved {len(documents)} documents (confidence: {confidence_analysis['overall_confidence']:.2f})")

        return {
            "documents": documents,
            "documents_text": "\n\n".join(documents),
            "confidence": confidence_analysis,
            "year_context": {
                "enrolled_year": enrolled_year,
                "applicable_catalog": self.get_applicable_catalog_year(enrolled_year),
                "academic_level": academic_level,
                "retrieval_attempts": retrieval_attempts
            },
            "metadata": {
                "total_results": len(final_results),
                "year_aware_results": len([r for r in final_results if r.payload.get('_priority_weight', 1.0) > 0.5]),
                "fallback_results": len([r for r in final_results if r.payload.get('_priority_weight', 1.0) <= 0.5]),
                "search_strategy": "year_aware_priority_filtering"
            }
        }

    def _rerank_results(self, query: str, results: List, top_k: int) -> List:
        """Rerank results using cross-encoder if available"""
        if not self.cross_encoder or len(results) <= 1:
            return results[:top_k]

        try:
            # Prepare pairs for cross-encoder
            pairs = [[query, hit.payload["text"]] for hit in results]
            scores = self.cross_encoder.predict(pairs)

            # Combine cross-encoder scores with priority weights
            for i, hit in enumerate(results):
                cross_score = scores[i]
                priority_weight = hit.payload.get('_priority_weight', 1.0)
                hit.payload["_final_score"] = cross_score * priority_weight

            # Sort by final score
            results.sort(key=lambda x: x.payload.get("_final_score", x.score), reverse=True)

        except Exception as e:
            print(f"Cross-encoder reranking failed: {e}")

        return results[:top_k]

    def _calculate_year_aware_confidence(
        self,
        results: List,
        enrolled_year: Optional[int],
        academic_level: str,
        retrieval_attempts: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate confidence metrics for year-aware retrieval"""

        if not results:
            return {
                "overall_confidence": 0.0,
                "year_relevance": 0.0,
                "level_match": 0.0,
                "temporal_accuracy": 0.0,
                "recommendation": "no_results_found"
            }

        # Calculate year relevance
        year_relevance = 0.0
        if enrolled_year:
            target_year = self.get_applicable_catalog_year(enrolled_year)
            matching_year_results = sum(1 for r in results
                                      if r.payload.get("academic_year") == target_year)
            year_relevance = matching_year_results / len(results)

        # Calculate level match
        matching_level_results = sum(1 for r in results
                                   if r.payload.get("catalog_type") == academic_level)
        level_match = matching_level_results / len(results)

        # Calculate temporal accuracy (how recent/relevant the data is)
        temporal_scores = []
        current_year = datetime.now().year
        for result in results:
            year_str = result.payload.get("academic_year", "")
            try:
                doc_year = int(year_str.split('-')[0]) if year_str else current_year - 5
                years_old = current_year - doc_year
                temporal_score = max(0, 1 - (years_old * 0.1))  # Decay by 10% per year
                temporal_scores.append(temporal_score)
            except:
                temporal_scores.append(0.5)  # Neutral score for unknown years

        temporal_accuracy = sum(temporal_scores) / len(temporal_scores) if temporal_scores else 0.0

        # Calculate overall confidence
        weights = {
            "year_relevance": 0.4,
            "level_match": 0.3,
            "temporal_accuracy": 0.2,
            "base_retrieval": 0.1
        }

        base_retrieval_score = min(len(results) / 5.0, 1.0)  # Normalize to [0,1]

        overall_confidence = (
            weights["year_relevance"] * year_relevance +
            weights["level_match"] * level_match +
            weights["temporal_accuracy"] * temporal_accuracy +
            weights["base_retrieval"] * base_retrieval_score
        )

        # Determine recommendation
        if overall_confidence >= 0.8:
            recommendation = "high_confidence_year_specific"
        elif overall_confidence >= 0.6:
            recommendation = "moderate_confidence_some_year_data"
        elif overall_confidence >= 0.4:
            recommendation = "low_confidence_mixed_years"
        else:
            recommendation = "very_low_confidence_fallback_data"

        return {
            "overall_confidence": round(overall_confidence, 3),
            "year_relevance": round(year_relevance, 3),
            "level_match": round(level_match, 3),
            "temporal_accuracy": round(temporal_accuracy, 3),
            "recommendation": recommendation,
            "confidence_factors": {
                "target_year_matches": sum(1 for r in results if r.payload.get("academic_year") == self.get_applicable_catalog_year(enrolled_year)),
                "level_matches": matching_level_results,
                "total_results": len(results),
                "retrieval_strategy_attempts": len(retrieval_attempts)
            }
        }

    def _create_empty_response(self, query: str, enrolled_year: Optional[int],
                             academic_level: str, retrieval_attempts: List[Dict]) -> Dict[str, Any]:
        """Create response when no documents are found"""
        return {
            "documents": [],
            "documents_text": "",
            "confidence": {
                "overall_confidence": 0.0,
                "year_relevance": 0.0,
                "level_match": 0.0,
                "temporal_accuracy": 0.0,
                "recommendation": "no_documents_found"
            },
            "year_context": {
                "enrolled_year": enrolled_year,
                "applicable_catalog": self.get_applicable_catalog_year(enrolled_year),
                "academic_level": academic_level,
                "retrieval_attempts": retrieval_attempts
            },
            "metadata": {
                "total_results": 0,
                "year_aware_results": 0,
                "fallback_results": 0,
                "search_strategy": "year_aware_priority_filtering",
                "failure_reason": "no_matching_documents"
            }
        }

# Global instance for backward compatibility
_year_aware_retriever = None

def get_year_aware_retriever() -> YearAwareRetriever:
    """Get singleton instance of year-aware retriever"""
    global _year_aware_retriever
    if _year_aware_retriever is None:
        _year_aware_retriever = YearAwareRetriever()
    return _year_aware_retriever

def year_aware_retrieve(
    query: str,
    enrolled_year: Optional[int] = None,
    academic_level: str = "undergraduate",
    top_k: int = 5
) -> List[str]:
    """
    Simplified interface for year-aware retrieval (backward compatibility)

    Returns:
        List of document texts
    """
    retriever = get_year_aware_retriever()
    result = retriever.retrieve_with_year_awareness(query, enrolled_year, academic_level, top_k)
    return result.get("documents", [])

def year_aware_retrieve_with_confidence(
    query: str,
    enrolled_year: Optional[int] = None,
    academic_level: str = "undergraduate",
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Full interface for year-aware retrieval with all metadata

    Returns:
        Complete response dictionary with documents, confidence, and metadata
    """
    retriever = get_year_aware_retriever()
    return retriever.retrieve_with_year_awareness(query, enrolled_year, academic_level, top_k)