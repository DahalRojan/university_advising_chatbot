#!/usr/bin/env python3
"""
Unified Retrieval System for Accurate Academic Advising

This module provides a simplified, reliable retrieval system that balances
year-awareness with comprehensive course information retrieval.

Key Features:
- Unified retrieval strategy combining year-aware and standard retrieval
- Intelligent fallback mechanisms
- Course information prioritization
- High accuracy with reduced complexity
"""

import os
import time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Load configuration
config_path = Path(__file__).parent.parent / "config" / ".env"
load_dotenv(config_path)

class UnifiedAcademicRetriever:
    """
    Unified retrieval system combining year-aware and standard retrieval
    for optimal accuracy and reliability
    """

    def __init__(self):
        self._standard_retriever = None
        self._year_aware_retriever = None

    def _get_standard_retriever(self):
        """Lazy load standard retriever"""
        if self._standard_retriever is None:
            from core.retriever import advanced_retrieve_with_confidence
            self._standard_retriever = advanced_retrieve_with_confidence
        return self._standard_retriever

    def _get_year_aware_retriever(self):
        """Lazy load year-aware retriever"""
        if self._year_aware_retriever is None:
            from core.retriever_year_aware import year_aware_retrieve_with_confidence
            self._year_aware_retriever = year_aware_retrieve_with_confidence
        return self._year_aware_retriever

    def retrieve_academic_content(
        self,
        query: str,
        enrolled_year: Optional[int] = None,
        academic_level: str = "undergraduate",
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Unified retrieval that intelligently combines year-aware and standard retrieval

        Args:
            query: User's academic question
            enrolled_year: Student's enrollment year (optional)
            academic_level: Academic level (undergraduate/graduate)
            top_k: Number of results to retrieve

        Returns:
            Combined retrieval results with optimal accuracy
        """
        print(f"[UNIFIED] Starting unified retrieval for: '{query[:50]}...'")
        start_time = time.time()

        # Strategy 1: Try year-aware retrieval if enrollment year is available
        year_aware_results = None
        year_aware_confidence = 0.0

        if enrolled_year:
            print(f"[UNIFIED] Attempting year-aware retrieval (year: {enrolled_year}, level: {academic_level})")
            try:
                year_aware_retriever = self._get_year_aware_retriever()
                year_aware_results = year_aware_retriever(
                    query,
                    enrolled_year=enrolled_year,
                    academic_level=academic_level,
                    top_k=top_k
                )
                year_aware_confidence = year_aware_results.get('confidence', {}).get('overall_confidence', 0.0)
                print(f"[UNIFIED] Year-aware confidence: {year_aware_confidence:.2f}")

            except Exception as e:
                print(f"[UNIFIED] Year-aware retrieval failed: {e}")
                year_aware_results = None
                year_aware_confidence = 0.0

        # Strategy 2: Always get standard retrieval as backup/supplement
        print(f"[UNIFIED] Getting standard retrieval")
        try:
            standard_retriever = self._get_standard_retriever()
            standard_results = standard_retriever(query, top_k=top_k)
            standard_confidence = standard_results.get('confidence', {}).get('confidence_score', 0.0)
            print(f"[UNIFIED] Standard confidence: {standard_confidence:.2f}")
        except Exception as e:
            print(f"[UNIFIED] Standard retrieval failed: {e}")
            standard_results = {"documents": [], "documents_text": "", "confidence": {"confidence_score": 0.0}}
            standard_confidence = 0.0

        # Strategy 3: Intelligent combination based on confidence and content
        final_results = self._combine_results(
            year_aware_results, year_aware_confidence,
            standard_results, standard_confidence,
            enrolled_year, query
        )

        retrieval_time = time.time() - start_time
        print(f"[UNIFIED] Unified retrieval completed in {retrieval_time:.3f}s")

        return final_results

    def _combine_results(
        self,
        year_aware_results: Optional[Dict],
        year_aware_confidence: float,
        standard_results: Dict,
        standard_confidence: float,
        enrolled_year: Optional[int],
        query: str
    ) -> Dict[str, Any]:
        """
        Intelligently combine year-aware and standard results for optimal accuracy
        """
        print(f"[UNIFIED] Combining results - YA confidence: {year_aware_confidence:.2f}, Standard: {standard_confidence:.2f}")

        # Case 1: High confidence year-aware results available
        if year_aware_results and year_aware_confidence >= 0.85:
            print(f"[UNIFIED] Using high-confidence year-aware results")
            return {
                "documents": year_aware_results.get("documents", []),
                "documents_text": year_aware_results.get("documents_text", ""),
                "confidence": {
                    "overall_confidence": year_aware_confidence,
                    "strategy": "year_aware_high_confidence",
                    "year_relevance": year_aware_results.get('confidence', {}).get('year_relevance', 0.0)
                },
                "metadata": {
                    **year_aware_results.get("metadata", {}),
                    "retrieval_strategy": "year_aware_primary"
                }
            }

        # Case 2: Good year-aware results but supplement with standard
        elif year_aware_results and year_aware_confidence >= 0.60:
            print(f"[UNIFIED] Combining good year-aware with standard results")
            return self._merge_results(year_aware_results, standard_results, "year_aware_supplemented")

        # Case 3: Year-aware results available but low confidence - blend carefully
        elif year_aware_results and year_aware_confidence >= 0.30:
            print(f"[UNIFIED] Blending low-confidence year-aware with standard results")
            return self._merge_results(standard_results, year_aware_results, "standard_with_year_context")

        # Case 4: No year-aware or very low confidence - use standard
        else:
            print(f"[UNIFIED] Using standard results (year-aware unavailable or very low confidence)")
            return {
                "documents": standard_results.get("documents", []),
                "documents_text": standard_results.get("documents_text", ""),
                "confidence": {
                    "overall_confidence": standard_confidence,
                    "strategy": "standard_fallback",
                    "year_relevance": 0.0
                },
                "metadata": {
                    **standard_results.get("retrieval_details", {}),
                    "retrieval_strategy": "standard_fallback"
                }
            }

    def _merge_results(self, primary_results: Dict, secondary_results: Dict, strategy: str) -> Dict[str, Any]:
        """
        Merge two sets of results, prioritizing the primary set
        """
        primary_docs = primary_results.get("documents", [])
        secondary_docs = secondary_results.get("documents", [])

        # Combine documents, removing duplicates while preserving order
        combined_docs = []
        seen_docs = set()

        # Add primary documents first
        for doc in primary_docs:
            doc_hash = hash(doc[:200])  # Use first 200 chars as identifier
            if doc_hash not in seen_docs:
                combined_docs.append(doc)
                seen_docs.add(doc_hash)

        # Add unique secondary documents
        for doc in secondary_docs:
            doc_hash = hash(doc[:200])
            if doc_hash not in seen_docs and len(combined_docs) < 15:  # Limit total documents
                combined_docs.append(doc)
                seen_docs.add(doc_hash)

        # Combine text
        combined_text = "\n\n".join(combined_docs)

        # Calculate combined confidence
        primary_confidence = primary_results.get("confidence", {}).get("overall_confidence", 0.0)
        if not primary_confidence:
            primary_confidence = primary_results.get("confidence", {}).get("confidence_score", 0.0)

        secondary_confidence = secondary_results.get("confidence", {}).get("overall_confidence", 0.0)
        if not secondary_confidence:
            secondary_confidence = secondary_results.get("confidence", {}).get("confidence_score", 0.0)

        # Weight towards primary results
        combined_confidence = (primary_confidence * 0.7) + (secondary_confidence * 0.3)

        return {
            "documents": combined_docs,
            "documents_text": combined_text,
            "confidence": {
                "overall_confidence": combined_confidence,
                "strategy": strategy,
                "primary_confidence": primary_confidence,
                "secondary_confidence": secondary_confidence,
                "year_relevance": primary_results.get('confidence', {}).get('year_relevance', 0.0)
            },
            "metadata": {
                "retrieval_strategy": strategy,
                "primary_docs": len(primary_docs),
                "secondary_docs": len(secondary_docs),
                "total_docs": len(combined_docs)
            }
        }

# Global instance for reuse
_unified_retriever = None

def get_unified_retriever() -> UnifiedAcademicRetriever:
    """Get singleton unified retriever instance"""
    global _unified_retriever
    if _unified_retriever is None:
        _unified_retriever = UnifiedAcademicRetriever()
    return _unified_retriever

def unified_retrieve(
    query: str,
    enrolled_year: Optional[int] = None,
    academic_level: str = "undergraduate",
    top_k: int = 10
) -> Dict[str, Any]:
    """
    Simplified interface for unified academic retrieval

    This function provides the best of both year-aware and standard retrieval
    with intelligent fallback and result combination strategies.
    """
    retriever = get_unified_retriever()
    return retriever.retrieve_academic_content(query, enrolled_year, academic_level, top_k)